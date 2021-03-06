#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pygtk
pygtk.require('2.0')

import logging
import os
import sys

if os.name == 'nt' and hasattr(sys, 'frozen'):
    # True only if running as a py2exe app
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

from twisted.internet import gtk2reactor
gtk2reactor.install()

import minic
minic.APP_ROOT = os.path.dirname(os.path.realpath(sys.argv[0]))

from twisted.internet import reactor
from twisted.python.logfile import LogFile

from tx_logging.observers import LevelFileLogObserver

from minic.settings import (
    SETTINGS_ROOT, LOG_ROOT, LOG_SETTINGS, user_settings,
)
from minic.ui import show_error, MainWindow
from minic.util import ugettext_lazy as _, pid_exists


class PidLock(object):

    def __init__(self):
        self.pidpath = os.path.join(SETTINGS_ROOT, 'minic.pid')
        if not os.path.exists(self.pidpath):
            return
        with open(self.pidpath, 'r') as f:
            pid = int(f.readline().strip())
        if pid_exists(pid):
            raise RuntimeError(_("Another instance is still running"))

    def __enter__(self):
        with open(self.pidpath, 'w') as f:
            f.write(str(os.getpid()))

    def __exit__(self, *args):
        os.remove(self.pidpath)


def check_dir(path):
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError:
            raise RuntimeError(_("Failed to create path: \n{0}".format(path)))


def check_dirs():
    check_dir(SETTINGS_ROOT)
    check_dir(LOG_ROOT)


def setup_logging():
    filename = LOG_SETTINGS['file_path']
    log_file = LogFile.fromFullPath(
        filename,
        rotateLength=LOG_SETTINGS['max_bytes'],
        maxRotatedFiles=LOG_SETTINGS['max_backups']
    ) if filename is not None else sys.stdout

    log_level = getattr(logging, LOG_SETTINGS['level'])

    observer = LevelFileLogObserver(log_file, log_level)
    observer.timeFormat = LOG_SETTINGS['time_format']
    observer.start()


def main():
    try:
        setup_logging()
    except Exception as e:
        show_error(_("Failed to setup logging: {0}").format(unicode(e)))
        return
    try:
        user_settings.load()
    except Exception as e:
        raise
        show_error(_("Failed load user settings: {0}").format(unicode(e)))
        return

    MainWindow()
    reactor.run()


if __name__ == "__main__":
    try:
        check_dirs()
    except RuntimeError as e:
        show_error(e)
        sys.exit()

    try:
        pid_lock = PidLock()
    except Exception as e:
        show_error(e)
        sys.exit()

    with pid_lock:
        main()
