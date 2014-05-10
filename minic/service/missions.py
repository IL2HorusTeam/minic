# -*- coding: utf-8 -*-
"""
Commander's missions service.
"""
import time
import tx_logging

from twisted.internet import defer
from twisted.internet.task import LoopingCall

from il2ds_middleware.service import MissionsService as DefaultMissionsService

from minic.constants import MISSION_STATE
from minic.service import ClientServiceMixin
from minic.settings import missions
from minic.util import ugettext_lazy as _


LOG = tx_logging.getLogger(__name__)


class MissionsService(DefaultMissionsService, ClientServiceMixin):
    """
    Custom service for missions flow management.
    """

    def __init__(self, log_watcher=None):
        self.mission_info = None
        self.state = MISSION_STATE.STOPPED
        self.time_left = 0

        self._timer = LoopingCall(self._timer_tick)

        self.on_state_changed = None
        self.on_timer_tick = None

        DefaultMissionsService.__init__(self, log_watcher)

    def register_callbacks(self,
                           on_state_changed=None,
                           on_timer_tick=None):
        self.on_state_changed = on_state_changed
        self.on_timer_tick = on_timer_tick

    @ClientServiceMixin.radar_refresher
    def began(self, info=None):
        DefaultMissionsService.began(self, info)
        self.time_left = self.mission_info['duration'] * 60
        self._timer.start(interval=1, now=False)
        self._set_state(MISSION_STATE.RUNNING)

    @ClientServiceMixin.radar_refresher
    def ended(self, info=None):
        DefaultMissionsService.ended(self, info)
        self._on_ended()

    def startService(self):
        DefaultMissionsService.startService(self)
        return self.cl_client.mission_destroy()

    @defer.inlineCallbacks
    def stopService(self):
        yield DefaultMissionsService.stopService(self)
        self._on_ended()

    def _on_ended(self):
        if self._timer.running:
            self._timer.stop()

        self.mission_info = None
        self.time_left = 0
        self._set_state(MISSION_STATE.STOPPED)

    ############################################################################
    # TODO: if connection lost? if connection established again?
    ############################################################################

    @defer.inlineCallbacks
    def mission_run(self):
        self._set_state(MISSION_STATE.STARTING)

        mission_info = missions.get_current_mission()

        if mission_info is None:
            LOG.error("Failed to run mission: current mission is not set")
            self._set_state(MISSION_STATE.STOPPED)
            defer.returnValue(None)

        file_name = mission_info['file_name']

        try:
            yield self.cl_client.mission_load(file_name)
        except Exception as e:
            LOG.error("Failed to load mission '{0}': {1}".format(
                      file_name, unicode(e)))
            self._set_state(MISSION_STATE.STOPPED)
            defer.returnValue(None)

        self.mission_info = mission_info

        try:
            yield self.cl_client.mission_begin()
        except Exception as e:
            LOG.error("Failed to begin mission '{0}': {1}".format(
                      file_name, unicode(e)))
            self.mission_info = None
            self._set_state(MISSION_STATE.STOPPED)

    def mission_stop(self):
        self._set_state(MISSION_STATE.STOPPING)
        return self.cl_client.mission_destroy()

    def mission_restart(self):
        self._set_state(MISSION_STATE.RESTARTING)
        # TODO:

    def mission_update_current(self):
        print 'mission_update_current'
        # TODO:

    def _timer_tick(self):
        self.time_left -= 1

        # TODO:

        if self.on_timer_tick:
            self.on_timer_tick()

    def _set_state(self, state):
        self.state = state
        if self.on_state_changed:
            self.on_state_changed(state)

    @property
    def is_mission_running(self):
        return self.state == MISSION_STATE.RUNNING

    @property
    def time_left_str(self):
        return time.strftime('%H:%M:%S', time.gmtime(self.time_left))
