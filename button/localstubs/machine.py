from common import traceme


class ADC:
    ...


class Pin:
    OUT = 'OUT'
    IN = 'IN'

    @traceme("Pin")
    def __init__(self, pin, dir_):
        self.pin_num = pin

    @traceme("Pin")
    def value(self, val=None):
        if val is None:
            """ check if file exists, in such case return contents of file, otherwise return 0 """
            try:
                with open("/tmp/pins/%s" % self.pin_num, "r") as f:
                    sval = f.read()
                    val = int(sval)
                    print("pin(%s) is %s" % (self.pin_num, val))
                    return val
            except Exception:
                return 0


class PWM:
    @traceme("PWM")
    def freq(self, *a, **kwa):
        ...

    @traceme("PWM")
    def duty(self, *a, **kwa):
        ...
