# -*- coding: utf-8 -*-
import tx_logging

from collections import namedtuple

from il2ds_middleware.parser import (
    ConsoleParser, DeviceLinkParser, EventLogParser,
)
from il2ds_middleware.protocol import (
    DeviceLinkClient, ReconnectingConsoleClientFactory,
)
from il2ds_middleware.service import (
    LogWatchingService, ClientServiceMixin as BaseClientServiceMixin,
)

from twisted.application.service import MultiService, Service
from twisted.internet import defer

from minic.settings import (
    server_settings, CONSOLE_TIMEOUT, DEVICE_LINK_TIMEOUT,
)
from minic.util import ugettext_lazy as _


LOG = tx_logging.getLogger(__name__)


class ClientServiceMixin(BaseClientServiceMixin):

    @property
    def cl_client(self):
        return self.parent.cl_client

    @property
    def dl_client(self):
        return self.parent.dl_client

    @property
    def connection_was_lost(self):
        return self.parent.connection_was_lost


class CommanderService(MultiService, ClientServiceMixin):

    def __init__(self):
        MultiService.__init__(self)

        # Init pilots service --------------------------------------------------
        from minic.service.pilots import PilotsService
        pilots = PilotsService()
        pilots.setServiceParent(self)

        # Init objects service -------------------------------------------------
        from minic.service.objects import ObjectsService
        objects = ObjectsService()
        objects.setServiceParent(self)

        # Init missions service ------------------------------------------------
        from minic.service.missions import MissionsService
        log_watcher = LogWatchingService()
        missions = MissionsService(log_watcher)
        log_parser = EventLogParser((pilots, objects, missions, ))
        log_watcher.set_parser(log_parser)
        missions.setServiceParent(self)

        # Init console and DeviceLink parsers ----------------------------------
        console_parser = ConsoleParser((pilots, missions, ))
        device_link_parser = DeviceLinkParser()
        log_parser = EventLogParser((pilots, objects, missions, ))

        # Group parsers and services -------------------------------------------
        self.parsers = namedtuple(
            'commander_parsers', ['console', 'device_link', 'log'])(
            console_parser, device_link_parser, log_parser)
        self.services = namedtuple(
            'commander_services', ['pilots', 'objects', 'missions'])(
            pilots, objects, missions)

    def startService(self):
        self.services.missions.log_watcher.log_path = server_settings.log_path
        MultiService.startService(self)
        self.cl_client.chat_all(
            _("Hello! Minicommander takes control over this server."))

    @defer.inlineCallbacks
    def stopService(self):
        if self.parent.is_connected:
            self.cl_client.chat_all(_("Minicommander quits. Good bye!"))
        yield MultiService.stopService(self)


class RootService(Service):

    dl_client = None
    cl_client = None
    connection_was_lost = False

    def __init__(self):
        self.cl_connector = None
        self.dl_connector = None

        self.cb_connection_done = None
        self.cb_connection_closed = None
        self.cb_connection_lost = None

        self.commander = CommanderService()
        self.commander.parent = self

    def set_callbacks(self,
                      on_connection_done=None,
                      on_connection_failed=None,
                      on_connection_closed=None,
                      on_connection_lost=None):
        self.cb_connection_done = on_connection_done
        self.cb_connection_failed = on_connection_failed
        self.cb_connection_closed = on_connection_closed
        self.cb_connection_lost = on_connection_lost

    def startService(self):
        server_settings.load()

        # Prepare Device Link client -------------------------------------------
        self.dl_client = DeviceLinkClient(
            address=(server_settings.dl_host, server_settings.dl_port),
            parser=self.commander.parsers.device_link,
            timeout=CONSOLE_TIMEOUT)
        self.dl_client.on_start.addCallback(self.start_console_connection)

        # Prepare for connection with server -----------------------------------
        self.client_factory = ReconnectingConsoleClientFactory(
            parser=self.commander.parsers.console,
            timeout=DEVICE_LINK_TIMEOUT)

        from twisted.internet import reactor
        self.dl_connector = reactor.listenUDP(0, self.dl_client)

        Service.startService(self)

    def start_console_connection(self, dl_client):
        """
        Start reliable connection to game server's console with reconnectinon
        support.
        """
        self._update_connection_callbacks()

        from twisted.internet import reactor
        self.cl_connector = reactor.connectTCP(server_settings.cl_host,
                                               server_settings.cl_port,
                                               self.client_factory)

    @defer.inlineCallbacks
    def stopService(self):
        """
        Stop everything. This method is called automatically when the reactor
        is stopped.
        """
        if not self.running:
            defer.returnValue(None)

        # Stop commander service if running ------------------------------------
        if self.commander.running:
            yield self.commander.stopService()

        # Stop Device Link UDP listener ----------------------------------------
        yield defer.maybeDeferred(self.dl_connector.stopListening)

        # Disconnect from game server's console, if connecting was started
        # or if connection was already established
        if self.cl_connector:
            self.client_factory.stopTrying()
            self.cl_connector.disconnect()

        yield Service.stopService(self)

    def _update_connection_callbacks(self):
        """
        Update callbacks which are called after the connection with game
        server's console is established or lost.
        """
        if not self.client_factory.continueTrying:
            return

        # On connecting --------------------------------------------------------
        d = self.client_factory.on_connecting.addCallback(
            self.on_connection_done)

        if self.cb_connection_done:
            d.addCallback(self.cb_connection_done)
        if self.cb_connection_failed:
            d.addErrback(self.cb_connection_failed)

        # On connection lost ---------------------------------------------------
        d = self.client_factory.on_connection_lost.addCallbacks(
            self.on_connection_closed, self.on_connection_lost)

        if self.cb_connection_closed:
            d.addCallback(self.cb_connection_closed)
        if self.cb_connection_lost:
            d.addErrback(self.cb_connection_lost)

    def on_connection_done(self, client):
        """
        This method is called after the connection with server's console is
        established. Main work starts from here.
        """
        self.cl_client = client
        self.commander.startService()

    def on_connection_closed(self, unused):
        self.cl_client = None
        self.connection_was_lost = False

    @defer.inlineCallbacks
    def on_connection_lost(self, reason):
        """
        This method is called after the connection with server's console is
        lost. Stop every work and clean up resources.
        """
        self.cl_client = None
        self.connection_was_lost = True
        self._update_connection_callbacks()
        yield self.commander.stopService()
        defer.returnValue(reason)

    @property
    def is_connected(self):
        return self.cl_client is not None


root_service = RootService()
