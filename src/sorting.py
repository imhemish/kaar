import gi

from gi.repository import Gtk
from enum import Enum
# from .model import TodoTask
from datetime import date
from pytodotxt import Task

# should be same order as in ui.blp file for sorting
TaskSorting = Enum('TaskSorting', [
    "DESCRIPTION",
    "DUE_DATE",
    "CREATION_DATE",
    "COMPLETION_DATE"
    ])

SortingDirection = Enum('SortingDirection', ["ASCENDING", "DESCENDING"])

class TaskSorter(Gtk.Sorter):
    # Setting defaults
    current_sorting: TaskSorting = TaskSorting.DUE_DATE
    # Default direction is descending because generally you ought
    # to complete tasks in reverse priority

    def __init__(self, direction: SortingDirection = SortingDirection.DESCENDING):
        super().__init__()
        self.direction = direction
    
    def set_direction(self, direction: SortingDirection):
        self.direction = direction

        self.changed(Gtk.SorterChange.DIFFERENT)
    
    def set_sorting(self, new_sorting: TaskSorting) -> None:
        self.current_sorting = new_sorting
        print("New sorting: {}".format(self.current_sorting))

        # Notify to models that sorting algorithm has changed
        self.changed(Gtk.SorterChange.DIFFERENT)
    
    # Overriding Gtk.Sorter.compare method
    def do_compare(self, item1, item2) -> Gtk.Ordering:
        flag: Gtk.Ordering = Gtk.Ordering.EQUAL

        if self.current_sorting == TaskSorting.DESCRIPTION:
            # TODO: Add preference for case sensitive description filtering
            if item1.bare_description().lower() > item2.bare_description().lower():
                flag = Gtk.Ordering.LARGER
            elif item1.bare_description().lower() < item2.bare_description().lower():
                flag = Gtk.Ordering.SMALLER
        
        elif self.current_sorting == TaskSorting.CREATION_DATE:

            # If some task does not have a creation date, then the other gets priority
            if item1.creation_date == None:
                if item2.creation_date == None:
                    # Flag remains Gtk.Ordering.EQUAL
                    pass
                else:
                    flag = Gtk.Ordering.SMALLER
            elif date.fromisoformat(item1.creation_date) > date.fromisoformat(item2.creation_date):
                flag = Gtk.Ordering.LARGER
            elif date.fromisoformat(item1.creation_date) < date.fromisoformat(item2.creation_date):
                flag = Gtk.Ordering.SMALLER
            else:
                # A little bit opnionated here
                # If creation date of each is equal, then I am comparing due date
                if item1.attributes.get('due') == None:
                    if item2.attributes.get('due') == None:
                        pass
                    else:
                        flag = Gtk.Ordering.SMALLER
                elif date.fromisoformat(item1.attributes.get('due')[0]) > date.fromisoformat(item2.attributes.get('due')[0]):
                    flag = Gtk.Ordering.LARGER
                elif date.fromisoformat(item1.attributes.get('due')[0]) < date.fromisoformat(item2.attributes.get('due')[0]):
                    flag = Gtk.Ordering.SMALLER

        elif self.current_sorting == TaskSorting.COMPLETION_DATE:
            if item1.completion_date == None:
                if item2.completion_date == None:
                    pass
                else:
                    flag = Gtk.Ordering.SMALLER
            elif date.fromisoformat(item1.completion_date) > date.fromisoformat(item2.completion_date):
                flag = Gtk.Ordering.LARGER
            elif date.fromisoformat(item1.completion_date) < date.fromisoformat(item2.completion_date):
                flag = Gtk.Ordering.SMALLER
        
        elif self.current_sorting == TaskSorting.DUE_DATE:
            print("Sorting on the basis of due date")
            if item1.attributes.get('due') == None and item2.attributes.get('due') == None:
                pass # By default, EQUAL
            elif item1.attributes.get('due') == None and item2.attributes.get('due') != None:
                flag = Gtk.Ordering.LARGER
            elif item1.attributes.get('due') != None and item2.attributes.get('due') == None:
                flag = Gtk.Ordering.SMALLER
            elif date.fromisoformat(item1.attributes.get('due')[0]) > date.fromisoformat(item2.attributes.get('due')[0]):
                flag = Gtk.Ordering.LARGER
            elif date.fromisoformat(item1.attributes.get('due')[0]) < date.fromisoformat(item2.attributes.get('due')[0]):
                flag = Gtk.Ordering.SMALLER
        
        if flag == Gtk.Ordering.SMALLER and self.direction == SortingDirection.ASCENDING:
            flag = Gtk.Ordering.LARGER
        elif flag == Gtk.Ordering.LARGER and self.direction == SortingDirection.ASCENDING:
            flag = Gtk.Ordering.SMALLER
        
        return flag

task1 = Task('due:2023-04-08')
task2 = Task()

sorter = TaskSorter()
print(sorter.do_compare(task1, task2))