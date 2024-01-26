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

from gi.repository import Gtk, Gio, Adw, Gdk
from .window import KaarWindow
from .preferences_window import KaarPreferencesWindow, converter
from .model import TodoTask
from pytodotxt import TodoTxt, TodoTxtParser
from .filtering import Filtering
from .sorting import TaskSorter, TaskSorting
import threading

class KaarApplication(Adw.Application):
    settings: Gio.Settings

    def __init__(self):
        print("application initiated")
        super().__init__(application_id='net.hemish.kaar',
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('preferences', self.on_preferences_action)
        self.create_action('new', self.new_task, ['<primary>n'])
        self.create_action('edit', self.edit_task, ['<primary>e', 'F2'])
        self.create_action('delete', self.delete_task, ['<primary>d', 'Delete'])
        self.create_action('complete', self.complete_task, ['<primary>x'])
        #self.create_action('save', self.save_file, ['<primary>s'])
        #self.create_action('reload', self.reload_file, ['<primary>r'])
        self.create_action('hide', self.hide_tasks, ['<primary>h'])

        css_provider = Gtk.CssProvider()
        css_provider.load_from_resource("/net/hemish/kaar/style.css")
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.settings: Gio.Settings = Gio.Settings('net.hemish.kaar')

        self.should_autosave = self.settings.get_boolean("autosave")

    
    def do_activate(self):
        print("window was activated")
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        
        win = self.props.active_window
        if not win:
            win = KaarWindow(application=self)
            win.present()

    def on_about_action(self, widget, _):
        """Callback for the app.about action."""
        about = Adw.AboutWindow(transient_for=self.props.active_window,
                                application_name='Kaar',
                                application_icon='net.hemish.kaar',
                                developer_name='Hemish',
                                version='0.1.0',
                                developers=['Hemish'],
                                copyright='© 2023 Hemish')
        about.present()

    def on_preferences_action(self, widget, _):
        """Callback for the app.preferences action."""
        preferences = KaarPreferencesWindow(transient_for=self.props.active_window)
        preferences.present()
    
    def new_task(self, *args):
        task = TodoTask()
        self.list_store.append(task)
        # FIXME: the below function doesnt work with sorting functionality, as the new task is not added at end
        # self.props.active_window.list_view.scroll_to(len(self.single_selection), Gtk.ListScrollFlags.SELECT)
        
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
        self.props.active_window.update_projects_and_contexts_filters()
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
    app = KaarApplication()
    return app.run(sys.argv)
