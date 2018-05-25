import logging

logger = logging.getLogger(__name__)


class ConnProvider:
    def __init__(self, *, config, wlan, stdlib, blinker):
        self.config = config
        self.wlan = wlan
        self.stdlib = stdlib
        self.blinker = blinker

    async def init_client(self):
        logger.info("init client")
        conf = self.config.WIFI['client']
        wi = self.wlan
        stdlib = self.stdlib

        wi.active(True)
        logger.debug("sleep 1 sec after active(True)")
        await stdlib.sleep(1)
        # logger.debug("wi.scan()")
        # for x in wi.scan():
        #     logger.debug(" -> %r", x)
        wi.config(dhcp_hostname=conf["dhcp"])
        wi.connect(conf["ssid"], conf["pass"])
        logger.debug("asked to connect to ssid/pass")

        if conf.get("ip", None):
            logger.info("manually set ip/dns to %s/%s", conf["ip"], conf["dns"])
            ifconfig = wi.ifconfig()
            wi.ifconfig((conf["ip"], "255.255.255.0", ifconfig[2], conf["dns"]))
            logger.info("ifconfig set")

        while not wi.isconnected():
            await self.blinker.blink(0.2, 0.05)
            logger.debug("cli is not connected yet, sleeping")

        logger.info("client connected. ifconfig is cli=%s", wi.ifconfig())

        await self.blinker.blink(2, 0.5)

        return wi
