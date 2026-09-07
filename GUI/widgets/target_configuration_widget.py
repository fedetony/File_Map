from dataclasses import dataclass
from typing import Optional
from controllers.class_filemap_cli_manager import FileMapCliManager
from functional.class_icons import Icons
from models.class_style_provider import TEXT_ICONS
from PyQt6 import QtCore, QtWidgets


from functional.class_treeview_functions import *
from functional.class_struct_conditioner import *
from functional.class_struct_tracker import TreeStructTracker
from functional.class_icons import Icons


FIELDS_POSITION=[
    {"name": "ITEM",  "editable": False, "selectable": True,  "hidden": False},
    {"name": "VALUE", "editable": True,  "selectable": True,  "hidden": True},
    {"name": "TYPE",  "editable": False, "selectable": False, "hidden": True},
    {"name": "UNIT",  "editable": False, "selectable": True, "hidden": True},
    {"name": "INFO",  "editable": True, "selectable": True, "hidden": True},
]


conditions={"is_valid": "me_set('icon_key','valid') if node_get('Targets[0[is_valid[value]]]') else me_set('icon_key','not_valid')",
            }

TARGET_CHILD={"0": {"value":"Target 1", "type": "str",
                    "children":[
                    {"Database": {"value": "Database A", "type": "list", "subtype": "str", 
                        "meta": {"options": ["Database A", "Database B", "Database C"]}}},
                    {"Prefix": {"value": "", "type": "str", 
                        "meta": {"editable":True, "selectable":True}}},
                    {"Base Name": {"value": "", "type": "str", 
                        "meta": {"editable":True, "selectable":True}}},
                    {"Sufix": {"value": "", "type": "str", 
                        "meta": {"editable":True, "selectable":True}}},
                    {"is_valid": {"value": True, "type": "bool", 
                        "meta": {"editable":True, "selectable":True, "hidden":True}}},
                    {"Name": {"value": "", "type": "str", "icon_key":"valid",
                        "meta": {"conditions": conditions['is_valid'], "editable":False, "selectable":True}}},
                    ]},
                },
TARGET_STRUCT_EXAMPLE={
        "Targets": {"children":[                  
                TARGET_CHILD,
            ]},            
        }

# ============================================================
# Configuration
# ============================================================

@dataclass
class MapTargetConfig:
    """
    Pure data container.

    No validation.
    No formatting.
    No database logic.
    """
    database: str = ""
    name_base: str = ""
    prefix: str = ""
    postfix: str = ""


# ============================================================
# Configuration Widget
# ============================================================

class MapTargetConfigWidget(QtWidgets.QWidget):

    # Emits the complete configuration when accepted/applied.
    targetsChanged = QtCore.pyqtSignal(list)

    def __init__(self, fmap:FileMapCliManager, target_struct=None, parent=None):
        super().__init__(parent)

        self.fmap = fmap
        self.parent_widget = parent
        self._syncing_ui = False
        if target_struct:
            self.tar_struct = target_struct
        else:
            self.tar_struct = TARGET_STRUCT_EXAMPLE
        self.icons=Icons()
        self.all_icons_dict={
            "home":self.icons.icon("home"),
            }
        
        self._targets: list[MapTargetConfig] = []
        self._build_ui()
        self._do_connections()
        self._populate_databases()
        self._build_tar_configuration_tree()

    def _build_tar_configuration_tree(self):
        """Initialize and configure the style tree, delegates, condition engine, and context menu.

        Sets up treeview behavior, connects edit signals, evaluates conditions, and refreshes the UI.
        """
        self._do_evaluation=False
        self.tar_tv=TreeviewFunctions(self.tar_tv_obj,self.tar_struct,FIELDS_POSITION)
        # attach delegate to VALUE column (1)
        delegate = TypedItemDelegate(self.tar_tv)
        self.tar_tv_obj.setItemDelegateForColumn(1, delegate)
        self.tar_tv.data_change[list,object,str,str].connect(self.on_tree_item_edited)
        self.tar_tv.struct_data_change[list,object,str,str].connect(self.on_struct_item_edited)
        #self.tar_tv.expand_to_depth(1) #333) #Expand all
        # Condition Engine
        self.tar_ce=ConditionEngine(self.tar_tv.tracker)
        self._evaluate_conditions()
        self.tar_tv.item_clicked.connect(self.item_clicked)
        
        # Add cache tooltip, icons, backgrounds, styles
        self.tar_tv.set_icons_cache(self.all_icons_dict)
        # self.tar_tv.set_tar_cache(tar_dict)

        # Right click Menu 
        self.tar_tv.treeviewobj.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.tar_tv.treeviewobj.customContextMenuRequested.connect(self.tar_tv._on_context_menu)
        #self.tar_tv.item_right_clicked.connect(self.on_item_right_clicked)
        
        self.tar_tv.do_refresh()

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
        #     self._build_tar_dict()
        #     self.apply_tar_changes(name)

        # here send signal to main
        print("on_tree_item_edited triggered ->",track, value, typestr, subtype)
        pass

    def _change_setting_trigger_evaluate_conditions(self, track, value):
        """Set a tracked value and re-evaluate conditions if the update succeeds.

        Returns True if the value was applied to the tracker.
        """
        self._do_evaluation=False
        was_set=self.tar_tv.tracker.set_value(track,value)
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
        evaluated = self.tar_ce.evaluate_conditions_in_a_node(self.tar_tv.tracker.get_root())
        if evaluated or do_eval:
            expanded = self.tar_tv.get_expanded_paths()
            selected = self.tar_tv.get_selected_paths()
            # Delay the refresh AND the restore
            def delayed_refresh():
                self.tar_tv.do_refresh()
                self.tar_tv.restore_expanded_paths(expanded)
                self.tar_tv.restore_selected_paths(selected)
                self.tar_tv.treeview_fit_to_contents(0)
                # Important Clear circular reference flag
                self.tar_tv.tracker.remove_property_from_all_nodes(self.tar_tv.tracker.get_root(),"__conditions__applied__")
            # Need to wait until all data changes are applied.
            QtCore.QTimer.singleShot(0, delayed_refresh)

    def sync_ui(self, func):
        """Run a UI update while suppressing signal feedback."""
        self._syncing_ui = True
        func()
        self._syncing_ui = False

    @property
    def tracker(self)->TreeStructTracker:
        return self.tar_tv.tracker
    
    def set_value(self, track, value):
        """Sets the value and refreshes the conditions and treeview"""
        self._do_evaluation=True
        was_set=self.tar_tv.tracker.set_value(track,value)
        if was_set:
            self._evaluate_conditions()
        return was_set
    
    def item_clicked(self, key_item:QtGui.QStandardItem,index,val_item:dict):
        #knum = key_item.text(0) # key number
        track=val_item.get("path")
        if not isinstance(track,list):
            return
        track = track +["value"]
        name=self.tar_tv.tracker.get_value(track)
        if name in ["",None]:
            return
        # self.pageSelected.emit(name)

    # ========================================================
    # UI
    # ========================================================

    def _build_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ----------------------------------------------------
        # Toolbox
        # ----------------------------------------------------
        toolbox = QtWidgets.QGroupBox("Toolbox")
        toolbox_layout = QtWidgets.QFormLayout(toolbox)

        self.database_all_combo = QtWidgets.QComboBox()
        self.database_all_combo.setSizeAdjustPolicy(
            QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToContents
        )

        self.base_name_all_edit = QtWidgets.QLineEdit()
        self.base_name_all_edit.setPlaceholderText(
            "Set base name for all..."
        )

        self.apply_database_button = QtWidgets.QPushButton("Apply")
        self.apply_database_button.setIcon(self.icons.icon("db add"))

        self.apply_base_name_button = QtWidgets.QPushButton("Apply")
        self.apply_base_name_button.setIcon(self.icons.icon("pen"))

        # Database row
        db_widget = QtWidgets.QWidget()
        db_layout = QtWidgets.QHBoxLayout(db_widget)
        db_layout.setContentsMargins(0, 0, 0, 0)

        db_layout.addWidget(self.database_all_combo)
        db_layout.addWidget(self.apply_database_button)

        toolbox_layout.addRow(f"{TEXT_ICONS['database']} Database:", db_widget)

        # Base name row
        name_widget = QtWidgets.QWidget()
        name_layout = QtWidgets.QHBoxLayout(name_widget)
        name_layout.setContentsMargins(0, 0, 0, 0)

        name_layout.addWidget(self.base_name_all_edit)
        name_layout.addWidget(self.apply_base_name_button)

        toolbox_layout.addRow(f"{TEXT_ICONS['map']} Base name:", name_widget)
        main_layout.addWidget(toolbox)

        # ----------------------------------------------------
        # Tree
        # ----------------------------------------------------
        self.tar_tv_obj = QtWidgets.QTreeWidget()
        self.tar_tv_obj.setAlternatingRowColors(True)
        self.tar_tv_obj.setRootIsDecorated(True)
        self.tar_tv_obj.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)

        main_layout.addWidget(self.tar_tv_obj)

        # ----------------------------------------------------
        # Buttons
        # ----------------------------------------------------

        button_layout = QtWidgets.QHBoxLayout()
        self.add_button = QtWidgets.QPushButton("Add Target")
        self.add_button.setIcon(self.icons.icon("plus"))

        self.remove_button = QtWidgets.QPushButton("Remove Target")
        self.remove_button.setIcon(self.icons.icon("minus"))

        self.verify_button = QtWidgets.QPushButton("Verify")
        self.verify_button.setIcon(self.icons.icon("yes"))

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        button_layout.addStretch()
        button_layout.addWidget(self.verify_button)

        main_layout.addLayout(button_layout)

    def _do_connections(self):
        # ----------------------------------------------------
        # Connections
        # ----------------------------------------------------
        self.add_button.clicked.connect(self.add_target)
        self.remove_button.clicked.connect(self.remove_selected_target)
        self.apply_database_button.clicked.connect(self.apply_database_to_all)
        self.apply_base_name_button.clicked.connect(self.apply_base_name_to_all)
        self.verify_button.clicked.connect(self.verify)

        # self.tar_tv_obj.itemChanged.connect(self._item_changed)

    # ========================================================
    # Database population
    # ========================================================
    def _populate_databases(self):
        self.database_all_combo.clear()
        db_list = self.fmap.get_active_databases_in_dbm()
        self.db_options=[]
        for db in db_list:
            if db.active:
                database = str(db.database_filepath)
                db_name = str(db.name)
                db_file = str(db.db_file)
                self.database_all_combo.addItem(f"{db_name} — {db_file}", database)
                self.db_options.append((f"{db_name} — {db_file}", database, db))
            
    # ========================================================
    # Target management
    # ========================================================
    def add_target(self, config: Optional[MapTargetConfig] = None):
        if config is None:
            database = self.database_all_combo.currentData()
            config = MapTargetConfig(
                database=database or "",
                name_base="",
                prefix="",
                postfix="",
            )
        self._targets.append(config)
        self._rebuild_tree()
        self._emit_targets()

    def remove_selected_target(self):
        item = self.tar_tv_obj.currentItem()
        if item is None:
            return
        target_item = item
        # Walk upwards until Target node.
        while (
            target_item.parent() is not None
            and target_item.parent().parent() is not None
        ):
            target_item = target_item.parent()
        index = self.tar_tv_obj.indexOfTopLevelItem(target_item)
        if index < 0:
            return

        if index >= len(self._targets):
            return

        del self._targets[index]
        self._rebuild_tree()
        self._emit_targets()

    # ========================================================
    # Tree construction
    # ========================================================
    def _rebuild_tree(self):
        return
        self.tar_tv_obj.blockSignals(True)
        try:
            self.tar_tv_obj.clear()

            for index, config in enumerate(self._targets):

                target_item = QtWidgets.QTreeWidgetItem(
                    self.tar_tv_obj,
                    [
                        f"Target {index + 1}",
                        "",
                    ]
                )
                target_item.setExpanded(True)

                self._add_value_item(
                    target_item,
                    "🗄 Database",
                    config.database,
                    "database",
                )

                self._add_value_item(
                    target_item,
                    "🗺 Name Base",
                    config.name_base,
                    "name_base",
                )

                self._add_value_item(
                    target_item,
                    "← Prefix",
                    config.prefix,
                    "prefix",
                )

                self._add_value_item(
                    target_item,
                    "→ Postfix",
                    config.postfix,
                    "postfix",
                )

                # Derived preview
                preview = self._format_preview(config)

                self._add_value_item(
                    target_item,
                    "Name",
                    preview,
                    "preview",
                    editable=False,
                )

        finally:
            self.tar_tv_obj.blockSignals(False)

    def _add_value_item(
        self,
        parent,
        label,
        value,
        field,
        editable=True,
    ):
        return
        item = QtWidgets.QTreeWidgetItem(parent, [label, value])

        item.setData(
            0,
            QtCore.Qt.ItemDataRole.UserRole,
            field,
        )

        item.setData(
            1,
            QtCore.Qt.ItemDataRole.UserRole,
            field,
        )

        if editable:

            item.setFlags(
                item.flags()
                | QtCore.Qt.ItemFlag.ItemIsEditable
            )

        else:

            item.setFlags(
                item.flags()
                & ~QtCore.Qt.ItemFlag.ItemIsEditable
            )

        return item

    # ========================================================
    # Tree → configuration
    # ========================================================

    def _item_changed(self, item, column):
        return
        if column != 1:
            return
        target_item = item
        while target_item.parent() is not None:
            target_item = target_item.parent()

        index = self.tar_tv_obj.indexOfTopLevelItem(
            target_item
        )

        if index < 0 or index >= len(self._targets):
            return

        field = item.data(
            0,
            QtCore.Qt.ItemDataRole.UserRole,
        )

        if field not in (
            "database",
            "name_base",
            "prefix",
            "postfix",
        ):
            return

        setattr(
            self._targets[index],
            field,
            item.text(1),
        )

        self._update_preview(index)

        self._emit_targets()

    # ========================================================
    # Toolbox operations
    # ========================================================

    def apply_database_to_all(self):
        database = self.database_all_combo.currentData()
        if not database:
            return
        for config in self._targets:
            config.database = str(database)
        self._rebuild_tree()
        self._emit_targets()

    def apply_base_name_to_all(self):
        name = self.base_name_all_edit.text()
        for config in self._targets:
            config.name_base = name
        self._rebuild_tree()
        self._emit_targets()

    # ========================================================
    # Preview
    # ========================================================
    def _format_preview(self, config: MapTargetConfig) -> str:
        # ----------------------------------------------------
        # Intentionally dumb for now.
        #
        # Put your existing formatting engine here later:
        #
        # %, #, ?, &, !
        #
        # etc.
        # ----------------------------------------------------
        return (
            f"{config.prefix}"
            f"{config.name_base}"
            f"{config.postfix}"
        )

    def _update_preview(self, index):
        return
        if index < 0 or index >= len(self._targets):
            return
        config = self._targets[index]
        target_item = self.tar_tv_obj.topLevelItem(index)
        if target_item is None:
            return
        for row in range(target_item.childCount()):
            item = target_item.child(row)
            field = item.data(
                0,
                QtCore.Qt.ItemDataRole.UserRole,
            )
            if field == "preview":
                item.setText(
                    1,
                    self._format_preview(config)
                )
                break

    # ========================================================
    # Verification
    # ========================================================

    def verify(self) -> bool:
        errors = []
        # ----------------------------------------------------
        # Basic validation
        # ----------------------------------------------------
        for index, config in enumerate(self._targets):
            target_name = f"Target {index + 1}"
            if not config.database:
                errors.append(
                    f"{target_name}: no database selected."
                )
            if not config.name_base:
                errors.append(
                    f"{target_name}: base name is empty."
                )
        # ----------------------------------------------------
        # Generate final names
        # ----------------------------------------------------
        generated = []
        for index, config in enumerate(self._targets):
            if not config.database:
                continue
            final_name = self._format_preview(config)
            if not final_name:
                errors.append(
                    f"Target {index + 1}: "
                    "generated map name is empty."
                )
                continue
            generated.append(
                (
                    index,
                    config.database,
                    final_name,
                )
            )

        # ----------------------------------------------------
        # Duplicate targets
        #
        # Same database + same map name
        # ----------------------------------------------------
        seen = {}
        for index, database, name in generated:
            key = (database.lower(), name.lower())
            if key in seen:
                other_index = seen[key]
                errors.append(
                    f"Target {index + 1}: map "
                    f"'{name}' already exists in "
                    f"Target {other_index + 1}."
                )

            else:
                seen[key] = index

        # ----------------------------------------------------
        # Database existence check
        # ----------------------------------------------------

        # Put your fmap database/map lookup here.
        #
        # Example:
        #
        # maps = self.fmap.get_maps_in_db(database)
        #
        # if name in maps:
        #     errors.append(...)

        # ----------------------------------------------------
        # Result
        # ----------------------------------------------------
        if errors:
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid Map Targets",
                "\n".join(
                    f"• {error}"
                    for error in errors
                ),
            )
            return False
        return True

    # ========================================================
    # Public API
    # ========================================================
    def get_targets(self) -> list[MapTargetConfig]:
        return [
            MapTargetConfig(
                database=config.database,
                name_base=config.name_base,
                prefix=config.prefix,
                postfix=config.postfix,
            )
            for config in self._targets
        ]

    def set_targets(
        self,
        targets: list[MapTargetConfig],
        ):
        self._targets = [
            MapTargetConfig(
                database=target.database,
                name_base=target.name_base,
                prefix=target.prefix,
                postfix=target.postfix,
            )
            for target in targets
        ]
        self._rebuild_tree()

    def _emit_targets(self):
        self.targetsChanged.emit(
            self.get_targets()
        )

################################################################################################
#################################################################################################
#############################################################################################
#############################################################################################

class NavigationMenu(QtCore.QObject):

    pageSelected = pyqtSignal(str)

    def __init__(self, treeview_obj:QTreeView, tar_struct=None, parent=None):
        super().__init__(parent)
        
        # Nice icons
        self.icons=Icons()
        self.all_icons_dict={
            "home":self.icons.icon("home"),
            "devices":self.icons.icon("devices"),
            "databases":self.icons.icon("databases"),
            "mapping":self.icons.icon("mapping"),
            "backup":self.icons.icon("backup map"),
            "sort":self.icons.icon("sort"),
            "settings":self.icons.icon("settings"),
            "about":self.icons.icon("info"),
            }
        # Define main structure or use example
        self.tar_tv_obj=treeview_obj
        if isinstance(tar_struct,dict):
            self.tar_struct=tar_struct
        else:
            self.tar_struct=NAV_STRUCT_EXAMPLE

        
        