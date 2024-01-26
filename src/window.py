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

from gi.repository import Adw, Gtk, Gio
from .model import TaskFactory, TodoTask
from .tab import TabChild

@Gtk.Template(resource_path='/net/hemish/kaar/blp/ui.ui')
class KaarWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'KaarWindow'
    search_entry: Gtk.SearchEntry = Gtk.Template.Child()
    search_bar: Gtk.SearchBar = Gtk.Template.Child()
    save_button: Gtk.Button = Gtk.Template.Child()
    filters_box: Gtk.ListBox = Gtk.Template.Child()
    projects_box: Gtk.ListBox = Gtk.Template.Child()
    contexts_box: Gtk.ListBox = Gtk.Template.Child()
    tab_view : Adw.TabView = Gtk.Template.Child()

    # Defining models for projects and contexts box which provide the filters
    projects_model: Gtk.StringList = Gtk.StringList()
    contexts_model: Gtk.StringList = Gtk.StringList()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        app = self.get_application()
        self.settings: Gio.Settings = app.settings

        file = self.settings.get_string("uri")

        self.tab_view.append(TabChild(file, self.settings, self)).set_title(file.split("/")[-1])
        self.tab_view.append(TabChild(file, self.settings, self))
        self.settings.bind("autosave", self.save_button, "visible", Gio.SettingsBindFlags.INVERT_BOOLEAN)

        self.tab_view.connect("notify::selected-page", lambda *args: self.update_projects_and_contexts_filters())
        

        self.search_entry.connect("search-changed", lambda entry: self.tab_view.get_selected_page().get_child().search_filter.changed(Gtk.FilterChange.DIFFERENT))

        self.search_bar.set_key_capture_widget(self)

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

    def create_flow_box_item(self, string_obj: Gtk.StringObject, *args) -> Adw.ActionRow:
        row: Adw.ActionRow = Adw.ActionRow()
        row.set_title(string_obj.get_string())
        return row
    
    def update_projects_and_contexts_filters(self) -> None:
        for k in range(self.contexts_model.get_n_items()+1):
            self.contexts_model.remove(0)
        
        for k in range(self.projects_model.get_n_items()+1):
            self.projects_model.remove(0)

        store: Gio.ListStore = self.tab_view.get_selected_page().get_child().list_store

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
            

