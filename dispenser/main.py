import logging
import math
import os
import _thread as th

from microdot import Microdot, Response, redirect


import config as conf_mod
import template


logger = logging.getLogger(__name__)



class StdlibProvider:  # pragma: no cover
    """ class providing various stdlib things """
    def sleep(self, time_):
        import utime  # module exists only on esp32

        utime.sleep(time_)

    def init_wifi(self):
        import webrepl  # module exists only on esp32
        import conn  # module uses code which exists only on esp32

        webrepl.start()
        conn.init_wifi()

    def init_logging(self):
        logging.basicConfig(level=logging.DEBUG)


class TreatmeContainer:  # pragma: no cover
    def __init__(self):
        """ very naive implementation """
        from servo import Servo

        self.config = conf_mod
        self.threads = th
        self.servo = Servo(self.config.SERVO_PIN)
        self.stdlib = StdlibProvider()
        self.templates = template
        self.treat_logic = TreatLogic(config=self.config, threads=self.threads, servo=self.servo, stdlib=self.stdlib)
        self.app = TreatApp(treat_logic=self.treat_logic, config=self.config, stdlib=self.stdlib, templates=self.templates)


class TreatLogic:
    def __init__(self, *,  config, threads, servo, stdlib):
        self.config = config
        self.threads = threads
        self.servo = servo
        self.stdlib = stdlib

    def treat(self, sizes: list):
        speedtimes = self._sizes_to_speedtimes(sizes)
        self.threads.start_new_thread(self.turnmany, (speedtimes,), {})

    def _sizes_to_speedtimes(self, sizes):
        speed = self.config.TURN_SPEED
        return [
            (speed * math.copysign(1, size), abs(size * self.config.FULL_ANGLE_TIME / speed))
            for size in sizes
        ]

    def turnmany(self, speed_times: list):
        """ 
        function called inside thread. turn servo at speed/time according to speed_times

        speed_times - list of (speed, time) tuple
        """
        for speed, time_ in speed_times:
            self.turn(speed, time_)

    def turn(self, speed, time):

        servo = self.servo
        stdlib = self.stdlib

        logger.debug("turn(speed=%s, time=%s)", speed, time)
        logger.debug("set speed to %s", speed)
        servo.speed(speed)

        logger.debug("wait %s seconds", time)
        stdlib.sleep(time)

        logger.debug("set speed to 0")
        servo.speed(0)


class TreatApp:
    def __init__(self, treat_logic, config, stdlib, templates):
        self.treat_logic = treat_logic
        self.config = config
        self.stdlib = stdlib
        self.templates = templates

        self.app = Microdot()
        self.app.route("/")(self.index)
        self.app.route("/treat", methods=["POST"])(self.treat)

    def run(self):  # pragma: no cover
        self.stdlib.init_logging()
        self.stdlib.init_wifi()
        self.app.run(debug=True, port=self.config.LISTEN_PORT)

    def index(self, req):
        return Response(body=self.templates.INDEX, headers={"Content-Type": "text/html"})

    def _parse_sizes(self, req) -> list:
        """ return sizes from portion and sizes POST parameters 
        """
        sizes = req.json.get("sizes", None)
        portion_idx = float(req.json.get("portion", 2))

        logger.debug("portion_idx=%s (%s)", portion_idx, type(portion_idx))

        if sizes:
            sizes = [float(size) for size in sizes.split(",")]
        else:
            sizes = self.config.PORTION_SIZES[portion_idx]

        logger.debug("sizes=%s", sizes)
        return sizes

    def treat(self, req):

        sizes = self._parse_sizes(req)

        self.treat_logic.treat(sizes)

        return Response(body={"result": "ok"})


if __name__ == '__main__':  # pragma: no cover
    ctr = TreatmeContainer()
    ctr.app.run()
