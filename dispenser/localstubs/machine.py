from common import traceme


class ADC:
    ...

class Pin:
    OUT = 'OUT'

class PWM:
    @traceme("PWM")
    def freq(self, *a, **kwa):
        ...

    @traceme("PWM")
    def duty(self, *a, **kwa):
        ...
