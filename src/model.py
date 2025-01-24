import gi
from pytodotxt import Task
from gi.repository import GObject, Gtk, Adw, Gdk
import datetime
from typing import List

# This represents a single task row, which is actually made up of stack
# containing two views: edit and view as defined in task.blp
@Gtk.Template(resource_path='/net/hemish/kaar/blp/task.ui')
class TaskStack(Gtk.Stack):
    __gtype_name__ = "TaskStack"
    entry_row: Adw.EntryRow = Gtk.Template.Child()
    task_label: Gtk.Label = Gtk.Template.Child()
    check_button = Gtk.Template.Child()
    priority_label = Gtk.Template.Child()
    tags_flow_box: Gtk.FlowBox = Gtk.Template.Child()
    dates_flow_box: Gtk.FlowBox = Gtk.Template.Child()
    gesture_click: Gtk.GestureClick = Gtk.Template.Child()
    gesture_long_press: Gtk.GestureLongPress = Gtk.Template.Child()
    popover_menu: Gtk.PopoverMenu = Gtk.Template.Child()

    # Creates a label which holds name of projects, contexts, and due, completion dates
    def create_flow_box_item(self, object: str) -> Gtk.Label:
        #print("create function was called")
        label = Gtk.Label(label=object, hexpand=False, halign=Gtk.Align.START)
        label.add_css_class("tag")
        label.add_css_class("osd")
        return label
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.entry_row.connect("apply", self.on_entry_apply)
        self.connect("notify::visible-child-name", self.on_view_change)

        # Shows right click actions like delete, toggle editing
        self.gesture_click.connect("pressed", self.on_right_click)
        # same for touch devices
        self.gesture_long_press.connect("pressed", self.on_right_click)
        self.popover_menu.set_parent(self)
    
    def on_entry_apply(self, *args):
        print("entry apply")
        self.set_visible_child_name("view")
    
    # this is required because i can not create a bidirectional binding between
    # task_object.line and entry_row.text it causes circular dependencies due 
    # to the nature of line property
    def on_view_change(self, *args):
        print("view changed")
        if self.get_visible_child_name() == 'edit':
            print("view changed to edit mode")
            self.entry_row.set_text(str(self.object))
            self.entry_row.grab_focus()
        else:
            print("view changed to view mode")

            try:
                # Sometimes get_ancestor causes error because the widget sometimes
                # are disowned, that's why a try
                window: Adw.ApplicationWindow = self.get_ancestor(Adw.ApplicationWindow)
            except:
                pass

            print("line resetted")
            self.object.line = self.entry_row.get_text()

            # Reset tags and dates each time
            self.tags_flow_box.remove_all()
            for tag in self.object.tags:
                self.tags_flow_box.append(self.create_flow_box_item(tag))

            self.dates_flow_box.remove_all()
            for date in self.object._dates:
                self.dates_flow_box.append(self.create_flow_box_item(date))
            
            try:
                # sidebar projects and contexts
                window.update_projects_and_contexts_filters()

                # Save the file if 'autosave' gsetting is True
                # this should necessarily be after setting self.object.line
                # so that we save the new value, otherwise older values will be saved

                # this somehow fixes a bug, do not touch
                self.object.mode = "view"

                window.tab_view.get_selected_page().get_child().save_if_required()
            except:
                pass
    
    def on_right_click(self, *args):
        
            # Sometimes get_ancestor causes error because the widget sometimes
            # are disowned, that's why a try
            window: Adw.ApplicationWindow = self.get_ancestor(Adw.ApplicationWindow)
            tabchild = window.tab_view.get_selected_page().get_child()

            # We need to select the item on right click
            # as actions win.edit, win.delete work on selected item
            # so thats why all this code

            # You can't pass a reference to object to be selected in Gtk.SingleSelection
            # you can only set selected by position, so here traversing through model to find position
            for i, object in enumerate(tabchild.list_view.get_model()):
                if self.object == object:
                    tabchild.list_view.get_model().set_selected(i)
                    break


            # now show the popover menu
            self.popover_menu.popup()

# factory which would be used by list view for displaying tasks
class TaskFactory(Gtk.SignalListItemFactory):
    render_pango_markup: bool
    hide_check_buttons: bool

    def __init__(self, render_pango_markup: bool, hide_check_buttons: bool, **kwargs):
        super().__init__(**kwargs)
        # Setting up factory
        self.connect("setup", self.create_task_item)
        self.connect("bind", self.bind_task_item)
        self.connect("unbind", self.unbind_task_item)
        self.render_pango_markup = render_pango_markup
        self.hide_check_buttons = hide_check_buttons
    
    def create_task_item(self, fact, list_item) -> None:
        stack = TaskStack()
        if self.render_pango_markup:
            stack.task_label.set_use_markup(True)
        stack.check_button.set_visible(not self.hide_check_buttons)
        list_item.set_child(stack)
    
    def bind_task_item(self, fact, list_item) -> None:
        task_stack = list_item.get_child()
        task_object: TodoTask = list_item.get_item()
        task_stack.object = task_object

        task_stack.task_label.set_label(task_object.duplicatedescription)
        task_object.bind_property("duplicatedescription", task_stack.task_label, "label")

        task_stack.set_visible_child_name(task_object.mode)
        task_object.bind_property("mode", task_stack, "visible-child-name", GObject.BindingFlags.BIDIRECTIONAL)

        task_stack.entry_row.set_text(task_object.line)

        task_stack.check_button.set_active(task_object.is_completed)
        task_stack.completed_binding = task_stack.check_button.bind_property("active", task_object, "completed", GObject.BindingFlags.BIDIRECTIONAL)


        if task_object.duplicatepriority != None: 
            task_stack.priority_label.set_label(task_object.duplicatepriority)
        task_object.bind_property("duplicatepriority", task_stack.priority_label, "label")

        # Calculate tags and dates and put them appropriately
        task_stack.tags_flow_box.remove_all()
        for tag in task_object.tags:
            task_stack.tags_flow_box.append(task_stack.create_flow_box_item(tag))
        
        task_stack.dates_flow_box.remove_all()
        for date in task_object._dates:
            task_stack.dates_flow_box.append(task_stack.create_flow_box_item(date))

        # Holding a reference to signal to later disconnect it in unbind_task_item
        task_object.completed_signal = task_object.connect("notify::completed", lambda *args: task_stack.activate_action("win.save_if_required"))

    def unbind_task_item(self, fact, list_item) -> None:
        task_object: TodoTask = list_item.get_item()
        task_stack = list_item.get_child()

        task_object.disconnect(task_object.completed_signal)

        task_stack.completed_binding.unbind()
        

# a subclass of pytodotxt.Task and GObject.Object to be consumed by Gtk Widgets and GListModels
class TodoTask(Task, GObject.Object):
    mode = GObject.Property(type=str, default="view")
    __gtype_name__ = "TodoTask"

    def __init__(self, *args):
        super().__init__(*args) # Initialised pytodotxt.Task
        GObject.Object.__init__(self) # Initialises GObject
        self.notify("completed")
        self.mode = 'view' # Initial mode is view task
        self._line = str(self)
        self._dates = self.calculate_date_strings()

        # Calculate tags initially
        self.tags = [*map(lambda x: "+"+x, self.projects), *map(lambda x: "@"+x, self.contexts)]
        
    @GObject.Property(type=str)
    def line(self):
        self._line = str(self)
        return self._line
    
    @line.setter
    def line(self, value):
        self.parse(value)
        self._line = str(self)
        # When task line is set, notify that description, completed might have changed
        # and also update dates and tags
        self.notify("duplicatedescription")
        self.notify("completed")
        self._dates = self.calculate_date_strings()
        self.duplicatepriority = self.priority
        self.tags = [*map(lambda x: "+"+x, self.projects), *map(lambda x: "@"+x, self.contexts)]
    
    @GObject.Property(type=str)
    def duplicatedescription(self):
        return self.bare_description()

    @GObject.Property(type=bool, default=False)
    def completed(self):
        return self.is_completed
    
    @completed.setter
    def completed(self, value):
        self.is_completed = value

    @GObject.Property(type=str)
    def duplicatepriority(self):
        return self.priority

    @duplicatepriority.setter
    def duplicatepriority(self, value):
        self.priority = value

    def calculate_date_strings(self) -> List[str]:
        dates = []
        due = self.attributes.get("due")
        if due:
            dates.append(f'Due: {datetime.date.fromisoformat(str(due[0])).strftime("%x")}')
        if self.creation_date:
            dates.append(f'Created: {datetime.date.fromisoformat(str(self.creation_date)).strftime("%x")}')
        if self.completion_date:
            dates.append(f'Completed: {datetime.date.fromisoformat(str(self.completion_date)).strftime("%x")}')
        # %x formats the date according to current locale
        return dates

