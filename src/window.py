# window.py
#
# Copyright 2024 Hemish
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw, Gtk, Gio, Gdk
from .model import TodoTask
from gettext import gettext as _

@Gtk.Template(resource_path='/net/hemish/kaar/blp/ui.ui')
class KaarWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'KaarWindow'
    root_stack: Gtk.Stack = Gtk.Template.Child()
    search_entry: Gtk.SearchEntry = Gtk.Template.Child()
    search_bar: Gtk.SearchBar = Gtk.Template.Child()
    save_button: Gtk.Button = Gtk.Template.Child()
    filters_box: Gtk.ListBox = Gtk.Template.Child()
    projects_box: Gtk.ListBox = Gtk.Template.Child()
    contexts_box: Gtk.ListBox = Gtk.Template.Child()
    tab_view : Adw.TabView = Gtk.Template.Child()
    tab_overview : Adw.TabOverview = Gtk.Template.Child()
    open_button: Gtk.Button = Gtk.Template.Child()
    status_open_button: Gtk.Button = Gtk.Template.Child()
    projects_clear: Gtk.Button = Gtk.Template.Child()
    contexts_clear: Gtk.Button = Gtk.Template.Child()

    # Defining models for projects and contexts box which provide the filters
    projects_model: Gtk.StringList = Gtk.StringList()
    contexts_model: Gtk.StringList = Gtk.StringList()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        app = self.get_application()
        self.settings: Gio.Settings = app.settings

        w = self.settings.get_int("last-window-width")
        h = self.settings.get_int("last-window-height")
        self.set_default_size(w, h)

        self.set_title(_("Kaar"))
        
        self.open_button.connect("clicked", self.on_open_button)
        self.status_open_button.connect("clicked", self.on_open_button)

        self.settings.bind("autosave", self.save_button, "visible", Gio.SettingsBindFlags.INVERT_BOOLEAN)

        self.tab_view.connect("notify::selected-page", lambda *args: self.update_projects_and_contexts_filters())
        
        self.search_entry.connect("search-changed", self.on_search_changed)

        self.search_bar.set_key_capture_widget(self.tab_view)

        ######## List of contexts and projects in sidebar for filtering ########
        self.filters_box.connect("row-selected", lambda *args: self.tab_view.get_selected_page().get_child().filtering.set_current_filtering(args[1].get_name()))
        self.contexts_box.connect("selected-rows-changed", lambda *args: self.tab_view.get_selected_page().get_child().filtering.set_contexts([row.get_title() for row in args[0].get_selected_rows()]))
        self.projects_box.connect("selected-rows-changed", lambda *args: self.tab_view.get_selected_page().get_child().filtering.set_projects([row.get_title() for row in args[0].get_selected_rows()]))

        self.contexts_box.connect("unselect-all", lambda *args: self.tab_view.get_selected_page().get_child().filtering.set_contexts([]))
        self.projects_box.connect("unselect-all", lambda *args: self.tab_view.get_selected_page().get_child().filtering.set_projects([]))
        
        # Select first row, i.e. All Tasks
        self.filters_box.select_row(self.filters_box.get_row_at_index(0))

        self.contexts_box.bind_model(self.contexts_model, self.create_flow_box_item, None, None)
        self.projects_box.bind_model(self.projects_model, self.create_flow_box_item, None, None)

        self.update_projects_and_contexts_filters()
        ############################################################################

        ######## Registering the actions ########
        self.create_action("delete", self.delete_task, ['<primary>d', 'Delete'] )
        self.create_action('new', self.new_task, ['<primary>n'])
        self.create_action('edit', self.edit_task, ['<primary>e', 'F2'])
        self.create_action('complete', self.complete_task, ['<primary>x'])
        self.create_action('save', self.save_meta, ['<primary>s'])
        self.create_action('save_if_required', self.save_if_required_meta)
        self.create_action('reload', self.reload_meta, ['<primary>r'])
        self.create_action("close_tab", self.close_tab, ['<primary>w'])
        ##########################################

        self.check_if_no_tabs_are_open()
        self.tab_view.connect("notify::n-pages", self.check_if_no_tabs_are_open)
        self.tab_view.connect("notify::n-pages", self.save_session_details)

        self.tab_view.connect("close-page", self.handle_close_tab)

        self.tab_overview.connect("create-tab", self.on_open_button)

        self.projects_clear.connect('clicked', lambda *args: self.projects_box.unselect_all())
        self.contexts_clear.connect('clicked', lambda *args: self.contexts_box.unselect_all())


        if self.settings.get_boolean("restore-session"):
            for file in self.settings.get_strv("files"):
                try:
                    self.get_application().open_file(Gio.File.new_for_uri(file))
                except: pass
            try:
                fileuri = self.settings.get_string("last-file")
                for page in self.tab_view.get_pages():
                    if page.get_child().file == fileuri:
                        self.tab_view.set_selected_page(page)
            except: pass

    def create_flow_box_item(self, string_obj: Gtk.StringObject, *args) -> Adw.ActionRow:
        return Adw.ActionRow(title=string_obj.get_string())
    
    def check_if_no_tabs_are_open(self, *args):
        if self.tab_view.get_n_pages() == 0:
            self.root_stack.set_visible_child_name("status")
            self.lookup_action("close_tab").set_enabled(False)
        else:
            self.root_stack.set_visible_child_name("main")
            self.lookup_action("close_tab").set_enabled(True)
    
    def save_session_details(self, *args):
        fileURIs = []
        for page in self.tab_view.get_pages():
            fileURIs.append(page.get_child().file)
        self.settings.set_strv("files", fileURIs)

    def update_projects_and_contexts_filters(self) -> None:
        self.projects_box.unselect_all()
        self.contexts_box.unselect_all()

        for k in range(self.contexts_model.get_n_items()):
            self.contexts_model.remove(0)
        
        for k in range(self.projects_model.get_n_items()):
            self.projects_model.remove(0)
        
        page = self.tab_view.get_selected_page()

        if page != None:
            store: Gio.ListStore = page.get_child().list_store

            projects = set()
            contexts = set()

            for i in range(store.get_n_items()):
                task: TodoTask = store.get_item(i)
                projects = {*projects, *task.projects}
                contexts = {*contexts, *task.contexts}
            
            for j in projects:
                self.projects_model.append(j)
            for j in contexts:
                self.contexts_model.append(j)
        
        self.projects_box.unselect_all()
        self.contexts_box.unselect_all()
    
    def on_open_button(self, *args):
        def callback(source, res):
            res: Gio.File = self.file_dialog.open_finish(res)
            self.get_application().open_file(res)
        
        self.file_dialog = Gtk.FileDialog()
        self.file_dialog.open(parent=self, callback=callback)
    
    def on_search_changed(self, entry):
        page = self.tab_view.get_selected_page()
        if page != None:
            page.get_child().search_filter.changed(Gtk.FilterChange.DIFFERENT)
    
    def delete_task(self, *args):
        tabchild = self.tab_view.get_selected_page().get_child()

        # The model is single selection model
        item = tabchild.list_view.get_model().get_selected_item()
        
        found, position = tabchild.list_store.find(item)
        if found:
            tabchild.list_store.remove(position)

        self.update_projects_and_contexts_filters()
        tabchild.save_if_required()
    
    def edit_task(self, *args):
        object = self.tab_view.get_selected_page().get_child().list_view.get_model().get_selected_item()
        if object.mode == 'view':
            object.mode = "edit"
        else:
            object.mode = 'view'
    
    def new_task(self, *args):
        print("new task called")
        task = TodoTask()
        tabchild = self.tab_view.get_selected_page().get_child()

        if tabchild.filtering.current_filtering == "complete":
            task.is_completed = True

        # if you are in a filtered view, append those
        for string_object in self.projects_model:
            task.add_project(string_object.get_string())
        for string_object in self.contexts_model:
            task.add_context(string_object.get_string())

        tabchild.list_store.append(task)
        print("new task appended")

        # FIXME: Scroll and select newly added task
        #self.props.active_window.list_viewscroll_to(, Gtk.ListScrollFlags.SELECT)
        
        # Auto set the mode to edit on blank task
        task.mode = 'edit'
        print("changed to edit mode")
    
    def complete_task(self, *args):
        tabchild = self.tab_view.get_selected_page().get_child()
        object = tabchild.list_view.get_model().get_selected_item()
        if not object.completed:
            object.completed = True
        else:
            object.completed = False
        object.line = str(object)

        tabchild.save_if_required()
    
    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.get_application().set_accels_for_action(f"win.{name}", shortcuts)
    
    def update_window_title(self, *args):
        unsaved = False
        for page in self.tab_view.get_pages():
            if page.get_needs_attention():
                unsaved = True
                break # Optimising
        if unsaved:

            # Translators: This meant to be used in window title. The · here symbolises unsaved files.
            self.set_title(_("Kaar ·"))
        else:
            self.set_title(_("Kaar"))

    def save_meta(self, *args):
        self.tab_view.get_selected_page().get_child().save_file()
    
    def save_if_required_meta(self, *args):
        self.tab_view.get_selected_page().get_child().save_if_required()
    
    def reload_meta(self, *args):
        self.tab_view.get_selected_page().get_child().reload_file()
    
    def close_tab(self, *args):
        self.tab_view.close_page(self.tab_view.get_selected_page())
    
    def do_close_request(self, *args):
        if self.tab_view.get_n_pages() != 0:
            self.settings.set_string("last-file", self.tab_view.get_selected_page().get_child().file)

        unsaved = False
        for page in self.tab_view.get_pages():
            if page.get_needs_attention():
                unsaved = True
                break # Optimising
        if unsaved:

            # Unsaved dialog
            dialog: Adw.AlertDialog = Adw.AlertDialog.new(_("Unsaved File(s)"), _("One or more files are unsaved"))
            dialog.add_response("cancel", _("Cancel"))
            dialog.add_response("save", _("Save and Exit"))
            dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
            dialog.add_response("exit", _("Exit without saving"))
            dialog.set_close_response("cancel")
            dialog.set_default_response("cancel")

            def on_response(*args):
                if args[1] == "save":
                    for page in self.tab_view.get_pages():
                        page.get_child().save_file()
                    self.destroy()
                elif args[1] == "cancel":
                    pass # Do not exit
                elif args[1] == "exit":
                    self.destroy()
            
            dialog.connect("response",  on_response)
            print("dialog bound to response signal")
            dialog.present(self)
            print("dialog presented")
            return Gdk.EVENT_STOP # True (or const EVENT_STOP) needs to be returned to implementation of vfunc close_request
            # to ignore close
        else:
            # Exit finally
            self.settings.set_int("last-window-width", self.get_width())
            self.settings.set_int("last-window-height", self.get_height())
            self.destroy()
            return Gdk.EVENT_PROPAGATE
    
    def handle_close_tab(self, tab_view: Adw.TabView, tab_page: Adw.TabPage, *args):
        if tab_page.get_needs_attention():
            dialog: Adw.AlertDialog = Adw.AlertDialog.new(_("Unsaved File"), _("The file in the tab is unsaved"))
            dialog.add_response("cancel", _("Cancel"))
            dialog.add_response("save", _("Save and Close"))
            dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
            dialog.add_response("close", _("Close without saving"))
            dialog.set_close_response("cancel")
            dialog.set_default_response("cancel")

            def on_response(*args):
                if args[1] == "save":
                    tab_page.get_child().save_file()
                    tab_view.close_page_finish(tab_page, True)
                elif args[1] == "close":
                    tab_view.close_page_finish(tab_page, True)
                elif args[1] == "cancel":
                    tab_view.close_page_finish(tab_page, False)
        
            dialog.connect("response",  on_response)
            dialog.present(self)
            return Gdk.EVENT_STOP
        else:
            return Gdk.EVENT_PROPAGATE