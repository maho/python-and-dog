import logging
import utime

import network

import config

logger = logging.getLogger(__name__)

def init_wifi():
    """ returns ap,client wifi objects"""
    cli = None
    ap = None
    print("print config.WIFI=", config.WIFI)
    logger.debug("logger.debug config.WIFI=%r", config.WIFI)
    if config.WIFI['ap']:
        ap = init_ap()

    if config.WIFI['client']:
        cli = init_client()

    return ap, cli


def init_client():
    logger.info("init client")
    conf = config.WIFI['client']
    wi = network.WLAN(network.STA_IF)
    wi.active(True)
    logger.debug("sleep 1 sec after active(True)")
    utime.sleep(1)
    logger.debug("wi.scan()")
    for x in wi.scan():
        logger.debug(" -> %r", x)
    wi.config(dhcp_hostname=conf["dhcp"])
    wi.connect(conf["ssid"], conf["pass"])
    logger.debug("asked to connect to ssid/pass")
        
    if conf["ip"]:
        logger.info("manually set ip/dns to %s/%s", conf["ip"], conf["dns"])
        ifconfig = wi.ifconfig()
        wi.ifconfig((conf["ip"], "255.255.255.0", ifconfig[2], conf["dns"]))
        logger.info("ifconfig set")

    while not wi.isconnected():
        utime.sleep(0.2)
        logger.debug("cli is not connected yet, sleeping")

    logger.info("client connected. ifconfig is cli=%s", wi.ifconfig())

    return wi

def init_ap():
    logger.info("init ap")
    conf = config.WIFI['ap']
    wi = network.WLAN(network.AP_IF)
    wi.active(True)
    logger.debug("sleep 0.2 sec after active(True)")
    utime.sleep(0.2)
    wi.config(essid=conf["ssid"])
    wi.config(authmode=network.AUTH_WPA_WPA2_PSK, password=conf["pass"])
    logger.debug("configured ssid/pass")
    if conf["ip"]:
        logger.info("manually set ip/dns to %s/%s", conf["ip"], conf["dns"])
        ifconfig = wi.ifconfig()
        wi.ifconfig((conf["ip"], "255.255.255.0", ifconfig[2], conf["dns"]))
        logger.info("ifconfig set")

    return wi
