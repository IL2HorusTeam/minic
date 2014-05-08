# -*- coding: utf-8 -*-
import gtk
import os
import tx_logging

from minic.resources import image_path
from minic.service import root_service
from minic.settings import user_settings, missions
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
        FILE_NAME = 2
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
        def file_name_renderer(treeviewcolumn, cell, model, iterator):
            value = model.get_value(iterator, MissionsDialog.COLUMNS.FILE_NAME)
            if not value:
                value = _("Not selected")
            cell.set_property('text', value)

        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_("File"), renderer,
                                    text=MissionsDialog.COLUMNS.FILE_NAME)
        column.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        column.set_resizable(True)
        column.set_expand(True)
        column.set_cell_data_func(renderer, file_name_renderer)
        self.treeview.append_column(column)
        self.column_file_name = column

        # Duration column ------------------------------------------------------
        def on_duration_edited(cell, path, new_value):
            if not new_value:
                show_error(_("Duration value cannot be empty"), self)
                return
            try:
                value = int(new_value)
            except ValueError:
                show_error(_("Duration value must be an integer"), self)
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
        new_id = missions.generate_id()

        if len(self.store) == 0:
            # Create default row
            cursor = 0
            name = _("Some mission")
            file_name = None
            duration = 60
        else:
            # Copy existing row
            cursor = self.current_cursor
            id_, selected_name, file_name, duration = self.store[cursor]

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
                i_name, i_suffix = split_name(name=row[MissionsDialog.COLUMNS.NAME])
                if i_name != name or not i_suffix:
                    continue
                if suffix <= i_suffix:
                    suffix = i_suffix + 1

            name = "{0}.{1}".format(name, suffix)
            cursor += 1

        self.store.insert(cursor, (new_id, name, file_name, duration))
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
        row = store[cursor]
        data = (row[0], row[1], row[2], row[3], )

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
        row = store[cursor]
        data = (row[0], row[1], row[2], row[3], )

        del store[cursor]
        cursor += delta
        store.insert(cursor, data)
        self.treeview.set_cursor(cursor)

    def on_move_to_bottom(self, widget):
        store = self.store
        cursor = self.current_cursor
        row = store[cursor]
        data = (row[0], row[1], row[2], row[3], )

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

        if column == self.column_file_name:
            if not user_settings.server_path:
                show_error(_("Please, set path to game server"), self)
                return

            file_name = self.store[path][MissionsDialog.COLUMNS.FILE_NAME]
            root_dir = os.path.join(os.path.dirname(user_settings.server_path),
                                    'Missions')
            chooser = gtk.FileChooserDialog(title=_("Select IL-2 FB mission"),
                                            action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                            buttons=(gtk.STOCK_CANCEL,
                                                     gtk.RESPONSE_CANCEL,
                                                     gtk.STOCK_OPEN,
                                                     gtk.RESPONSE_OK))
            if file_name:
                chooser.set_filename(root_dir + file_name)
            else:
                chooser.set_current_folder(root_dir)

            f_filter = gtk.FileFilter()
            f_filter.set_name("IL-2 FB missions (*.mis)")
            f_filter.add_pattern("*.mis")
            chooser.add_filter(f_filter)

            response = chooser.run()
            file_name = chooser.get_filename()
            chooser.destroy()

            if response != gtk.RESPONSE_OK:
                return

            if not file_name.startswith(root_dir):
                show_error(_("Please, select missions only for the server "
                             "you specified in settings"), self)
            else:
                file_name = file_name[len(root_dir):]
                self.store[path][MissionsDialog.COLUMNS.FILE_NAME] = file_name

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
            if row[MissionsDialog.COLUMNS.FILE_NAME] is None:
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
        for m in missions.load():
            store.append((m['id'], m['name'], m['file_name'], m['duration'], ))
        self._on_data_changed()

    def _save_data(self):
        missions.save(self.store)

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
        self.mission_selector = mission_selector

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

        self._update_missions_box()

        return frame

    def on_edit_missions_clicked(self, widget):
        d = MissionsDialog(self)
        result = d.run()
        if result == gtk.RESPONSE_APPLY:
            self._update_missions_box()
        d.destroy()

    def _update_missions_box(self):
        store = self.mission_selector.get_model()

        current_index = self.mission_selector.get_active()
        current_id = missions.get_current_id() if current_index == -1 else \
                     store[current_index][0]

        store.clear()
        new_index = -1

        for i, m in enumerate(missions.load()):
            id_ = m['id']
            store.append((id_, m['name'], ))
            if current_id is not None and current_id == id_:
                new_index = i

        if len(store) and new_index == -1:
            new_index = 0
        # if len(store) and missions.get_current_id() is None:
        #

        self.mission_selector.set_active(new_index)

    def on_mission_selector_changed(self, widget):
        store = widget.get_model()
        index = widget.get_active()
        if index == -1:
            missions.set_current_id(None)
        else:
            missions.set_current_id(store[index][0])

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
