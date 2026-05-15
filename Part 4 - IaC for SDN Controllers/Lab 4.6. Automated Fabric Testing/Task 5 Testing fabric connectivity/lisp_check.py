#!/usr/bin/env python3
"""
SD-Access LISP Fabric Validation
=================================
TC1  LispSessionCheck         - All active (non-Listening) LISP sessions Up on fabric devices
TC2  LispEidRegistrationCheck - IPv4 /32 host EIDs registered & Up on all control-plane nodes
TC3  LispReachabilityCheck    - Registered hosts pingable from core switches

Usage:
    python lisp_check.py [options]

CLI Parameters:
    --testbed  PATH   pyATS testbed YAML file                  (required)
                      e.g. --testbed testbed.yaml
    --fabric   PATH   Catalyst Center fabric YAML file         (required)
                      Source of FABRIC_DEVICES and CONTROL_PLANE_NODES.
                      Devices with any fabric_role       → checked for LISP sessions (TC1)
                      Devices with CONTROL_PLANE_NODE    → checked for EID registrations (TC2)
                      Core switches (TC3 ping source)    → auto-discovered from testbed (CORE* hostnames)
    --loglevel LEVEL  Logging verbosity: DEBUG / INFO / WARNING (default: INFO)

Examples:
    python lisp_check.py --testbed testbed.yaml --fabric ../TF_NETASCODE/data/fabric.yaml
    python lisp_check.py --testbed testbed.yaml --fabric ../TF_NETASCODE/data/fabric.yaml --loglevel DEBUG
"""

import re
import sys
import logging
import yaml
from concurrent.futures import ThreadPoolExecutor
from ipaddress import ip_network
from pyats import aetest

log = logging.getLogger('ats.lisp_check')

CORE_SWITCHES: list = []  # populated at runtime from testbed (CORE* hostname pattern)


def _parse_args():
    import argparse
    parser = argparse.ArgumentParser(
        prog='python lisp_check.py',
        description=(
            'SD-Access LISP Fabric Validation\n\n'
            '  TC1  LispSessionCheck         — active (non-Listening) LISP sessions Up\n'
            '  TC2  LispEidRegistrationCheck — IPv4 /32 host EIDs registered & Up\n'
            '  TC3  LispReachabilityCheck    — registered hosts pingable from core switches'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '--testbed', required=True, metavar='PATH',
        help='pyATS testbed YAML file  [required]',
    )
    parser.add_argument(
        '--fabric', required=True, metavar='PATH',
        help='Catalyst Center fabric YAML file  [required]',
    )
    parser.add_argument(
        '--loglevel', default='INFO', metavar='LEVEL',
        help='Logging verbosity: DEBUG / INFO / WARNING  (default: %(default)s)',
    )
    args, remaining = parser.parse_known_args()

    # Configure our module logger — root logger level is WARNING by default
    # so log.info() is silently dropped unless we add our own handler here.
    _level = getattr(logging, args.loglevel.upper(), logging.INFO)
    log.setLevel(_level)
    if not log.handlers:
        _h = logging.StreamHandler()
        _h.setFormatter(logging.Formatter(
            fmt='%(asctime)s: %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S',
        ))
        log.addHandler(_h)
    log.propagate = False   # prevent duplicates if pyATS later adds root handlers

    # Restore --testbed and --loglevel so pyATS can also consume them
    sys.argv[1:] = ['--testbed', args.testbed, '--loglevel', args.loglevel] + remaining
    return args.fabric, args.testbed


def _load_fabric(fabric_path):
    """Return (fabric_devices, control_plane_nodes) from the YAML file."""
    with open(fabric_path) as fh:
        data = yaml.safe_load(fh)
    fabric_devs, control_plane = [], []
    for d in data['catalyst_center']['inventory']['devices']:
        name  = d['name'].split('.')[0]   # strip .sdn.lab suffix
        roles = d.get('fabric_roles', [])
        if roles:
            fabric_devs.append(name)
        if 'CONTROL_PLANE_NODE' in roles:
            control_plane.append(name)
    return fabric_devs, control_plane


_fabric_path, _testbed_path = _parse_args()
FABRIC_DEVICES, CONTROL_PLANE_NODES = _load_fabric(_fabric_path)


# ---------------------------------------------------------------------------
class CommonSetup(aetest.CommonSetup):

    @aetest.subsection
    def connect_to_devices(self, testbed, steps):
        global CORE_SWITCHES
        CORE_SWITCHES = sorted(
            name for name in testbed.devices
            if name.upper().startswith('CORE')
        )
        log.info(f'Core switches discovered from testbed: {CORE_SWITCHES}')

        all_devices = FABRIC_DEVICES + CORE_SWITCHES
        errors = {}

        def _connect(name):
            try:
                testbed.devices[name].connect(via='cli', log_stdout=False)
            except Exception as e:
                errors[name] = str(e)

        with ThreadPoolExecutor(max_workers=len(all_devices)) as pool:
            pool.map(_connect, all_devices)

        # Report per-device results after all threads finish
        for name in all_devices:
            with steps.start(f'Connect {name}') as step:
                if name in errors:
                    step.failed(errors[name])


# ---------------------------------------------------------------------------
class LispSessionCheck(aetest.Testcase):
    """TC1 – All active (non-Listening) LISP peer sessions must be Up on every fabric device."""

    @aetest.test
    def verify_sessions(self, testbed, steps):
        for device_name in FABRIC_DEVICES:
            device = testbed.devices[device_name]
            with steps.start(f'{device_name}: show lisp session all') as step:
                try:
                    parsed = device.parse('show lisp session all')
                except Exception as e:
                    step.failed(f'Parser error: {e}')

                failures = []
                for vrf, vrf_data in parsed.get('vrf', {}).items():
                    peers = vrf_data.get('peers', {})
                    not_up = []
                    total_active = 0
                    for peer_ip, sessions in peers.items():
                        for sess in sessions:
                            state = sess.get('state', '')
                            if state.lower() == 'listening':
                                continue      # ignore listening sessions
                            total_active += 1
                            if state.lower() != 'up':
                                not_up.append(f'{peer_ip} ({state})')
                    log.info(f'  {device_name} vrf "{vrf}": '
                             f'{total_active - len(not_up)}/{total_active} '
                             f'active sessions Up (listening ignored)')
                    if not_up:
                        failures.append(
                            f'vrf {vrf}: not Up — ' + ', '.join(not_up)
                        )
                if failures:
                    step.failed(' | '.join(failures))


# ---------------------------------------------------------------------------
class LispEidRegistrationCheck(aetest.Testcase):
    """TC2 – IPv4 /32 host EIDs registered and Up on all control-plane nodes."""

    # Class attribute so TC3 can read the results without coupling testcase IDs
    registered_hosts: list = []

    @aetest.test
    def list_and_verify_eids(self, testbed, steps):
        all_hosts = []

        for cp_name in CONTROL_PLANE_NODES:
            device = testbed.devices[cp_name]
            with steps.start(f'Parse "show lisp site" on {cp_name}') as step:
                try:
                    parsed = device.parse('show lisp site')
                except Exception as e:
                    step.failed(f'Parser error: {e}')

            # Collect IPv4 /32 host routes from this control plane node
            for lisp_id, lisp_data in parsed.get('lisp_id', {}).items():
                for site, site_data in lisp_data.get('site_name', {}).items():
                    for iid, iid_data in site_data.get('instance_id', {}).items():
                        for eid_prefix, eid_data in iid_data.get('eid_prefix', {}).items():
                            if ':' in eid_prefix:       # skip IPv6
                                continue
                            try:
                                net = ip_network(eid_prefix, strict=False)
                            except ValueError:
                                continue
                            if net.prefixlen != 32:     # host routes only
                                continue
                            all_hosts.append({
                                'prefix': eid_prefix,
                                'ip':     str(net.network_address),
                                'iid':    iid,
                                'up':     eid_data.get('up', False),
                                'rloc':   eid_data.get('who_last_registered', '—'),
                                'cp':     cp_name,
                            })

        # Deduplicate by IP across control plane nodes (keep first occurrence)
        seen, hosts = set(), []
        for h in sorted(all_hosts, key=lambda x: x['ip']):
            if h['ip'] not in seen:
                seen.add(h['ip'])
                hosts.append(h)

        # Print summary table
        log.info('')
        log.info('=' * 75)
        log.info(f'  Registered IPv4 /32 hosts across {len(CONTROL_PLANE_NODES)} '
                 f'control plane node(s): {", ".join(CONTROL_PLANE_NODES)}')
        log.info(f'  {"EID Prefix":<22} {"IID":<8} {"Up":<6} RLOC (last registered by)')
        log.info('  ' + '-' * 68)
        for h in hosts:
            log.info(f'  {h["prefix"]:<22} {h["iid"]:<8} {str(h["up"]):<6} {h["rloc"]}')
        log.info(f'  Total: {len(hosts)} registered IPv4 host EIDs')
        log.info('=' * 75)

        with steps.start('At least 1 host EID registered') as step:
            if not hosts:
                step.failed('No IPv4 /32 EIDs registered on any control plane node')

        down = [h for h in hosts if not h['up']]
        with steps.start(
            f'All EIDs Up: {len(hosts) - len(down)}/{len(hosts)}'
        ) as step:
            if down:
                step.failed(
                    f'{len(down)} EID(s) not Up: '
                    + ', '.join(h['prefix'] for h in down)
                )

        LispEidRegistrationCheck.registered_hosts = hosts


# ---------------------------------------------------------------------------
class LispReachabilityCheck(aetest.Testcase):
    """TC3 – Registered host EIDs reachable via ping from core switches."""

    @aetest.test
    def ping_from_core(self, testbed, steps):
        hosts = LispEidRegistrationCheck.registered_hosts
        if not hosts:
            self.skipped('No host EIDs collected in TC2 — skipping ping test')

        for switch_name in CORE_SWITCHES:
            switch = testbed.devices[switch_name]
            with steps.start(
                f'{switch_name}: ping {len(hosts)} discovered host(s)'
            ) as outer_step:
                failed_hosts = []
                for h in sorted(hosts, key=lambda x: x['ip']):
                    ip  = h['ip']
                    iid = h['iid']
                    result = switch.execute(f'ping {ip} repeat 5')
                    m = re.search(
                        r'Success rate is (\d+) percent \((\d+)/(\d+)\)',
                        result
                    )
                    if m:
                        pct  = int(m.group(1))
                        rcvd, sent = m.group(2), m.group(3)
                        log.info(f'  {switch_name} → {ip:<18} IID {iid:<6} '
                                 f'{pct}% ({rcvd}/{sent})')
                        if pct == 0:
                            failed_hosts.append(f'{ip} (0%)')
                    else:
                        log.warning(f'  {switch_name} → {ip}: unparseable output')
                        failed_hosts.append(f'{ip} (no result)')

                if failed_hosts:
                    outer_step.failed(
                        f'{len(failed_hosts)}/{len(hosts)} hosts unreachable: '
                        + ', '.join(failed_hosts)
                    )


# ---------------------------------------------------------------------------
class CommonCleanup(aetest.CommonCleanup):

    @aetest.subsection
    def disconnect(self, testbed):
        def _disconnect(name):
            try:
                testbed.devices[name].disconnect()
            except Exception:
                pass

        with ThreadPoolExecutor(max_workers=len(FABRIC_DEVICES + CORE_SWITCHES)) as pool:
            pool.map(_disconnect, FABRIC_DEVICES + CORE_SWITCHES)


# ---------------------------------------------------------------------------
if __name__ == '__main__':
    from genie.testbed import load
    testbed = load(_testbed_path)
    aetest.main(testbed=testbed)
