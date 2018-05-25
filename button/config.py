BLINK_LED_PIN = 22
BUTTON_PIN = 15

# TREAT_URL = "http://ustat.home:5060/foo/"
# TREAT_URL = "http://192.168.1.118:5060/foo/"
TREAT_URL = "http://treatme.home:2477/treat"
PORTION_IDX = 1

LOGGING = {'id': 'button1',
           # 'rsyslog_host': 'ustat.home'
           'rsyslog_host': '192.168.1.118'
           }

from config_local import *  # noqa
