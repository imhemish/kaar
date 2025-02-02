from gi.repository import Adw
from gi.repository import Gtk, Gio
from gettext import gettext as _
from typing import List
from .enums import FilterOption

from .sorting import TaskSorting

def get_priority_list(settings: Gio.Settings) -> List[str]:
    return settings.get_strv("sorting-priority")

def set_priority_list(settings: Gio.Settings, priority_list: List[str]):
    settings.set_strv("sorting-priority", priority_list)

# Defining translated strings
sorting_strings = {
    "DUE_DATE": _("Due Date"),
    "CREATION_DATE": _("Creation Date"),
    "DESCRIPTION": _("Description"),
    "COMPLETION_DATE": _("Completion Date")
}

filter_options_strings = {
    "ALL": _("All"),
    "DUE": _("Due"),
    "COMPLETE": _("Completed"),
    "INCOMPLETE": _("Incomplete")
}

@Gtk.Template(resource_path='/net/hemish/kaar/blp/preferences.ui')
class KaarPreferencesDialog(Adw.PreferencesDialog):
    __gtype_name__ = 'KaarPreferencesDialog'
    autosave: Adw.SwitchRow = Gtk.Template.Child()
    autoreload: Adw.SwitchRow = Gtk.Template.Child()
    restore_session: Adw.SwitchRow = Gtk.Template.Child()
    vertically_center_tasks: Adw.SwitchRow = Gtk.Template.Child()
    hide_check_buttons: Adw.SwitchRow = Gtk.Template.Child()
    hidden_tasks: Adw.SwitchRow = Gtk.Template.Child()
    priority_up_button: Gtk.Button = Gtk.Template.Child()
    priority_down_button: Gtk.Button = Gtk.Template.Child()
    priority_list_box: Gtk.ListBox = Gtk.Template.Child()
    pango_markup: Adw.SwitchRow = Gtk.Template.Child()
    default_filter_option: Adw.ComboRow = Gtk.Template.Child()

    priority_list: List[str]

    def __init__(self, settings: Gio.Settings, **kwargs):
        super().__init__(**kwargs)

        # Use same Gio.Settings instance for entire app
        self.settings: Gio.Settings = settings

        self.autosave.set_active(self.settings.get_boolean("autosave"))
        self.settings.bind("autosave", self.autosave, "active", Gio.SettingsBindFlags.DEFAULT)

        self.autoreload.set_enable_expansion(self.settings.get_boolean("autoreload"))
        # Instead of a switch row, autoreload is expander row, so conencting to enable-expansion
        # as expansion is controlled by the switch adjacent to expander arrow
        self.settings.bind("autoreload", self.autoreload, "enable-expansion", Gio.SettingsBindFlags.DEFAULT)

        self.restore_session.set_active(self.settings.get_boolean("restore-session"))
        self.settings.bind("restore-session", self.restore_session, "active", Gio.SettingsBindFlags.DEFAULT)

        self.vertically_center_tasks.set_active(self.settings.get_boolean("vertically-center-tasks"))
        self.settings.bind("vertically-center-tasks", self.vertically_center_tasks, "active", Gio.SettingsBindFlags.DEFAULT)

        self.hide_check_buttons.set_active(self.settings.get_boolean("hide-check-buttons"))
        self.settings.bind("hide-check-buttons", self.hide_check_buttons, "active", Gio.SettingsBindFlags.DEFAULT)

        self.hidden_tasks.set_active(self.settings.get_boolean("hidden-tasks"))
        self.settings.bind("hidden-tasks", self.hidden_tasks, "active", Gio.SettingsBindFlags.DEFAULT)

        self.hidden_tasks.set_active(self.settings.get_boolean("render-pango-markup"))
        self.settings.bind("render-pango-markup", self.pango_markup, "active", Gio.SettingsBindFlags.DEFAULT)

        string_list = [filter_options_strings.get(option.name) for option in FilterOption]
        self.default_filter_option.set_model(Gtk.StringList(strings=string_list))
        self.default_filter_option.set_selected(self.settings.get_enum("default-filter-option"))
        self.default_filter_option.connect("notify::selected", lambda *_: self.settings.set_enum("default-filter-option", self.default_filter_option.get_selected()))

        self.priority_up_button.connect('clicked', self.on_priority_changer_button_up)

        self.priority_list = get_priority_list(self.settings)

        for i, val in enumerate(self.priority_list):
            row = self.priority_list_box.get_row_at_index(i)
            row.set_name(val)
            row.set_title(sorting_strings[val])
        
        
    
    def on_priority_changer_button_up(self, *args):

        index = self.priority_list_box.get_selected_row().get_index()
        if index != 0:
            selected_row = self.priority_list_box.get_selected_row()
            previous_row = self.priority_list_box.get_row_at_index(index-1)
            selected_row_name = selected_row.get_name()
            previous_row_name = previous_row.get_name()

            self.priority_list_box.select_row(previous_row)

            self.priority_list[index], self.priority_list[index-1] = self.priority_list[index-1], self.priority_list[index]
            set_priority_list(self.settings, self.priority_list)
            
            selected_row.set_name(previous_row_name)
            selected_row.set_title(sorting_strings.get(previous_row_name))
            previous_row.set_name(selected_row_name)
            previous_row.set_title(sorting_strings.get(selected_row_name))
