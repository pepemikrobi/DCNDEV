from pyats import aetest, topology

test_destinations = {
        '8.8.8.8',
        '208.67.222.222',
        '10.16.2.3'
    }

class CommonSetup (aetest.CommonSetup):

    @aetest.subsection
    def dynamic_loop_add (self, testbed):
        aetest.loop.mark (PingTest, device=testbed)

class PingTest (aetest.Testcase):

    @aetest.setup
    def connect (self, steps, device):
        return
    #     device.connect(via="cli", log_stdout=False, learn_hostname=True)

    @aetest.test
    def ping (self, steps, device, destinations):
        return
        # for dest in destinations:
        #     with steps.start(f"Ping from {device.hostname} to {dest}", continue_=True) as step:
        #         try:
        #             device.ping (dest)
        #         except:
        #             step.failed (f"Ping from {device.hostname} to {dest} failed")
        #         else:
        #             step.passed (f"Ping from {device.hostname} to {dest} succeeded")

    @aetest.cleanup
    def disconnect (self, device):
        return
        # device.disconnect()

if __name__ == "__main__":
    print (f"Staring ping test{'.'*10}")
    
    my_testbed = topology.loader.load("podX.yaml")
    ping_test = aetest.main(testbed=my_testbed, destinations=test_destinations)
