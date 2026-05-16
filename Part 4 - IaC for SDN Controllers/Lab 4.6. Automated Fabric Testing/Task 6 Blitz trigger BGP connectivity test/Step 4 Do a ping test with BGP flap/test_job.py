import os
import sys
import yaml
import tempfile
from genie.harness.main import gRun
from pyats.topology import loader

DIR          = os.path.dirname(os.path.abspath(__file__))
TESTBED_FILE = os.path.abspath(os.path.join(DIR, "../testbed.yaml"))
TRIGGER_FILE = os.path.join(DIR, "bgp_shut_trigger.yaml")
sys.path.insert(0, DIR)  # make blitz_helpers importable

import blitz_helpers


def main():
    testbed = loader.load(TESTBED_FILE)

    # Collect LISP /32 hosts from control-plane nodes (also writes lisp_hosts.yaml)
    hosts = blitz_helpers.collect_lisp_hosts()

    # Inject the collected list into the trigger YAML loop placeholder
    with open(TRIGGER_FILE) as f:
        trigger_data = yaml.safe_load(f)

    for section in trigger_data['FabricPingLispHosts_PreTest']['test_sections']:
        if 'ping_lisp_hosts' in section:
            section['ping_lisp_hosts'][0]['loop']['value'] = hosts
            break

    tmp_fd, tmp_path = tempfile.mkstemp(suffix='.yaml', dir=DIR)
    try:
        with os.fdopen(tmp_fd, 'w') as f:
            yaml.dump(trigger_data, f)

        gRun(testbed=testbed,
             trigger_uids=[ \
                 'FabricPingLispHosts_PreTest', \
                 'TriggerShutNoShutBgpNeighbor_R1' \
                 ],
             trigger_datafile=tmp_path,
             devices=["PODX_R1", "PODX_R2", "CORE_SW1", "CORE_SW2"],
             subsection_datafile=os.path.join(DIR, "subsections.yaml"))
    finally:
        os.unlink(tmp_path)


if __name__ == '__main__':
    main()
