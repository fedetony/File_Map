from PyQt6 import QtCore, QtGui, QtWidgets 
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import *

import class_treeview_functions
import class_struct_conditioner
from class_struct_tracker import TreeStructTracker


FIELDS_POSITION=[
    {"name": "ITEM",  "editable": False, "selectable": True,  "hidden": False},
    {"name": "VALUE", "editable": True,  "selectable": True,  "hidden": True},
    {"name": "TYPE",  "editable": False, "selectable": False, "hidden": True},
    {"name": "UNIT",  "editable": False, "selectable": True, "hidden": True},
    {"name": "INFO",  "editable": True, "selectable": True, "hidden": True},
]
conditions={"rapid": "me_set('meta[hidden]',False) if node_get('rapid[Show[value]]') else me_set('meta[hidden]',True)",
            }

NAV_STRUCT_EXAMPLE={
        "FileMap": {"children":[                  
                {"1": {"value": "About", "type": "str", "unit":"",  
                           "meta": {"editable": False, "selectable": True,  "hidden": False}}},
                {"2": {"value": "Devices", "type": "str", "unit":"",  
                             "meta": {"editable": False, "selectable": True,  "hidden": False}}},
                {"3": {"value": "Databases", "type": "str", "unit":"",  
                               "meta": {"editable": False, "selectable": True,  "hidden": False}}},
                {"4": {"value": "Mapping", "type": "str", "unit":"",  
                             "meta": {"editable": False, "selectable": True,  "hidden": False}}},
                {"5": {"value": "Backup", "type": "str", "unit":"",  
                            "meta": {"editable": False, "selectable": True,  "hidden": False}}},
                {"6": {"value": "Sort", "type": "str", "unit":"",  
                          "meta": {"editable": False, "selectable": True,  "hidden": False}}},
                {"7": {"value": "Settings", "type": "str", "unit":"",  
                              "meta": {"editable": False, "selectable": True,  "hidden": False}}},
            ]},            
        }

class NavigationMenu(QtCore.QObject):

    pageSelected = pyqtSignal(str)

    def __init__(self, treeview_obj:QTreeView, nav_struct=None, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        # Define main structure or use example
        self.nav_tv_obj=treeview_obj
        if isinstance(nav_struct,dict):
            self.nav_struct=nav_struct
        else:
            self.nav_struct=NAV_STRUCT_EXAMPLE

        self._syncing_ui = False
        self._build_nav_configuration_tree()

    def _build_nav_configuration_tree(self):
        """Initialize and configure the style tree, delegates, condition engine, and context menu.

        Sets up treeview behavior, connects edit signals, evaluates conditions, and refreshes the UI.
        """
        self._do_evaluation=False
        self.nav_tv=class_treeview_functions.TreeviewFunctions(self.nav_tv_obj,self.nav_struct,FIELDS_POSITION)
        # attach delegate to VALUE column (1)
        delegate = class_treeview_functions.TypedItemDelegate(self.nav_tv)
        self.nav_tv_obj.setItemDelegateForColumn(1, delegate)
        self.nav_tv.data_change[list,object,str,str].connect(self.on_tree_item_edited)
        self.nav_tv.struct_data_change[list,object,str,str].connect(self.on_struct_item_edited)
        #self.nav_tv.expand_to_depth(1) #333) #Expand all
        # Condition Engine
        self.nav_ce=class_struct_conditioner.ConditionEngine(self.nav_tv.tracker)
        self._evaluate_conditions()
        self.nav_tv.item_clicked.connect(self.item_clicked)
        
        # Add cache tooltip, icons, backgrounds, styles
        # self.nav_tv.set_icons_cache(self.all_icons_dict)
        # self.nav_tv.set_nav_cache(nav_dict)

        # Right click Menu 
        self.nav_tv.treeviewobj.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.nav_tv.treeviewobj.customContextMenuRequested.connect(self.nav_tv._on_context_menu)
        #self.nav_tv.item_right_clicked.connect(self.on_item_right_clicked)
        
        self.nav_tv.do_refresh()

    @QtCore.pyqtSlot(list, object, str, str)
    def on_struct_item_edited(self, track, value, typestr, subtype):
        # Decide what to do with item value changed from code
        if self._do_evaluation:
            self._evaluate_conditions()

    @QtCore.pyqtSlot(list, object, object, str, str)
    def on_tree_item_edited_old_new(self, track, old_value, new_value, typestr, subtype):
        # Decide what to do with item value changed from user with old value
        pass

    @QtCore.pyqtSlot(list, object, str, str)
    def on_tree_item_edited(self, track, value, typestr, subtype):
        # Decide what to do with item value changed
        self._evaluate_conditions()
        # name=track[0]
        # obj=self._get_obj_from_track(track)
        # if obj:            
        #     self._build_nav_dict()
        #     self.apply_nav_changes(name)

        # here send signal to main
        print("on_tree_item_edited triggered ->",track, value, typestr, subtype)
        pass

    def _change_setting_trigger_evaluate_conditions(self, track, value):
        """Set a tracked value and re-evaluate conditions if the update succeeds.

        Returns True if the value was applied to the tracker.
        """
        self._do_evaluation=False
        was_set=self.nav_tv.tracker.set_value(track,value)
        if was_set:
            self._evaluate_conditions()
        # self._do_evaluation=False
        return was_set

    def _evaluate_conditions(self):
        """Evaluate condition rules and refresh the treeview when changes occur.

        Rebuilds UI state, restoring expansion and selection after condition updates.
        """
        do_eval=self._do_evaluation
        self._do_evaluation=False
        evaluated = self.nav_ce.evaluate_conditions_in_a_node(self.nav_tv.tracker.get_root())
        if evaluated or do_eval:
            expanded = self.nav_tv.get_expanded_paths()
            selected = self.nav_tv.get_selected_paths()
            # Delay the refresh AND the restore
            def delayed_refresh():
                self.nav_tv.do_refresh()
                self.nav_tv.restore_expanded_paths(expanded)
                self.nav_tv.restore_selected_paths(selected)
                self.nav_tv.treeview_fit_to_contents(0)
                # Important Clear circular reference flag
                self.nav_tv.tracker.remove_property_from_all_nodes(self.nav_tv.tracker.get_root(),"__conditions__applied__")
            # Need to wait until all data changes are applied.
            QtCore.QTimer.singleShot(0, delayed_refresh)


    def sync_ui(self, func):
        """Run a UI update while suppressing signal feedback."""
        self._syncing_ui = True
        func()
        self._syncing_ui = False

    @property
    def tracker(self)->TreeStructTracker:
        return self.nav_tv.tracker
    
    def set_value(self, track, value):
        """Sets the value and refreshes the conditions and treeview"""
        self._do_evaluation=True
        was_set=self.nav_tv.tracker.set_value(track,value)
        if was_set:
            self._evaluate_conditions()
        return was_set
    
    def item_clicked(self, key_item:QtGui.QStandardItem,index,val_item:dict):
        #knum = key_item.text(0) # key number
        track=val_item.get("path")
        if not isinstance(track,list):
            return
        track = track +["value"]
        name=self.nav_tv.tracker.get_value(track)
        if name in ["",None]:
            return
        self.pageSelected.emit(name)