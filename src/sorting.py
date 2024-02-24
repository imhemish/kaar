import gi

from gi.repository import Gtk
from enum import Enum
from .model import TodoTask
from datetime import date

# should be same order as in gschema
TaskSorting = Enum('TaskSorting', [
    "DUE_DATE",
    "CREATION_DATE",
    "DESCRIPTION",
    "COMPLETION_DATE"
    ])

# the task with most near approaching date is shown first
# doesnt have a descending order (design choice)
class DueDateSorter(Gtk.Sorter):
    """a custom Gtk.Sorter which sorts tasks according to Due Date"""
    def __init__(self, *args):
        super().__init__(*args)
    
    def do_get_order(self):
        return Gtk.SorterOrder.PARTIAL
    
    def do_compare(self, item1: TodoTask, item2: TodoTask) -> Gtk.Ordering:
        flag: Gtk.Ordering = Gtk.Ordering.EQUAL

        # Both don't have a due date
        if item1.attributes.get('due') == None and item2.attributes.get('due') == None:
            pass # By default, EQUAL

        # One task has due date, other doesnt
        elif item1.attributes.get('due') == None and item2.attributes.get('due') != None:
            flag = Gtk.Ordering.LARGER
        elif item1.attributes.get('due') != None and item2.attributes.get('due') == None:
            flag = Gtk.Ordering.SMALLER
        
        # Both have due dates, ad one is earlier than other
        elif date.fromisoformat(item1.attributes.get('due')[0]) > date.fromisoformat(item2.attributes.get('due')[0]):
            flag = Gtk.Ordering.LARGER
        elif date.fromisoformat(item1.attributes.get('due')[0]) < date.fromisoformat(item2.attributes.get('due')[0]):
            flag = Gtk.Ordering.SMALLER
        
        return flag

# The task which has earlier creation date, ie. was created a long time ago
# ought to be completed first, its a little opinionated, but ok
class CreationDateSorter(Gtk.Sorter):
    """a custom Gtk.Sorter which sorts tasks on basis of Creation Date"""
    def __init__(self, *args):
        super().__init__(*args)
    
    def do_get_order(self):
        return Gtk.SorterOrder.PARTIAL
    
    def do_compare(self, item1: TodoTask, item2: TodoTask) -> Gtk.Ordering:
        flag: Gtk.Ordering = Gtk.Ordering.EQUAL
        #print("Creation Date compare")
        if item1.creation_date == None and item2.creation_date == None:
            pass
        elif item1.creation_date == None and item2.creation_date != None:
            flag = Gtk.Ordering.LARGER
        elif item1.creation_date != None and item2.creation_date == None:
            flag = Gtk.Ordering.SMALLER
        elif item1.creation_date > item2.creation_date:
            flag = Gtk.Ordering.LARGER
        elif item1.creation_date < item2.creation_date:
            flag = Gtk.Ordering.SMALLER
        
        return flag

# The task which has later completion date, ie. was just completed
# would be shown first (opiniondates, design choice)
class CompletionDateSorter(Gtk.Sorter):
    """a custom Gtk.Sorter which sorts tasks on basis of completion date"""
    def __init__(self, *args):
        super().__init__(*args)
    
    def do_get_order(self):
        return Gtk.SorterOrder.PARTIAL
    
    def do_compare(self, item1: TodoTask, item2: TodoTask) -> Gtk.Ordering:
        #print("Completion Date compare")
        flag: Gtk.Ordering = Gtk.Ordering.EQUAL
        if item1.completion_date == None and item2.completion_date == None:
            pass
        elif item1.creation_date == None and item2.completion_date != None:
            flag = Gtk.Ordering.SMALLER
        elif item1.completion_date != None and item2.completion_date == None:
            flag = Gtk.Ordering.LARGER
        elif item1.completion_date > item2.completion_date:
            # The task which has later completion date, ie. was just completed
            # would be shown first
            flag = Gtk.Ordering.LARGER
        elif item1.completion_date < item2.completion_date:
            flag = Gtk.Ordering.SMALLER
        
        return flag

# Ideally we should be using a Gtk.StringSorter for sorting description because
# it efficiently and correctly sorts strings including non-latin unicode characters
# But it requires use of Gtk.Expression which is broken in PyGObject
# See https://gitlab.gnome.org/GNOME/pygobject/-/issues/457
# (I think its fixed? but i dont know how to implement it)
class DescriptionSorter(Gtk.Sorter):
    def __init__(self):
        super().__init__()
    def do_get_order(self):
        return Gtk.SorterOrder.PARTIAL
    
    def do_compare(self, item1: TodoTask, item2: TodoTask) -> Gtk.Ordering:
        #print("Description compare")
        flag: Gtk.Ordering = Gtk.Ordering.EQUAL
        item1_description = item1.bare_description()
        item2_description = item2.bare_description()
        if item1_description == None and item2_description == None:
            pass
        elif item1_description == None and item2_description != None:
            flag = Gtk.Ordering.SMALLER
        elif item1_description != None and item2.description == None:
            flag = Gtk.Ordering.LARGER
        elif item1_description > item2_description:
            flag = flag = Gtk.Ordering.LARGER
        elif item1_description < item2_description:
            flag = flag = Gtk.Ordering.SMALLER
        return flag

# a sorter which uses multi sorter internally to encompass
# due date, description, creation date, etc sorters
class TaskSorter(Gtk.Sorter):

    def __init__(self, sorting_priority):
        super().__init__()
        self.multi_sorter = Gtk.MultiSorter()
        self.sorting_priority = sorting_priority
        for i in self.sorting_objects_from_sorting_priority(self.sorting_priority):
            self.multi_sorter.append(i)
        self.changed(Gtk.SorterChange.DIFFERENT)
        

    @staticmethod
    def sorting_objects_from_sorting_priority(sorting_priority):
        sorters = []
        for i in sorting_priority:
            if i == TaskSorting.DUE_DATE:
                sorters.append(DueDateSorter())
            elif i == TaskSorting.CREATION_DATE:
                sorters.append(CreationDateSorter())
            elif i == TaskSorting.DESCRIPTION:
                sorters.append(DescriptionSorter())
            elif i == TaskSorting.COMPLETION_DATE:
                sorters.append(CompletionDateSorter())
        return sorters

    
    def set_sorting_priority(self, new_sorting_priority) -> None:
        self.sorting_priority = new_sorting_priority
        #print("New sorting: {}".format(self.sorting_priority))
        
        for i in range(self.multi_sorter.get_n_items()):
            self.multi_sorter.remove(i)
        for i in self.sorting_objects_from_sorting_priority(self.sorting_priority):
            self.multi_sorter.append(i)

        # Notify to models that sorting algorithm has changed
        self.changed(Gtk.SorterChange.DIFFERENT)
    
    # Overriding Gtk.Sorter.compare method
    def do_compare(self, item1, item2) -> Gtk.Ordering:
        #print("Running compare function for {} and {}".format(item1, item2))
        return self.multi_sorter.compare(item1, item2)

    def do_get_order(self):
        return Gtk.SorterOrder.PARTIAL
