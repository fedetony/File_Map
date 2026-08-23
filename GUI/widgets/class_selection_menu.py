# class_selection_menu.py
import pandas as pd
from PyQt6 import QtCore, QtGui, QtWidgets 
from PyQt6.QtWidgets import *

from functional.class_treeview_functions import *
from functional.class_struct_conditioner import *
from functional.class_icons import Icons
from functional.class_struct_tracker import TreeStructTracker
from controllers.class_filemap_cli_manager import *
from widgets.class_delegates import ActiveMapDelegate,ItemTypeDelegate

from models.class_style_provider import *

from functional.class_LogHandler import LM
log=LM.get_logger_with_handler("SelectionMenuTree","debug",True,None)

#On registry

#field_list=['id','dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype']
FIELDS_POSITION=[
    {"name": "ITEM",  "editable": False, "selectable": True,  "hidden": False},
    {"name": "VALUE", "editable": True,  "selectable": True,  "hidden": False}, # tablename
    {"name": 'mount'.upper(),  "editable": False, "selectable": True, "hidden": False},
    {"name": 'serial'.upper(),  "editable": False, "selectable": True, "hidden": False},
    {"name": 'quantity'.upper(),  "editable": False, "selectable": True, "hidden": False},
    {"name": 'itempath'.upper(),  "editable": False, "selectable": True, "hidden": False},  
    {"name": 'itemtype'.upper(), "editable": False,  "selectable": True,  "hidden": False},
    {"name": 'from_db'.upper(),  "editable": False, "selectable": True, "hidden": False},  
    {"name": 'from_map'.upper(), "editable": False,  "selectable": True,  "hidden": False}, 

    {"name": "TYPE",  "editable": False, "selectable": False, "hidden": True},
    {"name": "INFO",  "editable": True, "selectable": True, "hidden": True},

]
conditions={"MapValidation": "me_set('meta[hidden]',False) if node_get('rapid[Show[value]]') else me_set('meta[hidden]',True)",
            }
MAP_NODE_TEMPLATE={"Map": {"value": "Selection", "type": "str", "subtype": "str", 
                           "mount":"",
                           "serial":"",
                           "itempath":"",
                           "itemtype":"",
                           "from_db":"",
                           "from_map":"",
                           "quantity":"0",
                           "meta": {"editable": True}},
                           "children":[],
                }
ITEM_NODE_TEMPLATE={"PathorFile": {"value": "Selection", "type": "str", "subtype": "str", 
                           "mount":"",
                           "serial":"",
                           "itempath":"",
                           "itemtype":"",
                           "from_db":"",
                           "from_map":"",
                           "quantity":"0",
                           "meta": {"editable": False}}}
SELECT_STRUCT_EXAMPLE={
        "Database": { 
            "value":"", "type": "str",
            "meta": {"hidden":False, "editable":False},
            "children":[                               

            ],
        },  
        }

class SelectionMenu(QtCore.QObject):

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

    mapping_running_state = QtCore.pyqtSignal(str,bool)

    def __init__(self, fmap:FileMapCliManager, treeview_obj:QTreeView, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        # Define main structure or use example
        self.fmap = fmap
        self.sel_tv_obj = treeview_obj
        self.icons=Icons()
        self.database = ""
        self.sel_struct=SELECT_STRUCT_EXAMPLE.copy()
        self._syncing_ui = False
        self._build_selection_configuration_tree()
        self.generate_selection_struct()
    
    @property
    def tracker(self):
        return self.sel_ce.tracker

    def _build_selection_configuration_tree(self):
        """Initialize and configure the style tree, delegates, condition engine, and context menu.

        Sets up treeview behavior, connects edit signals, evaluates conditions, and refreshes the UI.
        """
        self._sort_field=None
        self._sort_ascending=True
        self._do_evaluation=False
        self.sel_tv=TreeviewFunctions(self.sel_tv_obj,self.sel_struct,FIELDS_POSITION)
        # attach delegate to VALUE column (1)
        delegate = TypedItemDelegate(self.sel_tv)
        #date_delegate = DateDelegate(self.sel_tv,output_format="%d %b %Y %H:%M")
        #color_size_delegate = ColoredTextDelegate(self.sel_tv_obj) 
        self.sel_tv_obj.setItemDelegateForColumn(1, delegate)
        # Header sorting
        header = self.sel_tv_obj.header()
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(True)
        header.sectionClicked.connect(self._tree_header_clicked)

        def field_col(field:str)->int:
            for col, fie in enumerate(FIELDS_POSITION):
                if str(fie["name"])==field.upper():     
                    return col
            return 0
        icons_dict = {
            "database": self.icons.icon("db admin"),
            "map":      self.icons.icon("selection map"),
            "dir":      self.icons.icon("folder ok"),
            "file":     self.icons.icon("data list"),
        }
        mount_col=field_col("mount")        
        serial_col=field_col("serial")
        itemtype_col=field_col("itemtype")
        item_type_delegate = ItemTypeDelegate(icons_dict,
                                              itemtype_column=itemtype_col,
                                              parent=self.sel_tv)
        active_map_delegate = ActiveMapDelegate(fmap=self.fmap,
                                                mount_column=mount_col,
                                                serial_column=serial_col,
                                                parent=self.sel_tv)
        
        self.sel_tv_obj.setItemDelegateForColumn(itemtype_col, item_type_delegate)
        self.sel_tv_obj.setItemDelegateForColumn(mount_col, active_map_delegate)
        self.sel_tv_obj.setItemDelegateForColumn(serial_col, active_map_delegate)

        #     if str(field["name"]).startswith("dt_".upper()):
        #          self.sel_tv_obj.setItemDelegateForColumn(col, date_delegate)
        #     if str(field["name"])=="mapsize".upper():
        #          self.sel_tv_obj.setItemDelegateForColumn(col, color_size_delegate)

        self.sel_tv.data_change[list,object,str,str].connect(self.on_tree_item_edited)
        self.sel_tv.data_change_old_new[list, object ,object, str, str].connect(self.on_tree_item_edited_old_new)
        self.sel_tv.struct_data_change[list,object,str,str].connect(self.on_struct_item_edited)

        #self.sel_tv.expand_to_depth(1) #333) #Expand all
        # Condition Engine
        self.sel_ce=ConditionEngine(self.sel_tv.tracker)
        self._evaluate_conditions()
        
        # Add cache tooltip, icons, backgrounds, styles
        #self.sel_tv.set_icons_cache(self.all_icons_dict)
        #self.sel_tv.set_style_cache(self.style_dict)
        # self.sel_tv.set_map_cache(sel_dict)

        # Allow multiselect
        self.sel_tv_obj.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        # Right click Menu 
        self.sel_tv.treeviewobj.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.sel_tv.treeviewobj.customContextMenuRequested.connect(self.sel_tv._on_context_menu)
        self.sel_tv.item_right_clicked.connect(self.on_item_right_clicked)
        
        self.sel_tv.do_refresh()

    def _tree_header_clicked(self, column: int):
        if not 0 <= column < len(FIELDS_POSITION):
            return
        field = str(FIELDS_POSITION[column]["name"])

        if field == "ITEM":
            pro_field = None              # original database loading order
        elif field == "VALUE":
            pro_field = "tablename"
        else:
            pro_field = field.lower()

        # Toggle direction when clicking the same column
        if pro_field and getattr(self, "_sort_field", None) == pro_field:
            self._sort_ascending = not self._sort_ascending
        else:
            self._sort_field = pro_field    
            self._sort_ascending = True

        self._update_regenerate()
    
    @QtCore.pyqtSlot(list, object, str, str)
    def on_struct_item_edited(self, track, value, typestr, subtype):
        # Decide what to do with item value changed from code
        if self._do_evaluation:
            self._evaluate_conditions()

    @QtCore.pyqtSlot(list, object, object, str, str)
    def on_tree_item_edited_old_new(self, track, old_value, new_value, typestr, subtype):
        # Decide what to do with item value changed from user with old value
        is_valid, msg = self.fmap.map_validation(self.database,new_value)
        if "value" in track:
            # Rename was triggered
            a_map = old_value #self.tracker.get_value(track)
            if not is_valid:
                self._change_setting_trigger_evaluate_conditions(track, old_value)
                log.warning(msg)
            QtCore.QTimer.singleShot(0, self._update_regenerate)

    @QtCore.pyqtSlot(list, object, str, str)
    def on_tree_item_edited(self, track, value, typestr, subtype):
        # Decide what to do with item value changed
        self._evaluate_conditions()

        print("on_tree_item_edited triggered ->",track, value, typestr, subtype)
    
    def _change_setting_trigger_evaluate_conditions(self, track, value):
        """Set a tracked value and re-evaluate conditions if the update succeeds.

        Returns True if the value was applied to the tracker.
        """
        self._do_evaluation=False
        was_set=self.sel_tv.tracker.set_value(track,value)
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
        evaluated = self.sel_ce.evaluate_conditions_in_a_node(self.sel_tv.tracker.get_root())
        if evaluated or do_eval:
            expanded = self.sel_tv.get_expanded_paths()
            selected = self.sel_tv.get_selected_paths()
            # Delay the refresh AND the restore
            def delayed_refresh():
                self.sel_tv.do_refresh()
                self.sel_tv.restore_expanded_paths(expanded)
                self.sel_tv.restore_selected_paths(selected)
                self.sel_tv.treeview_fit_to_contents(0)
                # Important Clear circular reference flag
                self.sel_tv.tracker.remove_property_from_all_nodes(self.sel_tv.tracker.get_root(),"__conditions__applied__")
            # Need to wait until all data changes are applied.
            QtCore.QTimer.singleShot(0, delayed_refresh)
    
    def _update_regenerate(self):
        self.generate_selection_struct()
    
    def on_item_right_clicked(self,index:QtCore.QModelIndex, info_dict: dict, pos: QtCore.QPoint):
        """Right click menu"""
        #self.build_context_menu(index,info_dict,pos)
        return
    
    def generate_selection_struct(self, node_list:list=None):
        # delete all children

        v_dict=self.tracker.validate_node(["Database"])
        for child in v_dict.get("children_keys"):
            vc_dict=self.tracker.validate_node(["Database",child])
            self.tracker.delete_node(["Database",child])

        self.sel_struct=SELECT_STRUCT_EXAMPLE.copy() #clear struct
        self.tracker
        if not node_list:
            self._refresh_the_tv()
            return 
        devices_set=self._get_devices_sets(node_list)
        if not devices_set:
            self._refresh_the_tv()
            return 
        for iii,(mount,serial) in enumerate(devices_set):
            db_name = self.fmap.fm.extract_filename(self.database)
            db_path = self.fmap.fm.extract_path(self.database)
            self.tracker.set_value(["Database","value"],db_name)
            self.tracker.set_value(["Database","itempath"],db_path)
            self.tracker.set_value(["Database","itemtype"],"database")
            map_node=MAP_NODE_TEMPLATE["Map"].copy()
            map_name=f"{iii} Selection:" 
            map_node["value"] = f"{self.fmap.timestamp}_Selection_{iii}"
            map_node["mount"] = mount
            map_node["serial"] = serial
            map_node["itemtype"] = "map"
            map_node["from_db"] = ""
            map_node["from_map"] = ""
            common_path=""
            sum_quants=0

            self.tracker.add_child(["Database"],map_name,map_node)
            for jjj,node in enumerate(node_list):
                if isinstance(node,TreeNode):
                    path_list=[]
                    mount_serial_pair=self.fmap.get_mount_serial_of_map(node.db,node.map)
                    if mount == mount_serial_pair[0] and serial == mount_serial_pair[1]:
                        item_node=ITEM_NODE_TEMPLATE["PathorFile"].copy()
                        path_list.append(node.path)
                        item_node["value"] = node.name
                        item_node["mount"] = mount
                        item_node["serial"] = serial
                        item_path=self.fmap.fm.remove_mount_from_path(mount,node.path,True)
                        if node.i_am=="file":
                            item_node["quantity"] = str(1)
                            sum_quants+=1
                        else:
                            # count items in db
                            count_items=self.count_items(node.db,node.map,item_path)
                            sum_quants+=count_items
                            item_node["quantity"] = str(count_items)
                        item_node["itemtype"] = f"{TEXT_ICONS[node.i_am]} {node.i_am}"                        
                        item_node["itempath"] = item_path
                        item_node["from_db"] = self.fmap.fm.extract_filename(node.db)
                        item_node["from_map"] = node.map
                        item_node["id_db_map"] = node.db_id
                        self.tracker.add_child(["Database",map_name],str(jjj),item_node)
            # get common path
            common_path = self.fmap.fm.get_common_path(path_list)
            map_node["itempath"] = common_path
            map_node["quantity"] = str(sum_quants)
        # root=self.tracker.get_root()
        # print(root)
        self._refresh_the_tv()
        

    def _refresh_the_tv(self):
        #Refresh the treeview
        self.sel_tv.refresh_treeview(self.sel_struct,self.sel_tv.modelobj,self.sel_tv_obj)
        self.sel_tv.expand_to_depth(3)
        for column in range(self.sel_tv.modelobj.columnCount()):
            self.sel_tv_obj.resizeColumnToContents(column)

    def count_items(self,database,a_map,path):
        """Counts the amount of files under a path"""
        fm=self.fmap.cma.get_file_map(database)
        
        if fm:
            where=f"filepath LIKE {fm.db.quotes(path+'%')}"
            count=fm.db.get_data_from_table(a_map,"COUNT(*)",where)
            if count:
                return count[0][0]
        return 0
    
    def _get_devices_sets(self,node_list)->list:
        """Returns a set of the (mount,serial) tuples in the selection"""
        ms_list=[]
        for node in node_list:
            if isinstance(node,TreeNode) and node.i_am in ["map","dir","file"]:
                mount_serial_pair=self.fmap.get_mount_serial_of_map(node.db,node.map)
                ms_list.append(mount_serial_pair)
        return list(set(ms_list))




    def set_end_database(self,database):
        self.database=database

        
