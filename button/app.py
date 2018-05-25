import logging
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio  # type: ignore


logger = logging.getLogger(__name__)


class App:
    def __init__(self, *, config, stdlib, dispenser_client):
        self.config = config
        self.stdlib = stdlib
        self.dispenser_client = dispenser_client

        self.button = stdlib.pin(config.BUTTON_PIN, "in")

    async def run(self):
        """ main loop of app """
        while True:
            await self.wait_until_pressed()
            logger.debug("button is pressed")
            await self.dispenser_client.treat()
            logger.debug("sent (or not) treat")

    async def wait_until_pressed(self):
        old_state = self.button.value()

        while True:
            await asyncio.sleep(0.05)
            new_state = self.button.value()
            if new_state == 0 and old_state == 1:
                return
            old_state = new_state
