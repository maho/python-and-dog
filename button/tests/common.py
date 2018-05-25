class PinStub:
    def __init__(self):
        self.values_called = {0: 0, 1: 0}

    def value(self, val: int):
        assert val in [0, 1]
        self.values_called[val] += 1


class StdlibStub:

    def __init__(self, *, config):
        self.total_slept = 0.0
        self.pin_stub = PinStub()
        self.config = config

    def pin(self, number: int, direction: str) -> PinStub:
        return self.pin_stub

    async def sleep(self, seconds: float):
        self.total_slept += seconds
