import os
from dataclasses import dataclass
from PyQt6 import QtCore, QtWidgets, QtGui
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QStyledItemDelegate,
    QComboBox,
    QTableWidget,
)

from functional.class_table_widget_functions import TableWidgetFunctions
from controllers.class_filemap_cli_manager import FileMapCliManager

from functional.class_icons import Icons


@dataclass
class MapTargetItem:
    name:str=""

    source_db:str=""
    source_map:str=""
    source_map_type:str=""
    source_mount:str=""
    source_serial:str=""

    target_database:str=""
    prefix:str=""
    base_name:str=""
    suffix:str=""
    
    target_map_name:str=""
    is_map_valid:bool=False
    is_db_valid:bool=False
    info:str=""

@dataclass
class FileTargetItem:
    name:str=""
    source_db:str=""
    source_map:str=""
    source_map_type:str=""
    source_mount:str=""
    source_serial:str=""

    target_path:str=""
    prefix:str=""
    base_name:str=""
    suffix:str=""
    extension:str=""
    
    target_file_name:str=""
    is_file_valid:bool=False
    is_path_valid:bool=False

    target_filepath:str=""
    info:str=""

from dataclasses import fields
from typing import TypeVar

T = TypeVar("T")

def copy_shared_fields(source, target: T) -> T:
    target_fields = {field.name for field in fields(target)}

    for field in fields(source):
        if field.name in target_fields:
            setattr(target, field.name, getattr(source, field.name))

    return target


class TargetManagerWidget(QtWidgets.QWidget):

    targetChanged = QtCore.pyqtSignal(object)
    def __init__(self,fmap: FileMapCliManager,target_type = "map", parent=None):
        super().__init__(parent)

        self.fmap=fmap
        self.target_type=target_type
        self.icons=Icons()
        self.target_ref_dict={} #(mount,serial):File/MaptargetItem
        self.key_mount_serial = {} # Table key: (mount,serial)
        self.targets={}
        self.current_id=None
        self.tracker = None
        # Set available db
        self.database_ref={} # names shown : db filepath
        self.target_db_options=[] # list of names
        self.delegate_set=False
        self._populate_databases()

        self._define_structs()
        self._create_ui()
        self._connect_ui()
        # Clear target list
        self.set_targets([])

    # ---------------------------------------------------
    # Structs
    # ---------------------------------------------------

    def _define_structs(self):
        if self.target_type == "map":

            self.table_struct={
                "0":{
                    "Status":"No Map Selection",
                    "Name":"",
                    "Target Name":"",
                    "Target Database":"",
                    "Target Map":"",
                }
            }
        elif self.target_type == "file":
            self.table_struct={
                "0":{
                    "Status": "No File Selected",
                    "Name": "",
                    "Target Name": "",
                    "Target Mount": "",
                    "Target Path": "",
                    "Target File": "",
                }
            }
        
        self.table_mask={
            "__any__":{
                "Status":{"__m__1":"is_not_change","__mv__1":""},
                "Name":{"__m__1":"is_not_change","__mv__1":""},
                "Target Name":{},
                "Target Database":{},
                "Target Path":{},
                "Target Map":{"__m__1":"is_not_change","__mv__1":""},
                "Target File":{"__m__1":"is_not_change","__mv__1":""},
                "Origin Mount":{"__m__1":"is_not_change","__mv__1":""},
                "Origin Serial":{"__m__1":"is_not_change","__mv__1":""},
            }
        }

    # ---------------------------------------------------
    # UI
    # ---------------------------------------------------

    def _create_ui(self):
        layout=QtWidgets.QVBoxLayout(self)
        #splitter=QtWidgets.QSplitter()
        # ---------------- Table ----------------
        if self.target_type == "file":
            left=QtWidgets.QGroupBox("File Targets:")
        else:
            left=QtWidgets.QGroupBox("Map Targets:")
        left_layout=QtWidgets.QVBoxLayout(left)

        self.table_obj=QtWidgets.QTableWidget()
        self.twf=TableWidgetFunctions(
            self.table_obj, self.table_struct, self.table_mask, None, [])

        left_layout.addWidget(self.table_obj)
        layout.addWidget(left)

    # ---------------------------------------------------
    # Connections
    # ---------------------------------------------------
    def _connect_ui(self):
        # self.table_obj.itemSelectionChanged.connect(self._selection_changed)
        self.twf.signal_data_change[list, str, str, str].connect(self._table_widget_data_changed)
        #self.twf.signal_item_button_right_clicked[list, QtCore.QPoint].connect(self._table_item_right_clicked)

        # Use with tablewidget delegate
        # self.twf.signal_item_combobox_currentindexchanged[int, str, list].connect(self._table_item_comboboxindexchanged)
        
    # ---------------------------------------------------
    # Table refresh
    # ---------------------------------------------------
    def _refresh_table(self):
        self._refresh_status()
        self.twf.data_struct=self.table_struct
        self.twf.refresh_tablewidget(
            self.table_struct, self.twf.modelobj, self.table_obj)
        
    def _refresh_status(self):
        icon_dict={"track_list":[], "icon_list":[]}
        for key,item in self.targets.items():
            # Base Name
            
            icon_dict["track_list"].append([key,"Target Name"])
            icon_dict["icon_list"].append(self.icons.icon("pen"))
            self.table_struct[key]["Status"] = item.info
            # Status
            if isinstance(item,MapTargetItem):
                if item.is_map_valid:
                    icon=self.icons.icon("yes")
                else:
                    icon=self.icons.icon("no")
            self.icons.icon("db"),
            if isinstance(item,FileTargetItem):
                if item.is_file_valid:
                    icon=self.icons.icon("yes")
                else:
                    icon=self.icons.icon("no")
            icon_dict["track_list"].append([key,"Status"])
            icon_dict["icon_list"].append(icon)
            self.table_struct[key]["Status"] = item.info
        
        self.twf.set_items_icons(icon_dict)

    # ---------------------------------------------------
    # Selection
    # ---------------------------------------------------
    # def _selection_changed(self):
    #     items=self.table_obj.selectedItems()
    #     if not items:
    #         return

    #     item=items[0]
    #     track=self.twf.get_track_of_item_in_table(item)
    #     if not track:
    #         return

    #     obj=self.targets.get(track[0])
    #     if not obj:
    #         return

    #     self.current_id=track[0]
    #     ms=self.key_mount_serial[self.current_id]
    #     if ms:
    #         obj=self.get_a_target(ms[0],ms[1])
            
    #         self._refresh_status()

    # ---------------------------------------------------
    # Public
    # ---------------------------------------------------
    def set_targets(self,map_list:list[MapTargetItem|FileTargetItem]):
        """Populate a list of targets, only if target is not already set"""
        ms_list=[]
        for tar in map_list:
            ms_list.append((tar.source_mount,tar.source_serial))
        
        if not ms_list:
            self.table_struct={}
            self.targets={}
            self.key_mount_serial={}
            self.target_ref_dict = {}
            self.delegate_set=False
            self._refresh_table()
            return

        # Remove maps not in maplist
        ms_ref_list=list(self.target_ref_dict.keys())
        for ms in ms_ref_list:
            if ms not in ms_list:
                tar_to_del=self.get_a_target(ms[0],ms[1])
                # kkk=self.get_target_key_from_mount_serial(ms[0],ms[1])
                # if kkk in self.table_struct.keys():
                #     self.table_struct.pop(kkk)
                #     self.targets.pop(kkk)
                #     self.key_mount_serial.pop(kkk)
                self.remove_from_targets(tar_to_del)
        
        # add new maps
        for tar in map_list:
            if self.is_in_targets(tar):
                continue
            # if not set already set it up
            self.add_to_targets(tar)


        self.targets={}
        self.key_mount_serial={}
        
        self.table_struct={}
        # populate with what is in target_ref_dict
        for idx,(ms,item) in enumerate(self.target_ref_dict.items()):
            key=str(idx) # self._get_unique_id(str(idx),list(self.table_struct.keys()),"")
            self.key_mount_serial[key]=ms
            self.set_target(key,item)
        
        self._refresh_table()
    
    def get_targets(self)->list:
        return list(self.targets.values())

    def get_target(self,key:str)->MapTargetItem|None:
        return self.targets.get(key)
    
    def get_target_key_from_mount_serial(self,mount:str,serial:str)->str|None:
        for key in self.targets.keys():
            mmm: MapTargetItem|FileTargetItem = self.targets.get(key)
            if mmm.source_mount == mount and mmm.source_serial == serial:
                return key
        return None  

    def set_combobox_delegate(self,column):
        if not self.delegate_set:
            delegate = ComboBoxDelegate(
                self.table_obj,
                lambda index: self._get_current_database_options(index)
            )
            self.table_obj.setItemDelegateForColumn(column, delegate)
            self.delegate_set=True
    
    def set_fileopen_delegate(self,column):
        if not self.delegate_set:
            self.path_delegate = FilePathDelegate(self.table_obj)

            self.table_obj.setItemDelegateForColumn(column,  # Target Path
                self.path_delegate)

    
    def _get_current_database_options(self, index):
        self._populate_databases()
        return self.target_db_options


    def set_target(self,key:str,target:MapTargetItem|FileTargetItem):
        """Sets the target item to the table struct"""
        self.twf.tablewidgetobj.clearSelection()
        self.targets[key]=target
        # print("target:", target)
        target_dict={}
        if isinstance(target,MapTargetItem):
            # print("Before >>>>>>>>>>>>>>>><",target.info)
            target = self.validate_target_db_map(target)
            # print("After  >>>>>>>>>>>>>>>><",target.info,"-->",target.target_map_name)
            target_dict={
                "Status":target.info,
                "Name":target.name,
                "Target Name":target.base_name,
                "Target Database":target.target_database,
                "Target Map":target.target_map_name,
            }
            self.table_struct.update({key:target_dict})
            # self._add_database_combobox(key,target.target_database)
            self.set_combobox_delegate(3) # Target Database

        elif isinstance(target,FileTargetItem):
            target = self.validate_target_path_file(target)
            target_dict={
                "Status":target.info,
                "Name":target.name,
                "Target Name":target.base_name,
                "Target Path":target.target_path,
                "Target File":target.target_file_name,
            }
            self.table_struct.update({key:target_dict})
            self.set_fileopen_delegate(3)

           
        # for jjj,(tr_field,value) in enumerate(target_dict.items()):
        #     track = [key, tr_field]
        #     self.twf.set_tracked_value_to_dict(track, 
        #                                        value, 
        #                                        self.table_struct, 
        #                                        "", 
        #                                        jjj+1 == len(target_dict),#last one
        #                                        )
        
        
    
    def is_in_targets(self,target:MapTargetItem|FileTargetItem)->bool:
        """Is the target already in targets"""
        return (target.source_mount,target.source_serial) in self.target_ref_dict
    
    def add_to_targets(self,target:MapTargetItem|FileTargetItem):
        """Is the target already in targets"""
        if not self.is_in_targets(target):
            key=(target.source_mount,target.source_serial)
            self.target_ref_dict[key]=target
    
    def remove_from_targets(self,target:MapTargetItem|FileTargetItem):
        """Remove from targets"""
        if self.is_in_targets(target):
            key=(target.source_mount,target.source_serial)
            #self.remove_key_from_tablewidgets(key)
            self.target_ref_dict.pop(key)

    def remove_key_from_tablewidgets(self,key):
            """Remove old combo widgets"""
            it_w_dict = self.twf.itemwidget_dict
            new_track_list=[]
            new_widget_list=[]
            for track,widget in zip (it_w_dict["track_list"],it_w_dict["widget_list"]):
                if key != track[0]:
                    new_track_list.append(track)
                    new_widget_list.append(widget)
            it_w_dict={}        
            it_w_dict.update({"track_list": new_track_list})
            it_w_dict.update({"widget_list": new_widget_list})
            self.twf.set_items_widgets(it_w_dict)

            
    
    def get_a_target(self,mount,serial)->MapTargetItem|FileTargetItem|None:
        """Returns the item if found"""
        return self.target_ref_dict.get((mount,serial))
        
    # --------------------------------------------------
    # Databases
    # --------------------------------------------------
    def _populate_databases(self):
        self.database_ref={}
        options=[]
        for db in self.fmap.get_active_databases_in_dbm():
            if db.active:
                name=f"{db.name}-{db.db_file}"
                options.append(name)
                self.database_ref.update({name:str(db.database_filepath)})
        self.target_db_options=options

    def validate_target_path_file(self,target:FileTargetItem)->FileTargetItem:    
        result=f"{target.prefix}{target.base_name}{target.suffix}"

        if not self.fmap.is_mount_serial_active(target.source_mount,target.source_serial):
            target.info='Source device not active'
            target.is_path_valid=False
            target.is_file_valid=False
            target.target_filepath = ""
            return target
        
        if not target.target_path:
            target.info='No Target path given'
            target.is_path_valid=False
            target.is_file_valid=False
            target.target_filepath = ""
            return target
        
        # full_path=os.path.join(target.source_mount,target.target_path)
        full_path=target.target_path
        (file_exist, is_file)=self.fmap.fm.validate_path_file(full_path)
        if not file_exist:
            target.info='Path does not exist'
            target.is_path_valid=False
            target.is_file_valid=False
            target.target_filepath = ""
            return target
    
        target.is_path_valid=True
        a_path=f"{target.name}" # path to use with !
        processed_name=self.fmap.cma.format_new_table_name(result,a_path)
        if not target.extension:
            processed_name=self.fmap.fm.extract_filename(processed_name,True)
        else:
            processed_name=self.fmap.fm.extract_filename(processed_name,False)
            ext = target.extension if target.extension.startswith(".") else f".{target.extension}"
            processed_name += ext
        
        filepath=os.path.join(full_path,processed_name)
        (file_exist, is_file)=self.fmap.fm.validate_path_file(filepath)
        ms=(target.source_mount,target.source_serial)
        if not file_exist:
            is_ok,msg = self._is_ok_name_in_target_ref(processed_name,ms)
            if is_ok:
                target.target_file_name=processed_name
                target.target_filepath=filepath
            else:
                target.target_file_name = ""
                target.target_filepath = ""
        else:
            msg = 'File already exist'
            target.is_path_valid=True
            target.is_file_valid=False
            target.target_file_name = processed_name
            target.target_filepath = ""
            is_ok = False

        target.is_file_valid=is_ok
        target.info=msg
        return target
    
    def validate_target_db_map(self,target:MapTargetItem)->MapTargetItem:
        
        result=f"{target.prefix}{target.base_name}{target.suffix}"
        
        tar_db=target.target_database
        if not tar_db:
            target.info='No Target database given'
            target.is_db_valid=False
            target.is_map_valid=False
            target.target_map_name = ""
            return target
        
        db_filepath=self.database_ref.get(tar_db)
        if not db_filepath:
            target.info='Target database not active'
            target.is_db_valid=False
            target.is_map_valid=False
            target.target_map_name = ""
            return target  
        
        target.is_db_valid=True
        a_path=f"{target.name}" # path to use with !
        processed_name=self.fmap.cma.format_new_table_name(result,a_path)
        
        is_ok, msg = self.fmap.map_validation(db_filepath,processed_name)
        ms=(target.source_mount,target.source_serial)
        if is_ok:
            is_ok,msg = self._is_ok_name_in_target_ref(processed_name,ms)

        target.is_map_valid=is_ok
        target.info=msg
        if is_ok:
            target.target_map_name=processed_name
        else:
            target.target_map_name=""
        return target            
    
    def _is_ok_name_in_target_ref(self,new_name,my_ms):
        """returns True if the item is ok"""
        if not new_name:
            return False, "No Map name"
        count=0
        for ms,item in self.target_ref_dict.items():
            if ms == my_ms:
                continue
            if isinstance(item,MapTargetItem):
                if item.target_map_name and item.target_map_name == new_name:
                    count+=1
                    
            if isinstance(item,FileTargetItem):
                if item.target_file_name and item.target_file_name == new_name:
                    count+=1

        if count>=1:
            return False, "Item Name Duplicated"
        return True,""
    
    def _add_database_combobox(self, key, db: str):
        """Adds combobox to item with the database selection
        """
        combobox = QtWidgets.QComboBox()
        # Tablewidget deletes objects after using setCellwidget, you can not set different comboboxes
        # now combobox objects are delegated to cell information.
        self._populate_databases()
        if not self.target_db_options:
            return
        first_db=self.target_db_options[0]
        for ppp in self.target_db_options:
            combobox.addItem(str(ppp))

        # set db as default
        if not db:
            index = combobox.findText(first_db, QtCore.Qt.MatchFlag.MatchFixedString)
            combobox.setCurrentIndex(index)
            ms=self.key_mount_serial.get(key)
            target=self.get_a_target(ms[0],ms[1])
            target.target_database=first_db
            track = [key, "Target Database"]
            self.twf.set_tracked_value_to_dict(track, first_db, self.table_struct, "", False)

        # add or replace widget on twf
        it_w_dict = self.twf.itemwidget_dict
        # self.remove_key_from_tablewidgets(key)
        track_list = it_w_dict["track_list"]
        is_ontrack=False
        for tr in track_list:
            if tr[0]==key:
                is_ontrack=True
                break
        if not is_ontrack:                
            track_list.append([key, "Target Database"])
            widget_list = it_w_dict["widget_list"]
            widget_list.append(combobox)
            it_w_dict.update({"track_list": track_list})
            it_w_dict.update({"widget_list": widget_list})
            self.twf.set_items_widgets(it_w_dict)
        # print(self.twf.itemwidget_dict)
    
    def _table_widget_data_changed(self, track: list[str], val: any, valtype: str, subtype: str):
        """Sets the changed information in table widget by user into the Structure
        """
        if not track:
            return
        processed_val = self.twf.check_restrictions.set_type_to_value(val, valtype, subtype)
        self.twf.set_tracked_value_to_dict(track, processed_val, self.table_struct, subtype, False)

        key=track[0]
        ms=self.key_mount_serial.get(key)
        target=self.get_a_target(ms[0],ms[1])
            
        str_item = track[1]
        target_changed=False
        if  str_item == "Target Database" and target.target_database != processed_val:
            target.target_database = processed_val
            target_changed=True
        if str_item == "Target Name" and target.base_name != processed_val:
            target.base_name = processed_val
            target_changed=True
        if str_item == "Target Path" and target.target_path != processed_val:
            target.target_path = processed_val
            target_changed=True
        
        if target_changed:
            self.set_target(key, target)
            QtCore.QTimer.singleShot(0, self._refresh_table)

            

    def _get_unique_id(self, desired_id:str,list_of_ids:list,prefix:str="")->str:
        """Gets a unique id with a prefix that is not in the list of ids.

        Returns:
            str: An id which is not taken.

        Args:
            desired_id (str): wanted id
            list_of_ids (list): list od ids to compare
            prefix (str, optional): Prefix for id naming "{prefix}#". Defaults to "".

        Returns:
            str: Unique id using "{prefix}#" format
        """
        if not self._is_id_in_list(desired_id,list_of_ids) and desired_id != "" and desired_id is not None:
            return desired_id

        if desired_id is None or desired_id != "":
            desired_id = prefix
        iii = 1
        copydid = desired_id + str(iii)
        while self._is_id_in_list(copydid ,list_of_ids):
            iii = iii + 1
            copydid = desired_id + str(iii)
        return copydid
    
    def _is_id_in_list(self, an_id:any,list_of_ids:list) -> bool:
        """Check if the id is in the list of ids
        """
        return an_id in list_of_ids



class ComboBoxDelegate(QtWidgets.QStyledItemDelegate):

    def __init__(self, parent, items_provider):
        super().__init__(parent)

        # Function that returns the current items
        self.items_provider = items_provider

    def createEditor(self, parent, option, index):
        combo = QtWidgets.QComboBox(parent)

        # Get fresh values EVERY time the editor is created
        items = self.items_provider(index)

        combo.addItems(items)

        combo.activated.connect(
            lambda _: self._commit_and_close(combo)
        )

        return combo

    def setEditorData(self, editor, index):
        if not isinstance(editor, QtWidgets.QComboBox):
            return

        value = index.data(
            QtCore.Qt.ItemDataRole.DisplayRole
        )

        if value is None:
            return

        pos = editor.findText(value)

        if pos >= 0:
            editor.setCurrentIndex(pos)

    def setModelData(self, editor, model, index):
        if not isinstance(editor, QtWidgets.QComboBox):
            return

        model.setData(
            index,
            editor.currentText(),
            QtCore.Qt.ItemDataRole.EditRole
        )

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def _commit_and_close(self, editor):
        self.commitData.emit(editor)
        self.closeEditor.emit(editor)

class FilePathDelegate(QtWidgets.QStyledItemDelegate):
    """
    Delegate for a table cell that opens a QFileDialog when edited.

    The selected directory is written back to the model, which triggers
    the normal QTableWidget item-change machinery.
    """
    def createEditor(self, parent, option, index):
        editor = QtWidgets.QPushButton("...", parent)
        editor.clicked.connect(lambda: self._open_dialog(index))
        return editor

    def setEditorData(self, editor, index):
        pass

    def setModelData(self, editor, model, index):
        pass

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def _open_dialog(self, index):
        model = index.model()

        current_path = index.data(
            QtCore.Qt.ItemDataRole.DisplayRole
        ) or ""

        view = self.parent()

        path = QtWidgets.QFileDialog.getExistingDirectory(
            view,
            "Select Target Path",
            current_path,
            QtWidgets.QFileDialog.Option.ShowDirsOnly,
        )

        if path:
            model.setData(
                index,
                path,
                QtCore.Qt.ItemDataRole.EditRole
            )
