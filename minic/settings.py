# -*- coding: utf-8 -*-
import json
import platform
import os


APPLICATION_GROUP = 'IL2HorusTeam'

if not any(platform.win32_ver()):
    APPLICATION_GROUP = '.' + APPLICATION_GROUP

USER_FILES_ROOT = os.path.join(
    os.path.expanduser("~"), APPLICATION_GROUP, 'minic')
LOG_ROOT = os.path.join(USER_FILES_ROOT, 'logs')

LOG_SETTINGS = {
    'filename': os.path.join(LOG_ROOT, 'minic.log'),
    'maxBytes': 1024 * 1024 * 5,  # 5 MiB
    'backupCount': 10,
    'level': 'INFO',
    'timeFormat': None,
}


class Settings(object):

    filename = None
    __container = None

    def __init__(self, filename):
        self.filename = filename
        self.__container = {}

    @property
    def filepath(self):
        return os.path.join(USER_FILES_ROOT, self.filename)

    def load(self):
        """
        .. todo:: may raise some exception
        """
        if not os.path.exists(self.filepath):
            self.__container = {}
        else:
            with open(self.filepath, 'r') as f:
                self.__container = json.load(f)

    def sync(self):
        """
        .. todo:: may raise some exception
        """
        with open(self.filepath, 'w') as f:
            json.dump(self.__container, f, indent=2)

    def __getattr__(self, name):
        """
        Called when `__getattribute__` is failed.
        """
        return self.__container.get(name)

    def __setattr__(self, name, value):
        try:
            # Do not call `hasattr` because `__getattr__` will always succeed
            super(Settings, self).__getattribute__(name)
        except AttributeError:
            self.__container[name] = value
        else:
            # If attribute belongs directly to instance
            super(Settings, self).__setattr__(name, value)


user_settings = Settings('minic.conf')
