import uasyncio

from logging_handlers import RSyslogFileHandler


class StdlibProvider:
    """ """
    def __init__(self, *, config):
        # import esp
        # print("osdebug")
        # esp.osdebug(0)
        self.config = config.LOGGING

    def init_logging(self):
        import logging
        logging.basicConfig(level=logging.DEBUG)
        root_logger = logging.getLogger(None)

        root_logger.addHandler(RSyslogFileHandler("log.log", maxBytes=200*1024, backupCount=3,
                                                  remote_addr=self.config['rsyslog_host'],
                                                  identifier=self.config['id']))

    def pin(self, number: int, direction: str):
        """ returns machine.Pin """
        from machine import Pin
        assert direction in ["in", "out"]

        pindir = Pin.OUT if direction == "out" else Pin.IN

        return Pin(number, pindir)

    async def sleep(self, t):
        await uasyncio.sleep(t)
