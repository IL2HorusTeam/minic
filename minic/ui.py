# -*- coding: utf-8 -*-
import gtk
import tx_logging

from il2ds_middleware.constants import MISSION_STATUS

from minic.constants import MISSION_STATUS_INFO
from minic.models import MissionManager
from minic.resources import image_path
from minic.service import root_service
from minic.settings import user_settings
from minic.util import ugettext_lazy as _


LOG = tx_logging.getLogger('ui')


def show_message(message, message_type, parent=None):
    md = gtk.MessageDialog(parent,
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
        f_filter.set_name("il2server.exe")
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

    class COLUMNS(object):
        ID = 0
        NAME = 1
        RELATIVE_PATH = 2
        DURATION = 3

    def __init__(self, parent):
        super(MissionsDialog, self).__init__(
            title=_("Missions"),
            parent=parent,
            flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        b_apply = gtk.Button(stock=gtk.STOCK_APPLY)
        b_apply.connect('clicked', self.on_apply_clicked)
        self.action_area.add(b_apply)

        self.set_default_size(700, 400)
        self._build_components()
        self._load_data()
        self.show_all()

    def _build_components(self):
        scrolled_tree = self._build_treeview()
        panel = self._build_side_panel()

        hbox = gtk.HBox(False, 3)
        hbox.pack_start(scrolled_tree, expand=True, fill=True, padding=0)
        hbox.pack_end(panel, expand=False, fill=False, padding=0)

        self.vbox.pack_start(hbox, True, True, 0)

    def _build_treeview(self):
        store = gtk.ListStore(long, str, str, int)
        self.treeview = gtk.TreeView(model=store)
        self.treeview.connect('cursor-changed',
                              self.on_treeview_cursor_changed)
        self.treeview.connect('button-press-event',
                              self.on_treeview_button_press_event)

        # ID column ------------------------------------------------------------
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn(None, renderer,
                                    text=MissionsDialog.COLUMNS.ID)
        column.set_visible(False)
        self.treeview.append_column(column)

        # Name column ----------------------------------------------------------
        def on_name_edited(cell, path, new_value):
            if not new_value:
                show_error(_("Name value cannot be empty"), self)
            else:
                self.store[path][MissionsDialog.COLUMNS.NAME] = new_value

        renderer = gtk.CellRendererText()
        renderer.set_property('editable', True)
        renderer.connect('edited', on_name_edited)
        column = gtk.TreeViewColumn(_("Name"), renderer,
                                    text=MissionsDialog.COLUMNS.NAME)
        column.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        column.set_resizable(True)
        column.set_expand(True)
        self.treeview.append_column(column)

        # File column ----------------------------------------------------------
        def relative_path_renderer(treeviewcolumn, cell, model, iterator):
            value = model.get_value(iterator,
                                    MissionsDialog.COLUMNS.RELATIVE_PATH)
            if not value:
                value = _("Not selected")
            cell.set_property('text', value)

        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn(
            _("File"), renderer, text=MissionsDialog.COLUMNS.RELATIVE_PATH)
        column.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        column.set_resizable(True)
        column.set_expand(True)
        column.set_cell_data_func(renderer, relative_path_renderer)
        self.treeview.append_column(column)
        self.column_relative_path = column

        # Duration column ------------------------------------------------------
        def on_duration_edited(cell, path, new_value):
            if not new_value:
                show_error(_("Duration value cannot be empty"), self)
                return
            try:
                value = int(new_value)
            except ValueError:
                show_error(_("Duration value must be an integer"), self)
                return

            if value <= 0:
                show_error(_("Duration value must be greater than 0"), self)
            else:
                self.store[path][MissionsDialog.COLUMNS.DURATION] = value

        renderer = gtk.CellRendererText()
        renderer.set_property('editable', True)
        renderer.connect('edited', on_duration_edited)
        column = gtk.TreeViewColumn(_("Duration (min)"), renderer,
                                    text=MissionsDialog.COLUMNS.DURATION)
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
        self.b_delete = button

        vbox.pack_start(gtk.HSeparator(), False, False, 0)

        button = gtk.Button(stock=gtk.STOCK_GOTO_TOP)
        button.set_tooltip_text(_("Move selected mission to top"))
        button.connect('clicked', self.on_move_to_top)
        vbox.pack_start(button, False, False, 0)
        self.b_move_to_top = button

        button = gtk.Button(stock=gtk.STOCK_GO_UP)
        button.set_tooltip_text(_("Move selected mission up"))
        button.connect('clicked', self.on_move_up)
        vbox.pack_start(button, False, False, 0)
        self.b_move_up = button

        button = gtk.Button(stock=gtk.STOCK_GO_DOWN)
        button.set_tooltip_text(_("Move selected mission down"))
        button.connect('clicked', self.on_move_down)
        vbox.pack_start(button, False, False, 0)
        self.b_move_down = button

        button = gtk.Button(stock=gtk.STOCK_GOTO_BOTTOM)
        button.set_tooltip_text(_("Move selected mission to bottom"))
        button.connect('clicked', self.on_move_to_bottom)
        vbox.pack_start(button, False, False, 0)
        self.b_move_to_bottom = button

        return vbox

    def on_new_clicked(self, widget):
        new_id = MissionManager.generate_id()

        if len(self.store) == 0:
            # Create default row
            cursor = 0
            name = _("New mission")
            relative_path = None
            duration = 60
        else:
            # Copy existing row
            cursor = self.current_cursor
            id_, selected_name, relative_path, duration = self.store[cursor]

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
                i_name, i_suffix = split_name(row[MissionsDialog.COLUMNS.NAME])
                if i_name != name or not i_suffix:
                    continue
                if suffix <= i_suffix:
                    suffix = i_suffix + 1

            name = "{0}.{1}".format(name, suffix)
            cursor += 1

        self.store.insert(cursor, (new_id, name, relative_path, duration))
        self._on_data_changed()
        self.treeview.set_cursor(cursor)

    def on_delete_clicked(self, widget):
        cursor = self.current_cursor
        if cursor is None:
            return

        del self.store[cursor]
        self._on_data_changed()

        total = len(self.store)
        if total:
            if cursor < total - 1:
                self.treeview.set_cursor(cursor)
            else:
                self.treeview.set_cursor(total - 1)

    def on_move_to_top(self, widget):
        store = self.store
        cursor = self.current_cursor
        data = tuple(store[cursor])

        del store[cursor]
        store.prepend(data)
        self.treeview.set_cursor(0)

    def on_move_up(self, widget):
        self._move_current_row(delta=-1)

    def on_move_down(self, widget):
        self._move_current_row(delta=1)

    def _move_current_row(self, delta):
        store = self.store
        cursor = self.current_cursor
        data = tuple(store[cursor])

        del store[cursor]
        cursor += delta
        store.insert(cursor, data)
        self.treeview.set_cursor(cursor)

    def on_move_to_bottom(self, widget):
        store = self.store
        cursor = self.current_cursor
        data = tuple(store[cursor])

        del store[cursor]
        store.append(data)
        self.treeview.set_cursor(len(store) - 1)

    def on_treeview_cursor_changed(self, widget):
        cursor = self.current_cursor
        total = len(self.store)
        if cursor is None:
            self._set_controls_sensitive(False,
                                         self.b_delete, self.b_move_to_top,
                                         self.b_move_up, self.b_move_down,
                                         self.b_move_to_bottom)
        elif total <= 1:
            self._set_controls_sensitive(False,
                                         self.b_move_to_top, self.b_move_up,
                                         self.b_move_down,
                                         self.b_move_to_bottom)
        else:
            flag = cursor > 0
            self._set_controls_sensitive(flag,
                                         self.b_move_to_top, self.b_move_up)
            flag = cursor < total - 1
            self._set_controls_sensitive(flag,
                                         self.b_move_to_bottom,
                                         self.b_move_down)

    def on_treeview_button_press_event(self, treeview, event):
        if not event.button == 1:
            return

        info = treeview.get_path_at_pos(int(event.x), int(event.y))
        if info is None:
            return

        path, column, cell_x, cell_y = info
        store = treeview.get_model()

        if column == self.column_relative_path:

            if not user_settings.server_path:
                show_error(_("Please, set path to game server"), self)
                return

            relative_path = store[path][MissionsDialog.COLUMNS.RELATIVE_PATH]
            chooser = gtk.FileChooserDialog(title=_("Select IL-2 FB mission"),
                                            action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                            buttons=(gtk.STOCK_CANCEL,
                                                     gtk.RESPONSE_CANCEL,
                                                     gtk.STOCK_OPEN,
                                                     gtk.RESPONSE_OK))
            if relative_path is None:
                chooser.set_current_folder(MissionManager.get_root_path())
            else:
                file_name = MissionManager.absolute_path(relative_path)
                chooser.set_filename(file_name)

            f_filter = gtk.FileFilter()
            f_filter.set_name("IL-2 FB missions (*.mis)")
            f_filter.add_pattern("*.mis")
            chooser.add_filter(f_filter)

            response = chooser.run()
            relative_path = chooser.get_filename()
            chooser.destroy()

            if response != gtk.RESPONSE_OK:
                return

            try:
                relative_path = \
                    MissionManager.short_relative_path(relative_path)
            except ValueError as e:
                show_error(unicode(e))
            else:
                store[path][MissionsDialog.COLUMNS.RELATIVE_PATH] = \
                    relative_path

    def _on_data_changed(self):
        flag = len(self.store) > 0
        self._set_controls_sensitive(flag, self.b_delete)
        if not flag:
            self._set_controls_sensitive(False,
                                         self.b_move_to_top, self.b_move_up,
                                         self.b_move_down,
                                         self.b_move_to_bottom)

    def _set_controls_sensitive(self, value, *widgets):
        map(lambda x: x.set_sensitive(value), widgets)

    def on_apply_clicked(self, widget):
        names = []
        for row in self.store:
            if row[MissionsDialog.COLUMNS.RELATIVE_PATH] is None:
                names.append(row[MissionsDialog.COLUMNS.NAME])
        if names:
            message = _("Please, select files for next missions: {0}.").format(
                        ', '.join(names))
            show_error(message, self)
        else:
            self._save_data()
            self.response(gtk.RESPONSE_APPLY)

    def _load_data(self):
        store = self.store
        store.clear()
        for mission in MissionManager.all():
            store.append(mission)
        self._on_data_changed()

    def _save_data(self):
        MissionManager.update(self.store)

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
        self.set_size_request(350, 215)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_icon_from_file(image_path(self.icon_name))
        self.build_tray_icon()

        tool_bar = self.build_tool_bar()
        connection_frame = self.build_connection_frame()
        missions_frame = self.build_missions_frame()

        # Build layout ---------------------------------------------------------
        vbox = gtk.VBox(False, 3)
        vbox.pack_start(tool_bar, expand=False, fill=False, padding=0)
        vbox.pack_start(connection_frame, expand=False, fill=True, padding=0)
        vbox.pack_start(missions_frame, expand=False, fill=True, padding=0)
        self.add(vbox)

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

    def build_tool_bar(self):
        toolbar = gtk.Toolbar()

        # Settings -------------------------------------------------------------
        settings = gtk.ToolButton(gtk.STOCK_PREFERENCES)
        settings.connect("clicked", self.on_menu_settings_clicked)
        toolbar.insert(settings, 0)

        toolbar.insert(gtk.SeparatorToolItem(), 1)

        # Quit -----------------------------------------------------------------
        quit = gtk.ToolButton(gtk.STOCK_QUIT)
        quit.connect("clicked", self.on_quit)
        toolbar.insert(quit, 2)

        return toolbar

    def on_menu_settings_clicked(self, widget):
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
        label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#7d2315'))
        button = gtk.Button(_("Connect"), gtk.STOCK_CONNECT)
        button.set_tooltip_text(_("Connect to server"))
        button.connect('clicked', self.on_connect_clicked)
        to_page(label, button)

        # Connected page
        label = gtk.Label(_("Established"))
        label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#009944'))
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

        root_service.set_callbacks(self.on_connection_done,
                                   self.on_connection_failed,
                                   self.on_connection_closed,
                                   self.on_connection_lost)
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

        # Current mission row --------------------------------------------------
        label = to_label(_("Current"))

        store = gtk.ListStore(long, str)
        mission_selector = gtk.ComboBox(store)
        cell = gtk.CellRendererText()
        mission_selector.pack_start(cell)
        # display only 2nd column of data model:
        mission_selector.add_attribute(cell, 'text', 1)
        mission_selector.set_tooltip_text(_("Current mission"))
        mission_selector.connect('changed', self.on_mission_selector_changed)

        def patch_mission_selector():
            import types

            def clear_store(self):
                self.is_clearing = True
                gtk.ListStore.clear(self)
                self.is_clearing = False

            store.is_clearing = False
            store.clear = types.MethodType(clear_store, store)

            def set_active_not_from_ui(self, index):
                self.is_changed_not_from_ui = True
                self.set_active(index)
                self.is_changed_not_from_ui = False

            mission_selector.is_changed_not_from_ui = False
            mission_selector.set_active_not_from_ui = types.MethodType(
                set_active_not_from_ui, mission_selector)

        patch_mission_selector()
        self.mission_selector = mission_selector

        button = to_button(gtk.STOCK_EDIT)
        button.set_tooltip_text(_("Edit missions list"))
        button.connect('clicked', self.on_edit_missions_clicked)
        self.b_mission_list_edit = button

        hbox = gtk.HBox(False, 2)
        hbox.pack_start(mission_selector, True, True, 0)
        hbox.pack_start(button, False, False, 0)

        table.attach(label, 0, 1, 0, 1, gtk.FILL)
        table.attach(hbox, 1, 2, 0, 1)

        # State row ------------------------------------------------------------
        label = to_label(_("State"))
        table.attach(label, 0, 1, 1, 2, gtk.FILL)

        self.lb_mission_status = to_label("MISSION STATE")
        table.attach(self.lb_mission_status, 1, 2, 1, 2)

        # Time left row --------------------------------------------------------
        label = to_label(_("Time left"))
        table.attach(label, 0, 1, 2, 3, gtk.FILL)

        self.lb_mission_time_left = to_label("TIME LEFT")
        table.attach(self.lb_mission_time_left, 1, 2, 2, 3)

        # Controls row ---------------------------------------------------------
        button = to_button(gtk.STOCK_GOTO_FIRST)
        button.set_tooltip_text(_("First mission"))
        button.connect('clicked', self.on_b_mission_first_clicked)
        self.b_mission_first = button

        button = to_button(gtk.STOCK_MEDIA_PREVIOUS)
        button.set_tooltip_text(_("Previous mission"))
        button.connect('clicked', self.on_b_mission_prev_clicked)
        self.b_mission_prev = button

        button = to_button(gtk.STOCK_MEDIA_STOP)
        button.set_tooltip_text(_("Stop mission"))
        method = root_service.commander.services.missions.mission_stop
        button.connect('clicked', lambda *args: method())
        self.b_mission_stop = button

        button = to_button(gtk.STOCK_MEDIA_PLAY)
        button.set_tooltip_text(_("Run mission"))
        method = root_service.commander.services.missions.mission_run
        button.connect('clicked', lambda *args: method())
        self.b_mission_run = button

        button = to_button(gtk.STOCK_REFRESH)
        button.set_tooltip_text(_("Restart mission"))
        method = root_service.commander.services.missions.mission_restart
        button.connect('clicked', lambda *args: method())
        self.b_mission_restart = button

        button = to_button(gtk.STOCK_MEDIA_NEXT)
        button.set_tooltip_text(_("Next mission"))
        button.connect('clicked', self.on_b_mission_next_clicked)
        self.b_mission_next = button

        button = to_button(gtk.STOCK_GOTO_LAST)
        button.set_tooltip_text(_("Last mission"))
        button.connect('clicked', self.on_b_mission_last_clicked)
        self.b_mission_last = button

        hbox = gtk.HBox(False, 7)
        hbox.pack_start(self.b_mission_first, False, False, 0)
        hbox.pack_start(self.b_mission_prev, False, False, 0)
        hbox.pack_start(self.b_mission_stop, False, False, 0)
        hbox.pack_start(self.b_mission_run, False, False, 0)
        hbox.pack_start(self.b_mission_restart, False, False, 0)
        hbox.pack_start(self.b_mission_next, False, False, 0)
        hbox.pack_start(self.b_mission_last, False, False, 0)

        alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        alignment.set_padding(5, 0, 0, 0)
        alignment.add(hbox)

        table.attach(alignment, 0, 2, 3, 4)

        # Build frame ----------------------------------------------------------
        alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        alignment.set_padding(3, 3, 3, 3)
        alignment.add(table)

        frame = gtk.Frame(label=_("Mission"))
        frame.add(alignment)

        self._update_missions_box()
        self._display_mission_status()
        self._display_mission_time_left()

        root_service.commander.services.missions.register_callbacks(
            self.on_mission_status_changed,
            self.on_mission_timer_tick)

        return frame

    def on_edit_missions_clicked(self, widget):
        d = MissionsDialog(self)
        result = d.run()
        if result == gtk.RESPONSE_APPLY:
            self._update_missions_box()
        d.destroy()

    def _update_missions_box(self):
        store = self.mission_selector.get_model()

        old_index = self.mission_selector.get_active()
        old_id = (MissionManager.get_current_id() if old_index == -1 else
                  store[old_index][0])

        store.clear()
        new_index = -1

        for i, m in enumerate(MissionManager.all()):
            store.append((m.id, m.name, ))
            if old_id is not None and old_id == m.id:
                new_index = i

        if len(store) and new_index == -1:
            # Explicilty set current mission if if was not set
            new_index = 0

        if new_index == -1:
            # if mission list is empty, disable all mission flow controls
            self._update_mission_flow_buttons()
            # but if some mission was running, make it possible to stop it
            if root_service.commander.services.missions.is_mission_playing:
                self.b_mission_stop.set_sensitive(True)
        else:
            self.mission_selector.set_active(new_index)

    def on_mission_selector_changed(self, widget):
        store = widget.get_model()

        if store.is_clearing:
            return

        index = widget.get_active()

        old_id = MissionManager.get_current_id()
        new_id = None if index == -1 else store[index][0]

        if new_id != old_id:
            MissionManager.set_current_id(new_id)
            missions = root_service.commander.services.missions
            if (
                widget.is_changed_not_from_ui is False
                and missions.is_mission_playing
            ):
                missions.update_playing_mission()

        self._update_mission_flow_buttons()

    def _lock_mission_controls(self):
        self.mission_selector.set_sensitive(False)
        self.b_mission_list_edit.set_sensitive(False)
        self._disable_mission_flow_buttons()

    def _unlock_mission_controls(self):
        self.mission_selector.set_sensitive(True)
        self.b_mission_list_edit.set_sensitive(True)
        self._update_mission_flow_buttons()

    def _update_mission_flow_buttons(self):
        total = len(self.mission_selector.get_model())

        if total:
            index = self.mission_selector.get_active()

            missions = root_service.commander.services.missions
            is_running = missions.is_mission_playing

            self.b_mission_first.set_sensitive(index > 0)
            self.b_mission_prev.set_sensitive(total > 1)
            self.b_mission_stop.set_sensitive(is_running)
            self.b_mission_run.set_sensitive(
                root_service.is_connected and not is_running)
            self.b_mission_restart.set_sensitive(is_running)
            self.b_mission_next.set_sensitive(total > 1)
            self.b_mission_last.set_sensitive(index < total - 1)
        else:
            self._disable_mission_flow_buttons()

    def _disable_mission_flow_buttons(self):
        self.b_mission_first.set_sensitive(False)
        self.b_mission_prev.set_sensitive(False)
        self.b_mission_stop.set_sensitive(False)
        self.b_mission_run.set_sensitive(False)
        self.b_mission_restart.set_sensitive(False)
        self.b_mission_next.set_sensitive(False)
        self.b_mission_last.set_sensitive(False)

    def on_connection_done(self, *args):
        self._update_connection_page(MainWindow.CONNECTION_TABS.CONNECTED)

    def on_connection_failed(self, *args):
        self._update_connection_page(MainWindow.CONNECTION_TABS.DISCONNECTED)

    def on_connection_closed(self, *args):
        self._update_connection_page(MainWindow.CONNECTION_TABS.DISCONNECTED)

    def on_connection_lost(self, reason):
        self._update_connection_page(MainWindow.CONNECTION_TABS.CONNECTING)

    def _update_connection_page(self, page):
        self.connection_stack.set_current_page(page)
        self._update_mission_flow_buttons()

    def on_b_mission_first_clicked(self, widget):
        self.mission_selector.set_active(0)

    def on_b_mission_prev_clicked(self, widget):
        index = self.mission_selector.get_active()
        if index == 0:
            index = len(self.mission_selector.get_model()) - 1
        else:
            index -= 1
        self.mission_selector.set_active(index)

    def on_b_mission_next_clicked(self, widget):
        index = self.mission_selector.get_active()
        max_index = len(self.mission_selector.get_model()) - 1
        if index == max_index:
            index = 0
        else:
            index += 1
        self.mission_selector.set_active(index)

    def on_b_mission_last_clicked(self, widget):
        index = len(self.mission_selector.get_model()) - 1
        self.mission_selector.set_active(index)

    def on_mission_status_changed(self, status):
        # Update current mission on UI
        current_id = MissionManager.get_current_id()
        new_index = MissionManager.get_index_by_id(current_id)
        old_index = self.mission_selector.get_active()

        if new_index != old_index:
            self.mission_selector.set_active_not_from_ui(new_index)

        # Update mission info
        self._display_mission_status()
        self._display_mission_time_left()

        # Update status of mission flow controls
        if status in [
            MISSION_STATUS.STARTING, MISSION_STATUS.STOPPING,
            MISSION_STATUS.LOADING,
        ]:
            self._lock_mission_controls()
        else:
            self._unlock_mission_controls()

    def on_mission_timer_tick(self):
        self._display_mission_time_left()

    def _display_mission_status(self):
        status = root_service.commander.services.missions.status
        info = MISSION_STATUS_INFO[status]

        name = unicode(info['verbose_name'])
        color_code = '#{0}'.format(info['color_hex'])

        self.lb_mission_status.set_text(name)
        self.lb_mission_status.modify_fg(
            gtk.STATE_NORMAL, gtk.gdk.color_parse(color_code))

    def _display_mission_time_left(self):
        self.lb_mission_time_left.set_text(
            root_service.commander.services.missions.time_left_str)
