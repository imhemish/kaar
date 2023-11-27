import gi
from pytodotxt import Task
from gi.repository import GObject, Gtk

@Gtk.Template(resource_path='/net/hemish/kamm/blp/task.ui')
class TaskStack(Gtk.Stack):
    __gtype_name__ = "TaskStack"
    entry_row = Gtk.Template.Child()
    preview_row = Gtk.Template.Child()
    priority = Gtk.Template.Child()
    due = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_visible_child_name("preview")
        
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
        task_stack.preview_row.set_title(task_object.description)
        task_object.bind_property("description", task_stack.preview_row, "title", GObject.BindingFlags.BIDIRECTIONAL)
        task_stack.preview_row.set_subtitle(str(task_object.completed))

class TodoTask(GObject.Object):
    def __init__(self, description: str, completed: bool):
        super().__init__()
        self._description = description
        self._completed = completed
    
    @GObject.Property(type=str)
    def description(self):
        return self._description

    @GObject.Property(type=bool, default=True)
    def completed(self):
        return self._completed

