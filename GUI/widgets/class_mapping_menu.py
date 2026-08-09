import pandas as pd
from PyQt6 import QtCore, QtGui, QtWidgets 
from PyQt6.QtWidgets import *

from functional.class_treeview_functions import *
from functional.class_struct_conditioner import *
from functional.class_icons import Icons
from functional.class_struct_tracker import TreeStructTracker
from controllers.class_filemap_cli_manager import *
from widgets.class_date_delegate import DateDelegate

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

    roles_map={
            "DisplayRole":(QtCore.Qt.ItemDataRole.DisplayRole,str), 
            "ToolTipRole":(QtCore.Qt.ItemDataRole.ToolTipRole,str),
            "StatusTipRole":(QtCore.Qt.ItemDataRole.StatusTipRole,str),
            "WhatsThisRole":(QtCore.Qt.ItemDataRole.WhatsThisRole,str),
            "DecorationRole":(QtCore.Qt.ItemDataRole.DecorationRole,QtGui.QColor),
            "ForegroundRole":(QtCore.Qt.ItemDataRole.ForegroundRole,QtGui.QColor),
            "FontRole":(QtCore.Qt.ItemDataRole.FontRole,QtGui.QFont),
            "TextAlignmentRole":(QtCore.Qt.ItemDataRole.TextAlignmentRole,QtCore.Qt.AlignmentFlag),
            "CheckStateRole":(QtCore.Qt.ItemDataRole.CheckStateRole,QtCore.Qt.CheckState),
            "SizeHintRole":(QtCore.Qt.ItemDataRole.SizeHintRole,QtCore.QSize),
            }

    def __init__(self, fmap:FileMapCliManager, treeview_obj:QTreeView, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        # Define main structure or use example
        self.fmap = fmap
        self.map_tv_obj = treeview_obj
        self.icons=Icons()
        self.all_icons_dict={}
        self._set_icons_dict()
        self._set_style_dict()
        self.map_struct=MAP_STRUCT_EXAMPLE.copy()
        self._syncing_ui = False
        self.info_cache=[] # list of info dicts
        self._build_map_configuration_tree()
        self.map_struct=self.generate_mapping_struct()

    def _set_icons_dict(self):
        self.all_icons_dict={
            "Device Map": self.icons.icon("device map"),
            "Keep": self.icons.icon("keep map"),
            "Remove": self.icons.icon("remove map"),
            "Backup": self.icons.icon("backup map"),
            "Selection Map": self.icons.icon("selection map"),
        }

    def _set_style_dict(self):

        #     DisplayRole         -> str
        #     ToolTipRole         -> str
        #     StatusTipRole       -> str
        #     WhatsThisRole       -> str
        #     DecorationRole      -> QIcon | QPixmap
        #     ForegroundRole      -> QColor | QBrush
        #     BackgroundRole      -> QColor | QBrush
        #     FontRole            -> QFont
        #     TextAlignmentRole   -> Qt.AlignmentFlag
        #     CheckStateRole      -> Qt.CheckState
        #     SizeHintRole        -> QSize
        #     UserRole+N          -> anything
        self.style_dict = {
            "Device Map":[{"field":'maptype'.upper(), "ForegroundRole":QtGui.QColor("#3498db")},
                          {"field":'maptype'.upper(), "DecorationRole":self.icons.icon("device map")}],
            "Keep": [{"field":'maptype'.upper(), "ForegroundRole":QtGui.QColor("#27ae60"), 
                      "DecorationRole":self.icons.icon("keep map")}],
            "Remove": [{"field":'maptype'.upper(),"ForegroundRole":QtGui.QColor("#e74c3c"), 
                        "DecorationRole":self.icons.icon("remove map")}],
            "Backup": [{"field":'maptype'.upper(), "ForegroundRole":QtGui.QColor("#e67e22"), 
                        "DecorationRole":self.icons.icon("backup map")}],
            "Selection Map": [{"field":'maptype'.upper(),"ForegroundRole":QtGui.QColor("#9b59b6"), 
                               "DecorationRole":self.icons.icon("selection map")}],            
        }
        active_map = [{
                        "field": "mount".upper(),
                        "ForegroundRole": QtGui.QColor("#27ae60"),
                        "FontRole": QtGui.QFont("", -1, QtGui.QFont.Weight.Bold),
                        #"DecorationRole": self.icons.icon("selection map"),
                    },
                    {
                        "field": "serial".upper(),
                        "ForegroundRole": QtGui.QColor("#27ae60"),
                        "FontRole": QtGui.QFont("", -1, QtGui.QFont.Weight.Bold),
                        #"DecorationRole": self.icons.icon("selection map"),
                    }]
        style_dict=dict(self.style_dict)
        for key,style_list in style_dict.items():
            new_key = key +" Active"
            new_style_list = style_list + active_map
            self.style_dict[new_key]= new_style_list
            
            

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
        date_delegate = DateDelegate(self.map_tv,output_format="%d %b %Y %H:%M")
        self.map_tv_obj.setItemDelegateForColumn(1, delegate)
        for col, field in enumerate(FIELDS_POSITION):
            if str(field["name"]).startswith("dt_".upper()):
                 self.map_tv_obj.setItemDelegateForColumn(col, date_delegate)

        self.map_tv.data_change[list,object,str,str].connect(self.on_tree_item_edited)
        self.map_tv.struct_data_change[list,object,str,str].connect(self.on_struct_item_edited)
        #self.map_tv.expand_to_depth(1) #333) #Expand all
        # Condition Engine
        self.map_ce=ConditionEngine(self.map_tv.tracker)
        self._evaluate_conditions()
        
        # Add cache tooltip, icons, backgrounds, styles
        self.map_tv.set_icons_cache(self.all_icons_dict)
        self.map_tv.set_style_cache(self.style_dict)
        # self.map_tv.set_map_cache(map_dict)

        # Allow multiselect
        self.map_tv_obj.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
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
        for column in range(self.map_tv.modelobj.columnCount()):
            self.map_tv_obj.resizeColumnToContents(column)

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
                if field =='maptype':
                    child_node["icon_key"]=str(df[field][idx])
                    child_node["style_key"]=str(df[field][idx])
                    # check if is active
                    devices=self.fmap.device_monitor.devices
                    for mount,serial in devices:
                        if str(df['mount'][idx]) ==mount and str(df['serial'][idx])==serial:
                            child_node["style_key"]=str(df[field][idx])+" Active"        
                    
                if field !='tablename':
                    child_node[field]=str(df[field][idx])
            # add the node
            self.tracker.set_value(track+[key],child_node)
    
        
       
        