import os
from genie.harness.main import gRun
from pyats.topology import loader

DIR = os.path.dirname(os.path.abspath(__file__))
TESTBED_FILE = os.path.abspath(os.path.join(DIR, "../testbed.yaml"))

def main():
    testbed = loader.load(TESTBED_FILE)
    trigger_uids = [
        'TriggerShutNoShutBgpNeighbor'
    ]

    gRun(testbed=testbed,
         trigger_uids=trigger_uids,
         trigger_datafile=os.path.join(DIR, "bgp_shut_trigger.yaml"),
         devices=["POD5_R1", "POD5_R2"],
         subsection_datafile=os.path.join(DIR, "subsections.yaml"))

if __name__ == '__main__':
    main()
