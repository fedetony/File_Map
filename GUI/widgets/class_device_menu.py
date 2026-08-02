from PyQt6 import QtCore, QtGui, QtWidgets 
from PyQt6.QtWidgets import *

from functional.class_treeview_functions import *
from functional.class_struct_conditioner import *
from functional.class_struct_tracker import TreeStructTracker
from controllers.class_filemap_cli_manager import *

from functional.class_LogHandler import LM
log=LM.get_logger_with_handler("DeviceMenuTree","debug",True,None)


FIELDS_POSITION=[
    {"name": "ITEM",  "editable": False, "selectable": True,  "hidden": False},
    {"name": "VALUE", "editable": True,  "selectable": True,  "hidden": False},
    {"name": "TYPE",  "editable": False, "selectable": False, "hidden": True},
    {"name": "UNIT",  "editable": False, "selectable": True, "hidden": True},
    {"name": "INFO",  "editable": True, "selectable": True, "hidden": True},
]
conditions={"Serial": "me_set('meta[hidden]',False) if node_get('rapid[Show[value]]') else me_set('meta[hidden]',True)",
            }

DEV_STRUCT_EXAMPLE={
        "Devices": {"children":[                                  
            ]},            
        }
MAX_TIME_IN_S = 5

class DeviceMenu(QtCore.QObject):
    def __init__(self, fmap:FileMapCliManager, treeview_obj:QTreeView, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        # Define main structure or use example
        self.fmap = fmap
        self.dev_tv_obj = treeview_obj
        self.dev_struct=DEV_STRUCT_EXAMPLE.copy()
        self._syncing_ui = False
        self.info_cache=[] # list of info dicts
        self._build_dev_configuration_tree()
        self.dev_struct=self.generate_new_mount_serial_struct()

    @property
    def tracker(self):
        return self.dev_ce.tracker

    def _build_dev_configuration_tree(self):
        """Initialize and configure the style tree, delegates, condition engine, and context menu.

        Sets up treeview behavior, connects edit signals, evaluates conditions, and refreshes the UI.
        """
        self._do_evaluation=False
        self.dev_tv=TreeviewFunctions(self.dev_tv_obj,self.dev_struct,FIELDS_POSITION)
        # attach delegate to VALUE column (1)
        delegate = TypedItemDelegate(self.dev_tv)
        self.dev_tv_obj.setItemDelegateForColumn(1, delegate)
        self.dev_tv.data_change[list,object,str,str].connect(self.on_tree_item_edited)
        self.dev_tv.struct_data_change[list,object,str,str].connect(self.on_struct_item_edited)
        #self.dev_tv.expand_to_depth(1) #333) #Expand all
        # Condition Engine
        self.dev_ce=ConditionEngine(self.dev_tv.tracker)
        self._evaluate_conditions()
        
        # Add cache tooltip, icons, backgrounds, styles
        # self.dev_tv.set_icons_cache(self.all_icons_dict)
        # self.dev_tv.set_dev_cache(dev_dict)

        # Right click Menu 
        self.dev_tv.treeviewobj.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.dev_tv.treeviewobj.customContextMenuRequested.connect(self.dev_tv._on_context_menu)
        #self.dev_tv.item_right_clicked.connect(self.on_item_right_clicked)
        
        self.dev_tv.do_refresh()

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
        #     self._build_dev_dict()
        #     self.apply_dev_changes(name)

        # here send signal to main
        print("on_tree_item_edited triggered ->",track, value, typestr, subtype)
        pass

    def _change_setting_trigger_evaluate_conditions(self, track, value):
        """Set a tracked value and re-evaluate conditions if the update succeeds.

        Returns True if the value was applied to the tracker.
        """
        self._do_evaluation=False
        was_set=self.dev_tv.tracker.set_value(track,value)
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
        evaluated = self.dev_ce.evaluate_conditions_in_a_node(self.dev_tv.tracker.get_root())
        if evaluated or do_eval:
            expanded = self.dev_tv.get_expanded_paths()
            selected = self.dev_tv.get_selected_paths()
            # Delay the refresh AND the restore
            def delayed_refresh():
                self.dev_tv.do_refresh()
                self.dev_tv.restore_expanded_paths(expanded)
                self.dev_tv.restore_selected_paths(selected)
                self.dev_tv.treeview_fit_to_contents(0)
                # Important Clear circular reference flag
                self.dev_tv.tracker.remove_property_from_all_nodes(self.dev_tv.tracker.get_root(),"__conditions__applied__")
            # Need to wait until all data changes are applied.
            QtCore.QTimer.singleShot(0, delayed_refresh)

    def sync_ui(self, func):
        """Run a UI update while suppressing signal feedback."""
        self._syncing_ui = True
        func()
        self._syncing_ui = False
  
    @property
    def tracker(self)->TreeStructTracker:
        return self.dev_tv.tracker
    
    def set_value(self, track, value):
        """Sets the value and refreshes the conditions and treeview"""
        self._do_evaluation=True
        was_set=self.dev_tv.tracker.set_value(track,value)
        if was_set:
            self._evaluate_conditions()
        return was_set
    def get_devices_list(self):
        devices_list=self.fmap.device_monitor.devices
        if not devices_list:
            # Trigger Thread
            self.fmap.device_monitor.refresh()
        count = 0 
        while not devices_list and count < MAX_TIME_IN_S*10 :
            devices_list=self.fmap.device_monitor.devices
            count += 1
            time.sleep(0.1)
        if not devices_list:
            log.warning(f"No Devices found! Might be {platform.system()} did not respond. Try to refresh again later!")
            return []
        return devices_list
        
    def generate_new_mount_serial_struct(self):
        devices_list=self.get_devices_list()
        self.dev_struct=DEV_STRUCT_EXAMPLE.copy() #clear struct
        for dev_id,mount_serial in enumerate(devices_list):
            self.tracker.delete_node(["Devices",f"{dev_id}"])
            self.add_dev_to_struct(["Devices",f"{dev_id}"],"Mount",mount_serial[0], editable=True,selectable=True,hidden=False)
            self.add_dev_to_struct(["Devices",f"{dev_id}"],"Serial",mount_serial[1], editable=True,selectable=True,hidden=False)
            self.tracker.delete_node(["Devices",f"{dev_id}","Details"])
        # print(self.tracker.get_root())
        # refresh treeview
        self.dev_tv.refresh_treeview(self.dev_struct,self.dev_tv.modelobj,self.dev_tv_obj)
        self.dev_tv.expand_to_depth(3)
    
    def generate_new_info_struct(self):
        devices_list=self.get_devices_list()        
        self.dev_struct=DEV_STRUCT_EXAMPLE.copy() #clear struct
        for dev_id,mount_serial in enumerate(devices_list):
            self.tracker.delete_node(["Devices",f"{dev_id}"])
            self.add_dev_to_struct(["Devices",f"{dev_id}"],"Mount",mount_serial[0], editable=True,selectable=True,hidden=False)
            self.add_dev_to_struct(["Devices",f"{dev_id}"],"Serial",mount_serial[1], editable=True,selectable=True,hidden=False)
            info=self.get_device_info(dev_id, devices_list)
            for key,value in info.items(): 
                self.add_dev_to_struct(["Devices",f"{dev_id}","Details"],key, value, editable=True,selectable=True,hidden=False)
        
        # refresh treeview
        self.dev_tv.refresh_treeview(self.dev_struct,self.dev_tv.modelobj,self.dev_tv_obj)
        self.dev_tv.expand_to_depth(3)
    
    def get_device_info(self,device_id, devices_list):
        # Find id's mount and serial
        mount_serial=None
        for dev_id, m_s in enumerate(devices_list):
            if str(dev_id) == str(device_id):
                mount_serial= m_s
                break
        if not isinstance(mount_serial,list):
            return {}
        # search in cache
        for ic_id,ic_dict in enumerate(self.info_cache):
            ic_m_s = ic_dict.get("mount_serial")
            if not isinstance(ic_m_s,list):
                continue
            if ic_m_s == mount_serial:
                return ic_dict.get("info",{})
        # get device info
        info_dict=self.fmap.device_monitor.get_device_info(mount_serial[0])
        if info_dict is None:
            log.warning(f"Empty Mount information search for {mount_serial[0]}")
            return {}
        # Cache info if found
        self.info_cache.append({"mount_serial":mount_serial,"info":info_dict})
        return info_dict

    def add_dev_to_struct(self,track,key,value, editable=False,selectable=True,hidden=False):
        child_node = {
                "value": value, 
                "type": "str", 
                "unit":"", 
                "meta": {
                        "editable": editable, 
                        "selectable": selectable,  
                        "hidden": hidden
                        }
                }
        self.tracker.ensure_path(track+[key])
        self.tracker.set_value(track+[key],child_node)
        
        
        
       
        