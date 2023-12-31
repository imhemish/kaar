# window.py
#
# Copyright 2023 Hemish
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
from .model import TaskFactory
from .sorting import TaskSorting

@Gtk.Template(resource_path='/net/hemish/kamm/blp/ui.ui')
class KammWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'KammWindow'
    list_view: Gtk.ListView = Gtk.Template.Child()
    search_entry: Gtk.SearchEntry = Gtk.Template.Child()
    search_bar: Gtk.SearchBar = Gtk.Template.Child()
    save_button: Gtk.Button = Gtk.Template.Child()
    progress_bar: Gtk.ProgressBar = Gtk.Template.Child()
    filters_box: Gtk.ListBox = Gtk.Template.Child()
    sorting_direction_button: Gtk.Button = Gtk.Template.Child()
    sorting_dropdown: Gtk.DropDown = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        app = self.get_application()
        self.settings: Gio.Settings = app.settings

        # Initially filter out the tasks
        app.tasks_filter.changed(Gtk.FilterChange.DIFFERENT)

        # TODO: Auto vertically align without restart when preference is changed
        if self.settings.get_boolean("vertically-center-tasks"):
            self.list_view.set_valign(Gtk.Align.CENTER)

        self.settings.bind("autosave", self.save_button, "visible", Gio.SettingsBindFlags.INVERT_BOOLEAN)
        
        self.list_view.set_model(self.get_application().single_selection)
        self.list_view.set_factory(TaskFactory())

        self.search_entry.connect("search-changed", lambda entry: self.get_application().search_filter.changed(Gtk.FilterChange.DIFFERENT))

        self.search_bar.set_key_capture_widget(self)
        self.list_view.remove_css_class("view")

        self.filters_box.connect("row-selected", lambda *args: self.get_application().filtering.set_current_filtering(args[1].get_name()))

        # Remember Enum values start with 1, but Gtk.DropDown selected index starts from 0
        self.sorting_dropdown.set_selected(TaskSorting.DUE_DATE.value-1)
        self.sorting_dropdown.connect("notify::selected", lambda *args: self.get_application().sorter.set_sorting(TaskSorting(self.sorting_dropdown.get_selected()+1)))
