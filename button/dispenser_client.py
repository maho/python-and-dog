import uasyncio
import logging
import _thread

import urequests as requests


logger = logging.getLogger(__name__)


class DispenserClient:
    def __init__(self, *, config, blinker):
        self.config = config
        self.blinker = blinker
        self.request_lock = None
        self.request_exception = None

    def make_request(self, url, json):
        with self.request_lock:
            try:
                self.request_exception = None
                self.response = requests.post(self.config.TREAT_URL, json={'portion': self.config.PORTION_IDX})
            except Exception as e:
                self.request_exception = e

    async def treat(self):
        try:
            if self.request_lock and self.request_lock.locked():
                raise RuntimeError("request already in progress")

            self.request_lock = _thread.allocate_lock()

            _thread.start_new_thread(self.make_request, (self.config.TREAT_URL,
                                                         {'portion': self.config.PORTION_IDX}))
            while not self.request_lock.locked():
                await uasyncio.sleep(0.01)

            logger.info("request started, waiting for thread to finish")

            i = 0
            while self.request_lock.locked():
                i += 1
                logger.debug("thread is still alive, sleeping a while (%s) ", i)
                await self.blinker.blink(0.1, 0.05)

            if self.request_exception:
                raise self.request_exception

            if self.response.status_code // 100 != 2:
                raise RuntimeError("returned status %s" % self.response.status_code)

            await self.blinker.blink(0.6, 0.1)
            return True

        except Exception as e:
            logger.exc(e, "some error while calling %s", self.config.TREAT_URL)
            await self.blinker.blink(0.6, 0.03)
            return False
