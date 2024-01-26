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
from .model import TaskFactory, TodoTask

@Gtk.Template(resource_path='/net/hemish/kaar/blp/ui.ui')
class KaarWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'KaarWindow'
    list_view: Gtk.ListView = Gtk.Template.Child()
    search_entry: Gtk.SearchEntry = Gtk.Template.Child()
    search_bar: Gtk.SearchBar = Gtk.Template.Child()
    save_button: Gtk.Button = Gtk.Template.Child()
    progress_bar: Gtk.ProgressBar = Gtk.Template.Child()
    filters_box: Gtk.ListBox = Gtk.Template.Child()
    projects_box: Gtk.ListBox = Gtk.Template.Child()
    contexts_box: Gtk.ListBox = Gtk.Template.Child()

    # Defining models for projects and contexts box which provide the filters
    projects_model: Gtk.StringList = Gtk.StringList()
    contexts_model: Gtk.StringList = Gtk.StringList()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        app = self.get_application()
        self.settings: Gio.Settings = app.settings

        # Initially filter out the tasks
        app.tasks_filter.changed(Gtk.FilterChange.DIFFERENT)

        if self.settings.get_boolean("vertically-center-tasks"):
            self.list_view.set_valign(Gtk.Align.CENTER)
        
        # args[1] is the name of key received from changed signal which is "vertically-center-tasks" itself
        self.settings.connect("changed::vertically-center-tasks", lambda *args: self.list_view.set_valign(Gtk.Align.CENTER) if self.settings.get_boolean(args[1]) else self.list_view.set_valign(Gtk.Align.START))

        self.settings.bind("autosave", self.save_button, "visible", Gio.SettingsBindFlags.INVERT_BOOLEAN)
        
        self.list_view.set_model(self.get_application().single_selection)
        self.list_view.set_factory(TaskFactory())

        self.search_entry.connect("search-changed", lambda entry: self.get_application().search_filter.changed(Gtk.FilterChange.DIFFERENT))

        self.search_bar.set_key_capture_widget(self)
        self.list_view.remove_css_class("view")

        self.filters_box.connect("row-selected", lambda *args: self.get_application().filtering.set_current_filtering(args[1].get_name()))
        self.contexts_box.connect("selected-rows-changed", lambda *args: self.get_application().filtering.set_contexts([row.get_title() for row in args[0].get_selected_rows()]))
        self.projects_box.connect("selected-rows-changed", lambda *args: self.get_application().filtering.set_projects([row.get_title() for row in args[0].get_selected_rows()]))

        self.contexts_box.connect("unselect-all", lambda *args: self.get_application().filtering.set_contexts([]))
        self.projects_box.connect("unselect-all", lambda *args: self.get_application().filtering.set_projects([]))
        
        # Select first row, i.e. All Tasks
        self.filters_box.select_row(self.filters_box.get_row_at_index(0))

        self.contexts_box.bind_model(self.contexts_model, self.create_flow_box_item, None, None)
        self.projects_box.bind_model(self.projects_model, self.create_flow_box_item, None, None)

        self.update_projects_and_contexts_filters()

        css_provider = Gtk.CssProvider()
        css_provider.load_from_resource("/net/hemish/kaar/style.css")
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def create_flow_box_item(self, string_obj: Gtk.StringObject, *args) -> Adw.ActionRow:
        row: Adw.ActionRow = Adw.ActionRow()
        row.set_title(string_obj.get_string())
        return row
    
    def update_projects_and_contexts_filters(self) -> None:
        for k in range(self.contexts_model.get_n_items()):
            self.contexts_model.remove(0)
        
        for k in range(self.projects_model.get_n_items()):
            self.projects_model.remove(0)

        store: Gio.ListStore = self.get_application().list_store

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
            

