from time import sleep
from servo import Servo
from machine import Pin, ADC

import otacli
import config

if otacli.check():
    print("this line will be never reached")

servo = None


servo = Servo(config.SERVO_PIN)
adc = ADC(Pin(config.ADAC_PIN))

while True:
    sleep(0.1)
    v = adc.read()/4096
    vr = round(v, 1)
    print("vr=", vr, "v=", v)
    # servo.set(v)
    servo.set(v - 0.5)

