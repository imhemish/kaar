from gi.repository import Adw
from gi.repository import Gtk

@Gtk.Template(resource_path='/net/hemish/kamm/blp/preferences.ui')
class KammPreferencesWindow(Adw.PreferencesWindow):
    __gtype_name__ = 'KammPreferencesWindow'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)