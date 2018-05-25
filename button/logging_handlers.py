# COPIED FROM pycopy-lib in vast part

import os
from logging import Handler

import usyslog as lus


def try_remove(fn: str) -> None:
    """Try to remove a file if it existst."""
    try:
        os.remove(fn)
    except OSError:
        pass


def get_filesize(fn: str) -> int:
    """Return size of a file."""
    return os.stat(fn)[6]


class RotatingFileHandler(Handler):
    """
    A rotating file handler like RotatingFileHandler.

    Compatible with CPythons `logging.handlers.RotatingFileHandler` class.
    """

    def __init__(self, filename, maxBytes=0, backupCount=0):
        super().__init__()
        self.filename = filename
        self.maxBytes = maxBytes
        self.backupCount = backupCount

        try:
            self._counter = get_filesize(self.filename)
        except OSError:
            self._counter = 0

    def emit(self, record):
        """Write to file."""
        msg = "%s: %s" % (record.levelname, record.message)
        s_len = len(msg)

        if self.maxBytes and self.backupCount and self._counter + s_len > self.maxBytes:
            # remove the last backup file if it is there
            try_remove(self.filename + ".{0}".format(self.backupCount))

            for i in range(self.backupCount - 1, 0, -1):
                if i < self.backupCount:
                    try:
                        os.rename(
                            self.filename + ".{0}".format(i),
                            self.filename + ".{0}".format(i + 1),
                        )
                    except OSError:
                        pass

            try:
                os.rename(self.filename, self.filename + ".1")
            except OSError:
                pass
            self._counter = 0

        with open(self.filename, "a") as f:
            f.write(msg + "\n")

        self._counter += s_len


class RSyslogFileHandler(RotatingFileHandler):
    """ handler which is mix of RotatingFileHandler and udp syslog client.  when trying to
    emit first log, there is attempt to establish udp client. If it's not possible
    (eg. no WIFI connection yet), then another attempt is made in next emit. """

    def __init__(self, filename, maxBytes, backupCount, remote_addr, identifier):
        """ NOTE: it's good if remote_addr is an ip """
        super().__init__(filename=filename, maxBytes=maxBytes, backupCount=backupCount)

        self.remote_addr = remote_addr
        self.identifier = identifier

        self.udp_client = None
        self.file_flushed = False

    def init_rsyslog(self):
        import gc
        gc.collect()
        try:
            self.udp_client = lus.UDPClient(ip=self.remote_addr)
        except Exception as e:
            print("     [WARNING: could not initialize udp syslog handler, postponing %s ]" % e)
            self.udp_client = None

    def flush_file(self):
        try:
            print("     [will flush file]")
            self.udp_client.log(lus.S_INFO, "---- flushing file %s ----" % self.filename)
            with open(self.filename, "r") as f:
                for line in f:
                    self.udp_client.log(lus.S_INFO, "%s: %s" % (self.identifier, line))

            os.remove(self.filename)
            self.udp_client.log(lus.S_INFO, "---- end of flush, %s removed ----" % self.filename)
            print("     [end of flush]")

            self.file_flushed = True
        except Exception as e:
            print("     [Could not flush file to UDP - will try later: %s]" % e)

    def emit(self, record):
        super().emit(record)

        print(record.levelname, ":", record.name, ":", record.message)

        if not self.udp_client:
            self.init_rsyslog()

        if not self.file_flushed:
            self.flush_file()

        if not self.file_flushed:
            return  # no point to try send current log if archive was not sent

        try:

            msg = "%s: %s: %s" % (self.identifier, record.levelname, record.message)

            mapping = {'debug': lus.S_DEBUG,
                       'info': lus.S_INFO,
                       'warning': lus.S_WARN,
                       'error': lus.S_ERR}

            s_level = mapping.get(record.levelname, lus.S_INFO)
            self.udp_client.log(s_level, msg)

        except Exception as e:
            print("     [could not send msg to UDP rsyslog: %s]" % e)
