from gi.repository import Adw
from gi.repository import Gtk, Gio

@Gtk.Template(resource_path='/net/hemish/kamm/blp/preferences.ui')
class KammPreferencesWindow(Adw.PreferencesWindow):
    __gtype_name__ = 'KammPreferencesWindow'
    location: Adw.ActionRow = Gtk.Template.Child()
    autosave: Adw.SwitchRow = Gtk.Template.Child()
    open_button: Gtk.Button = Gtk.Template.Child()
    vertically_center_tasks: Adw.SwitchRow = Gtk.Template.Child()
    hidden_tasks: Adw.SwitchRow = Gtk.Template.Child()

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
    
    def on_open_button(self, *args):
        def callback(source, res):
            res: Gio.File = self.file_dialog.open_finish(res)
            self.settings.set_string("uri", res.get_uri())
            app = self.get_transient_for().get_application()
            app.file_uri = res.get_uri()
            app.reload_file()
        
        self.file_dialog = Gtk.FileDialog()
        res = self.file_dialog.open(parent=self, callback=callback)
