import logging
import os
import yaml
from concurrent.futures import ThreadPoolExecutor
from ipaddress import ip_network

from genie.testbed import load as genie_load

log = logging.getLogger(__name__)

_DIR          = os.path.dirname(os.path.abspath(__file__))
_TESTBED_PATH = os.path.abspath(os.path.join(_DIR, '../testbed.yaml'))
_FABRIC_PATH  = os.path.abspath(os.path.join(_DIR, '../../TF_NETASCODE/data/fabric.yaml'))
_HOSTS_FILE   = os.path.join(_DIR, 'lisp_hosts.yaml')


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_control_plane_nodes(fabric_path):
    log.info('Loading control-plane nodes from %s', fabric_path)
    with open(fabric_path) as fh:
        data = yaml.safe_load(fh)
    nodes = []
    for d in data['catalyst_center']['inventory']['devices']:
        name  = d['name'].split('.')[0]
        roles = d.get('fabric_roles', [])
        if 'CONTROL_PLANE_NODE' in roles:
            nodes.append(name)
    log.info('Found %d control-plane node(s): %s', len(nodes), nodes)
    return nodes


def _collect_host_eids(device):
    """Return list of {ip, iid} dicts for all IPv4 /32 EIDs on a control-plane node."""
    log.info('[%s] Running "show lisp site"', device.name)
    parsed = device.parse('show lisp site')
    hosts  = []
    for lisp_id, lisp_data in parsed.get('lisp_id', {}).items():
        for site, site_data in lisp_data.get('site_name', {}).items():
            for iid, iid_data in site_data.get('instance_id', {}).items():
                for eid_prefix, eid_data in iid_data.get('eid_prefix', {}).items():
                    if ':' in eid_prefix:
                        continue
                    try:
                        net = ip_network(eid_prefix, strict=False)
                    except ValueError:
                        continue
                    if net.prefixlen != 32:
                        continue
                    hosts.append({'ip': str(net.network_address), 'iid': iid})
    log.info('[%s] Collected %d /32 host EID(s)', device.name, len(hosts))
    return hosts


# ---------------------------------------------------------------------------
# Public API — called from Blitz trigger via 'api' action
# ---------------------------------------------------------------------------

def collect_lisp_hosts(
    testbed_path=_TESTBED_PATH,
    fabric_path=_FABRIC_PATH,
    output_file=_HOSTS_FILE,
):
    """Connect to LISP control-plane nodes, collect IPv4 /32 EIDs,
    save IPs to *output_file* (YAML), and return the list of IPs.

    Intended to be called from a Blitz 'api' action before ping tests.
    Opens its own connections to the control-plane nodes independently of
    the trigger's already-connected devices.
    """
    cp_nodes = _load_control_plane_nodes(fabric_path)
    if not cp_nodes:
        raise RuntimeError('No CONTROL_PLANE_NODE devices found in fabric YAML')

    testbed = genie_load(testbed_path)

    errors = {}
    def _connect(name):
        try:
            testbed.devices[name].connect(via='cli', log_stdout=False)
        except Exception as e:
            errors[name] = str(e)

    with ThreadPoolExecutor(max_workers=len(cp_nodes)) as pool:
        pool.map(_connect, cp_nodes)

    if errors:
        raise RuntimeError(f'Failed to connect to: {errors}')

    all_hosts = []
    for name in cp_nodes:
        all_hosts.extend(_collect_host_eids(testbed.devices[name]))

    for name in cp_nodes:
        try:
            testbed.devices[name].disconnect()
        except Exception:
            pass

    # Deduplicate by IP
    seen, hosts = set(), []
    for h in sorted(all_hosts, key=lambda x: x['ip']):
        if h['ip'] not in seen:
            seen.add(h['ip'])
            hosts.append(h)

    ips = [h['ip'] for h in hosts]
    log.info('Total unique /32 hosts collected: %d -> %s', len(ips), ips)
    with open(output_file, 'w') as fh:
        yaml.dump({'lisp_hosts': ips}, fh, default_flow_style=False)
    log.info('Wrote host list to %s', output_file)

    return ips


def load_lisp_hosts(filename=_HOSTS_FILE):
    """Load host IPs from a previously saved lisp_hosts.yaml.
    Returns [] if the file does not exist.
    Use this when collect_lisp_hosts() has already been run separately.
    """
    if not os.path.isabs(filename):
        filename = os.path.join(_DIR, filename)
    if not os.path.exists(filename):
        return []
    with open(filename) as fh:
        data = yaml.safe_load(fh)
    return data.get('lisp_hosts', [])
