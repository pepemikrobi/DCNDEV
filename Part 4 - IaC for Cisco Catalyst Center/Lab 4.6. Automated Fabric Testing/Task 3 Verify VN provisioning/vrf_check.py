"""
pyATS test to verify VRF provisioning for L3 Virtual Networks defined in a
Catalyst Center fabric YAML file (TF_NETASCODE/data/fabric.yaml by default).

Usage:
    python vrf_check.py --fabric ../TF_NETASCODE/data/fabric.yaml

Each VN found under catalyst_center.fabric.l3_virtual_networks must be present
as a VRF on every border and edge device defined in the same file.
"""

import argparse
import sys

import yaml
from pyats import aetest
from pyats.topology import loader


# ── parse --fabric before pyATS consumes sys.argv ────────────────────────────

def _parse_args():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--fabric",
        default="../TF_NETASCODE/data/fabric.yaml",
        help="Path to the Catalyst Center fabric YAML file.",
    )
    args, remaining = parser.parse_known_args()
    # Put remaining args back so pyATS can parse --testbed, --loglevel, etc.
    sys.argv[1:] = remaining
    return args.fabric


def _load_fabric(fabric_path):
    """Return (expected_vrfs, fabric_devices) extracted from the YAML file."""
    with open(fabric_path) as fh:
        data = yaml.safe_load(fh)

    expected_vrfs = (
        data["catalyst_center"]["fabric"]["fabric_sites"][0]["l3_virtual_networks"]
    )

    inventory_devices = (
        data.get("catalyst_center", {})
            .get("inventory", {})
            .get("devices", [])
    )

    # Border and edge device names (strip domain suffix to match testbed keys)
    fabric_device_names = [
        d["name"].split(".")[0]
        for d in inventory_devices
        if d.get("fabric_site")
    ]

    return expected_vrfs, fabric_device_names


FABRIC_PATH = _parse_args()
EXPECTED_VRFS, FABRIC_DEVICES = _load_fabric(FABRIC_PATH)


# ── common setup ─────────────────────────────────────────────────────────────

class CommonSetup(aetest.CommonSetup):

    @aetest.subsection
    def connect_to_devices(self, testbed, steps):
        """Connect to all fabric devices; mark subsection failed on any error."""
        for name in FABRIC_DEVICES:
            device = testbed.devices[name]
            with steps.start(f"Connect to {name}", continue_=True) as step:
                try:
                    device.connect(via="cli", log_stdout=False, learn_hostname=True)
                except Exception as exc:
                    step.failed(f"Cannot connect to {name}: {exc}")

    @aetest.subsection
    def mark_device_loop(self, testbed):
        """Create one VRFCheck testcase instance per fabric device."""
        aetest.loop.mark(VRFCheck, device_name=FABRIC_DEVICES)


# ── main testcase ─────────────────────────────────────────────────────────────

class VRFCheck(aetest.Testcase):
    """Verify that all expected VRFs are present on a single fabric device."""

    @aetest.setup
    def check_connected(self, testbed, device_name):
        """Abort this testcase early if the device is not connected."""
        device = testbed.devices[device_name]
        if not device.is_connected():
            self.skipped(f"{device_name} is not connected – skipping VRF checks")

    @aetest.test
    @aetest.loop(vrf=EXPECTED_VRFS)
    def verify_vrf_exists(self, testbed, device_name, vrf):
        """
        Parse 'show vrf' and confirm the VRF is present in the output.
        A VRF is considered present when its name appears in the parsed table.
        """
        device = testbed.devices[device_name]

        try:
            output = device.parse("show vrf")
        except Exception as exc:
            self.failed(
                f"[{device_name}] Failed to parse 'show vrf': {exc}"
            )

        # pyATS Genie parser returns a dict keyed under 'vrf'
        configured_vrfs = list(output.get("vrf", {}).keys())

        if vrf not in configured_vrfs:
            self.failed(
                f"[{device_name}] VRF '{vrf}' NOT found. "
                f"Configured VRFs: {configured_vrfs}"
            )
        else:
            self.passed(
                f"[{device_name}] VRF '{vrf}' is present. "
                f"All VRFs: {configured_vrfs}"
            )

    @aetest.test
    def verify_all_vrfs_present(self, testbed, device_name, expected_vrfs):
        """
        Single summary test: confirm every expected VRF exists on this device.
        Collects all failures before reporting so the full picture is visible.
        """
        device = testbed.devices[device_name]

        try:
            output = device.parse("show vrf")
        except Exception as exc:
            self.failed(
                f"[{device_name}] Failed to parse 'show vrf': {exc}"
            )

        configured_vrfs = list(output.get("vrf", {}).keys())
        missing = [v for v in expected_vrfs if v not in configured_vrfs]

        if missing:
            self.failed(
                f"[{device_name}] Missing VRFs: {missing}. "
                f"Configured VRFs: {configured_vrfs}"
            )
        else:
            self.passed(
                f"[{device_name}] All expected VRFs {expected_vrfs} are present."
            )

    @aetest.cleanup
    def disconnect(self, testbed, device_name):
        device = testbed.devices[device_name]
        if device.is_connected():
            device.disconnect()


# ── common cleanup ────────────────────────────────────────────────────────────

class CommonCleanup(aetest.CommonCleanup):

    @aetest.subsection
    def disconnect_remaining(self, testbed):
        """Ensure every device is disconnected even if a testcase cleanup missed it."""
        for name in FABRIC_DEVICES:
            device = testbed.devices[name]
            if device.is_connected():
                device.disconnect()


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    testbed = loader.load("testbed.yaml")
    aetest.main(testbed=testbed, expected_vrfs=EXPECTED_VRFS)
