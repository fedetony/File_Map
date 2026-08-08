import pandas as pd
from PyQt6 import QtCore, QtGui, QtWidgets 
from PyQt6.QtWidgets import *

from functional.class_treeview_functions import *
from functional.class_struct_conditioner import *
from functional.class_struct_tracker import TreeStructTracker
from controllers.class_filemap_cli_manager import *

from functional.class_LogHandler import LM
log=LM.get_logger_with_handler("MappingMenuTree","debug",True,None)

#On registry

#field_list=['id','dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype']
FIELDS_POSITION=[
    {"name": "ITEM",  "editable": False, "selectable": True,  "hidden": False},
    {"name": "VALUE", "editable": True,  "selectable": True,  "hidden": False}, # tablename

    {"name": 'mapname'.upper(), "editable": True,  "selectable": True,  "hidden": True}, # mapname

    #{"name": 'tablename'.upper(), "editable": True,  "selectable": True,  "hidden": False}, # tablename
    {"name": 'maptype'.upper(), "editable": False,  "selectable": True,  "hidden": False}, # maptype
    {"name": 'id'.upper(),  "editable": False, "selectable": True, "hidden": True},
    {"name": "MAPSIZE",  "editable": False, "selectable": True, "hidden": False},
    
    {"name": 'dt_map_created'.upper(),  "editable": False, "selectable": True, "hidden": False}, #'dt_map_created'
    {"name": 'dt_map_modified'.upper(),  "editable": False, "selectable": True, "hidden": False}, #'dt_map_modified'
    
    {"name": 'serial'.upper(),  "editable": False, "selectable": True, "hidden": False},
    {"name": 'mount'.upper(),  "editable": False, "selectable": True, "hidden": False},
    {"name": 'mappath'.upper(),  "editable": False, "selectable": True, "hidden": False}, #'mappath' 

    {"name": "TYPE",  "editable": False, "selectable": False, "hidden": True},
    {"name": "INFO",  "editable": True, "selectable": True, "hidden": True},

]
conditions={"Serial": "me_set('meta[hidden]',False) if node_get('rapid[Show[value]]') else me_set('meta[hidden]',True)",
            }

MAP_STRUCT_EXAMPLE={
        "Databases": {"children":[                                  
            ]},            
        }
MAX_TIME_IN_S = 5

class MappingMenu(QtCore.QObject):
    def __init__(self, fmap:FileMapCliManager, treeview_obj:QTreeView, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        # Define main structure or use example
        self.fmap = fmap
        self.map_tv_obj = treeview_obj
        self.map_struct=MAP_STRUCT_EXAMPLE.copy()
        self._syncing_ui = False
        self.info_cache=[] # list of info dicts
        self._build_map_configuration_tree()
        self.map_struct=self.generate_mapping_struct()

    @property
    def tracker(self):
        return self.map_ce.tracker

    def _build_map_configuration_tree(self):
        """Initialize and configure the style tree, delegates, condition engine, and context menu.

        Sets up treeview behavior, connects edit signals, evaluates conditions, and refreshes the UI.
        """
        self._do_evaluation=False
        self.map_tv=TreeviewFunctions(self.map_tv_obj,self.map_struct,FIELDS_POSITION)
        # attach delegate to VALUE column (1)
        delegate = TypedItemDelegate(self.map_tv)
        self.map_tv_obj.setItemDelegateForColumn(1, delegate)
        self.map_tv.data_change[list,object,str,str].connect(self.on_tree_item_edited)
        self.map_tv.struct_data_change[list,object,str,str].connect(self.on_struct_item_edited)
        #self.map_tv.expand_to_depth(1) #333) #Expand all
        # Condition Engine
        self.map_ce=ConditionEngine(self.map_tv.tracker)
        self._evaluate_conditions()
        
        # Add cache tooltip, icons, backgrounds, styles
        # self.map_tv.set_icons_cache(self.all_icons_dict)
        # self.map_tv.set_map_cache(map_dict)

        # Right click Menu 
        self.map_tv.treeviewobj.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.map_tv.treeviewobj.customContextMenuRequested.connect(self.map_tv._on_context_menu)
        #self.map_tv.item_right_clicked.connect(self.on_item_right_clicked)
        
        self.map_tv.do_refresh()

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
        #     self._build_map_dict()
        #     self.apply_map_changes(name)

        # here send signal to main
        print("on_tree_item_edited triggered ->",track, value, typestr, subtype)
        pass

    def _change_setting_trigger_evaluate_conditions(self, track, value):
        """Set a tracked value and re-evaluate conditions if the update succeeds.

        Returns True if the value was applied to the tracker.
        """
        self._do_evaluation=False
        was_set=self.map_tv.tracker.set_value(track,value)
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
        evaluated = self.map_ce.evaluate_conditions_in_a_node(self.map_tv.tracker.get_root())
        if evaluated or do_eval:
            expanded = self.map_tv.get_expanded_paths()
            selected = self.map_tv.get_selected_paths()
            # Delay the refresh AND the restore
            def delayed_refresh():
                self.map_tv.do_refresh()
                self.map_tv.restore_expanded_paths(expanded)
                self.map_tv.restore_selected_paths(selected)
                self.map_tv.treeview_fit_to_contents(0)
                # Important Clear circular reference flag
                self.map_tv.tracker.remove_property_from_all_nodes(self.map_tv.tracker.get_root(),"__conditions__applied__")
            # Need to wait until all data changes are applied.
            QtCore.QTimer.singleShot(0, delayed_refresh)

    def sync_ui(self, func):
        """Run a UI update while suppressing signal feedback."""
        self._syncing_ui = True
        func()
        self._syncing_ui = False
  
    @property
    def tracker(self)->TreeStructTracker:
        return self.map_tv.tracker
    
    def set_value(self, track, value):
        """Sets the value and refreshes the conditions and treeview"""
        self._do_evaluation=True
        was_set=self.map_tv.tracker.set_value(track,value)
        if was_set:
            self._evaluate_conditions()
        return was_set
    
    def _add_db_maps_to_struct(self,db:DatabaseInfo,db_key):
        db_filepath=str(db.database_filepath) # path object
        datamanage=self.fmap.get_map_info_datamanage(db_filepath) # includes other fields as size
        # Here select behavior of mapping
        editable=True
        selectable=True
        hidden=False
        fields_to_tab=None
        sort_by=None
        ascending=True
        # Form map structure
        self.tracker.delete_node(["Databases",db_key])
        self.add_map_to_struct(["Databases", db_key], 
                               datamanage, 
                               editable,selectable,hidden,
                               fields_to_tab,sort_by,ascending)
        
    def generate_mapping_struct(self):
        db_list=self.fmap.get_active_databases_in_dbm()
        self.map_struct=MAP_STRUCT_EXAMPLE.copy() #clear struct

        for db_id,db in enumerate(db_list):
            if not isinstance(db,DatabaseInfo):
                continue
            #self.tracker.delete_node(["Databases",f"{map_id}"])
            db_key=f"{db_id} {db.name}"
            log.debug(f"generate maping -> {db_key}")
            self._add_db_maps_to_struct(db,db_key)
        print(self.tracker.get_root())
    
        # refresh treeview
        self.map_tv.refresh_treeview(self.map_struct,self.map_tv.modelobj,self.map_tv_obj)
        self.map_tv.expand_to_depth(3)

    def add_map_to_struct(self,track,
                          datamanage:DataManage, 
                          editable=False,selectable=True,hidden=False,
                          fields_to_tab=None,sort_by=None,ascending=True):
        if not datamanage:
            return
        df=datamanage.get_selected_df(fields_to_tab,sort_by,ascending)
        #field_list=['id','dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype'] +['mapsize']
        
        for idx,tablename in enumerate(df['tablename']):
            key = f"{idx}"
            self.tracker.ensure_path(track+[key])
            child_node = {
                    "value": tablename, 
                    "type": "str", 
                    "unit":"", 
                    "meta": {
                            "editable": editable, 
                            "selectable": selectable,  
                            "hidden": hidden
                            }
                    }
            for field in datamanage.fields:
                if field !='tablename':
                    child_node[field]=str(df[field][idx])
            # add the node
            self.tracker.set_value(track+[key],child_node)
    
    
        
        
        
       
        