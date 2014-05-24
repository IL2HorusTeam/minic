# -*- coding: utf-8 -*-
from il2ds_middleware.constants import MISSION_STATUS

from minic.util import ugettext_lazy as _


MISSION_STATUS_INFO = {
    MISSION_STATUS.LOADING: {
        'verbose_name': _("Loading..."),
        'color_hex': 'FF8F00',
    },
    MISSION_STATUS.LOADED: {
        'verbose_name': _("Loaded"),
        'color_hex': 'FD5800',
    },
    MISSION_STATUS.STOPPING: {
        'verbose_name': _("Stopping..."),
        'color_hex': 'D44037',
    },
    MISSION_STATUS.NOT_LOADED: {
        'verbose_name': _("Not loaded"),
        'color_hex': '7D2315',
    },
    MISSION_STATUS.STARTING: {
        'verbose_name': _("Starting..."),
        'color_hex': '8FC31F',
    },
    MISSION_STATUS.PLAYING: {
        'verbose_name': _("Running"),
        'color_hex': '009944',
    },
}
