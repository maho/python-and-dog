try:
    import uasyncio  # type: ignore
except ImportError:
    import asyncio as uasyncio  # type: ignore


def run_until_complete(fn):
    def _inner(*args, **kwargs):
        return uasyncio.get_event_loop().run_until_complete(fn(*args, **kwargs))

    return _inner
