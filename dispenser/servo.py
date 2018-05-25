import logging
import machine
import math
import utime
from random import random


class Servo:
    def __init__(self, pin_num):
        self.pin = machine.Pin(pin_num, machine.Pin.OUT)
        self.pwm = machine.PWM(self.pin)
        self.pwm.freq(50)
        self.pwm.duty(0)

    def speed(self, speed):
        """ speed 1 is one turn per two seconds """

        if speed == 0:
            self.pwm.duty(0)
            return

        speed = max(min(speed, 1.0), -1.0)
        
        logging.debug("speed after reduction=%s", speed)

        # max rotation is for duty 38 clockwise  and 8 anticlockwise. 
        # 23 is no rotation (middle point)
        speed_range = 15  # 38 - 23
        duty = 23 + int(speed * speed_range)
        logging.debug("duty=%s", duty)
        self.pwm.duty(duty)

    # debug things, #TODO: remove this function
    def pm(self, speed):
        self.speed(speed)
        utime.sleep(10)
        self.speed(0)


