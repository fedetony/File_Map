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
# from widgets.class_target_widget import MapTargetItem
from widgets.class_simple_target_widget import MapTargetItem

from models.class_style_provider import *

from functional.class_LogHandler import LM
log=LM.get_logger_with_handler("SelectionMenuTree","debug",True,None)

#On registry

#field_list=['id','dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype']
FIELDS_POSITION=[
    {"name": "ITEM",  "editable": False, "selectable": True,  "hidden": False},
    {"name": "VALUE", "editable": True,  "selectable": True,  "hidden": False}, # tablename
    {"name": 'itemtype'.upper(), "editable": False,  "selectable": True,  "hidden": False},
    {"name": 'size'.upper(),  "editable": True, "selectable": True, "hidden": False},
    {"name": 'quantity'.upper(),  "editable": True, "selectable": True, "hidden": False},
    {"name": 'itempath'.upper(),  "editable": True, "selectable": True, "hidden": False},  
    {"name": 'mount'.upper(),  "editable": False, "selectable": True, "hidden": False},
    {"name": 'serial'.upper(),  "editable": False, "selectable": True, "hidden": False},
    {"name": 'from_db'.upper(),  "editable": False, "selectable": True, "hidden": False},  
    {"name": 'from_map'.upper(), "editable": False,  "selectable": True,  "hidden": False}, 
    
    {"name": "INDEX",  "editable": False, "selectable": False, "hidden": True}, # for sorting
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
                           "size":"",
                           "quantity":"0",
                           "meta": {"hidden":False,"editable": True}},
                           "children":[],
                }
ITEM_NODE_TEMPLATE={"PathorFile": {"value": "Selection", "type": "str", "subtype": "str", 
                           "mount":"",
                           "serial":"",
                           "itempath":"",
                           "itemtype":"",
                           "from_db":"",
                           "from_map":"",
                           "size":"",
                           "quantity":"0",
                           "meta": {"hidden":False,"editable": True}}}
SELECT_STRUCT_EXAMPLE={
        "Database": { 
            "value":"", "type": "str",
            "meta": {"hidden":False, "editable":True},
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
    target_items_changed = QtCore.pyqtSignal(object)

    def __init__(self, fmap:FileMapCliManager, treeview_obj:QTreeView, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        # Define main structure or use example
        self.fmap = fmap
        self.sel_tv_obj = treeview_obj
        self.icons=Icons()
        self.all_icons_dict = {}
        self.database = ""
        self.sel_struct=SELECT_STRUCT_EXAMPLE.copy()
        self._syncing_ui = False
        self.target_list=[]
        self._build_selection_configuration_tree()
        self.generate_selection_struct()
    
    @property
    def tracker(self):
        return self.sel_ce.tracker
    
    def _set_icons_dict(self):
        """Treeview cache icons"""
        self.all_icons_dict={
            "Device Map": self.icons.icon("device map"),
            "Selection Map": self.icons.icon("selection map"),
            "Database Icon": self.icons.icon("db activate"),
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
            "Device Map Style":[{"field":'item'.upper(), "ForegroundRole":QtGui.QColor("#3498db")},
                          {"field":'item'.upper(), "DecorationRole":self.icons.icon("device map")},
                          {"field":'value'.upper(), "ForegroundRole":QtGui.QColor("#3498db")}],
            
            "Selection Map Style": [{"field":'item'.upper(),"ForegroundRole":QtGui.QColor("#d061fc"), 
                               "DecorationRole":self.icons.icon("selection map")},
                               {"field":'value'.upper(),"ForegroundRole":QtGui.QColor("#d061fc")}], 

            "Database Style": [{"field":'item'.upper(),"ForegroundRole":QtGui.QColor("#ee9624"), 
                               "DecorationRole":self.icons.icon("db activate")},
                          {"field":'value'.upper(), "ForegroundRole":QtGui.QColor("#ee9624")}], 
            
        }

    def _build_selection_configuration_tree(self):
        """Initialize and configure the style tree, delegates, condition engine, and context menu.

        Sets up treeview behavior, connects edit signals, evaluates conditions, and refreshes the UI.
        """
        self.last_node_list=None
        self._sort_field=None
        self._sort_ascending=True
        self._do_evaluation=False
        self.sel_tv=TreeviewFunctions(self.sel_tv_obj,self.sel_struct,FIELDS_POSITION)
        # attach delegate to VALUE column (1)
        delegate = TypedItemDelegate(self.sel_tv)
        #date_delegate = DateDelegate(self.sel_tv,output_format="%d %b %Y %H:%M")
        #color_size_delegate = ColoredTextDelegate(self.sel_tv_obj) 
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
        value_col=field_col("value")
        self.sel_tv_obj.setItemDelegateForColumn(value_col, delegate)
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
        self._set_icons_dict()
        self._set_style_dict()
        self.sel_tv.set_icons_cache(self.all_icons_dict)
        self.sel_tv.set_style_cache(self.style_dict)
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

        sort_index=False
        if field == "ITEM":
            pro_field = None   # order by id
            sort_index=True
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

        self._update_regenerate(do_refresh=False)
        if not field == "ITEM":
            self.sel_tv.modelobj.sort(
                column,
                QtCore.Qt.SortOrder.AscendingOrder
                if self._sort_ascending
                else QtCore.Qt.SortOrder.DescendingOrder
            )
        else:
            index_col = next(
                i for i, field in enumerate(FIELDS_POSITION)
                if field["name"] == "INDEX")
            self.sel_tv.modelobj.sort(
                index_col,
                QtCore.Qt.SortOrder.AscendingOrder
                if self._sort_ascending
                else QtCore.Qt.SortOrder.DescendingOrder
            )

    
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

        # print("on_tree_item_edited triggered ->",track, value, typestr, subtype)
    
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
    
    def _update_regenerate(self,do_refresh=True):
        self.generate_selection_struct(do_refresh_tv=do_refresh)
    
    def on_item_right_clicked(self,index:QtCore.QModelIndex, info_dict: dict, pos: QtCore.QPoint):
        """Right click menu"""
        #self.build_context_menu(index,info_dict,pos)
        return
    
    def generate_selection_struct(self, node_list:list=None,do_refresh_tv=True):
        # delete all children
        if node_list is not None:
            do_indexing=True
            self.last_node_list=node_list
        else:
            do_indexing=False
            node_list=self.last_node_list
        v_dict=self.tracker.validate_node(["Database"])
        for child in v_dict.get("children_keys"):
            #vc_dict=self.tracker.validate_node(["Database",child])
            self.tracker.delete_node(["Database",child])

        self.sel_struct=SELECT_STRUCT_EXAMPLE.copy() #clear struct

        if not node_list:
            self._evaluate_target_items()
            self._refresh_the_tv()
            return 
        
        devices_set=self._get_devices_sets(node_list)
        if not devices_set:
            self._evaluate_target_items() #node_list)
            self._refresh_the_tv()
            return 
        
        node_list = self._recycle_node_list(node_list)
        node_list = self._set_mount_serial_to_node_list(node_list)
        node_list = self._set_quantities_to_node_list(node_list)
        node_list=self._sort_the_node_list(node_list)
        index=0
        common_path_lists={}
        for iii,(mount,serial) in enumerate(devices_set):
            # Set common dictionary with lists for each device
            common_path_lists[(mount,serial)]=[]
            db_name = self.fmap.fm.extract_filename(self.database)
            db_path = self.fmap.fm.extract_path(self.database)
            self.tracker.set_value(["Database","value"],db_name)
            self.tracker.set_value(["Database","itempath"],db_path)
            self.tracker.set_value(["Database","itemtype"],f"{TEXT_ICONS['database']} database")
            self.tracker.set_or_create_property(["Database","style_key"], "Database Style" )
            map_node=MAP_NODE_TEMPLATE["Map"].copy()
            map_name=f"{iii} Selection:" 
            # map_node["value"] = f"{self.fmap.timestamp}_Selection_{iii}"
            map_node["value"] = f"Selection_Map_{iii}"
            map_node["mount"] = mount
            map_node["serial"] = serial
            map_node["itemtype"] = f"{TEXT_ICONS['map']} map"
            map_node["from_db"] = ""
            map_node["from_map"] = ""
            map_node["size"] = ""
            map_node, index = self._index_node(map_node,index,do_indexing)
            map_node["style_key"]="Selection Map Style"
            common_path=""
            sum_quants=0
            sum_size = 0
            self.tracker.add_child(["Database"],map_name,map_node)
            for jjj,node in enumerate(node_list):
                if isinstance(node,TreeNode):
                    mount_serial_pair=(node.mount,node.serial)
                    
                    if mount == mount_serial_pair[0] and serial == mount_serial_pair[1]:
                        item_node=ITEM_NODE_TEMPLATE["PathorFile"].copy()
                        common_path_lists[(mount,serial)].append(node.path)
                        item_node["value"] = node.name
                        item_node["mount"] = mount
                        item_node["serial"] = serial
                        # Quantity
                        sum_quants+=node.quantity
                        item_node["quantity"] = str(node.quantity)
                        # Size
                        node_size_txt=""
                        if isinstance(node.size,(int|float)):
                            sum_size+=node.size
                            node_size_txt=FM.get_size_str_formatted(node.size,10,True)
                            node_size_txt=node_size_txt.replace(".00 By"," Bytes").strip()
                        item_node["size"] = node_size_txt
                        item_node["itemtype"] = f"{TEXT_ICONS[node.i_am]} {node.i_am}"                        
                        item_node["itempath"] = node.itempath
                        # print(f"Set itempath for {node.name} -> {node.itempath}")
                        from_db=self.fmap.fm.extract_filename(node.db) if node.db else ""
                        from_map=node.map if node.db else ""
                        item_node["from_db"] = from_db
                        item_node["from_map"] = from_map
                        item_node["id_db_map"] = node.db_id
                        item_node, index = self._index_node(item_node,index,do_indexing)
                        self.tracker.add_child(["Database",map_name],str(jjj),item_node)

            # get common path
            common_path = self.fmap.fm.get_common_path(common_path_lists[(mount,serial)])
            map_node["itempath"] = common_path
            size_txt=""
            if sum_size:
                size_txt=FM.get_size_str_formatted(sum_size,10,True)
                size_txt=size_txt.replace(".00 By"," Bytes").strip()
            map_node["size"] = size_txt
            map_node["quantity"] = str(sum_quants)

            # Check if Device map and set style
            val_obj = self.tracker.get_validate_node_as_obj(["Database",map_name])
            if val_obj.children_count == 1:
                map_key=val_obj.children_keys[0]
                i_typ=self.tracker.get_value(["Database",map_name,map_key,"itemtype"])
                if "dir" in i_typ:
                    map_node["value"] = f"Device_Map_{iii}"
                    map_node["style_key"]="Device Map Style"
            
        # root=self.tracker.get_root()
        # print(root)
        # Evaluate targets after generating new tree  
        self._evaluate_target_items()
        if do_refresh_tv:
            self._refresh_the_tv()    
    
    def _index_node(self,dict_node:dict,index,do_index:bool):
        if do_index:
            dict_node["index"]=f"{index:010d}"
        return dict_node, index+1


    def _recycle_node_list(self,node_list:list[TreeNode])->list[TreeNode]:
        if not self.last_node_list:
            return node_list
        ln_dict={}
        for lnode in self.last_node_list:
            ln_dict[lnode.id]=lnode
        def a_sett(nodeto:TreeNode,nodefrom:TreeNode,attr:str):
            if hasattr(nodefrom,attr):
                val=getattr(nodefrom,attr)
                setattr(nodeto,attr,val)
        for node in node_list:
            if node.id in ln_dict.keys():
                nnn=ln_dict[node.id]
                a_sett(node,nnn,"mount")
                a_sett(node,nnn,"serial")
                a_sett(node,nnn,"quantity")
                a_sett(node,nnn,"itempath")
        return node_list
    
    def _set_mount_serial_to_node_list(self,node_list:list[TreeNode])->list[TreeNode]:
        for node in node_list:
            if not hasattr(node,"mount") or not hasattr(node,"serial"):                
                mount_serial_pair=self.fmap.get_mount_serial_of_map(node.db,node.map)
                if not mount_serial_pair:
                    continue
                setattr(node,"mount",mount_serial_pair[0])
                setattr(node,"serial",mount_serial_pair[1])
        return node_list
    
    def _set_quantities_to_node_list(self,node_list:list[TreeNode])->list[TreeNode]:
        for node in node_list:
            if not hasattr(node,"mount"):
                    continue
            if not hasattr(node,"quantity") or not hasattr(node,"itempath"):
                item_path=self.fmap.fm.remove_mount_from_path(node.mount,node.path,True)
                setattr(node,"itempath",item_path)
                if node.i_am=="file":
                    setattr(node,"quantity",1)
                elif node.i_am=="dir":
                    # count items in db
                    count_items=self.count_items(node.db,node.map,item_path)
                    setattr(node,"quantity",count_items)
                else:
                    setattr(node,"quantity",0)
        return node_list

    def _sort_the_node_list(self, node_list: list[TreeNode]) -> list[TreeNode]:
        if not node_list or self._sort_field is None:
            return node_list

        field_map = {
            "item": None,
            "tablename": "name",
            "itemtype": "i_am",
            "size": "size",
            "quantity": "quantity",
            "itempath": "itempath",
            "mount": "mount",
            "serial": "serial",
            "from_db": "db",
            "from_map": "map",
        }

        attr = field_map.get(self._sort_field)

        # Unknown field: preserve original order.
        if attr is None:
            return node_list

        numeric_fields = {"size", "quantity"}

        def sort_key(node):
            value = getattr(node, attr, None)
            if value is None:
                return (0, 0) if self._sort_field in numeric_fields else (0, "")
            if self._sort_field in numeric_fields:
                try:
                    return (1, float(value))
                except (TypeError, ValueError):
                    return (0, 0)
            return (1, str(value).casefold())

        return sorted(
            node_list,
            key=sort_key,
            reverse=not self._sort_ascending,
        )

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
                if node.db and node.map: # from db mapping
                    mount_serial_pair=self.fmap.get_mount_serial_of_map(node.db,node.map)
                    ms_list.append(mount_serial_pair)
                else:
                    if hasattr(node,"mount") and hasattr(node,"serial"): # from fe mapping
                        mount_serial_pair=(node.mount,node.serial)
                        ms_list.append(mount_serial_pair)
                
        return list(set(ms_list))

    def set_end_database(self,database):
        self.database=database
    
    def _evaluate_target_items(self): 
        # Get the data from the tracker
        self.target_list=[]
        db_val_obj=self.tracker.get_validate_node_as_obj(["Database"])
        for map_name in db_val_obj.children_keys:
                
            mount=self.tracker.get_value(["Database",map_name,"mount"])
            serial=self.tracker.get_value(["Database",map_name,"serial"])
            name=self.tracker.get_value(["Database",map_name,"value"])
            # add tagets
            target_item=MapTargetItem(name=name,
                                      source_mount=mount,
                                      source_serial=serial,
                                      )
            self.target_list.append(target_item)
        
        self.target_items_changed.emit(self.target_list)

        
