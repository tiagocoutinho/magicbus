from magicbus._compat import ntob
import errno
import os
thismodule = os.path.abspath(__file__)
import sys
import time

from magicbus import bus
from magicbus.plugins import loggers, opsys, signalhandler
from magicbus.test import assertEqual, assertNotEqual
from magicbus.test import Process

loggers.FileLogger(bus, "test_signals.log").subscribe()
pidfile = opsys.PIDFile(bus, os.path.join(thismodule + ".pid"))


class TestSignalHandling(object):

    def test_SIGHUP_tty(self):
        # When not daemonized, SIGHUP should exit the process.
        try:
            from signal import SIGHUP
        except ImportError:
            return "skipped (no SIGHUP)"

        try:
            from os import kill
        except ImportError:
            return "skipped (no os.kill)"

        p = Process([sys.executable, thismodule, "tty"])
        p.start()
        pid = pidfile.wait()
        os.kill(pid, SIGHUP)
        pidfile.join()

    def test_SIGHUP_daemonized(self):
        # When daemonized, SIGHUP should restart the server.
        try:
            from signal import SIGHUP, SIGTERM, SIGKILL
        except ImportError:
            return "skipped (no SIGHUP)"

        try:
            from os import kill
        except ImportError:
            return "skipped (no os.kill)"

        if os.name not in ['posix']:
            return "skipped (not on posix)"

        p = Process([sys.executable, thismodule, "daemonize"])
        p.start()
        pid = pidfile.wait()
        os.kill(pid, SIGHUP)

        # Give the server some time to restart
        time.sleep(1)
        new_pid = pidfile.wait()
        assertNotEqual(new_pid, pid)
        os.kill(new_pid, SIGTERM)
        pidfile.join()

    def test_SIGTERM_tty(self):
        # SIGTERM should shut down the server whether daemonized or not.
        try:
            from signal import SIGTERM
        except ImportError:
            return "skipped (no SIGTERM)"

        try:
            from os import kill
        except ImportError:
            return "skipped (no os.kill)"

        # Spawn a normal, undaemonized process.
        p = Process([sys.executable, thismodule, "tty"])
        p.start()
        pid = pidfile.wait()
        os.kill(pid, SIGTERM)
        pidfile.join()

    def test_SIGTERM_daemonized(self):
        # SIGTERM should shut down the server whether daemonized or not.
        try:
            from signal import SIGTERM
        except ImportError:
            return "skipped (no SIGTERM)"

        try:
            from os import kill
        except ImportError:
            return "skipped (no os.kill)"

        if os.name not in ['posix']:
            return "skipped (not on posix)"

        # Spawn a daemonized process and test again.
        p = Process([sys.executable, thismodule, "daemonize"])
        p.start()
        pid = pidfile.wait()
        os.kill(pid, SIGTERM)
        pidfile.join()


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'daemonize':
        opsys.Daemonizer(bus).subscribe()
    pidfile.subscribe()
    signalhandler.SignalHandler(bus).subscribe()
    bus.debug = True
    bus.start()
    bus.block()
