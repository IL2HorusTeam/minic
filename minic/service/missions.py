# -*- coding: utf-8 -*-
"""
Commander's missions service.
"""
import time
import tx_logging

from copy import copy

from twisted.internet import defer
from twisted.internet.task import LoopingCall

from il2ds_middleware.constants import MISSION_STATUS
from il2ds_middleware.service import MissionsService as DefaultMissionsService

from minic.models import MissionManager
from minic.service import ClientServiceMixin
from minic.util import ugettext_lazy as _


LOG = tx_logging.getLogger(__name__)


class MissionsService(DefaultMissionsService, ClientServiceMixin):
    """
    Custom service for missions flow management.
    """
    mission_was_running = False
    current_mission = None
    time_left = 0

    _status_changed_cb = None
    _timer_tick_cb = None

    def __init__(self, log_watcher=None):
        self._timer = LoopingCall(self._timer_tick)
        DefaultMissionsService.__init__(self, log_watcher)

    def register_callbacks(self,
                           on_status_changed=None,
                           on_timer_tick=None):
        self._status_changed_cb = on_status_changed
        self._timer_tick_cb = on_timer_tick

    @ClientServiceMixin.radar_refresher
    def began(self, info=None):
        DefaultMissionsService.began(self, info)
        if self.current_mission is None:
            return

        self.time_left = self.current_mission.duration * 60
        self._timer.start(interval=1, now=False)
        self._set_status(MISSION_STATUS.PLAYING)

        self.cl_client.chat_all(unicode(_("Mission '{0}' is playing.")
                                .format(self.current_mission.name)))
        self.cl_client.chat_all(unicode(self.time_left_verbose_str))

    @ClientServiceMixin.radar_refresher
    def ended(self, info=None):
        DefaultMissionsService.ended(self, info)
        if self.current_mission is None:
            return
        self.cl_client.chat_all(unicode(_("Mission '{0}' was stopped.")
                                .format(self.current_mission.name)))
        self._on_ended()

    def startService(self):
        DefaultMissionsService.startService(self)
        if self.connection_was_lost and self.mission_was_running:
            return self.mission_run()

    @defer.inlineCallbacks
    def stopService(self):
        self.mission_was_running = self.is_mission_playing
        yield DefaultMissionsService.stopService(self)
        self._on_ended()

    def _on_ended(self):
        if self._timer.running:
            self._timer.stop()

        self.current_mission = None
        self.time_left = 0
        self._set_status(MISSION_STATUS.NOT_LOADED)

    @defer.inlineCallbacks
    def mission_run(self):
        mission = copy(MissionManager.get_current_mission())
        if mission is None:
            LOG.error("Failed to run mission: current mission is not set")
            self._set_status(MISSION_STATUS.NOT_LOADED)
            defer.returnValue(None)

        self._set_status(MISSION_STATUS.LOADING)
        self.cl_client.chat_all(
            unicode(_("Loading mission '{0}'...").format(mission.name)))
        relative_path = MissionManager.full_relative_path(mission.relative_path)

        try:
            yield self.cl_client.mission_load(relative_path)
            self._set_status(MISSION_STATUS.LOADED)
        except Exception as e:
            LOG.error("Failed to load mission '{0}': {1}".format(
                      mission.name, unicode(e)))
            self.cl_client.chat_all(unicode(_("Failed to load mission.")))
            self._set_status(MISSION_STATUS.NOT_LOADED)
            defer.returnValue(None)

        self._set_status(MISSION_STATUS.STARTING)
        self.current_mission = mission
        self.cl_client.chat_all(
            unicode(_("Starting mission '{0}'...").format(mission.name)))
        try:
            yield self.cl_client.mission_begin()
        except Exception as e:
            LOG.error("Failed to begin mission '{0}': {1}".format(
                      mission.name, unicode(e)))
            self.cl_client.chat_all(unicode(_("Failed to start mission.")))
            self.current_mission = None
            self._set_status(MISSION_STATUS.NOT_LOADED)

    def mission_stop(self):
        self._set_status(MISSION_STATUS.STOPPING)
        name = self.current_mission.name
        self.cl_client.chat_all(
            unicode(_("Stopping mission '{0}'...").format(name)))
        return self.cl_client.mission_destroy()

    def mission_restart(self):
        name = self.current_mission.name
        self.cl_client.chat_all(
            unicode(_("Restarting mission '{0}'...").format(name)))
        return self.update_playing_mission()

    @defer.inlineCallbacks
    def update_playing_mission(self):
        try:
            yield self.mission_stop()
            yield self.mission_run()
        except Exception as e:
            LOG.error("Failed to update playing mission: {0}".format(
                      unicode(e)))

    def _timer_tick(self):
        self.time_left -= 1
        if self._timer_tick_cb:
            self._timer_tick_cb()

        if self.time_left == 0:
            current_index = MissionManager.get_index_by_id(self.current_mission.id)

            def on_stopped(unused):
                new_index = (current_index + 1) % MissionManager.count()
                new_id = MissionManager.get_id_by_index(new_index)
                MissionManager.set_current_id(new_id)
                return self.mission_run()

            self.mission_stop().addCallback(on_stopped)

    def _set_status(self, status):
        self.status = status
        if self._status_changed_cb:
            self._status_changed_cb(status)

    @property
    def is_mission_playing(self):
        return self.status == MISSION_STATUS.PLAYING

    @property
    def time_left_str(self):
        return time.strftime('%H:%M:%S', time.gmtime(self.time_left))

    @property
    def time_left_verbose_str(self):
        return _("Time left: {0}.").format(self.time_left_str)
