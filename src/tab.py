import gi
from gi.repository import Gtk, Adw, Gio, GObject

from .filtering import Filtering
from .sorting import TaskSorting, TaskSorter
from .preferences import get_priority_list
from .model import TaskFactory, TodoTask
from .pseudo_async import _async
from .enums import FilterOption

from time import sleep
from pytodotxt import TodoTxt, TodoTxtParser

from gettext import gettext as _

@Gtk.Template(resource_path="/net/hemish/kaar/blp/tab.ui")
class TabChild(Gtk.Box):

    ####### For things from UI definition ########
    __gtype_name__ = "TabChild"
    list_view: Gtk.ListView = Gtk.Template.Child()
    progress_bar: Gtk.ProgressBar = Gtk.Template.Child()
    tab_stack: Gtk.Stack = Gtk.Template.Child()
    toast_overlay: Adw.ToastOverlay = Gtk.Template.Child()
    ##############################################

    file: str
    settings: Gio.Settings
    parent_window: Adw.ApplicationWindow

    ######## Models, filters, sorting ########
    list_store: Gio.ListStore
    search_filter: Gtk.CustomFilter
    tasks_filter: Gtk.CustomFilter
    sorter: TaskSorter
    filtering: Filtering
    ####################################

    _unsaved: bool = False

    changed_dialog_shown: bool = False

    @GObject.Property(type=bool, default=False)
    def unsaved(self):
        return self._unsaved
    
    @unsaved.setter
    def unsaved(self, value):
        self._unsaved = value
        # Update window title as soon as unsaved status is changed
        self.parent_window.update_window_title(unsaved=self.unsaved)
    
    _autoreload = False

    @GObject.Property(type=bool, default=False)
    def autoreload(self):
        return self._autoreload
    
    @autoreload.setter
    def autoreload(self, value):
        self._autoreload = value

        # one may change the autoreload setting in between
        self.parent_window.update_window_title(self.unsaved)


    def __init__(self, file: str, settings: Gio.Settings, parent_window,*args):
        self.file = file
        super().__init__(*args)

        self.settings = settings
        self.parent_window = parent_window

        # a hack to give List view a better appearance
        self.list_view.remove_css_class("view")

        ######## Code block for handling "Vertically Center Tasks preference" ########
        if self.settings.get_boolean("vertically-center-tasks"):
            self.list_view.set_valign(Gtk.Align.CENTER)
        # args[1] is the name of key received from changed signal which is "vertically-center-tasks" itself
        self.settings.connect("changed::vertically-center-tasks", lambda *args: self.list_view.set_valign(Gtk.Align.CENTER) if self.settings.get_boolean(args[1]) else self.list_view.set_valign(Gtk.Align.START))
        ##############################################################################

        ######## Models, sorting, filtering, searching ########
        self.list_store = Gio.ListStore()

        self.search_filter = Gtk.CustomFilter()
        search_model = Gtk.FilterListModel()
        search_model.set_filter(self.search_filter)
        search_model.set_model(self.list_store)

        # TODO: improve search functionality, maybe branch out in separate file
        self.search_filter.set_filter_func(lambda object: self.parent_window.search_entry.get_text().lower() in str(object).lower())

        self.tasks_filter = Gtk.CustomFilter()
        tasks_filter_model = Gtk.FilterListModel()
        tasks_filter_model.set_model(search_model)
        tasks_filter_model.set_filter(self.tasks_filter)

        self.filtering = Filtering(self, lambda: self.tasks_filter.changed(Gtk.FilterChange.DIFFERENT))
        self.filtering.set_current_filtering(FilterOption[parent_window.filters_box.get_selected_row().get_name()])
        self.tasks_filter.set_filter_func(self.filtering.filter)

        tasks_sorting_model = Gtk.SortListModel()

        sorting_priority = []
        for i in range(4):
            sorting_priority.append(TaskSorting[get_priority_list(self.settings)[0]])

        self.sorter = TaskSorter(sorting_priority=sorting_priority)
        tasks_sorting_model.set_sorter(self.sorter)
        tasks_sorting_model.set_model(tasks_filter_model)

        self.single_selection = Gtk.SingleSelection()
        self.single_selection.set_model(tasks_sorting_model)
        #######################################################

        # When hidden tasks is toggled, automatically hide or unhide tasks depending upon whether h:1 is set or not
        self.settings.connect("changed::hidden-tasks", lambda *args: self.tasks_filter.changed(Gtk.FilterChange.DIFFERENT))

        ######## Configuring the ListView of tasks ########
        self.list_view.set_model(self.single_selection)
        self.list_view.set_factory(TaskFactory(self.settings.get_boolean("render-pango-markup"), self.settings.get_boolean("hide-check-buttons")))
        ###################################################

        self.file_obj = Gio.File.new_for_uri(self.file)

        # Start monitoring the file for external changes
        self.monitor()


        self.settings.connect("changed::sorting-priority", self.on_sorting_change)

        self.autoreload = self.settings.get_boolean("autoreload")
        self.settings.bind("autoreload", self, "autoreload", Gio.SettingsBindFlags.DEFAULT)

        #Initially loading file
        self.reload_file()

        # Initially check if there are no files, then show the status page
        # saying no files open
        self.check_empty_and_act_accordingly()
        self.single_selection.connect("items-changed", self.check_empty_and_act_accordingly)

    def check_empty_and_act_accordingly(self, *args):
        if self.single_selection.get_n_items() == 0:
            # show status page saying no files open
            self.tab_stack.set_visible_child_name("status")
        else:
            self.tab_stack.set_visible_child_name("main")

    def on_sorting_change(self, *args):
        sorting_priority = []
        for i in range(4):
            sorting_priority.append(TaskSorting[get_priority_list(self.settings)[i]])
        self.sorter.set_sorting_priority(sorting_priority)

    def reload_file(self, *args):
        print("reload file called")
        self.list_store.remove_all()

        done, contents, tag = self.file_obj.load_contents(cancellable=None)

        try:
            if done:
                for task in TodoTxtParser(task_type=TodoTask).parse(contents):
                    self.list_store.append(task)

                # Show file loaded toast only when autoreload functionality is on
                # (design choice)
                if self.autoreload:
                    toast = Adw.Toast.new(_("File Loaded"))
                    toast.set_timeout(1)
                    self.toast_overlay.add_toast(toast)
        except Exception as e:
            print(e)
        
        # Reload filters
        self.tasks_filter.changed(Gtk.FilterChange.DIFFERENT)
        self.search_filter.changed(Gtk.FilterChange.DIFFERENT)
    
    def save_file(self, *args):
        print("save file called")
        pb: Gtk.ProgressBar = self.progress_bar

        # Show progress bar, and set it to 0
        pb.set_fraction(0)
        pb.set_visible(True)

        @_async
        def report_progress():
            # Update progress bar after some small time
            # in background
            for i in range(10):
                pb.set_fraction((i+1)/10)
                sleep(0.03)
            sleep(0.15)
            pb.set_visible(False)

        tasks = []

        for item in self.list_store:
            tasks.append(str(item))
        
        self.unmonitor()
        # Unmonitor the file for changes as we are changing the file
        # and it would count as change

        bt = bytes("\n".join(tasks), 'utf-8')

        self.file_obj.replace_contents(contents=bt, etag=None, make_backup=False, flags=Gio.FileCreateFlags.NONE)

        self.monitor()

        report_progress()
        self.unsaved = False
    
    def save_if_required(self):
        # Only save if the user has set 'autosave' preference to True
        print("save if required called")
        self.unsaved = True
        if self.settings.get_boolean("autosave"):
            print("saving as it is required")
            self.unsaved = False
            self.save_file()

        # save_if_required is called, when any task is edited, deleted.
        # So, we invalidate the sort, as the edited task may have a due date
        # or a priority and might need to be ranked higher
        print("sorter changed will be called now")
        self.sorter.changed(Gtk.SorterChange.DIFFERENT)

    def monitor(self):
        self.file_monitor = self.file_obj.monitor(flags=Gio.FileMonitorFlags.NONE, cancellable=None)
        self.file_monitor.set_rate_limit(2000)
        self.file_monitor.connect("changed", self.on_file_changed_externally)
    
    def unmonitor(self):
        try:
            self.file_monitor.cancel()
            self.file_monitor.dispose()
            #self.file_monitor = self.file_obj.monitor()
        except: pass
    
    def on_file_changed_externally(self, *args):
        if not self.autoreload:
            dialog: Adw.AlertDialog = Adw.AlertDialog.new(_("File Changed"), _("The file seems to have changed by an external program. Do you want to reload it?"))
            dialog.add_response("reload", _("Reload"))
            dialog.set_response_appearance("reload", Adw.ResponseAppearance.SUGGESTED)
            dialog.add_response("no", _("No"))
            dialog.set_close_response("no")
            dialog.set_default_response("reload")

            def on_response(*args):
                if args[1] == "reload":
                    self.reload_file()
                self.changed_dialog_shown = False
            dialog.connect("response",  on_response)

            if not self.changed_dialog_shown:
                dialog.present(self.parent_window)
                self.changed_dialog_shown = True
        else:
            self.reload_file()
