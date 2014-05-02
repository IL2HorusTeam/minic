# -*- coding: utf-8 -*-
import gtk

import tx_logging

from minic.resources import image_path, ui_path
from minic.settings import user_settings
from minic.util import ugettext_lazy as _


LOG = tx_logging.getLogger('ui')


def show_message(message, message_type, window=None):
    md = gtk.MessageDialog(
        window,
        gtk.DIALOG_DESTROY_WITH_PARENT,
        message_type,
        gtk.BUTTONS_CLOSE,
        unicode(message))
    md.run()
    md.destroy()


def show_error(message, window=None):
    show_message(message, gtk.MESSAGE_ERROR, window)


class SettingsWindow(object):

    def __init__(self):
        root = gtk.Builder()
        root.add_from_file(ui_path('settings'))

        self.window = root.get_object('window')
        self.window.set_size_request(350, 70)

        self.server_path = root.get_object('server_path')
        self._add_filter_for_path_selector()

        signals = {
            'on_b_apply_clicked': self.on_b_apply_clicked,
            'on_b_cancel_clicked': self.on_b_cancel_clicked,
        }
        root.connect_signals(signals)

        self._load_data()

    def _add_filter_for_path_selector(self):
        f_filter = gtk.FileFilter()
        f_filter.set_name("IL-2 FB DS")
        f_filter.add_pattern("il2server.exe")
        self.server_path.add_filter(f_filter)

    def _load_data(self):
        p = user_settings.server_path
        if p:
            self.server_path.set_filename(p)

    def _save_data(self):
        user_settings.server_path = self.server_path.get_filename()
        user_settings.sync()

    def show(self):
        self.window.show()

    def on_b_apply_clicked(self, widget):
        self._save_data()
        self.window.destroy()

    def on_b_cancel_clicked(self, widget):
        self.window.destroy()


class MainWindow(gtk.Window):

    title = _("Minic")
    icon_name = "logo.png"

    def __init__(self):
        super(MainWindow, self).__init__()

        self.set_title(self.title)
        self.set_size_request(250, 150)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_icon_from_file(image_path(self.icon_name))
        self.build_tray_icon()

        menu_bar = self.build_menu_bar()
        connection_frame = self.build_connection_frame()

        vbox = gtk.VBox(False, 3)
        vbox.pack_start(menu_bar, expand=False, fill=False, padding=0)
        vbox.pack_start(connection_frame, expand=False, fill=True, padding=0)
        self.add(vbox)

        self.connect('delete-event', lambda w, e: w.hide() or True)
        self.show_all()

    def build_menu_bar(self):
        m_bar = gtk.MenuBar()

        # Settings -------------------------------------------------------------
        m_settings = gtk.MenuItem(_("Settings"))
        m_settings.connect('button-press-event', self.on_menu_settings_click)
        m_bar.append(m_settings)

        # Quit -----------------------------------------------------------------
        m_quit = gtk.MenuItem(_("Quit"))
        m_quit.connect('activate', gtk.main_quit)
        m_bar.append(m_quit)

        return m_bar

    def on_menu_settings_click(self, widget, event):
        # Intercept only left mouse button
        if event.button != 1:
            return False
        SettingsWindow().show()

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
        button.connect('clicked', self.on_connect_clicked)
        to_page(label, button)

        # Connected page
        label = gtk.Label(_("Established"))
        label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#080'))
        button = gtk.Button(_("Disconnect"), gtk.STOCK_DISCONNECT)
        button.connect('clicked', self.on_disconnect_clicked)
        to_page(label, button)

        # Connecting page
        label = gtk.Label(_("Connecting") + '...')
        label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#555'))
        button = gtk.Button(_("Stop"), gtk.STOCK_STOP)
        button.connect('clicked', self.on_connect_stop_clicked)
        to_page(label, button)

        # Build frame ----------------------------------------------------------
        alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        alignment.set_padding(3, 3, 3, 3)
        alignment.add(stack)

        frame = gtk.Frame(label=_("Connection"))
        frame.add(alignment)
        return frame

    def on_connect_clicked(self, widget):
        print 'on_connect_clicked'

    def on_disconnect_clicked(self, widget):
        print 'on_disconnect_clicked'

    def on_connect_stop_clicked(self, widget):
        print 'on_connect_stop_clicked'

    def build_tray_icon(self):
        icon = gtk.status_icon_new_from_file(image_path(self.icon_name))
        icon.set_tooltip(self.title)
        icon.connect('popup-menu', self.on_tray_icon_popup)

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
        m_quit.connect('activate', gtk.main_quit)

        menu.show_all()
        menu.popup(None, None, None, event_button, event_time)
