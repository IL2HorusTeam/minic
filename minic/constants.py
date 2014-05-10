# -*- coding: utf-8 -*-
from candv import VerboseValueConstant, Constants

from minic.util import ugettext_lazy as _


class MISSION_STATE(Constants):

    STARTING = VerboseValueConstant('#555', _("Starting..."))
    RUNNING = VerboseValueConstant('#080', _("Running"))

    STOPPING = VerboseValueConstant('#555', _("Stopping..."))
    STOPPED = VerboseValueConstant('#B00', _("Stopped"))
