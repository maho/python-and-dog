from common import traceme


class WLAN:
    @traceme("WLAN")
    def __init__(self, *args, **kwargs):
        ...

    @traceme("WLAN")
    def active(self, *args, **kwargs):
        return True

    @traceme("WLAN")
    def scan(self, *args, **kwargs):
        return []

    @traceme("WLAN")
    def config(self, *a, **kwa):
        ...

    @traceme("WLAN")
    def connect(self, *a, **kwa):
        ...

    @traceme("WLAN")
    def isconnected(self, *a, **kwa):
        return True

    @traceme("WLAN")
    def ifconfig(self, *a, **kwa):
        return []


STA_IF = 'STA_IF'
