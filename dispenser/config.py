WIFI = {'ap': {'ssid': 'dispenser',
               'pass': 'dispenserpass',
               # if set to None, no ip is set
               'ip': None,
               'dns': None},

        'client': {'ssid': 'some_network',
                   'pass': 'some_pass',
                   'dhcp': 'treatme',
                   # if set to None, no ip is set
                   'ip': None,
                   'dns': None}}

SERVO_PIN = 19

TURN_SPEED = 1

FULL_ANGLE_TIME = 2

# full turnarounds (full angles)
PORTION_SIZES = {1: [0.2, -0.3], 
                 2: [0.2, -0.6],
                 3: [0.2, -1.6],
                -1: [2]}


LISTEN_PORT = 2477

try:
    from config_local import *   # noqa:
except Exception:
    pass


