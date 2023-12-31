import gi

from gi.repository import Gtk
from enum import Enum
from .model import TodoTask
from datetime import date

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
    direction: SortingDirection = SortingDirection.DESCENDING
    # Default direction is descending because generally you ought
    # to complete tasks in reverse priority

    def __init__(self):
        super().__init__()
    
    def set_sorting(self, new_sorting: TaskSorting) -> None:
        self.current_sorting = new_sorting

        # Notify to models that sorting algorithm has changed
        self.changed(Gtk.SorterChange.DIFFERENT)
    
    # Overriding Gtk.Sorter.compare method
    def do_compare(self, item1: TodoTask, item2: TodoTask) -> Gtk.Ordering:
        flag: Gtk.Ordering = Gtk.Ordering.EQUAL

        if self.current_sorting == TaskSorting.DESCRIPTION:
            if item1.bare_description() > item2.bare_description():
                flag = Gtk.Ordering.LARGER
            elif item1.bare_description() < item2.bare_description():
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
            if item1.attributes.get('due') == None:
                if item2.attributes.get('due') == None:
                    pass
                else:
                    flag = Gtk.Ordering.SMALLER
            elif item2.attributes.get('due') == None:
                if item1.attributes.get('due') == None:
                    pass
                else:
                    flag = Gtk.Ordering.LARGER
            elif date.fromisoformat(item1.attributes.get('due')[0]) > date.fromisoformat(item2.attributes.get('due')[0]):
                flag = Gtk.Ordering.LARGER
            elif date.fromisoformat(item1.attributes.get('due')[0]) < date.fromisoformat(item2.attributes.get('due')[0]):
                flag = Gtk.Ordering.SMALLER
        
        if flag == Gtk.Ordering.SMALLER and self.direction == SortingDirection.DESCENDING:
            flag = Gtk.Ordering.LARGER
        
        return flag
                    
