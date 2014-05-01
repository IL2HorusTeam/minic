# -*- coding: utf-8 -*-
import os
import platform

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
