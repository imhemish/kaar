# main.py
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

import sys
import gi
import time

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw
from .window import KammWindow
from .preferences_window import KammPreferencesWindow
from .model import TodoTask
from pytodotxt import TodoTxt, TodoTxtParser
from .filtering import Filtering


class KammApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        print("application initiated")
        super().__init__(application_id='net.hemish.kamm',
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('preferences', self.on_preferences_action)
        self.create_action('new', self.new_task, ['<primary>n'])
        self.create_action('edit', self.edit_task, ['<primary>e', 'F2'])
        self.create_action('delete', self.delete_task, ['<primary>d', 'Delete'])
        self.create_action('complete', self.complete_task, ['<primary>x'])
        self.create_action('save', self.save_file, ['<primary>s'])
        self.create_action('reload', self.reload_file, ['<primary>r'])
        self.create_action('hide', self.hide_tasks, ['<primary>h'])

        print("actions created")

        self.settings: Gio.Settings = Gio.Settings('net.hemish.kamm')

        self.should_autosave = self.settings.get_boolean("autosave")

        self.list_store = Gio.ListStore()

        self.file_uri = self.settings.get_string("uri")

        self.search_filter = Gtk.CustomFilter()
        self.tasks_filter = Gtk.CustomFilter()
        self.search_model = Gtk.FilterListModel()
        self.tasks_filter_model = Gtk.FilterListModel()
        self.search_model.set_model(self.list_store)
        self.search_model.set_filter(self.search_filter)
        self.tasks_filter_model.set_model(self.search_model)
        self.tasks_filter_model.set_filter(self.tasks_filter)
        self.single_selection = Gtk.SingleSelection()
        self.single_selection.set_model(self.tasks_filter_model)
        
        self.filtering: Filtering = Filtering(self, lambda: self.tasks_filter.changed(Gtk.FilterChange.DIFFERENT))
        self.tasks_filter.set_filter_func(self.filtering.filter)

        # When hidden tasks is toggled, automatically hide or unhide tasks depending upon whether h:1 is set or not
        self.settings.connect("changed::hidden-tasks", lambda *args: self.tasks_filter.changed(Gtk.FilterChange.DIFFERENT))

        #Initially loading file
        print("reload file called")
        self.reload_file()

        print("file haas been loaded")

    def reload_file(self, *args):
        print("hooney i was callee")
        self.list_store.remove_all()
        self.file_path = Gio.File.new_for_uri(self.file_uri).get_parse_name()
        print(self.file_path)

        self.todotxt = TodoTxt(self.file_path, parser=TodoTxtParser(task_type=TodoTask))
        try:
            print("trying")
            self.todotxt.parse()
            print("success")
        except Exception as e:
            print(e)
        print(self.todotxt)
        for task in self.todotxt.tasks:
            print(task)
            self.list_store.append(task)
        # Reload filters
        self.tasks_filter.changed(Gtk.FilterChange.DIFFERENT)
        self.search_filter.changed(Gtk.FilterChange.DIFFERENT)
    
    def save_file(self, *args):
        # TODO: Implement progressbar animatin
        #pb: Gtk.ProgressBar = self.props.active_window.progress_bar
        #pb.set_fraction(0)
        #pb.set_visible(True)
        #len_list = len(self.list_store)
        # x = 0
        self.todotxt.tasks = []
        for item in self.list_store:
            self.todotxt.tasks.append(item)
            #x += 1
            #pb.set_fraction(x/len_list)
            #print("progressed by {}".format(x/len_list))
        self.todotxt.save()
        #pb.set_visible(False)
    
    def save_if_required(self):
        if self.settings.get_boolean("autosave"):
            self.save_file()
    
    def do_activate(self):
        print("window was activated")
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        
        win = self.props.active_window
        if not win:
            win = KammWindow(application=self)
            self.search_filter.set_filter_func(lambda object: self.props.active_window.search_entry.get_text().lower() in str(object).lower())
            win.present()

    def on_about_action(self, widget, _):
        """Callback for the app.about action."""
        about = Adw.AboutWindow(transient_for=self.props.active_window,
                                application_name='kamm',
                                application_icon='net.hemish.kamm',
                                developer_name='Hemish',
                                version='0.1.0',
                                developers=['Hemish'],
                                copyright='© 2023 Hemish')
        about.present()

    def on_preferences_action(self, widget, _):
        """Callback for the app.preferences action."""
        preferences = KammPreferencesWindow(transient_for=self.props.active_window)
        preferences.present()
    
    def new_task(self, *args):
        task = TodoTask()
        self.list_store.append(task)
        self.props.active_window.list_view.scroll_to(len(self.single_selection)+1, Gtk.ListScrollFlags.SELECT)
        
        # Auto set the mode to edit on blank task
        task.mode = 'edit'
    
    def edit_task(self, *args):
        object = self.props.active_window.list_view.get_model().get_selected_item()
        if object.mode == 'view':
            object.mode = "edit"
        else:
            object.mode = 'view'
    
    def delete_task(self, *args):
        index = self.props.active_window.list_view.get_model().get_selected()
        self.list_store.remove(index)
        self.save_if_required()
    
    def complete_task(self, *args):
        object = self.props.active_window.list_view.get_model().get_selected_item()
        if not object.completed:
            object.completed = True
        else:
            object.completed = False
        object.line = str(object)

        self.save_if_required()
    
    def hide_tasks(self, *args):
        self.settings.set_boolean("hidden-tasks", not self.settings.get_boolean("hidden-tasks"))

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
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    """The application's entry point."""
    app = KammApplication()
    return app.run(sys.argv)
