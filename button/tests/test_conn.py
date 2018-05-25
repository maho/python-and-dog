import unittest

from aconn import ConnProvider
from blinker import Blinker

from .common import StdlibStub
from .utils import run_until_complete


class ConfigStub:
    BLINK_LED_PIN = 2


class BlinkerStub(Blinker):
    def __init__(self, config, stdlib):
        super().__init__(config=config, stdlib=stdlib)

        self.ordered_blinks = []

    async def blink(self, time, delay):
        self.ordered_blinks.append((time, delay))
        await super().blink(time=time, delay=delay)


class WLANStub:
    def __init__(self):
        self.is_active = None
        self.config_data = {}
        self.connected_ssid = self.connected_pass = None
        self.connect_attempts = 10
        self.number_asked_for_isconnected = 0
        self._ifconfig_data = None

    def active(self, val):
        self.is_active = val

    def scan(self):
        return [('something', 'something_else'),
                ('something2', 'something_else_2')]

    def config(self, **kwargs):
        self.config_data.update(kwargs)

    def connect(self, ssid, pass_):
        self.connected_ssid = ssid
        self.connected_pass = pass_

    def isconnected(self):
        self.number_asked_for_isconnected += 1

        if self.number_asked_for_isconnected >= 10:
            return True

        return False

    def ifconfig(self, data_=None):
        if data_:
            self._ifconfig_data = data_
        return self._ifconfig_data


class TestConn(unittest.TestCase):

    def setUp(self):
        self.config = ConfigStub()

        self.config.WIFI = {'client': {'dhcp': 'DHCPID',
                                       'ssid': 'SSID',
                                       'pass': 'PASS',
                                       'dns': '1.2.3.4'}}

        self.wlan = WLANStub()
        self.stdlib = StdlibStub(config=ConfigStub())
        self.blinker = BlinkerStub(config=self.config, stdlib=self.stdlib)

        self.aconn = ConnProvider(config=self.config, wlan=self.wlan, stdlib=self.stdlib, blinker=self.blinker)

    @run_until_complete
    async def test_init_client(self):

        await self.aconn.init_client()

        # wlan.active() has been called
        self.assertTrue(self.wlan.is_active)
        # wlan.config is set with these settings
        self.assertEqual({"dhcp_hostname": "DHCPID"}, self.wlan.config_data)
        # wlan.connect is set to ...
        self.assertEqual("SSID", self.wlan.connected_ssid)
        self.assertEqual("PASS", self.wlan.connected_pass)

        # sanity check
        self.assertEqual(self.wlan.number_asked_for_isconnected, 10)
        # check if waited 2.8 (1 seconds at the beginning + 9*0.2) seconds
        # and 2 more seconds for last blink
        self.assertAlmostEqual(self.stdlib.total_slept, 4.8)

        # check if at first we have fast blinking, then slow - after success
        self.assertTrue(len(self.blinker.ordered_blinks) >= 2,
                        msg="self.blinker.ordered_blinks should >= 2 but has %s" % len(self.blinker.ordered_blinks))
        first_blinks = self.blinker.ordered_blinks[:-1]
        last_blink = self.blinker.ordered_blinks[-1]

        # first are fast
        self.assertEqual(first_blinks[0], (0.2, 0.05))
        # last is slow
        self.assertEqual(last_blink, (2, 0.5))

    @run_until_complete
    async def test_init_client_with_ip(self):
        # GIVEN: config ip is set
        self.config.WIFI["client"]["ip"] = "12.12.12.12"
        # GIVEN: ifconfig set to some data
        self.wlan._ifconfig_data = ("9.9.9.9", "111.222.112.221", "10.10.10.10", "11.11.11.11")

        await self.aconn.init_client()

        # check if ifconfig is set
        self.assertEqual(self.wlan._ifconfig_data,
                         ("12.12.12.12", "255.255.255.0", "10.10.10.10", "1.2.3.4"))


if __name__ == '__main__':
    unittest.main()
