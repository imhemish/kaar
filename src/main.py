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
import random

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw
from .window import KammWindow
from .preferences_window import KammPreferencesWindow
from .model import TodoTask
from pytodotxt import TodoTxt, TodoTxtParser


class KammApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(application_id='net.hemish.kamm',
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('preferences', self.on_preferences_action)
        self.create_action('new', self.new_task, ['<primary>n'])
        self.create_action('edit', self.edit_task, ['<primary>e', 'F2', 'Return'])
        self.create_action('delete', self.delete_task, ['<primary>d', 'Delete'])
        self.create_action('complete', self.complete_task, ['<primary>x'])

        self.list_store = Gio.ListStore()
        self.single_selection = Gtk.SingleSelection()
        self.single_selection.set_model(self.list_store)
        todotxt = TodoTxt("/home/hemish/todo2.txt", parser=TodoTxtParser(task_type=TodoTask))
        todotxt.parse()
        print(todotxt)
        for task in todotxt.tasks:
            print(task)
            self.list_store.append(task)

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            win = KammWindow(application=self)
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
        self.list_store.append(TodoTask())
        self.props.active_window.list_view.scroll_to(len(self.single_selection)-1, Gtk.ListScrollFlags.SELECT)
    
    def edit_task(self, *args):
        object = self.props.active_window.list_view.get_model().get_selected_item()
        if object.mode == 'view':
            object.mode = "edit"
        else:
            object.mode = 'view'
    
    def delete_task(self, *args):
        index = self.props.active_window.list_view.get_model().get_selected()
        self.list_store.remove(index)
    
    def complete_task(self, *args):
        object = self.props.active_window.list_view.get_model().get_selected_item()
        if not object.completed:
            object.completed = True
        else:
            object.completed = False
        object.line = str(object)
        

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
