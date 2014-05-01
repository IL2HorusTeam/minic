# -*- coding: utf-8 -*-
import gtk

import tx_logging

from minic.resources import image_path
from minic.util import ugettext_lazy as _


LOG = tx_logging.getLogger('ui')


def show_message(message, message_type, window=None):
    md = gtk.MessageDialog(
        window,
        gtk.DIALOG_DESTROY_WITH_PARENT,
        message_type,
        gtk.BUTTONS_CLOSE,
        message
    )
    md.run()
    md.destroy()


def show_error(message, window=None):
    show_message(message, gtk.MESSAGE_ERROR, window)


class MainWindow(gtk.Window):

    title = _("Minic")
    icon_name = "logo.png"

    def __init__(self):
        super(MainWindow, self).__init__()

        LOG.error('hello')

        self.set_title(self.title)
        self.set_size_request(250, 150)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_icon_from_file(image_path(self.icon_name))
        self.build_tray_icon()

        menu_bar = self.build_menu_bar()

        vbox = gtk.VBox(False, 2)
        vbox.pack_start(menu_bar, False, False, 0)
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
        print 'on_menu_settings_click'

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
