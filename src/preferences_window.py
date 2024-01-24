from gi.repository import Adw
from gi.repository import Gtk, Gio
from gettext import gettext as _

from .sorting import TaskSorting


def converter(index):
    returned = "sorting-priority-"
    if index == 0:
        returned+='first'
    elif index == 1:
        returned+='second'
    elif index == 2:
        returned+='third'
    elif index == 3:
        returned+='fourth'
    return returned
        
sorting_strings = {
    "DUE_DATE": _("Due Date"),
    "CREATION_DATE": _("Creation Date"),
    "DESCRIPTION": _("Description"),
    "COMPLETION_DATE": _("Competion Date")
}

@Gtk.Template(resource_path='/net/hemish/kamm/blp/preferences.ui')
class KammPreferencesWindow(Adw.PreferencesWindow):
    __gtype_name__ = 'KammPreferencesWindow'
    location: Adw.ActionRow = Gtk.Template.Child()
    autosave: Adw.SwitchRow = Gtk.Template.Child()
    open_button: Gtk.Button = Gtk.Template.Child()
    vertically_center_tasks: Adw.SwitchRow = Gtk.Template.Child()
    hidden_tasks: Adw.SwitchRow = Gtk.Template.Child()
    priority_up_button: Gtk.Button = Gtk.Template.Child()
    priority_down_button: Gtk.Button = Gtk.Template.Child()
    priority_list_box: Gtk.ListBox = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Use same Gio.Settings instance for entire app
        self.settings: Gio.Settings = self.get_transient_for().settings


        self.autosave.set_active(self.settings.get_boolean("autosave"))
        self.settings.bind("autosave", self.autosave, "active", Gio.SettingsBindFlags.DEFAULT)


        self.vertically_center_tasks.set_active(self.settings.get_boolean("vertically-center-tasks"))
        self.settings.bind("vertically-center-tasks", self.vertically_center_tasks, "active", Gio.SettingsBindFlags.DEFAULT)
        

        self.hidden_tasks.set_active(self.settings.get_boolean("hidden-tasks"))
        self.settings.bind("hidden-tasks", self.hidden_tasks, "active", Gio.SettingsBindFlags.DEFAULT)


        self.settings.bind("uri", self.location, "subtitle", Gio.SettingsBindFlags.GET)
        self.open_button.connect("clicked", self.on_open_button)

        self.priority_up_button.connect('clicked', self.on_priority_changer_button_up)

        for i in range(4):
            row = self.priority_list_box.get_row_at_index(i)
            row.set_name(self.settings.get_string(converter(i)))
            row.set_title(self.settings.get_string(converter(i)))
        
    
    def on_priority_changer_button_up(self, *args):

        index = self.priority_list_box.get_selected_row().get_index()
        if index != 0:
            selected_row = self.priority_list_box.get_selected_row()
            previous_row = self.priority_list_box.get_row_at_index(index-1)
            selected_row_name = selected_row.get_name()
            previous_row_name = previous_row.get_name()

            print(converter(index), previous_row_name)
            self.settings.set_string(converter(index), previous_row_name)
            print(converter(index-1), selected_row_name)
            self.settings.set_string(converter(index-1), selected_row_name)
            
            selected_row.set_name(previous_row_name)
            selected_row.set_title(sorting_strings.get(previous_row_name))
            previous_row.set_name(selected_row_name)
            previous_row.set_title(sorting_strings.get(selected_row_name))

    def on_open_button(self, *args):
        def callback(source, res):
            res: Gio.File = self.file_dialog.open_finish(res)
            self.settings.set_string("uri", res.get_uri())
            app = self.get_transient_for().get_application()
            app.file_uri = res.get_uri()
            app.reload_file()
        
        self.file_dialog = Gtk.FileDialog()
        res = self.file_dialog.open(parent=self, callback=callback)
