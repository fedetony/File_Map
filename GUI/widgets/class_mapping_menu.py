import pandas as pd
from PyQt6 import QtCore, QtGui, QtWidgets 
from PyQt6.QtWidgets import *

from functional.class_treeview_functions import *
from functional.class_struct_conditioner import *
from functional.class_icons import Icons
from functional.class_struct_tracker import TreeStructTracker
from controllers.class_filemap_cli_manager import *
from widgets.class_delegates import DateDelegate, ColoredTextDelegate
from controllers.mapping_worker_thread import *
from widgets.class_qt_map_progress import QtMapProgress
from widgets.mapping_dialog import MappingDialog
from widgets.selection_dialog import SelectionDialog,SelectionDialogSetter
from widgets.repeated_duplicate_result_dialog import RepeatedDuplicateResultDialog
from widgets.search_dialog import SearchDialog,SearchDialogSetter
from widgets.compare_dialog import CompareResultDialog
from widgets.class_file_dialogs import DeleteConfirmDialog
from widgets.map_cloneing_dialog import CloneMapDialog
from models.class_style_provider import *

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

    mapping_running_state = QtCore.pyqtSignal(str,bool)

    def __init__(self, fmap:FileMapCliManager, treeview_obj:QTreeView, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        # Define main structure or use example
        self.fmap = fmap
        self.menu_enabled_map = {}
        self.dialog_register = {}
        self.menu_icon_map = {}
        self.map_tv_obj = treeview_obj
        self.icons=Icons()
        self._set_icons_to_menu_icon_map()
        self.worker_manager = WorkerManager()
        self.all_icons_dict = {}
        self.db_db_key_register = {}
        self._set_icons_dict()
        self._set_style_dict()
        self.map_struct=MAP_STRUCT_EXAMPLE.copy()
        self._syncing_ui = False
        self.info_cache = [] # list of info dicts
        self._build_map_configuration_tree()
        self.map_struct=self.generate_mapping_struct()
        self.search_dialog=None
        
    def _set_icons_to_menu_icon_map(self):
        """Menu icons"""
        self.menu_icon_map = {
            "Create Map": self.icons.icon("mapping"),
            "Rename Map": self.icons.icon("rename"),
            "Clone Map": self.icons.icon("clone"),
            "Delete Map": self.icons.icon("delete map"),
            "Update Map": self.icons.icon("update map"),
            "Continue Mapping": self.icons.icon("continue mapping"),
            "Find Duplicates": self.icons.icon("find duplicates"),
            "Find Repeated": self.icons.icon("find repeated"),
            "Search Map": self.icons.icon("search map"),
            "Search Maps": self.icons.icon("search map"),

            "Tree": self.icons.icon("tree"),
            "Directory": self.icons.icon("dir explore"),
           
            "File Structure": self.icons.icon("file struct"),
            "Data List": self.icons.icon("data list"),
        
            "Shallow Compare": self.icons.icon("shallow compare"),
            "Deep Compare": self.icons.icon("deep compare"),
        
            "Deepen Shallow Map":self.icons.icon("shallow"),
            
            "Delete Selected Maps": self.icons.icon("delete map"),
            "Update Selected Maps": self.icons.icon("update map"),
            "Do a Map Selection": self.icons.icon("selection map"),
            "Do a File Selection": self.icons.icon("db activate"),
        }
    
    def _set_icons_dict(self):
        """Treeview cache icons"""
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
            "Incomplete": [{"field":'maptype'.upper(),"ForegroundRole":QtGui.QColor("#b11717"), 
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
        
        self.style_dict["Shallow"]=[{"field":'mapsize'.upper(), "ForegroundRole":QtGui.QColor("#9a15d8")}]
        self.style_dict["Calculate"]=[{"field":'mapsize'.upper(), "ForegroundRole":QtGui.QColor("#e2c338")}]
            

    @property
    def tracker(self):
        return self.map_ce.tracker

    def _build_map_configuration_tree(self):
        """Initialize and configure the style tree, delegates, condition engine, and context menu.

        Sets up treeview behavior, connects edit signals, evaluates conditions, and refreshes the UI.
        """
        self._sort_field=None
        self._sort_ascending=True
        self._do_evaluation=False
        self.map_tv=TreeviewFunctions(self.map_tv_obj,self.map_struct,FIELDS_POSITION)
        # attach delegate to VALUE column (1)
        delegate = TypedItemDelegate(self.map_tv)
        date_delegate = DateDelegate(self.map_tv,output_format="%d %b %Y %H:%M")
        color_size_delegate = ColoredTextDelegate(self.map_tv_obj) 
        self.map_tv_obj.setItemDelegateForColumn(1, delegate)
        # Header sorting
        header = self.map_tv_obj.header()
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(True)
        header.sectionClicked.connect(self._tree_header_clicked)

        for col, field in enumerate(FIELDS_POSITION):
            if str(field["name"]).startswith("dt_".upper()):
                 self.map_tv_obj.setItemDelegateForColumn(col, date_delegate)
            if str(field["name"])=="mapsize".upper():
                 self.map_tv_obj.setItemDelegateForColumn(col, color_size_delegate)

        self.map_tv.data_change[list,object,str,str].connect(self.on_tree_item_edited)
        self.map_tv.data_change_old_new[list, object ,object, str, str].connect(self.on_tree_item_edited_old_new)
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
        self.map_tv.item_right_clicked.connect(self.on_item_right_clicked)
        
        self.map_tv.do_refresh()

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
        if "value" in track:
            self._update_menu_enabled_states()
            # Rename was triggered
            a_map = old_value #self.tracker.get_value(track)
            db = self.db_db_key_register.get(track[1])
            database = str(db.database_filepath)
            if self._is_menu_action_enabled("Rename Map", database, a_map) in (True,None):
                was_renamed = self.fmap.rename_map(database,old_value,new_value)
                if not was_renamed:
                    self._change_setting_trigger_evaluate_conditions(track, old_value)
                else:
                    QtCore.QTimer.singleShot(0, self._update_regenerate)
            else:
                log.warning("Renaming Not allowed while the database Mapping Dialog is open")

                
            

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
        if datamanage:
            df = datamanage.get_selected_df()
            editable = all(
                self._is_menu_action_enabled("Rename Map", db_filepath, a_map)
                in (True, None)
                for a_map in df["tablename"]
            )
        selectable=True
        hidden=False
        fields_to_tab=None
        sort_by=self._sort_field
        ascending=self._sort_ascending
        # Form map structure
        self.tracker.delete_node(["Databases",db_key])
        self.add_map_to_struct(["Databases", db_key], 
                               datamanage, 
                               editable,selectable,hidden,
                               fields_to_tab,sort_by,ascending)
        
    def generate_mapping_struct(self):
        db_list=self.fmap.get_active_databases_in_dbm()
        self.map_struct=MAP_STRUCT_EXAMPLE.copy() #clear struct
        self.db_db_key_register = {}
        for db_id,db in enumerate(db_list):
            if not isinstance(db,DatabaseInfo):
                continue
            #self.tracker.delete_node(["Databases",f"{map_id}"])
            db_key=f"{db_id} {db.name}"
            self.db_db_key_register[db_key]=db
            # log.debug(f"generate maping -> {db_key}")
            self._add_db_maps_to_struct(db,db_key)
        # print(self.tracker.get_root())
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
        df=datamanage.get_selected_df(None,sort_by,ascending).copy()
        if sort_by in ("dt_map_created", "dt_map_modified"):
            df[sort_by]=pd.to_datetime(df[sort_by],errors="coerce")
        elif sort_by == "mapsize":
            df["_mapsize_sort"]=(df["mapsize"].astype(str)
                .str.extract(r"^\s*([\d.]+)",expand=False).astype(int))
            sort_by="_mapsize_sort"
            df=DataManage.get_df_sorted(df, sort_by, 
                        datamanage.fields + ["_mapsize_sort"], ascending)
        #field_list=['id','dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype'] +['mapsize']
        
        for idx,row in df.iterrows():
            tablename=row['tablename']
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
                    child_node["icon_key"]=str(row[field])
                    # check if is active
                    is_active=False
                    devices=self.fmap.device_monitor.devices
                    for mount,serial in devices:
                        if str(row['mount']) ==mount and str(row['serial'])==serial:
                            is_active=True
                            break
                    if is_active:
                        child_node["style_key"]=str(row[field])+" Active"   
                    else:
                        child_node["style_key"]=str(row[field])
                    
                if field !='tablename':
                    child_node[field]=str(row[field])
            # add the node
            self.tracker.set_value(track+[key],child_node)
    

    def on_item_right_clicked(self,index:QtCore.QModelIndex, info_dict: dict, pos: QtCore.QPoint):
        """Right click menu"""
        self.build_context_menu(index,info_dict,pos)
        return

        track_field = self.map_tv.track_from_index(index) # property track
        aprop=track_field[-1]
        field=str(aprop).upper()
        # info_dict contains all dictionary ...
        node = info_dict["node"]
        track = info_dict["path"] # -> node track
        val=self.tracker.get_value(track+[field.lower()])
        log.debug(f"Right clicked -> row,col =({index.row()},{index.column()}), {field} , {track}, {val}")
        selected_indexes = self.map_tv_obj.selectionModel().selectedIndexes()
        # 
        selected=[]
        for idx in selected_indexes:
            if idx.column() == index.column():
                selected.append(idx)
                log.debug(f"RClick selected -> {idx.row()},{idx.column()},{self.map_tv.track_from_index(idx)}")

        context = {
            "index": index,
            "field": field,
            "property": aprop,
            "value": val,
            "track": track,
            "node": node,
            "selected": selected,
        }

    def build_context_menu(self, index: QtCore.QModelIndex, info_dict: dict, pos: QtCore.QPoint):
        """Build and display the context menu for the selected map(s)."""
        if not index.isValid():
            return
        selection_model = self.map_tv_obj.selectionModel()
        if selection_model is None:
            return
        # ---------------------------------------------------------
        # Selected rows
        # ---------------------------------------------------------
        selected_indexes = selection_model.selectedRows(index.column())
        selected_maps = []
        for idx in selected_indexes:
            stored = idx.data(USER_ROLE)
            if not isinstance(stored, dict):
                continue

            selected_maps.append({
                "index": idx,
                "node": stored.get("node", {}),
                "track": stored.get("path", []),
                "stored": stored,
            })

        # Make sure the right-clicked item is represented.
        if not selected_maps:
            selected_maps.append({
                "index": index,
                "node": info_dict.get("node", {}),
                "track": info_dict.get("path", []),
                "stored": info_dict,
            })

        # ---------------------------------------------------------
        # Context
        # ---------------------------------------------------------
        context = {
            "index": index,
            "node": info_dict.get("node", {}),
            "track": info_dict.get("path", []),
            "stored": info_dict,
            "field": str(
                self.map_tv.track_from_index(index)[-1]
            ).upper(),
            "selected_maps": selected_maps,
        }

        # ---------------------------------------------------------
        # Build menu
        # ---------------------------------------------------------
        if len(info_dict.get("path", []))<3:
            return
        menu = None
        count = len(selected_maps)
        if count == 1:
            menu = self.build_single_map_menu(
                selected_maps[0],
                context
            )
        elif count == 2:
            menu = self.build_two_map_menu(
                selected_maps,
                context
            )
        elif count > 2:
            menu = self.build_multi_map_menu(
                selected_maps,
                context
            )

        # ---------------------------------------------------------
        # Show menu
        # ---------------------------------------------------------
        if menu is not None and menu.actions():
            menu.exec(self.map_tv_obj.viewport().mapToGlobal(pos))

    def build_single_map_menu(self, selected_map, context):
        menu = QtWidgets.QMenu(f'Map "{selected_map["track"][-1]}"')
        self._update_menu_enabled_states()

        for name, callback in [
            ("Create Map", self._menu_create_map),
            ("Rename Map", self._menu_rename_map),
            ("Clone Map", self._menu_clone_map),
            ("Delete Map", self._menu_delete_map),
            ("Update Map", self._menu_update_map),
            ("Continue Mapping", self._menu_continue_mapping),
        ]:
            self._add_action_to_menu(menu, name, callback, context)

        menu.addSeparator()

        for name, callback in [
            ("Find Duplicates", self._menu_find_duplicates),
            ("Find Repeated", self._menu_find_repeated),
            ("Search Map", self._menu_search_map),
        ]:
            self._add_action_to_menu(menu, name, callback, context)

        menu.addSeparator()

        browse = menu.addMenu("Browse")

        for name, callback in [
            ("Tree", self._menu_browse_tree),
            ("Directory", self._menu_browse_directory),
        ]:
            self._add_action_to_menu(browse, name, callback, context)

        export = browse.addMenu("Export")

        for name, callback in [
            ("Tree", self._menu_export_tree),
            ("Directory", self._menu_export_directory),
            ("File Structure", self._menu_export_file_structure),
            ("Data List", self._menu_export_data_list),
        ]:
            self._add_action_to_menu(export, name, callback, context)

        menu.addSeparator()
        self._add_action_to_menu(menu, "Do a File Selection", self._menu_do_file_selection, context)
        self._add_action_to_menu(menu, "Do a Map Selection", self._menu_do_map_selection, context)

        menu.addSeparator()
        self._add_action_to_menu(menu, "Deepen Shallow Map", self._menu_deepen_shallow_map, context)

        return menu
    
    def build_two_map_menu(self, selected_maps, context):
        menu = QtWidgets.QMenu("2 Maps Selected")
        self._update_menu_enabled_states()
        for name, callback in [
            ("Search Maps", self._menu_search_map),
            ("Shallow Compare", self._menu_compare_shallow),
            ("Deep Compare", self._menu_compare_deep),
        ]:
            self._add_action_to_menu(menu, name, callback, context)

        menu.addSeparator()
        
        self._add_action_to_menu(
            menu, "Deepen Shallow Map",
            self._menu_deepen_shallow_map, context
        )

        return menu

    def build_multi_map_menu(self, selected_maps, context):
        menu = QtWidgets.QMenu(f"{len(selected_maps)} Maps Selected")
        self._update_menu_enabled_states()
        for name, callback in [
            ("Search Maps", self._menu_search_map),
            ("Delete Selected Maps", self._menu_delete_maps),
            ("Update Selected Maps", self._menu_update_maps),
        ]:
            self._add_action_to_menu(menu, name, callback, context)

        return menu

    def _add_action_to_menu(self, menu, name, callback, context=None):
        """Create and configure a menu action."""
        action = menu.addAction(name)

        if icon := self.menu_icon_map.get(name):
            action.setIcon(icon)

        is_enabled = self.menu_enabled_map.get(name, True)

        if context and isinstance(is_enabled, dict):
            is_enabled = all(
                is_enabled.get(pair, True)
                for pair in self._get_dbmap_pairs_from_context(context)
            )

        action.setEnabled(is_enabled)
        action.triggered.connect(
            lambda: callback(context) if context else callback()
        )

        return action
    
    # ---------------------------------------------------------
    # Menu Actions
    # ---------------------------------------------------------

    def _menu_rename_map(self, context):
        database = self._get_db_from_context(context)
        a_map = self._get_map_from_context(context)

        if not self._is_menu_action_enabled("Rename Map", database, a_map) in (True, None):
            log.warning(
                "Renaming not allowed while the database "
                "Mapping Dialog is open"
            )
            return

        new_name, ok = QtWidgets.QInputDialog.getText(
            self.parent_widget,
            "Rename Map",
            f'Rename "{a_map}" to:',
            QtWidgets.QLineEdit.EchoMode.Normal,
            a_map,
        )

        if not ok:
            return

        new_name = new_name.strip()

        if not new_name or new_name == a_map:
            return
        was_renamed = self.fmap.rename_map(database, a_map, new_name)

        if not was_renamed:
            QtWidgets.QMessageBox.warning(
                self.parent_widget,
                "Rename Map",
                f'Could not rename "{a_map}" to "{new_name}".',
            )
            return
        QtCore.QTimer.singleShot(0, self._update_regenerate)


    def _menu_clone_map(self, context):
        db_from = self._get_db_from_context(context)
        map_from = self._get_map_from_context(context)

        db_list = self.fmap.get_active_databases_in_dbm()

        databases = [
            (
                str(db.database_filepath),
                str(db.name),
                str(db.db_file),
            ) for db in db_list]

        dialog = CloneMapDialog(self.fmap, databases, db_from, map_from, self.parent_widget)

        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        db_to, map_to = dialog.get_values()

        if db_to == db_from and map_to == map_from:
            return

        if not self.fmap.copy_table_from_to_database( db_from, map_from, db_to, map_to):
            QtWidgets.QMessageBox.warning(
                self.parent_widget,
                "Clone Map",
                f'Could not clone "{map_from}".',
            )
            return
        QtCore.QTimer.singleShot(0, self._update_regenerate)

    def _menu_delete_map(self, context):
        database = self._get_db_from_context(context)
        a_map = self._get_map_from_context(context)
        size_tup=self.fmap.get_map_size(database,a_map)
        count=size_tup[0]
        msg=f"Sure to DELETE Map {a_map} with {count} elements?"
        if self.fmap.user_dialogs.ask_confirmation(msg,False):
            self.fmap.delete_map_from_db(database,a_map,log_print=True)
            self._update_regenerate()

    def _menu_update_map(self, context):
        pass

    def _menu_continue_mapping(self, context):
        pass

    def _moded_mapping_dialog(self,context,mode):
        """Used for different modes for a selected map and database.
           modes are deepening, repeated, duplicates, update, continue. 
           Blocks the database for other processes and runs in temporal database
        """
        database = self._get_db_from_context(context)
        a_map = self._get_map_from_context(context)
        reg_db = self.dialog_register.get(database)
        if reg_db:
            dialog = reg_db["dialog"]
            if dialog.isVisible():
                dialog.raise_()
                dialog.activateWindow()
            else:
                dialog.show()
                dialog.raise_()
                dialog.activateWindow()
            return
        
        mappath = self.fmap.get_full_mount_path_of_map(database,a_map)
        if not mappath:
            return
        modding_info={"mode":mode,
                      "database":database,
                      "path_to_map":mappath,
                      "map_name":a_map}
        
        dialog = MappingDialog(
            self.fmap,
            self.worker_manager,
            modding_info,
            parent=self.parent_widget,
        )
        self._register_connect_show(context,dialog)

    def _menu_find_duplicates(self, context):
        self._moded_mapping_dialog(context,"duplicates")
        
    def _menu_find_repeated(self, context):
        self._moded_mapping_dialog(context,"repeated")

    def _menu_search_map(self, context):
        db_map_pairs = self._get_dbmap_pairs_from_context(context)
        self._start_search_dialog(db_map_pairs,
                                  
                                  parent=self.parent_widget)

    def _start_search_dialog(self,
                             db_map_pair_list:list,
                             modding_info:dict=None,
                             parent=None,
                             ):
        if not db_map_pair_list or len(db_map_pair_list)==0:
            log.error("You need to make a map selection to search!")
            return
        if not isinstance(modding_info,dict):
            modding_info={}
        search_setter=SearchDialogSetter(fmap=self.fmap, 
                            db_map_pair_list=db_map_pair_list,
                            worker_manager=self.worker_manager,
                            modding_info=modding_info,
                            parent=parent,
                            )   
        self.search_dialog=search_setter.get_dialog() 
        if not isinstance(self.search_dialog,SearchDialog):
            return    
        self.search_dialog.refresh_mapping_tree.connect(lambda: self.generate_mapping_struct)
        # Mapping State
        self.search_dialog.mapping_is_running_signal.connect(
            lambda: self._set_mapping_state(is_mapping= True))
        self.search_dialog.mapping_is_not_running_signal.connect(
            lambda: self._set_mapping_state(is_mapping= False))
        # self.search_dialog.dialog_exit.connect(self._mapping_dialog_closed)
        #self.search_dialog.exec() # blocks user until closing window
        self.search_dialog.show() # allows user to change windows, keep self refrence to not garbage collect :)
       

    def _menu_browse_tree(self, context):
        pass

    def _menu_browse_directory(self, context):
        pass

    def _menu_export_tree(self, context):
        pass

    def _menu_export_directory(self, context):
        pass

    def _menu_export_file_structure(self, context):
        pass

    def _menu_export_data_list(self, context):
        pass

    def _menu_do_a_selection(self, context, mode, styles_dict=None)->SelectionDialog:
        database = self._get_db_from_context(context)
        reg_db = self.dialog_register.get(database)
        if reg_db:
            dialog = reg_db["dialog"]
            if dialog.isVisible():
                dialog.raise_()
                dialog.activateWindow()
            else:
                dialog.show()
                dialog.raise_()
                dialog.activateWindow()
            return
        modding_info={"mode": mode,
                      "database":database,
                      "path_to_map":"",
                      "map_name":"",
                     }
        _styles_dict={}
        if not isinstance(styles_dict,dict):
            _styles_dict["explorer_style"]=DefaultExplorerStyle() # text, tooltips, icons
            _styles_dict["tree_style"]=DefaultTreeStyle() # role formatting by node, treemanager
        else:
            _styles_dict=styles_dict

        dialog_gs = SelectionDialogSetter(
            fmap = self.fmap,
            worker_manager = self.worker_manager,
            modding_info = modding_info,
            lazy_defaults = {},
            styles_dict = _styles_dict,
            parent=self.parent_widget,
        )
        dialog=dialog_gs.get_dialog()
        if not isinstance(dialog,SelectionDialog):
            return
        db = self._get_databaseinfo_from_context(context)
        dialog.refresh_mapping_tree.connect(lambda: self.generate_mapping_struct)
        self.dialog_register[database] = {
            "dbinfo": db,
            "dialog": dialog,
            "mapping": False,
        }
        # update tree after register to block renaming
        self._update_regenerate()
        # Mapping State
        dialog.mapping_is_running_signal.connect(
            lambda: self._set_mapping_state(database, True))
        dialog.mapping_is_not_running_signal.connect(
            lambda: self._set_mapping_state(database, False))

        dialog.dialog_exit.connect(self._mapping_dialog_closed)
        # dialog.exec() # blocks user until closing window
        dialog.show() # allows user to change windows
        return dialog

    def _menu_do_file_selection(self, context):
        self._menu_do_a_selection(context,"FESelection")

    def _menu_do_map_selection(self, context):
        _styles_dict={}
        _styles_dict["explorer_style"]=DBSelectionExplorerStyle() # text, tooltips, icons
        _styles_dict["tree_style"]=DBSelectionTreeStyle() # role formatting by node, treemanager
        self._menu_do_a_selection(context,"DBSelection",_styles_dict)

    def _menu_deepen_shallow_map(self, context):
        self._moded_mapping_dialog(context,"deepening")

    def _menu_compare_shallow(self, context):
        pass

    def _menu_compare_deep(self, context):
        pass

    def _menu_delete_maps(self, context):
        dbmap_pair_list = self._get_dbmap_pairs_from_context(context)
        map_list = self._get_maps_from_context(context)

        dialog = DeleteConfirmDialog(
            f"{map_list}",
            self.parent_widget,
            "Delete many files",
        )

        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        for database, a_map in dbmap_pair_list:
            self.fmap.delete_map_from_db(
                database,
                a_map,
                log_print=True,
            )

        self._update_regenerate()

    def _menu_update_maps(self, context):
        pass

    def _menu_create_map(self, context):
        database = self._get_db_from_context(context)
        reg_db = self.dialog_register.get(database)
        if reg_db:
            dialog = reg_db["dialog"]
            if dialog.isVisible():
                dialog.raise_()
                dialog.activateWindow()
            else:
                dialog.show()
                dialog.raise_()
                dialog.activateWindow()
            return
        modding_info={"mode":"create",
                      "database":database}
        
        dialog = MappingDialog(
            self.fmap,
            self.worker_manager,
            modding_info,
            parent=self.parent_widget,
        )
        self._register_connect_show(context,dialog)

    def _register_connect_show(self,context,dialog:MappingDialog):
        database = self._get_db_from_context(context)
        db = self._get_databaseinfo_from_context(context)
        dialog.refresh_mapping_tree.connect(lambda: self.generate_mapping_struct)
        self.dialog_register[database] = {
            "dbinfo": db,
            "dialog": dialog,
            "mapping": False,
        }
        # update tree after register to block renaming
        self._update_regenerate()
        # Mapping State
        dialog.mapping_is_running_signal.connect(
            lambda: self._set_mapping_state(database, True))
        dialog.mapping_is_not_running_signal.connect(
            lambda: self._set_mapping_state(database, False))

        dialog.dialog_exit.connect(self._mapping_dialog_closed)
        # dialog.exec() # blocks user until closing window
        dialog.show() # allows user to change windows
    
    def _mapping_dialog_closed(self, database:str):
        reg = self.dialog_register.get(database)
        self.dialog_register.pop(database, None)
        self._update_regenerate()
        
    def _set_mapping_state(self, database:str, is_mapping:bool):
        reg = self.dialog_register.get(database)
        if reg:
            was_mapping = reg["mapping"]
            reg["mapping"] = is_mapping
            # refresh after each mapping is finished
            if was_mapping and not is_mapping:
                self._update_regenerate()
        self.mapping_running_state.emit(database,is_mapping)
    
    # ---------------------------------------------------------
    # Context helpers
    # ---------------------------------------------------------
    
    def _get_db_from_context(self,context)->str:
        track=context["track"]
        if not track or len(track)<2:
            return ""
        db_key=track[1]
        db=self.db_db_key_register.get(db_key)
        if not isinstance(db,DatabaseInfo):
            return ""
        return str(db.database_filepath)
    
    def _get_databaseinfo_from_context(self,context)->DatabaseInfo:
        track=context["track"]
        if not track or len(track)<2:
            return None
        db_key=track[1]
        db=self.db_db_key_register.get(db_key)
        if not isinstance(db,DatabaseInfo):
            return None
        return db
    
    def _get_dbs_from_context(self,context)->list[str]:
        dbs_list=[]
        for cnot in context["selected_maps"]:
            track=cnot["track"]
            if not track or len(track)<2:
                return []
            db_key=track[1]
            db=self.db_db_key_register.get(db_key)
            if not isinstance(db,DatabaseInfo):
                continue
            a_db=str(db.database_filepath)
            if a_db not in dbs_list:
                dbs_list.append(a_db)
        return dbs_list
    
    def _get_databaseinfos_from_context(self,context)->list[str]:
        dbs_list=[]
        for cnot in context["selected_maps"]:
            track=cnot["track"]
            if not track or len(track)<2:
                return []
            db_key=track[1]
            db=self.db_db_key_register.get(db_key)
            if not isinstance(db,DatabaseInfo):
                continue
            if db not in dbs_list:
                dbs_list.append(db)
        return dbs_list
    
    def _get_dbmap_pairs_from_context(self,context)->list[tuple[str, str]]:
        dbmappair_list=[]
        for cnot in context["selected_maps"]:
            track=cnot["track"]
            a_map=self.tracker.get_value(track+["value"])
            if not track or len(track)<2:
                return []
            db_key=track[1]
            db=self.db_db_key_register.get(db_key)
            if not isinstance(db,DatabaseInfo):
                continue
            a_db=str(db.database_filepath)
            dbmappair_list.append((a_db,a_map))
        return dbmappair_list
    
    def _get_map_from_context(self,context)->str:
        a_map=self.tracker.get_value(context["track"]+["value"])
        return a_map
    
    def _get_maps_from_context(self,context)->list[str]:
        map_list=[]
        for cnot in context["selected_maps"]:
            a_map=self.tracker.get_value(cnot["track"]+["value"])
            map_list.append(a_map)
        return map_list
    
    # ---------------------------------------------------------
    # General helpers
    # ---------------------------------------------------------

    def _update_regenerate(self):
        self.fmap.set_active_databases_in_dbm()
        self._update_menu_enabled_states()
        self.generate_mapping_struct()
    
    def _is_menu_action_enabled(self, name, database, a_map):
        enabled = self.menu_enabled_map.get(name, True)

        if isinstance(enabled, dict):
            return enabled.get((database, a_map), True)

        return enabled
    
    def _update_menu_enabled_states(self):
        dbinfo_list=self.fmap.get_active_databases_in_dbm()
        for db in dbinfo_list:
            database=str(db.database_filepath)
            # Renaming allowed
            if database in self.dialog_register.keys():
                map_list = self.fmap.get_maps_in_db(database)
                for a_map in map_list:
                    self.menu_enabled_map["Rename Map"]= { (database, a_map): False }
            else:
                # Renaming allowed
                map_list = self.fmap.get_maps_in_db(database)
                for a_map in map_list:
                    self.menu_enabled_map["Rename Map"]= { (database, a_map): True }

    
        
    
        