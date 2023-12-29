from gi.repository import Gio, GObject
from .model import TodoTask

class Filtering(GObject.Object):
    filtering_types = ['all', 'due', 'due:', 'complete', 'project:', 'context:']

    #Default
    current_filtering: str = 'all'
    _should_hide_hidden_tasks = False

    @GObject.Property(type=bool, default=False)
    def should_hide_hidden_tasks(self):
        return self._should_hide_hidden_tasks
    
    @should_hide_hidden_tasks.setter
    def should_hide_hidden_tasks(self, value):
        self._should_hide_hidden_tasks = value

    def __init__(self, application):
        super().__init__()
        self.should_hide_hidden_tasks = application.settings.get_boolean("hidden-tasks")
        application.settings.bind("hidden-tasks", self, "should_hide_hidden_tasks", Gio.SettingsBindFlags.GET)

    def filter(self, object: TodoTask):
        # Make sure to use 'in' instead of '==' in here in if-else
        # because attributes.get returns a list and not a single element
        print("Filtering for {}".format(object.bare_description))
        flag = False


        if self.current_filtering == 'all':
            flag = True

        elif ('due' in self.current_filtering) and (':' in self.current_filtering):
            due_attributes = object.attributes.get('due')
            if due_attributes != None:
                flag =  (self.current_filtering.split(":")[1] in due_attributes)

        elif self.current_filtering == 'due':
            flag = bool(object.attributes.get('due'))

        elif self.current_filtering == 'complete':
            flag = bool(object.completed)

        elif 'project' in self.current_filtering:
            project_attributes = object.projects
            if project_attributes != None:
                flag = (self.current_filtering.split(":")[1] in project_attributes)
        
        elif 'context' in self.current_filtering:
            context_attributes = object.contexts
            if context_attributes != None:
                flag = (self.current_filtering.split(":")[1] in context_attributes)

        hidden_attribute = object.attributes.get('h')
        if hidden_attribute != None:
            if ('1' in hidden_attribute) and (self.should_hide_hidden_tasks):
                print("um it should be hidden")
                flag = False
        
        print("I am returning {}".format(flag))
        
        return flag
