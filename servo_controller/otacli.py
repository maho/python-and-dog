import network
import machine
import os
import time

import ospath
import uselect
import usocket
import utarfile

import config

def blink(msg=None, static={'v': 0}):
    lednum = getattr(config, "BLINK_LED", 2)
    led = machine.Pin(lednum, machine.Pin.OUT)
    static['v'] = (static['v'] + 1) % 2
    led.value(static['v'])
    if msg:
        print(msg)

class CheckTimeoutError(Exception):
    pass


def url_open(url):
    """ copied from micropython-lib - library upip """
    
    print("url=%s" % url)

    proto, _, host, urlpath = url.split('/', 3)
    host, port = host.split(":", 2)
    try:
        s = usocket.socket()
        # s.bind((config.OTA["bind_ip"], 1415))
        ai = usocket.getaddrinfo(host, port)
        print("ai = %r" % ai)
        print("ai[0][-1] = %s" % (ai[0][-1],))
    except OSError as e:
        fatal("Unable to resolve %s:%s (no Internet?)" % host, port,  e)
    
    try:

        print("set noblocking")
        s.setblocking(False)

        # poller = uselect.poll()
        # poller.register(s, uselect.POLLIN)

        try:
            err = s.connect(ai[0][-1])
            print("after connect, err=%s" % err )
        except OSError as e:
            print("Catched OSError", e)
            if e.args[0] != 115:  # EINPROGRESS
                raise

            print("EINPROGRESS, good")

        __, ssocks, __ = uselect.select([], [s], [], 3)  # wait only three seconds for connecting to repo

        if not ssocks:
            raise CheckTimeoutError("could not connect")

        s.setblocking(True)
        # MicroPython rawsocket module supports file interface directly
        s.write("GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n" % (urlpath, host))
        l = s.readline()
        protover, status, msg = l.split(None, 2)
        if status != b"200":
            if status == b"404" or status == b"301":
                raise NotFoundError("URL not found")
            raise ValueError(status)
        while 1:
            l = s.readline()
            if not l:
                raise ValueError("Unexpected EOF in HTTP headers")
            if l == b'\r\n':
                break
    except Exception as e:
        print("Exception in url_open", e)
        import sys
        sys.print_exception(e)
        s.close()
        raise e

    return s

def check():
    """ connect to service WIFI network, connect to service addr/port and check if 
        there are new files to put here """

    print('connecting to service %s network' % config.OTA["SSID"])
    blink()
    station = network.WLAN(network.STA_IF)

    try:
        station.active(True)
        station.connect(config.OTA["SSID"], config.OTA["password"])
        blink()

        for x in range(config.OTA["wifi_conn_timeout"]):
            if station.isconnected():
                print("connected to service wifi")
                break
            blink()
            time.sleep(1)
        else:
            print("service wifi timeout. network not active or too slow, giving up")
            blink()
            return False

        # set ip to service ip
        ifconfig = station.ifconfig()
        station.ifconfig((config.OTA["bind_ip"], "255.255.255.0", ifconfig[2], ifconfig[3]))
        blink()
        return check_over_ip(config.OTA["node_type"])
    finally:
        ## set it back
        # station.ifconfig(ifconfig)
        ## make station inactive
        station.disconnect()
        station.active(False)





def check_over_ip(node_type):
    """ tcp/ip stage of checking of OTA"""

    try:
        resp = url_open("http://10.11.12.13:1415/%s/version.txt" % node_type)
    except (OSError, CheckTimeoutError):
        blink("no version found")
        return False

    remote_version = resp.read().decode("utf-8").strip()
    blink("remote version = %s" % remote_version)

    try:
        local_version = open(".otaversion").read().strip()
    except OSError:
        blink("no local version found")
        local_version = ""

    blink("local_version = %s remote_version=%s" % (local_version, remote_version))

    if local_version == remote_version:
        blink("skipping")
        return False

    blink("doing OTA")

    resp = url_open("http://10.11.12.13:1415/%s/%s.tar" % (node_type, remote_version))

    ftar = utarfile.TarFile(fileobj=resp)
    meta = install_tar(ftar)

    fver = open(".otaversion", "wb")
    fver.write(remote_version)
    fver.close()

    del fver
    del resp
    del ftar
    del meta
    
    blink("OTA PERFORMED, doing reboot")
    machine.reset()



def install_tar(f):
    """ copied and modified from micropython-lib/upip """
    meta = {}
    for info in f:
        blink(info)
        fname = info.name

        outfname = fname
        if info.type != utarfile.DIRTYPE:
            blink("Extracting " + outfname)
            _makedirs(outfname)
            subf = f.extractfile(info)
            save_file(outfname, subf)
    return meta


# Expects *file* name
def _makedirs(name, mode=0o777):
    """ copied (and modified?) from micropython-lib upython """
    dirname = ospath.dirname(name)
    print("mkdir dirname=%s" % dirname)
    try:
        os.mkdir(dirname)
        print("made dir %s" % dirname)
    except OSError as e:
        if e.args[0] != errno.EEXIST and e.args[0] != errno.EISDIR:
            raise

file_buf = bytearray(512)

def save_file(fname, subf):
    global file_buf

    with open(fname, "wb") as outf:
        while True:
            sz = subf.readinto(file_buf)
            if not sz:
                break
            outf.write(file_buf, sz)






