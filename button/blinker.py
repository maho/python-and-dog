class Blinker:
    FAST_DELAY = 0.125
    SLOW_DELAY = 0.25

    def __init__(self, *, config, stdlib):
        self.config = config
        self.stdlib = stdlib

    async def blink_fast(self, time):
        await self.blink(time=time, delay=self.FAST_DELAY)

    async def blink_slow(self, time):
        await self.blink(time=time, delay=self.SLOW_DELAY)

    async def blink(self, time, delay):
        pin_number = self.config.BLINK_LED_PIN
        pin = self.stdlib.pin(pin_number, direction="out")

        for i in range(int(time / (delay * 2))):
            await self.stdlib.sleep(delay)
            pin.value(1)
            await self.stdlib.sleep(delay)
            pin.value(0)
