from pyats import aetest
from pyats.topology import loader

class VerifyConnectivity(aetest.Testcase):
    @aetest.test
    def connect_to_devices(self, testbed):
        for device_name, device in testbed.devices.items():
            try:
                device.connect(log_stdout=False)
            except Exception:
                self.failed(f"Failed to connect to {device_name}")

    @aetest.cleanup
    def disconnect_from_devices(self, testbed):
        for device in testbed.devices.values():
            if device.is_connected():
                device.disconnect()

# Load testbed and run test
testbed = loader.load('testbed.yaml')
aetest.main(testbed=testbed)
