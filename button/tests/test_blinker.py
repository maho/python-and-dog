import unittest

from blinker import Blinker

from .common import StdlibStub
from .utils import run_until_complete


class ConfigStub:
    ...


class TestBlinker(unittest.TestCase):

    def setUp(self):
        self.config = ConfigStub()

        self.config.BLINK_LED_PIN = 15
        self.stdlib = StdlibStub(config=ConfigStub())
        self.blinker = Blinker(config=self.config, stdlib=self.stdlib)

    @run_until_complete
    async def test_blink_slow(self):
        # WHEN called slow blinking
        await self.blinker.blink_slow(time=5)

        # THEN: we have slept 5 seconds (total)
        self.assertEqual(self.stdlib.total_slept, 5)

        # and we have called setting led 10 times (one per half second)
        led = self.stdlib.pin_stub
        self.assertEqual(led.values_called[1], 10)

    @run_until_complete
    async def test_blink_fast(self):
        # WHEN called slow blinking
        await self.blinker.blink_fast(time=5)

        # THEN: we have slept 5 seconds (total)
        self.assertEqual(self.stdlib.total_slept, 5)

        # and we have called setting led 10 times (one per half second)
        led = self.stdlib.pin_stub
        self.assertEqual(led.values_called[1], 20)


if __name__ == '__main__':
    unittest.main()
