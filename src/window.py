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

from gi.repository import Adw
from gi.repository import Gtk, Gio
from .model import TaskStack, TaskFactory

@Gtk.Template(resource_path='/net/hemish/kamm/blp/ui.ui')
class KammWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'KammWindow'
    list_view: Gtk.ListView = Gtk.Template.Child()
    search_entry: Gtk.SearchEntry = Gtk.Template.Child()
    search_bar: Gtk.SearchBar = Gtk.Template.Child()
    save_button: Gtk.Button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.list_view.set_model(self.get_application().single_selection)
        self.list_view.set_factory(TaskFactory())

        self.search_entry.connect("search-changed", lambda entry: self.get_application().search_filter.changed(Gtk.FilterChange.DIFFERENT))

        self.search_bar.set_key_capture_widget(self)

        self.get_application().settings.bind("autosave", self.save_button, "visible", Gio.SettingsBindFlags.INVERT_BOOLEAN)


