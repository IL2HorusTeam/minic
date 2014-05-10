# -*- coding: utf-8 -*-
import ConfigParser
import json
import platform
import os

from minic.util import ugettext_lazy as _


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


CONSOLE_TIMEOUT = 1.0
DEVICE_LINK_TIMEOUT = 1.0

# TODO: add version


class UserSettings(object):

    file_name = 'minic.conf'
    __container = None

    def __init__(self):
        self.__container = {}

    @property
    def file_path(self):
        return os.path.join(USER_FILES_ROOT, self.file_name)

    def load(self):
        """
        .. todo:: may raise some exception
        """
        if not os.path.exists(self.file_path):
            self.__container = {}
        else:
            with open(self.file_path, 'r') as f:
                self.__container = json.load(f)

    def sync(self):
        """
        .. todo:: may raise some exception
        """
        with open(self.file_path, 'w') as f:
            json.dump(self.__container, f, indent=2)

    def __getattr__(self, name):
        """
        Called when `__getattribute__` is failed.
        """
        return self.__container.get(name)

    def __setattr__(self, name, value):
        try:
            # Do not call `hasattr` because `__getattr__` will always succeed
            super(UserSettings, self).__getattribute__(name)
        except AttributeError:
            self.__container[name] = value
        else:
            # If attribute belongs directly to instance
            super(UserSettings, self).__setattr__(name, value)


user_settings = UserSettings()


class ServerSettings(dict):

    file_name = 'confs.ini'

    def __init__(self, *args, **kwargs):
        super(ServerSettings, self).__init__(*args, **kwargs)
        self.config = ConfigParser.ConfigParser()

    def load(self):
        self.clear()
        self.config.read(self._file_path())

        # Path to events log
        self['log_path'] = self._get_log_path()

        # Max number of network channels
        self['max_channels'] = int(self._get_value('NET', 'serverChannels', 32))
        # Difficulty value
        self['difficulty'] = int(self._get_value('NET', 'difficulty', 0))

        # Console host
        self['cl_host'] = self._get_value('NET', 'localHost', '127.0.0.1')
        # Console port
        self['cl_port'] = int(self._get_value('Console', 'IP', 20000))

        # Device Link host
        self['dl_host'] = self._get_value('DeviceLink', 'host', self['cl_host'])
        # Device Link port
        self['dl_port'] = int(self._get_value('DeviceLink', 'port', 10000))

        # Server name
        self['name'] = self._get_value(
            'NET', 'serverName').decode('unicode-escape')
        # Server description
        self['description'] = self._get_value(
            'NET', 'serverDescription').decode('unicode-escape')

    def _get_log_path(self):
        value = self._get_value('game', 'eventlog')
        if value is None:
            raise ValueError(
                _("Events log path is not set in {0}").format(self.file_name))
        return os.path.join(os.path.dirname(user_settings.server_path), value)

    def _get_value(self, section_name, attr_name, default=None):
        try:
            return self.config.get(section_name, attr_name)
        except:
            return default

    def _file_path(self):
        server_path = user_settings.server_path
        if server_path is None:
            raise ValueError(_("Path to server is not set"))
        server_path = os.path.dirname(server_path)
        file_path = os.path.join(server_path, self.file_name)
        if not os.path.exists(file_path):
            raise OSError(
                _("Server config '{0}' is not found").format(self.file_name))
        return file_path

    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("'{0}' object has no attribute '{1}'".format(
                                 self.__class__.__name__, name))


server_settings = ServerSettings()


class missions(object):

    _id_generator = None

    @classmethod
    def _get_settings(cls):
        value = user_settings.missions
        if value is None:
            value = {
                'list': [],
                'current_id': None,
            }
            user_settings.missions = value
        return value

    @classmethod
    def load(cls):
        return cls._get_settings().setdefault('list', [])

    @classmethod
    def save(cls, iterable):
        cls._get_settings()['list'] = [
            {
                'id': i[0],
                'name': i[1],
                'file_name': i[2],
                'duration': i[3],
            } for i in iterable
        ]
        user_settings.sync()

    @classmethod
    def count(cls):
        return len(cls.load())

    @classmethod
    def get_current_id(cls):
        return cls._get_settings().setdefault('current_id', None)

    @classmethod
    def set_current_id(cls, value):
        cls._get_settings()['current_id'] = value
        user_settings.sync()

    @classmethod
    def generate_id(cls):
        if cls._id_generator is None:

            def id_generator():
                number = max([m['id'] for m in cls.load()] or [0, ])
                while True:
                    number += 1
                    yield number

            cls._id_generator = id_generator()
        return next(cls._id_generator)

    @classmethod
    def get_current_mission(cls):
        current_id = cls.get_current_id()
        if current_id is not None:
            for m in cls.load():
                if m['id'] == current_id:
                    return m
