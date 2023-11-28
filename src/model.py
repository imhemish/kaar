import gi
from pytodotxt import Task
from gi.repository import GObject, Gtk, Adw
import datetime

@Gtk.Template(resource_path='/net/hemish/kamm/blp/task.ui')
class TaskStack(Gtk.Stack):
    __gtype_name__ = "TaskStack"
    entry_row = Gtk.Template.Child()
    preview_row = Gtk.Template.Child()
    check_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.entry_row.connect("apply", self.on_entry_apply)
        self.connect("notify::visible-child-name", self.on_view_change)
    
    def on_entry_apply(self, *args):
        self.set_visible_child_name("view")
    
    # this is required because i can not create a bidirectional binding between
    # task_object.line and entry_row.text it causes circular dependencies due 
    # to the nature of line property
    def on_view_change(self, *args):
        if self.get_visible_child_name() == 'edit':
            print("mode changed to edit, so updating text")
            self.entry_row.set_text(str(self.object))
        else:
            print("mode changed to view, so updating descirpiotn")
            self.object.line = self.entry_row.get_text()

        
class TaskFactory(Gtk.SignalListItemFactory):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect("setup", self.create_task_item)
        self.connect("bind", self.bind_task_item)
    
    def create_task_item(self, fact, list_item):
        list_item.set_child(TaskStack())
    
    def bind_task_item(self, fact, list_item):
        task_stack = list_item.get_child()
        task_object = list_item.get_item()
        task_stack.object = task_object
        task_stack.preview_row.set_title(task_object._duplicatedescription)
        task_object.bind_property("duplicatedescription", task_stack.preview_row, "title")
        task_stack.set_visible_child_name(task_object.mode)
        task_object.bind_property("mode", task_stack, "visible-child-name", GObject.BindingFlags.BIDIRECTIONAL)
        task_stack.entry_row.set_text(task_object.line)
        if task_object.completed:
            task_stack.check_button.set_active(True)
        task_object.bind_property("completed", task_stack.check_button, "active", GObject.BindingFlags.BIDIRECTIONAL)
        task_stack.preview_row.set_subtitle(task_object.dates)
        task_object.bind_property("dates", task_stack.preview_row, "subtitle")
        

class TodoTask(Task, GObject.Object):
    mode = GObject.Property(type=str, default="view")
    def __init__(self, *args):
        super().__init__(*args)
        GObject.Object.__init__(self)
        self.mode = 'view'
        self._line = str(self)
        self._dates = self.calculate_date_string()
        self._duplicatedescription = self.bare_description()
    
    @GObject.Property(type=str)
    def line(self):
        return self._line
    
    @line.setter
    def line(self, value):
        self.parse(value)
        self._line = str(self)
        self.duplicatedescription = self.bare_description()
        self.completed = self.is_completed
        self.dates = self._dates
    
    @GObject.Property(type=str)
    def duplicatedescription(self):
        self._duplicatedescription = self.bare_description()
        return self.bare_description()

    @GObject.Property(type=bool, default=False)
    def completed(self):
        return self.is_completed
    
    @completed.setter
    def completed(self, value):
        self.is_completed = value
    
    @duplicatedescription.setter
    def duplicatedescription(self, value):
        self._duplicatedescription = value

    def calculate_date_string(self):
        date = ""
        due = self.attributes.get("due")
        if due:
            date += f'Due: {datetime.date.fromisoformat(str(due[0])).strftime("%x")}'
        return date

    @GObject.Property(type=str)
    def dates(self):
        return self.calculate_date_string()
    
    @dates.setter
    def dates(self, value):
        self._dates = self.calculate_date_string()

        


