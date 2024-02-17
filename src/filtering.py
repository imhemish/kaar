from gi.repository import Gio, GObject
from .model import TodoTask

class Filtering(GObject.Object):
    filtering_types = ['all', 'due', 'complete', 'incomplete']

    #Default
    current_filtering: str = 'all'
    contexts: list = []
    projects: list = []
    _should_hide_hidden_tasks = False

    @GObject.Property(type=bool, default=False)
    def should_hide_hidden_tasks(self):
        return self._should_hide_hidden_tasks
    
    @should_hide_hidden_tasks.setter
    def should_hide_hidden_tasks(self, value):
        self._should_hide_hidden_tasks = value

    def __init__(self, application, changed_callback):
        super().__init__()
        self.should_hide_hidden_tasks = application.settings.get_boolean("hidden-tasks")
        application.settings.bind("hidden-tasks", self, "should_hide_hidden_tasks", Gio.SettingsBindFlags.GET)

        # Notifies the models that filtering has changed
        self.changed_callback = changed_callback

    def set_current_filtering(self, filter: str):
        self.current_filtering = filter
        self.changed_callback()
    
    def set_projects(self, projects: list):
        self.projects = projects
        self.changed_callback()
    
    def set_contexts(self, contexts: list):
        self.contexts = contexts
        self.changed_callback()

    def filter(self, object: TodoTask):
        # Make sure to use 'in' instead of '==' in here in if-else
        # because attributes.get returns a list and not a single element
        flag = False

        if self.current_filtering == 'all':
            flag = True

        elif self.current_filtering == 'due':
            flag = bool(object.attributes.get('due'))

        elif self.current_filtering == 'complete':
            flag = bool(object.completed)
        
        elif self.current_filtering == 'incomplete':
            flag = bool(not object.completed)

        for project in self.projects:
            if project in object.projects:
                flag = flag and True
            else:
                flag = flag and False
                # Even though flag was by default false
                # but still i did a flag=False on else condition
                # because it may have been switched to True by another tag
                # as we are accomodating a list of tags
        
        for context in self.contexts:
            if context in object.contexts:
                flag = flag and True
            else:
                flag = flag and False



        hidden_attribute = object.attributes.get('h')
        if hidden_attribute != None:
            if ('1' in hidden_attribute) and (self.should_hide_hidden_tasks):
                flag = False
        
        return flag
