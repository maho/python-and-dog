import unittest

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio  # type: ignore

from . import common
from .utils import run_until_complete

from app import App


class ConfigStub:
    BLINK_LED_PIN = 2
    BUTTON_PIN = 15


class DispenserClientStub:
    def __init__(self, **kwargs):
        self.treat_called = 0

    async def treat(self):
        self.treat_called += 1


class PinStub:
    """ stub of pin which will return 0 at the beginning, then will return `1` 5x, then
    will return `0` in all subsequent calls """

    def __init__(self):
        self.remaining_values = [0] + 10*[1] + [0]

    def value(self, val: int = 0):
        if not self.remaining_values:
            return 0
        return self.remaining_values.pop(0)


class StdlibStub(common.StdlibStub):
    def __init__(self, *, config):
        super().__init__(config=config)
        self.pin_stub = None

    def pin(self, number: int, direction: str) -> PinStub:  # type: ignore
        if self.pin_stub:
            return self.pin_stub

        self.pin_stub = PinStub()
        return self.pin_stub

    async def sleep(self, seconds: float):
        await super().sleep(seconds)
        await asyncio.sleep(0.01)  # to avoid extensive CPU usage


class TestApp(unittest.TestCase):

    def setUp(self):
        self.stdlib = StdlibStub(config=ConfigStub())
        self.dispenser_client = DispenserClientStub()
        self.app = App(config=ConfigStub(), stdlib=self.stdlib, dispenser_client=self.dispenser_client)

    @run_until_complete
    async def test_pressing_treat(self):
        """ check if pressing button ends in sending treat in dispenser client """
        # GIVEN: application which has stdlib stub, which has pin stub which will return
        # 0, 10 * 1 and then zeros

        # WHEN: run App's loop
        asyncio.create_task(self.app.run())

        # wait until in pin's remaining_values queue is exhausted
        while self.stdlib.pin_stub.remaining_values:
            await asyncio.sleep(0.1)

        # THEN: dispenser treat has been called
        self.assertEqual(self.dispenser_client.treat_called, 1)


if __name__ == '__main__':
    unittest.main()
