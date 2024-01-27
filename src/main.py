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

from gi.repository import Gtk, Gio, Adw, GObject
from .window import KaarWindow
from .tab import TabChild
from .preferences_window import KaarPreferencesWindow, converter
from .model import TodoTask
from .sorting import TaskSorting

class KaarApplication(Adw.Application):
    settings: Gio.Settings

    def __init__(self):
        print("application initiated")
        super().__init__(application_id='net.hemish.kaar',
                         flags=Gio.ApplicationFlags.HANDLES_OPEN)
        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('preferences', self.on_preferences_action)
        
        self.create_action('hide', self.hide_tasks, ['<primary>h'])

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
    
    def do_open(self, files, n_files, hint):
        for file in files:
            self.open_file(file)

    def open_file(self, file: Gio.File):
        active_window = self.get_active_window()
        if not active_window:
            active_window = KaarWindow(application=self)
            active_window.present()
        tabchild = TabChild(file.get_uri(), self.settings, active_window)
        tabpage: Adw.TabPage = active_window.tab_view.append(tabchild)
        tabchild.bind_property("unsaved", tabpage, "needs-attention", GObject.BindingFlags.DEFAULT)
        tabpage.set_title(file.get_basename())
        active_window.tab_view.set_selected_page(tabpage)

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
