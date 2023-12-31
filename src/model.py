import gi
from pytodotxt import Task
from gi.repository import GObject, Gtk, Adw, Gio
import datetime

# This represents a single task row, which is actually made up of stack
# containing two views: edit and view as defined in task.blp
@Gtk.Template(resource_path='/net/hemish/kamm/blp/task.ui')
class TaskStack(Gtk.Stack):
    __gtype_name__ = "TaskStack"
    entry_row: Adw.EntryRow = Gtk.Template.Child()
    task_label: Gtk.Label = Gtk.Template.Child()
    check_button = Gtk.Template.Child()
    priority_label = Gtk.Template.Child()
    tags_flow_box: Gtk.FlowBox = Gtk.Template.Child()
    dates_flow_box: Gtk.FlowBox = Gtk.Template.Child()

    def create_flow_box_item(self, object: str) -> Gtk.Box:
        print("create function was called")
        box = Gtk.Box()
        box.set_valign(Gtk.Align.END)
        box.set_hexpand(False)
        box.add_css_class("tag")
        box.add_css_class("osd")
        box.append(Gtk.Label.new(object))
        return box
    
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
            self.entry_row.set_text(str(self.object))
            self.entry_row.grab_focus()
        else:
            try:
                # Sometimes get_ancestor causes error because the widget sometimes
                # are disowned, that's why a try
                app = self.get_ancestor(Adw.ApplicationWindow).get_application()
            except:
                pass

            self.object.line = self.entry_row.get_text()

            self.tags_flow_box.remove_all()
            for tag in self.object.tags:
                self.tags_flow_box.append(self.create_flow_box_item(tag))

            self.dates_flow_box.remove_all()
            for date in self.object._dates:
                self.dates_flow_box.append(self.create_flow_box_item(date))
            # Save the file if 'autosave' gsetting is True
            # this block of code should necessarily be after setting self.object.line
            # so that we save the new value, otherwise older values will be saved
            try:
                app.save_if_required()
            except:
                pass

# factory which would be used by list view for displaying tasks
class TaskFactory(Gtk.SignalListItemFactory):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect("setup", self.create_task_item)
        self.connect("bind", self.bind_task_item)
    
    def create_task_item(self, fact, list_item):
        list_item.set_child(TaskStack())
    
    def bind_task_item(self, fact, list_item):
        task_stack = list_item.get_child()
        task_object: GObject.Object = list_item.get_item()
        task_stack.object = task_object

        task_stack.task_label.set_label(task_object._duplicatedescription)
        task_object.bind_property("duplicatedescription", task_stack.task_label, "label")

        task_stack.set_visible_child_name(task_object.mode)
        task_object.bind_property("mode", task_stack, "visible-child-name", GObject.BindingFlags.BIDIRECTIONAL)

        task_stack.entry_row.set_text(task_object.line)

        if task_object.completed:
            task_stack.check_button.set_active(True)
        task_object.bind_property("completed", task_stack.check_button, "active", GObject.BindingFlags.BIDIRECTIONAL)

        #task_stack.preview_row.set_subtitle(task_object.dates)
        #task_object.bind_property("dates", task_stack.preview_row, "subtitle")

        if task_object.duplicatepriority != None: 
            task_stack.priority_label.set_label(task_object.duplicatepriority)
        task_object.bind_property("duplicatepriority", task_stack.priority_label, "label")

        task_stack.tags_flow_box.remove_all()
        for tag in task_object.tags:
            task_stack.tags_flow_box.append(task_stack.create_flow_box_item(tag))
        
        task_stack.dates_flow_box.remove_all()
        for date in task_object._dates:
            task_stack.dates_flow_box.append(task_stack.create_flow_box_item(date))


        

# a subclass of pytodotxt.Task to be consumed by Gtk Widgets and GObjects
class TodoTask(Task, GObject.Object):
    mode = GObject.Property(type=str, default="view")

    def __init__(self, *args):
        super().__init__(*args)
        GObject.Object.__init__(self)
        self.mode = 'view'
        self._line = str(self)
        self._dates = self.calculate_date_strings()
        self._duplicatedescription = self.bare_description()
        self.tags = [*map(lambda x: "+"+x, self.projects), *map(lambda x: "@"+x, self.contexts)]
        

    
    @GObject.Property(type=str)
    def line(self):
        self._line = str(self)
        return self._line
    
    @line.setter
    def line(self, value):
        self.parse(value)
        self._line = str(self)
        self.duplicatedescription = self.bare_description()
        self.completed = self.is_completed
        self._dates = self.calculate_date_strings() # Doesnt matter what value you pass here
        self.duplicatepriority = self.priority
        self.tags = [*map(lambda x: "+"+x, self.projects), *map(lambda x: "@"+x, self.contexts)]
    
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

    @GObject.Property(type=str)
    def duplicatepriority(self):
        return self.priority

    @duplicatepriority.setter
    def duplicatepriority(self, value):
        self.priority = value

    def calculate_date_strings(self):
        dates = []
        due = self.attributes.get("due")
        if due:
            dates.append(f'Due: {datetime.date.fromisoformat(str(due[0])).strftime("%x")}')
        if self.creation_date:
            dates.append(f'Created: {datetime.date.fromisoformat(str(self.creation_date)).strftime("%x")}')
        if self.completion_date:
            dates.append(f'Completed: {datetime.date.fromisoformat(str(self.completion_date)).strftime("%x")}')

        return dates

