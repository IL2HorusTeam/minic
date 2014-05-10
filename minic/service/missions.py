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
        self.mission_was_running = False
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
        if self.mission_info is None:
            return

        self.time_left = self.mission_info['duration'] * 60
        self._timer.start(interval=1, now=False)
        self._set_state(MISSION_STATE.RUNNING)

        self.cl_client.chat_all(unicode(_("Mission '{0}' is running.").format(
                                        self.mission_info['name'])))
        self.cl_client.chat_all(unicode(self.time_left_verbose_str))

    @ClientServiceMixin.radar_refresher
    def ended(self, info=None):
        DefaultMissionsService.ended(self, info)
        if self.mission_info is None:
            return
        self.cl_client.chat_all(unicode(
            _("Mission '{0}' was stopped.").format(self.mission_info['name'])))
        self._on_ended()

    def startService(self):
        DefaultMissionsService.startService(self)
        d = self.cl_client.mission_destroy()
        if self.connection_was_lost and self.mission_was_running:
            d.addCallback(lambda unused: self.mission_run())
        return d

    @defer.inlineCallbacks
    def stopService(self):
        self.mission_was_running = self.is_mission_running
        yield DefaultMissionsService.stopService(self)
        self._on_ended()

    def _on_ended(self):
        if self._timer.running:
            self._timer.stop()

        self.mission_info = None
        self.time_left = 0
        self._set_state(MISSION_STATE.STOPPED)

    @defer.inlineCallbacks
    def mission_run(self):
        self._set_state(MISSION_STATE.STARTING)
        mission_info = missions.get_current_mission().copy()
        if mission_info is None:
            LOG.error("Failed to run mission: current mission is not set")
            self._set_state(MISSION_STATE.STOPPED)
            defer.returnValue(None)

        name = mission_info['name']
        self.cl_client.chat_all(
            unicode(_("Loading mission '{0}'...").format(name)))
        try:
            yield self.cl_client.mission_load(mission_info['file_name'])
        except Exception as e:
            LOG.error("Failed to load mission '{0}': {1}".format(
                      name, unicode(e)))
            self.cl_client.chat_all(unicode(_("Failed to load mission.")))
            self._set_state(MISSION_STATE.STOPPED)
            defer.returnValue(None)

        self.mission_info = mission_info
        self.cl_client.chat_all(
            unicode(_("Starting mission '{0}'...").format(name)))
        try:
            yield self.cl_client.mission_begin()
        except Exception as e:
            LOG.error("Failed to begin mission '{0}': {1}".format(
                      name, unicode(e)))
            self.cl_client.chat_all(unicode(_("Failed to start mission.")))
            self.mission_info = None
            self._set_state(MISSION_STATE.STOPPED)

    def mission_stop(self):
        self._set_state(MISSION_STATE.STOPPING)
        self.cl_client.chat_all(unicode(_("Stopping mission...")))
        return self.cl_client.mission_destroy()

    @defer.inlineCallbacks
    def mission_restart(self):
        self.cl_client.chat_all(unicode(_("Restarting mission...")))
        yield self.mission_stop()
        yield self.mission_run()

    def current_was_changed(self):
        self.mission_restart()

    def _timer_tick(self):
        self.time_left -= 1
        if self.on_timer_tick:
            self.on_timer_tick()

        if self.time_left == 0:
            current_index = missions.get_index_by_id(self.mission_info['id'])

            def on_stopped(unused):
                new_index = (current_index + 1) % missions.count()
                new_id = missions.get_id_by_index(new_index)
                missions.set_current_id(new_id)
                return self.mission_run()

            self.mission_stop().addCallback(on_stopped)

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

    @property
    def time_left_verbose_str(self):
        return _("Time left: {0}").format(self.time_left_str)
