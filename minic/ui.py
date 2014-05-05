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
        b_apply.connect('clicked', self.on_apply_clicked)

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

    def on_apply_clicked(self, widget):
        user_settings.server_path = self.server_path.get_filename()
        user_settings.sync()


class MissionsDialog(gtk.Dialog):

    def __init__(self, parent):
        super(MissionsDialog, self).__init__(
            title=_("Missions"),
            parent=parent,
            flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        b_apply = self.add_button(gtk.STOCK_APPLY, gtk.RESPONSE_APPLY)
        b_apply.connect('clicked', self.on_apply_clicked)

        self.set_default_size(500, 300)
        self._build_components()
        self.show_all()

    def _build_components(self):
        scrolled_tree = self._build_treeview()
        panel = self._build_side_panel()

        hbox = gtk.HBox(False, 3)
        hbox.pack_start(scrolled_tree, expand=True, fill=True, padding=0)
        hbox.pack_end(panel, expand=False, fill=False, padding=0)

        self.vbox.pack_start(hbox, True, True, 0)

    def _build_treeview(self):
        store = gtk.ListStore(str, str, int)
        self.treeview = gtk.TreeView(model=store)
        self.treeview.connect('cursor-changed', self.on_treeview_cursor_changed)

        # Name column ----------------------------------------------------------
        renderer = gtk.CellRendererText()
        renderer.set_property('editable', True)
        column = gtk.TreeViewColumn(_("Name"), renderer, text=0)
        column.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        column.set_resizable(True)
        column.set_expand(True)
        self.treeview.append_column(column)

        # File column ----------------------------------------------------------
        renderer = gtk.CellRendererText()
        renderer.set_property('editable', True)
        column = gtk.TreeViewColumn(_("File"), renderer, text=1)
        column.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        column.set_resizable(True)
        column.set_expand(True)
        self.treeview.append_column(column)

        # Duration column ------------------------------------------------------
        renderer = gtk.CellRendererText()
        renderer.set_property('editable', True)
        column = gtk.TreeViewColumn(_("Duration (min)"), renderer, text=2)
        self.treeview.append_column(column)

        # Build scrolled window ------------------------------------------------
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.add(self.treeview)

        return scrolled_window

    def _build_side_panel(self):
        vbox = gtk.VBox(False, 3)

        button = gtk.Button(stock=gtk.STOCK_NEW)
        button.set_tooltip_text(_("Add new mission to list"))
        button.connect('clicked', self.on_new_clicked)
        vbox.pack_start(button, False, False, 0)

        button = gtk.Button(stock=gtk.STOCK_DELETE)
        button.set_tooltip_text(_("Delete selected mission from list"))
        button.connect('clicked', self.on_delete_clicked)
        vbox.pack_start(button, False, False, 0)

        vbox.pack_start(gtk.HSeparator(), False, False, 0)

        button = gtk.Button(stock=gtk.STOCK_GOTO_TOP)
        button.set_tooltip_text(_("Move selected mission to top"))
        button.connect('clicked', self.on_move_to_top)
        vbox.pack_start(button, False, False, 0)

        button = gtk.Button(stock=gtk.STOCK_GO_UP)
        button.set_tooltip_text(_("Move selected mission up"))
        button.connect('clicked', self.on_move_up)
        vbox.pack_start(button, False, False, 0)

        button = gtk.Button(stock=gtk.STOCK_GO_DOWN)
        button.set_tooltip_text(_("Move selected mission down"))
        button.connect('clicked', self.on_move_down)
        vbox.pack_start(button, False, False, 0)

        button = gtk.Button(stock=gtk.STOCK_GOTO_BOTTOM)
        button.set_tooltip_text(_("Move selected mission to bottom"))
        button.connect('clicked', self.on_move_to_bottom)
        vbox.pack_start(button, False, False, 0)

        return vbox

    def on_new_clicked(self, widget):
        if len(self.store) == 0:
            # Create default row
            data = (_("Some mission"), None, 60)
            cursor = 0
        else:
            # TODO: do not allow existing empty cells

            # Copy existing row
            cursor = self.current_cursor
            selected_name, file_name, duration = self.store[cursor]

            def split_name(name):
                chunks = name.rsplit('.', 1)
                if len(chunks) == 1:
                    return chunks[0], 0
                else:
                    return chunks[0], int(chunks[1])

            # Define starting suffix for name of new mission
            name, suffix = split_name(selected_name)
            suffix += 1

            # Fix suffix if name already used
            for i, row in enumerate(self.store):
                if i == cursor:
                    continue
                i_name, i_suffix = split_name(name=row[0])
                if i_name != name or not i_suffix:
                    continue
                if suffix <= i_suffix:
                    suffix = i_suffix + 1

            name = "{0}.{1}".format(name, suffix)
            data = (name, file_name, duration)
            cursor += 1

        self.store.insert(cursor, data)
        self.treeview.set_cursor(cursor)
        self._on_data_changed()

    def on_delete_clicked(self, widget):
        cursor = self.current_cursor
        if cursor is None:
            return

        del self.store[cursor]

        length = len(self.store)
        if length:
            if cursor < length:
                self.treeview.set_cursor(cursor)
            else:
                self.treeview.set_cursor(length - 1)

        self._on_data_changed()

    def on_move_to_top(self, widget):
        print 'on_move_to_top'

    def on_move_up(self, widget):
        print 'on_move_up'

    def on_move_down(self, widget):
        print 'on_move_down'

    def on_move_to_bottom(self, widget):
        print 'on_move_to_bottom'

    def on_apply_clicked(self, widget):
        print 'on_apply_clicked'

    def on_treeview_cursor_changed(self, widget):
        print 'on_treeview_cursor_changed'

    def _on_data_changed(self):
        print '_on_data_changed'

    @property
    def store(self):
        return self.treeview.get_model()

    @property
    def current_cursor(self):
        cursor = self.treeview.get_cursor()[0]
        if cursor is not None:
            (cursor, ) = cursor
        return cursor


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

        def to_label(name):
            label = gtk.Label(name)
            label.set_alignment(xalign=0, yalign=0.5)
            return label

        def to_button(stock):
            image = gtk.Image()
            image.set_from_stock(stock, gtk.ICON_SIZE_BUTTON)
            button = gtk.Button()
            button.add(image)
            return button

        table = gtk.Table(rows=4, columns=2, homogeneous=False)
        table.set_col_spacings(10)

        # Name row -------------------------------------------------------------
        label = to_label(_("Current"))
        mission_selector = gtk.combo_box_new_text()
        mission_selector.set_tooltip_text(_("Current mission"))

        button = to_button(gtk.STOCK_EDIT)
        button.set_tooltip_text(_("Edit missions list"))
        button.connect('clicked', self.on_edit_missions_clicked)

        hbox = gtk.HBox(False, 2)
        hbox.pack_start(mission_selector, True, True, 0)
        hbox.pack_start(button, False, False, 0)

        table.attach(label, 0, 1, 0, 1, gtk.FILL)
        table.attach(hbox, 1, 2, 0, 1)

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
        hbox = gtk.HBox(False, 7)
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

        # Build frame ----------------------------------------------------------
        alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        alignment.set_padding(3, 3, 3, 3)
        alignment.add(table)

        frame = gtk.Frame(label=_("Mission"))
        frame.add(alignment)

        return frame

    def on_edit_missions_clicked(self, widget):
        d = MissionsDialog(self)
        result = d.run()
        # TODO:
        d.destroy()

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
