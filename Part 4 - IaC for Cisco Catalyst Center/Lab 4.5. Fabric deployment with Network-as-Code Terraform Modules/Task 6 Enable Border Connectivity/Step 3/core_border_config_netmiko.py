#!/usr/bin/env python3
"""
Generate CORE_SW border configuration from NaC fabric.yaml data.

Usage:
  python3 core_sw_border_config.py <pod_number> <core_sw_number>
                                   [--configure]
                                   [--core-username USER]
                                   [--core-password PASS]

  core_sw_number 1  →  CORE_SW1 (10.16.3.11), connects to POD{pod}_R1
  core_sw_number 2  →  CORE_SW2 (10.16.3.12), connects to POD{pod}_R2

Examples:
  python3 core_sw_border_config.py 5 1
  python3 core_sw_border_config.py 5 1 --configure \\
      --core-username admin --core-password secret
"""
import sys
import os
import re
import time
import argparse
import getpass
import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(SCRIPT_DIR, "data")

CORE_SW_HOSTS = {"1": "10.16.3.11", "2": "10.16.3.12"}


# ── YAML helpers ─────────────────────────────────────────────────────────────

def _deep_merge(base, override):
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v


def load_data(data_dir):
    merged = {}
    for fname in sorted(os.listdir(data_dir)):
        if fname.endswith((".yaml", ".yml")):
            with open(os.path.join(data_dir, fname)) as f:
                content = yaml.safe_load(f)
            if content:
                _deep_merge(merged, content)
    return merged.get("catalyst_center", {})


# ── IP helpers ────────────────────────────────────────────────────────────────

def ip_only(cidr):
    """'1.1.5.2/30' → '1.1.5.2'"""
    return cidr.split("/")[0]


def prefix_to_mask(cidr):
    """'1.1.5.2/30' → '255.255.255.252'"""
    bits = int(cidr.split("/")[1])
    n = (0xFFFFFFFF >> (32 - bits)) << (32 - bits)
    return ".".join(str((n >> (8 * i)) & 0xFF) for i in reversed(range(4)))


# ── SSH push (netmiko) ──────────────────────────────────────────────────────

def push_config(host, username, password, config_lines):
    """Send config lines to an IOS device via SSH using netmiko."""
    from netmiko import ConnectHandler
    
    device = {
        'device_type': 'cisco_ios',
        'host': host,
        'username': username,
        'password': password,
        'timeout': 15,
        'global_delay_factor': 1,
    }
    
    try:
        ssh = ConnectHandler(**device)
    except Exception as e:
        raise Exception(f"Error connecting to {host}: {e}")
    
    try:
        # Send configuration
        output = ssh.send_config_set(config_lines)
        # Save configuration
        output += ssh.send_command('write memory')
        return output
    finally:
        ssh.disconnect()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        usage="%(prog)s <pod> <core> [--configure] "
              "[--core-username USER] [--core-password PASS]",
        description=(
            "Generate CORE_SW border configuration from NaC fabric.yaml data.\n"
            "\n"
            "Positional arguments:\n"
            "  pod   Pod number (e.g. 5)\n"
            "  core  Core switch number: 1 or 2\n"
            "          1 = CORE_SW1 (10.16.3.11), connected to POD{pod}_R1\n"
            "          2 = CORE_SW2 (10.16.3.12), connected to POD{pod}_R2"
        ),
        epilog=(
            "Examples:\n"
            "  %(prog)s 5 1\n"
            "  %(prog)s 5 2 --configure --core-username admin --core-password secret"
        ),
    )
    parser.add_argument("pod",  help=argparse.SUPPRESS)
    parser.add_argument("core", help=argparse.SUPPRESS)
    parser.add_argument("--configure", action="store_true",
                        help="Connect to core device and apply the configuration")
    parser.add_argument("--core-username", metavar="USER",
                        help="SSH username for the core switch")
    parser.add_argument("--core-password", metavar="PASS",
                        help="SSH password for the core switch")
    parser.error = lambda msg: (parser.print_help(), print(f"\nerror: {msg}"), sys.exit(2))
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    args = parser.parse_args()

    pod  = args.pod
    core = args.core

    if not pod.isdigit() or int(pod) < 1:
        parser.error("<pod_number> must be a positive integer")
    if core not in ("1", "2"):
        parser.error("<core_sw_number> must be 1 or 2")

    cc     = load_data(DATA_DIR)
    fabric = cc.get("fabric", {})

    # Transit BGP AS (CORE side)
    transits   = fabric.get("transits", [])
    transit_as = transits[0]["autonomous_system_number"] if transits else "65001"

    # Find border device: name must contain POD{pod}_R{core}
    pattern       = re.compile(rf"POD{pod}_R{core}\b", re.IGNORECASE)
    border_device = None
    for bd in fabric.get("border_devices", []):
        if pattern.search(bd["name"]):
            border_device = bd
            break

    if not border_device:
        print(f"Error: No border device matching POD{pod}_R{core} found in {DATA_DIR}")
        sys.exit(1)

    border_as = border_device.get("local_autonomous_system_number", f"6550{pod}")

    # Navigate to virtual networks in l3_handoff
    try:
        vns = border_device["l3_handoffs"][0]["interfaces"][0]["virtual_networks"]
    except (KeyError, IndexError):
        print("Error: l3_handoffs / interfaces / virtual_networks missing from border device")
        sys.exit(1)

    if not vns:
        print("Error: No virtual_networks defined in l3_handoff interface")
        sys.exit(1)

    # From CORE_SW perspective:
    #   own SVI IP   = peer_ip_address  (we are the "peer" from the border router's view)
    #   BGP neighbor = local_ip_address (the border router's own IP)
    vn_data = []
    for vn in vns:
        vn_data.append({
            "name":       vn["name"],
            "vlan":       vn["vlan"],
            "core_ip":    ip_only(vn["peer_ip_address"]),
            "core_mask":  prefix_to_mask(vn["peer_ip_address"]),
            "border_ip":  ip_only(vn["local_ip_address"]),
        })

    # ── Build config lines ────────────────────────────────────────────────────
    config_lines = []

    for vd in vn_data:
        config_lines += [
            f"vlan {vd['vlan']}",
            f" name POD{pod}_R{core}_{vd['name']}",
            "!",
        ]

    vlan_list = ",".join(str(vd["vlan"]) for vd in vn_data)
    config_lines += [
        f"interface GigabitEthernet1/{pod}",
        f" switchport trunk allowed vlan add {vlan_list}",
        "!",
    ]

    for vd in vn_data:
        config_lines += [
            f"interface Vlan {vd['vlan']}",
            f" ip address {vd['core_ip']} {vd['core_mask']}",
            " no shutdown",
            "!",
        ]

    config_lines.append(f"router bgp {transit_as}")
    for vd in vn_data:
        config_lines.append(f" neighbor {vd['border_ip']} remote-as {border_as}")
    config_lines += [
        " !",
        " address-family ipv4 unicast",
    ]
    for vd in vn_data:
        config_lines.append(f"  neighbor {vd['border_ip']} activate")
        config_lines.append(f"  neighbor {vd['border_ip']} default-originate")
    config_lines.append(" !")

    # ── Display ───────────────────────────────────────────────────────────────
    print(f"! === CORE_SW{core} config for POD{pod} (border: {border_device['name']}) ===")
    print()
    print("\n".join(config_lines))

    # ── Optional push ─────────────────────────────────────────────────────────
    if not args.configure:
        return

    # Resolve credentials interactively if not supplied on CLI
    host     = CORE_SW_HOSTS[core]
    username = args.core_username
    password = args.core_password

    if not username:
        username = input("Username: ").strip()
    if not password:
        password = getpass.getpass("Password: ")

    print()
    answer = input("Apply the above configuration to the device? [yes/NO]: ").strip().lower()
    if answer != "yes":
        print("Aborted — no changes made.")
        return

    print(f"\nConnecting to {host} ...")
    try:
        output = push_config(host, username, password, config_lines)
        print("\n--- Device output ---")
        print(output)
        print("--- Configuration applied successfully ---")
    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()