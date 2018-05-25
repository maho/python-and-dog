import network

import uasyncio

import app
import aconn
import blinker
import config
import dispenser_client as dispenser_client
from stdlib import StdlibProvider


async def main():
    stdlib = StdlibProvider(config=config)
    stdlib.init_logging()

    wlan = network.WLAN(network.STA_IF)
    b = blinker.Blinker(config=config, stdlib=stdlib)
    conn = aconn.ConnProvider(config=config, wlan=wlan, stdlib=stdlib, blinker=b)
    di = dispenser_client.DispenserClient(config=config, blinker=b)

    await conn.init_client()
    app_ = app.App(config=config, dispenser_client=di, stdlib=stdlib)
    await app_.run()


if __name__ == '__main__':
    uasyncio.get_event_loop().run_until_complete(main())
