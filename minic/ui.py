# -*- coding: utf-8 -*-
import gtk
import tx_logging

from minic.resources import image_path, ui_path
from minic.service import root_service
from minic.settings import user_settings
from minic.util import ugettext_lazy as _


LOG = tx_logging.getLogger('ui')


def show_message(message, message_type, parent=None):
    md = gtk.MessageDialog(
        parent,
        gtk.DIALOG_DESTROY_WITH_PARENT,
        message_type,
        gtk.BUTTONS_CLOSE,
        unicode(message))
    md.run()
    md.destroy()


def show_error(message, parent=None):
    show_message(message, gtk.MESSAGE_ERROR, parent)


class SettingsDialog(gtk.Dialog):

    def __init__(self, parent):
        super(SettingsDialog, self).__init__(
            title=_("Settings"),
            parent=parent,
            flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        b_apply = self.add_button(gtk.STOCK_APPLY, gtk.RESPONSE_APPLY)
        b_apply.connect('clicked', self.on_b_apply_clicked)

        icon = self.render_icon(gtk.STOCK_PREFERENCES, gtk.ICON_SIZE_MENU)
        self.set_icon(icon)
        self.set_default_size(350, 70)

        self._build_components()
        self._load_data()
        self.show_all()

    def _build_components(self):
        table = gtk.Table(rows=1, columns=2, homogeneous=False)
        table.set_col_spacings(10)
        self.vbox.pack_start(table, True, True, 0)

        # Server path row ------------------------------------------------------
        label = gtk.Label(_("Server executable"))
        self.server_path = gtk.FileChooserButton(
            _("Select IL-2 FB DS executable"))
        self._add_filter_for_path_selector()

        table.attach(label, 0, 1, 0, 1, gtk.FILL)
        table.attach(self.server_path, 1, 2, 0, 1)

    def _add_filter_for_path_selector(self):
        f_filter = gtk.FileFilter()
        f_filter.set_name("IL-2 FB DS")
        f_filter.add_pattern("il2server.exe")
        self.server_path.add_filter(f_filter)

    def _load_data(self):
        p = user_settings.server_path
        if p:
            self.server_path.set_filename(p)

    def on_b_apply_clicked(self, widget):
        user_settings.server_path = self.server_path.get_filename()
        user_settings.sync()


class MainWindow(gtk.Window):

    title = _("Minic")
    icon_name = "logo.png"

    class CONNECTION_TABS(object):
        DISCONNECTED = 0
        CONNECTED = 1
        CONNECTING = 2

    def __init__(self):
        super(MainWindow, self).__init__()

        self.set_title(self.title)
        self.set_size_request(350, 200)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_icon_from_file(image_path(self.icon_name))
        self.build_tray_icon()

        menu_bar = self.build_menu_bar()
        connection_frame = self.build_connection_frame()
        missions_frame = self.build_missions_frame()

        # Build layout ---------------------------------------------------------
        vbox = gtk.VBox(False, 3)
        vbox.pack_start(menu_bar, expand=False, fill=False, padding=0)
        vbox.pack_start(connection_frame, expand=False, fill=True, padding=0)
        vbox.pack_start(missions_frame, expand=False, fill=True, padding=0)
        self.add(vbox)

        root_service.set_callbacks(self.on_connection_done,
                                   self.on_connection_closed,
                                   self.on_connection_lost)
        self.connect('delete-event', lambda w, e: w.hide() or True)
        self.show_all()

    def build_tray_icon(self):
        icon = gtk.status_icon_new_from_file(image_path(self.icon_name))
        icon.set_tooltip(self.title)
        icon.connect('activate', self.on_tray_icon_activate)
        icon.connect('popup-menu', self.on_tray_icon_popup)

    def on_tray_icon_activate(self, widget):
        if self.props.visible:
            self.hide()
        else:
            self.show()

    def on_tray_icon_popup(self, icon, event_button, event_time):
        menu = gtk.Menu()

        if self.props.visible:
        # Hide -----------------------------------------------------------------
            m_hide = gtk.ImageMenuItem(_("Hide"))
            img = gtk.image_new_from_file(image_path('hide.png'))
            img.show()
            m_hide.set_image(img)
            menu.append(m_hide)
            m_hide.connect('activate', lambda w: self.hide())
        else:
        # Show -----------------------------------------------------------------
            m_show = gtk.ImageMenuItem(_("Show"))
            img = gtk.image_new_from_file(image_path('show.png'))
            img.show()
            m_show.set_image(img)
            menu.append(m_show)
            m_show.connect('activate', lambda w: self.show())

        # Separator ------------------------------------------------------------
        menu.append(gtk.SeparatorMenuItem())

        # Quit -----------------------------------------------------------------
        m_quit = gtk.ImageMenuItem(_("Quit"))
        img = gtk.image_new_from_icon_name('application-exit',
                                           gtk.ICON_SIZE_MENU)
        img.show()
        m_quit.set_image(img)
        menu.append(m_quit)
        m_quit.connect('activate', self.on_quit)

        menu.show_all()
        menu.popup(None, None, None, event_button, event_time)

    def build_menu_bar(self):
        m_bar = gtk.MenuBar()

        # Settings -------------------------------------------------------------
        m_settings = gtk.MenuItem(_("Settings"))
        m_settings.connect('activate', self.on_menu_settings_activate)
        m_bar.append(m_settings)

        # Quit -----------------------------------------------------------------
        m_quit = gtk.MenuItem(_("Quit"))
        m_quit.connect('activate', self.on_quit)
        m_bar.append(m_quit)

        return m_bar

    def on_menu_settings_activate(self, widget):
        d = SettingsDialog(self)
        d.run()
        d.destroy()

    def on_quit(self, *args):
        return self.stop_root().addBoth(lambda unused: gtk.main_quit())

    def build_connection_frame(self):
        # Stack ----------------------------------------------------------------
        stack = gtk.Notebook()
        self.connection_stack = stack
        stack.set_show_tabs(False)
        stack.set_show_border(False)

        # Build pages ----------------------------------------------------------
        def to_page(label, button):
            hbox = gtk.HBox(False, 2)
            hbox.pack_start(label, expand=False, fill=False, padding=0)
            hbox.pack_end(button, expand=False, fill=False, padding=0)
            stack.append_page(hbox)

        # Disconnected page
        label = gtk.Label(_("Not established"))
        label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#B00'))
        button = gtk.Button(_("Connect"), gtk.STOCK_CONNECT)
        button.set_tooltip_text(_("Connect to server"))
        button.connect('clicked', self.on_connect_clicked)
        to_page(label, button)

        # Connected page
        label = gtk.Label(_("Established"))
        label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#080'))
        button = gtk.Button(_("Disconnect"), gtk.STOCK_DISCONNECT)
        button.set_tooltip_text(_("Disconnect for server"))
        button.connect('clicked', self.on_disconnect_clicked)
        to_page(label, button)

        # Connecting page
        label = gtk.Label(_("Connecting") + '...')
        label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#555'))
        button = gtk.Button(_("Stop"), gtk.STOCK_STOP)
        button.set_tooltip_text(_("Stop connection attempt"))
        button.connect('clicked', self.on_connect_stop_clicked)
        to_page(label, button)

        # Build frame ----------------------------------------------------------
        alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        alignment.set_padding(3, 3, 3, 3)
        alignment.add(stack)

        frame = gtk.Frame(label=_("Server connection"))
        frame.add(alignment)

        return frame

    def on_connect_clicked(self, widget):
        try:
            root_service.startService()
        except Exception as e:
            show_error(e)
        else:
            self.connection_stack.set_current_page(
                MainWindow.CONNECTION_TABS.CONNECTING)

    def on_connect_stop_clicked(self, widget):
        self.stop_root()
        self.connection_stack.set_current_page(
            MainWindow.CONNECTION_TABS.DISCONNECTED)

    def on_disconnect_clicked(self, widget):
        self.stop_root()

    def stop_root(self):
        def errback(reason):
            LOG.error("Failed to stop root service: {0}".format(
                      unicode(reason.value)))
        return root_service.stopService().addErrback(errback)

    def build_missions_frame(self):
        table = gtk.Table(rows=4, columns=2, homogeneous=False)
        table.set_col_spacings(10)

        def to_label(name):
            label = gtk.Label(name)
            label.set_alignment(xalign=0, yalign=0.5)
            return label

        # Name row -------------------------------------------------------------
        label = to_label(_("Current"))
        table.attach(label, 0, 1, 0, 1, gtk.FILL)

        mission_selector = gtk.combo_box_new_text()
        table.attach(mission_selector, 1, 2, 0, 1)

        # State row ------------------------------------------------------------
        label = to_label(_("State"))
        table.attach(label, 0, 1, 1, 2, gtk.FILL)

        label = to_label("MISSION STATE")
        table.attach(label, 1, 2, 1, 2)

        # Time left row --------------------------------------------------------
        label = to_label(_("Time left"))
        table.attach(label, 0, 1, 2, 3, gtk.FILL)

        label = to_label("TIME LEFT")
        table.attach(label, 1, 2, 2, 3)

        # Controls row ---------------------------------------------------------
        def to_button(stock):
            image = gtk.Image()
            image.set_from_stock(stock, gtk.ICON_SIZE_BUTTON)
            button = gtk.Button()
            button.add(image)
            return button

        hbox = gtk.HBox(False, 8)
        alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        alignment.set_padding(5, 0, 0, 0)
        alignment.add(hbox)

        table.attach(alignment, 0, 2, 3, 4)

        button = to_button(gtk.STOCK_GOTO_FIRST)
        button.set_tooltip_text(_("First mission"))
        hbox.pack_start(button, False, False, 0)

        button = to_button(gtk.STOCK_MEDIA_PREVIOUS)
        button.set_tooltip_text(_("Previous mission"))
        hbox.pack_start(button, False, False, 0)

        button = to_button(gtk.STOCK_MEDIA_STOP)
        button.set_tooltip_text(_("Stop mission"))
        hbox.pack_start(button, False, False, 0)

        button = to_button(gtk.STOCK_MEDIA_PLAY)
        button.set_tooltip_text(_("Run mission"))
        hbox.pack_start(button, False, False, 0)

        button = to_button(gtk.STOCK_REFRESH)
        button.set_tooltip_text(_("Restart mission"))
        hbox.pack_start(button, False, False, 0)

        button = to_button(gtk.STOCK_MEDIA_NEXT)
        button.set_tooltip_text(_("Next mission"))
        hbox.pack_start(button, False, False, 0)

        button = to_button(gtk.STOCK_GOTO_LAST)
        button.set_tooltip_text(_("Last mission"))
        hbox.pack_start(button, False, False, 0)

        button = gtk.Button(_("Edit"), gtk.STOCK_EDIT)
        button.set_tooltip_text(_("Edit missions"))
        hbox.pack_end(button, False, False, 0)

        # Build frame ----------------------------------------------------------
        alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        alignment.set_padding(3, 3, 3, 3)
        alignment.add(table)

        frame = gtk.Frame(label=_("Mission"))
        frame.add(alignment)

        return frame

    def on_connection_done(self, *args):
        self.connection_stack.set_current_page(
            MainWindow.CONNECTION_TABS.CONNECTED)

    def on_connection_closed(self, *args):
        self.connection_stack.set_current_page(
            MainWindow.CONNECTION_TABS.DISCONNECTED)
        self._on_disconnected()

    def on_connection_lost(self, reason):
        self.connection_stack.set_current_page(
            MainWindow.CONNECTION_TABS.CONNECTING)
        self._on_disconnected()

    def _on_disconnected(self):
        pass
