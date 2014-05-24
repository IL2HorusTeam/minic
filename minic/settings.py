# -*- coding: utf-8 -*-
import ConfigParser
import json
import platform
import os

import minic
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
            self.upgrade()

    def sync(self):
        """
        .. todo:: may raise some exception
        """
        with open(self.file_path, 'w') as f:
            self.version = minic.VERSION
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

    def upgrade(self):
        """
        Upgrade user settings from older versions.
        """
        if self.version != minic.VERSION:
            self._upgrade_to_0_1_8()
            self._upgrade_to_0_1_9()
            self.sync()

    def _upgrade_to_0_1_8(self):
        """
        Upgrade settings from the earliest version up to ``0.1.8``.
        """
        if self.version is not None:
            return

        from minic.models import MissionManager

        def fix_mission(mission):
            file_name = mission['file_name'].lstrip(os.path.sep)
            if file_name.startswith(MissionManager.dogfight_subpath):
                start = len(MissionManager.dogfight_subpath)
                file_name = file_name[start:].lstrip(os.path.sep)
            return (mission['id'], mission['name'], file_name, mission['duration'])

        MissionManager.update(map(fix_mission, MissionManager.all()))
        self.version = (0, 1, 8)

    def _upgrade_to_0_1_9(self):
        """
        Upgrade settings from ``0.1.8`` up to ``0.1.9``.
        """
        if tuple(self.version) != (0, 1, 8):
            return

        from minic.models import Mission, MissionManager
        MissionManager.update(map(
            lambda x: Mission(
                id=x['id'],
                name=x['name'],
                relative_path=x['file_name'],
                duration=x['duration']),
            MissionManager.all()))
        self.version = (0, 1, 9)


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
        self['cl_host'] = self._get_console_host()
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

    def _get_console_host(self):
        section = 'NET'
        attr_name = 'localHost'
        value = self._get_value(section, attr_name)
        if value is None:
            raise ValueError(
                _("Please, explicitly specify your local address as "
                  "'{0}' attribute in '{1}' secton in '{2}' file.").format(
                  attr_name, section, self.file_name))
        return value

    def _get_log_path(self):
        section = 'game'
        attr_name = 'eventlog'
        value = self._get_value(section, attr_name)
        if value is None:
            raise ValueError(
                _("Please, specify path to events log as "
                  "'{0}' attribute in '{1}' secton in '{2}' file.").format(
                  attr_name, section, self.file_name))
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
