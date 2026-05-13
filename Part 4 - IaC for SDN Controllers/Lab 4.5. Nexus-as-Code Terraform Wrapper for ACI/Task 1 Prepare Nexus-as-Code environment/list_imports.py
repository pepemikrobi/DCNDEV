#!/usr/bin/env python3
"""
list_imports.py
---------------
Reads the data/ YAML files, queries Catalyst Center for each defined resource,
and prints the `terraform import` commands for any that already exist.

Run from the TF_NETASCODE directory:
    python3 list_imports.py [--url URL] [--username USER]

The password is read from the TF_VAR_catc_password environment variable.
If not set, you will be prompted.
"""

import argparse
import base64
import getpass
import json
import os
import ssl
import sys
import urllib.request
import urllib.error

import yaml


# ── HTTP helpers ─────────────────────────────────────────────────────────────

def _ssl_ctx():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def get_token(url, username, password):
    creds = base64.b64encode(f"{username}:{password}".encode()).decode()
    req = urllib.request.Request(
        f"{url}/dna/system/api/v1/auth/token",
        method="POST",
        headers={"Authorization": f"Basic {creds}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, context=_ssl_ctx(), timeout=15) as r:
        return json.loads(r.read())["Token"]


def api_get(url, token, path):
    req = urllib.request.Request(
        f"{url}{path}",
        headers={"X-Auth-Token": token, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, context=_ssl_ctx(), timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


# ── CATC lookups ─────────────────────────────────────────────────────────────

def lookup_building(url, token, parent, name):
    """Return site ID of a building, or None."""
    data = api_get(url, token, f"/dna/intent/api/v1/site?name={parent}/{name}")
    if data and data.get("response"):
        return data["response"][0]["id"]
    return None


def lookup_fabric_site(url, token, site_id):
    """Return fabric site ID for a given site UUID, or None."""
    data = api_get(url, token, f"/dna/intent/api/v1/sda/fabricSites?siteId={site_id}")
    if data and data.get("response"):
        return data["response"][0]["id"]
    return None


def lookup_ip_pool(url, token, pool_name):
    """Return global IP pool ID by name, or None."""
    data = api_get(url, token, "/dna/intent/api/v1/global-pool")
    if data:
        for p in data.get("response", []):
            if p.get("ipPoolName") == pool_name:
                return p["id"]
    return None


def lookup_l3_vn(url, token, vn_name):
    """Return L3 virtual network ID by name, or None."""
    data = api_get(url, token,
        f"/dna/intent/api/v1/sda/layer3VirtualNetworks?virtualNetworkName={vn_name}")
    if data:
        for vn in data.get("response", []):
            if vn.get("virtualNetworkName") == vn_name:
                return vn["id"]
    return None


def lookup_anycast_gateway(url, token, fabric_id, pool_name):
    """Return anycast gateway ID for a fabric + pool, or None."""
    data = api_get(url, token,
        f"/dna/intent/api/v1/sda/anycastGateways?fabricId={fabric_id}&ipPoolName={pool_name}")
    if data:
        for gw in data.get("response", []):
            if gw.get("ipPoolName") == pool_name:
                return gw["id"]
    return None


def lookup_network_device_id(url, token, device_name=None, device_ip=None):
    """Return the network device UUID by hostname or management IP, or None."""
    if device_ip:
        data = api_get(url, token, f"/dna/intent/api/v1/network-device/ip-address/{device_ip}")
        if data and data.get("response"):
            return data["response"]["id"]
    if device_name:
        data = api_get(url, token,
            f"/dna/intent/api/v1/network-device?hostname={device_name}")
        if data and data.get("response"):
            return data["response"][0]["id"]
    return None


# ── YAML loading ─────────────────────────────────────────────────────────────

def load_data(data_dir="data"):
    merged = {}
    for fname in sorted(os.listdir(data_dir)):
        if fname.endswith((".yaml", ".yml")):
            with open(os.path.join(data_dir, fname)) as f:
                content = yaml.safe_load(f)
            if content:
                _deep_merge(merged, content)
    return merged.get("catalyst_center", {})


def _deep_merge(base, override):
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v


# ── credentials from tfvars ──────────────────────────────────────────────────

def read_tfvars(path="terraform.tfvars"):
    result = {}
    if not os.path.exists(path):
        return result
    with open(path) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                result[k.strip()] = v.strip().strip('"')
    return result


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="List terraform import commands for resources already in Catalyst Center"
    )
    parser.add_argument("--url",      help="Catalyst Center URL")
    parser.add_argument("--username", help="CATC username")
    args = parser.parse_args()

    tfvars   = read_tfvars()
    url      = args.url      or tfvars.get("catc_url")      or input("Catalyst Center URL: ").strip()
    username = args.username or tfvars.get("catc_username") or input("Username: ").strip()
    password = os.environ.get("TF_VAR_catc_password") or getpass.getpass("Password (or set TF_VAR_catc_password): ")
    url      = url.rstrip("/")

    print(f"\nAuthenticating to {url} ...", file=sys.stderr)
    token = get_token(url, username, password)
    print("Token obtained.\n", file=sys.stderr)

    if not os.path.isdir("data"):
        sys.exit("Run from the TF_NETASCODE directory (data/ not found)")

    cc = load_data("data")

    # Collect results: list of (description, tf_address, catc_id | None)
    rows = []
    site_uuid_cache = {}    # full_site_name → site UUID
    fabric_id_cache = {}    # full_site_name → fabric site UUID

    # ── 1. Buildings ──────────────────────────────────────────────────────────
    for bldg in cc.get("sites", {}).get("buildings", []):
        parent = bldg["parent_name"]
        name   = bldg["name"]
        full   = f"{parent}/{name}"
        addr   = f'module.nac.catalystcenter_building.building["{full}"]'
        rid    = lookup_building(url, token, parent, name)
        if rid:
            site_uuid_cache[full] = rid
        rows.append(("Building", full, addr, rid))

    # ── 2. Fabric sites ───────────────────────────────────────────────────────
    for fs in cc.get("fabric", {}).get("fabric_sites", []):
        full  = fs["name"]
        addr  = f'module.nac.catalystcenter_fabric_site.fabric_site["{full}"]'
        # resolve site UUID
        site_uuid = site_uuid_cache.get(full)
        if not site_uuid:
            parts     = full.rsplit("/", 1)
            site_uuid = lookup_building(url, token, parts[0], parts[1])
            if site_uuid:
                site_uuid_cache[full] = site_uuid
        fabric_id = lookup_fabric_site(url, token, site_uuid) if site_uuid else None
        if fabric_id:
            fabric_id_cache[full] = fabric_id
        rows.append(("Fabric Site", full, addr, fabric_id))

    # ── 3. Global IP pools ────────────────────────────────────────────────────
    for pool in cc.get("network_settings", {}).get("ip_pools", []):
        name = pool["name"]
        addr = f'module.nac.catalystcenter_ip_pool.ip_pool_v4["{name}"]'
        rid  = lookup_ip_pool(url, token, name)
        rows.append(("IP Pool", name, addr, rid))

    # ── 4. L3 Virtual Networks ────────────────────────────────────────────────
    for vn in cc.get("fabric", {}).get("l3_virtual_networks", []):
        name = vn["name"]
        addr = f'module.nac.catalystcenter_fabric_l3_virtual_network.l3_vn["{name}"]'
        rid  = lookup_l3_vn(url, token, name)
        rows.append(("L3 VN", name, addr, rid))

    # ── 5. Anycast gateways ───────────────────────────────────────────────────
    for fs in cc.get("fabric", {}).get("fabric_sites", []):
        full      = fs["name"]
        fabric_id = fabric_id_cache.get(full)
        for gw in fs.get("anycast_gateways", []):
            pool_name = gw["ip_pool_name"]
            addr      = f'module.nac.catalystcenter_anycast_gateway.anycast_gateway["{pool_name}"]'
            rid       = lookup_anycast_gateway(url, token, fabric_id, pool_name) if fabric_id else None
            rows.append(("Anycast GW", pool_name, addr, rid))

    # ── 6. Update Authentication Profile ─────────────────────────────────────
    for fs in cc.get("fabric", {}).get("fabric_sites", []):
        auth_name = fs.get("authentication_template", {}).get("name", "")
        if "Closed" not in auth_name:
            continue
        full      = fs["name"]
        addr      = f'module.nac.catalystcenter_update_authentication_profile.closed_authentication["{full}"]'
        fabric_id = fabric_id_cache.get(full)   # import key = fabric site ID
        rows.append(("Auth Profile", f"{auth_name} @ {full}", addr, fabric_id))

    # ── 7. Device roles (catalystcenter_device_role.role) ─────────────────────
    # Import ID = network device UUID; keyed by device name
    net_device_id_cache = {}   # device_name → network device UUID

    for device in cc.get("inventory", {}).get("devices", []):
        dev_name = device["name"]
        dev_ip   = device.get("device_ip")
        nd_id    = lookup_network_device_id(url, token, device_name=dev_name, device_ip=dev_ip)
        if nd_id:
            net_device_id_cache[dev_name] = nd_id
        addr = f'module.nac.catalystcenter_device_role.role["{dev_name}"]'
        rows.append(("Device Role", dev_name, addr, nd_id))

    # ── 8. Fabric border/edge devices ─────────────────────────────────────────
    for device in cc.get("inventory", {}).get("devices", []):
        dev_name    = device["name"]
        fabric_site = device.get("fabric_site")
        roles       = device.get("fabric_roles", [])
        if not fabric_site or not roles:
            continue

        fabric_id  = fabric_id_cache.get(fabric_site)
        nd_id      = net_device_id_cache.get(dev_name)
        if not nd_id:
            dev_ip = device.get("device_ip")
            nd_id  = lookup_network_device_id(url, token, device_name=dev_name, device_ip=dev_ip)
            if nd_id:
                net_device_id_cache[dev_name] = nd_id
        # Import ID format: <network_device_id>,<fabric_id>
        import_id = f"{nd_id},{fabric_id}" if (nd_id and fabric_id) else None

        if "BORDER_NODE" in roles:
            addr = f'module.nac.catalystcenter_fabric_device.border_device["{dev_name}"]'
            rows.append(("Border Device", dev_name, addr, import_id))
        if "EDGE_NODE" in roles:
            addr = f'module.nac.catalystcenter_fabric_device.edge_device["{dev_name}"]'
            rows.append(("Edge Device", dev_name, addr, import_id))

    # ── Output ────────────────────────────────────────────────────────────────
    COL = 14
    NAME_COL = 50
    ID_COL = 38

    header = f"{'TYPE':<{COL}}  {'NAME':<{NAME_COL}}  {'CATC ID':<{ID_COL}}  STATUS"
    print(header)
    print("-" * len(header))

    import_cmds = []
    for rtype, name, addr, rid in rows:
        status = "EXISTS" if rid else "not found"
        catc_id = rid or "-"
        print(f"{rtype:<{COL}}  {name:<{NAME_COL}}  {catc_id:<{ID_COL}}  {status}")
        if rid:
            import_cmds.append(f"terraform import '{addr}' {rid}")

    print()
    if import_cmds:
        print("# ── terraform import commands ──────────────────────────────────────────")
        print(f"# Run these from: {os.path.abspath('.')}")
        print(f"# Set TF_VAR_catc_password or pass -var catc_password=<pwd> as needed")
        print()
        for cmd in import_cmds:
            print(cmd)
    else:
        print("# No existing resources found — nothing to import.")


if __name__ == "__main__":
    main()
