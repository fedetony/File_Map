# FileMap Cli Manager
import io
import logging
from typing import Callable, Any
from contextlib import redirect_stdout

from controllers.class_configuration_manager import ConfigurationManager
from controllers.class_database_manager import DatabaseManager

from class_device_monitor import *
from class_autocomplete_input import *
from class_backup_actions import *
from class_file_mapper import *
from widgets.ask_confirmation_dialog import *
from controllers.class_database_manager import *

from functional.class_LogHandler import LM
log=LM.get_logger_with_handler("FileMapCli","debug",True,None)

class FileMapCliManager:
    """
    Coordinates configuration, DatabaseManager and FileMap CLI operations.

    Acts as the application's service layer between the GUI and the lower-level
    managers. Performs database activation, registration, configuration updates,
    and keeps the DatabaseManager synchronized with FileMap's state.
    """
    def __init__(self, 
                conf_manager:ConfigurationManager,
                dbm:DatabaseManager
                ):
        """
        Initialize managers and synchronize the initial active database state.
        """ 
        with redirect_stdout(LoggerWriter(log)):    
            # Get Filemap's inputs
            self.gui_db_map_size_cache = {} # "db":{"map":size | None }
            self._updating_databases=False
            self.mapping_to_pair = (None,None)
            self.cfg = conf_manager
            self.dbm = dbm
            (self.file_list, self.password_list, 
            self.key_list, activate_list ) = self.dbm.get_file_pwd_key_lists()
            self.user_dialogs=ConfirmationDialog()
            self.ba= BackupActions(self.file_list,
                                self.password_list,
                                self.key_list,
                                self.user_dialogs.ask_confirmation
                                )
            self.cma = self.ba.cma
            self.fm=FileManipulate()
            for name, activate in zip(self.file_list,activate_list):
                if activate:
                    self.cma.activate_databases(name)
            self.set_active_databases_in_dbm()
            self.device_monitor = DeviceMonitor(log_print=True)
            
    
    # -------------------------------------------------------
    # Databases Actions
    # -------------------------------------------------------

    def save_db_in_config(self, db_id_list, user=True):
        """
        Save the selected databases to the configuration.

        Existing entries are updated; new entries are added.
        """
        for db in self._get_db_list_from_id_list(db_id_list):
            is_ok_db, is_ok_k, *_ = self.dbm.verify_db_paths(db)
            if is_ok_db and is_ok_k:
                db.user_database = user
                self.cfg.save_database(db.config_dict, user)
                
    def remove_db_from_config(self, db_id_list, user=True):
        """
        Remove the selected databases from the configuration.
        """
        for db in self._get_db_list_from_id_list(db_id_list):
            self.cfg.remove_database(db.config_dict, user)
            db.user_database = None
        
    
    def _get_db_list_from_id_list(self,db_id_list)->list[DatabaseInfo]:
        """
        Convert a list of database IDs into DatabaseInfo objects.
        """
        the_dbs=[]
        for db_id in db_id_list:
            if isinstance(db_id,str):
                id_pos=int(db_id)
            elif isinstance(db_id,int):
                id_pos=db_id
            if id_pos >=0 and id_pos < len(self.dbm.databases):
                db=self.dbm.databases[id_pos]
                the_dbs.append(db)
        return the_dbs

    def set_db_name(self,db_id, new_name):
        """
        Rename a database in the DatabaseManager.
        """
        the_dbs=self._get_db_list_from_id_list([db_id])
        for db in the_dbs:
            db.name = new_name

    def set_autoload(self,autoload_list, set_auto:bool):
        """
        Enable or disable autoload for the selected databases.
        """
        the_dbs=self._get_db_list_from_id_list(autoload_list)
        for db in the_dbs:
            db.autoload = set_auto

    def activate_databases(self,db_id_list):
        """
        Activate the selected databases in FileMap and update their active state.
        """
        self._updating_databases = True
        activation_list=[]
        the_dbs=self._get_db_list_from_id_list(db_id_list)
        for db in the_dbs:
            is_ok_db, is_ok_k, db_filepath, k_filepath = self.dbm.verify_db_paths(db)
            if is_ok_db and is_ok_k:
                activation_list.append(db_filepath)
            else:
                if not is_ok_db:
                    log.error(f"The DB file could not be opened: {db.name} {db.db_file}")
                if not is_ok_k:
                    log.error(f"The Key file could not be opened: {db.name} {db.key_file}")
        for dbfname in activation_list:
            self.cma.activate_databases(dbfname)
        self.set_active_databases_in_dbm()
        self._updating_databases = False
    
    def deactivate_databases(self,db_id_list):
        """
        Deactivate the selected databases in FileMap and update their active state.
        """
        self._updating_databases = True
        deactivation_list=[]
        the_dbs=self._get_db_list_from_id_list(db_id_list)
        for db in the_dbs:
            _, _, db_filepath, k_filepath = self.dbm.verify_db_paths(db)
            deactivation_list.append(db_filepath)
        for dbfname in deactivation_list:
            self.cma.deactivate_databases(dbfname)
        self.set_active_databases_in_dbm()
        self._updating_databases = False
    
    def get_authentication_list(self,db_id_list:list[str])->list[tuple]:
        """
        Return authentication information for the selected databases.

        Returns:
            list[tuple]:
                (DatabaseInfo, db_path, requires_password, has_key, key_path)
        """
        authentication_list=[]
        the_dbs=self._get_db_list_from_id_list(db_id_list)
        for db in the_dbs:
            _, _, db_filepath, k_filepath = self.dbm.verify_db_paths(db)
            authentication_list.append((db, db_filepath, db.requires_password, db.has_key, k_filepath))
        return authentication_list

    def remove_database(self,db_id_list):
        """
        Remove the selected databases from FileMap and the DatabaseManager.
        """
        self._updating_databases = True
        removal_list=[]
        the_dbs=self._get_db_list_from_id_list(db_id_list)
        for db in the_dbs:
            _, _, db_filepath, k_filepath = self.dbm.verify_db_paths(db)
            removal_list.append(db_filepath)
        # Remove in filemap    
        for dbfname in removal_list:
            self.cma.remove_database_file(dbfname)
        # Remove in dbm
        for db in the_dbs:
            self.dbm.remove_database(db)
        self.set_active_databases_in_dbm()
        self._updating_databases = False
    
    def add_database(self,file_path,a_pwd=None,keyfile=None,activate=False):
        """
        Create a DatabaseInfo entry and register it with FileMap.
        """
        self._updating_databases = True
        # Add to database manager
        file_we=FM.extract_filename(file_path,with_extension=True)
        file_woe=FM.extract_filename(file_path,with_extension=False)
        path_we=FM.extract_path(file_path,True)
        k_file = None
        k_path = None
        if keyfile:
            k_file = FM.extract_filename(keyfile)
            k_path = FM.extract_path(keyfile)
        db=DatabaseInfo(
            name = file_woe,
            db_path = path_we,
            db_file = file_we,
            requires_password = (a_pwd == True),
            key_path = k_path,
            key_file = k_file,
            user_database = None,
        )
        self.dbm.databases.append(db)
        self.dbm.save()
        # Add to filemap
        self.cma.file_list.append(file_path)
        self.cma.password_list.append(a_pwd)
        self.cma.key_list.append(keyfile)
        
        if activate:
            self.cma.activate_databases(file_path)

        self.set_active_databases_in_dbm()
        self._updating_databases = False

    def get_autoload_db_id_list(self,db_id_list):
        """
        Split database IDs into autoload and non-autoload groups.
        """
        auto_db_list=[]
        notauto_db_list=[]
        the_dbs=self._get_db_list_from_id_list(db_id_list)
        for db_id, db in zip(db_id_list,the_dbs):
            if db.autoload:        
                auto_db_list.append(db_id)         
            else:
                notauto_db_list.append(db_id) 
        return auto_db_list, notauto_db_list
    
    def get_cond_db_id_list(self,db_id_list,condition):
        """
        Split database IDs into autoload and non-autoload groups.
        """
        key_db_list=[]
        nokey_db_list=[]
        the_dbs=self._get_db_list_from_id_list(db_id_list)
        for db_id, db in zip(db_id_list,the_dbs):
            if not hasattr(db,condition):
                log.error(f"No condition found in DBinfo for '{condition}'")
                break
            if getattr(db,condition):        
                key_db_list.append(db_id)         
            else:
                nokey_db_list.append(db_id) 
        return key_db_list, nokey_db_list

    def get_active_unactive_db_id_list(self,db_id_list):
        """
        Split database IDs into active and inactive groups.
        """
        active_db_list=[]
        unactive_db_list=[]
        the_dbs=self._get_db_list_from_id_list(db_id_list)
        for db_id, db in zip(db_id_list,the_dbs):
            if db.active:        
                active_db_list.append(db_id)         
            else:
                unactive_db_list.append(db_id) 
        return active_db_list, unactive_db_list
    
    def get_user_default_config(self,db_id_list):
        """
        Split database IDs into User, Default and None groups.
        """
        user_list=[]
        default_list=[]
        none_list=[]
        the_dbs=self._get_db_list_from_id_list(db_id_list)
        for db_id, db in zip(db_id_list,the_dbs):
            if db.config_name=="User":        
                user_list.append(db_id)         
            elif db.config_name=="Default":
                default_list.append(db_id) 
            else:
                none_list.append(db_id)
        return user_list, default_list, none_list
    
    def set_active_databases_in_dbm(self):
        """
        Synchronize DatabaseInfo.active with FileMap's active database list.
        """
        for db in self.dbm.databases:
            if isinstance(db,DatabaseInfo):
                _, _, db_filepath, k_filepath = self.dbm.verify_db_paths(db)
                if self.cma.is_database_active(db_filepath):
                    db.active=True
                else:
                    db.active=False
        self.refresh_map_size_cache()
        
    def get_active_databases_in_dbm(self)->list[DatabaseInfo]:
        return self.dbm.databases
    
    # -------------------------------------------------------
    # Mapping Actions
    # -------------------------------------------------------

    def map_validation(self, database,table_name):
        """Validate a new map name. 
        Returns:
            tuple (bool, message)"""

        not_allowed = '"/' + "'|><={}[]()"
        for char in table_name:
            if char in not_allowed:
                message=f'Map name does not allow these characters "{str(not_allowed)}".'
                log.warning(message)
                return False, message

        if not self.cma.validate_new_map(table_name, database):
            message = f'Map "{table_name}" already exists in database. Please enter a non existing map name'
            log.warning(message)
            return False, message

        return True, ""
    
    def is_map_in_db(self,database:str,map_name)->bool:
        if not map_name:
            return False
        if map_name in self.cma.get_maps_in_db(str(database)):   
            return True
        return False
    
    def get_maps_in_db(self,database:str)->list:
        return self.cma.get_maps_in_db(str(database))
    
    def get_all_maps_info_dict_in_db(self,database:str)->list:
        info_list=[]
        database=str(database)
        for a_map in self.get_maps_in_db(database):
            info_dict=self.cma.get_map_info_dict(database,a_map)
            info_list.append(info_dict)
        return info_list
            
    def create_new_map(self,database,
                        table_name: str,
                        path_to_map: str,
                        log_print: bool = True,
                        progress_bar: Callable | None = None,
                        shallow_map: bool = False,
                        press_to_continue: bool = False,
                        log_callback: Callable | None = None,
                        kill_ev: threading.Event | None = None
                        ):
        """Create a new New map"""
        selected_db=database
        self.mapping_to_pair = (None,None)
        if not selected_db:    
            return False
        # path_to_map=path_to_map.replace('//','/')
        path_to_map=FM.normalize_path(path_to_map)
        is_ok,msg=self.map_validation(database,table_name)
        if is_ok:
            temp_folder=FM.get_temp_directory_path(prefix="__filemap__",suffix=table_name)
            temp_db=FM.extract_filename(selected_db,False)+"_temp.db"
            
            temp_db_filepath=os.path.join(temp_folder,temp_db)
            # self.cma.create_filemap_database(temp_db_filepath) this asks for pwd
            fm=FileMapper(temp_db_filepath,None,None,False) #->creates new database and assigns mapper
            self.cma.file_list.append(temp_db_filepath)
            self.cma.password_list.append(None)
            self.cma.key_list.append(None)
            self.cma.activate_databases(temp_db_filepath)
            if not isinstance(fm,FileMapper):
                if log_callback:
                    log_callback(f"[red]Error creating database @ {temp_db_filepath}")
                return False
            if log_callback:
                log_callback(f"[yellow]Created temporary database @ {temp_db_filepath}")

            table_name=self.cma.format_new_table_name(table_name,path_to_map)
            if table_name not in ['',None]+fm.db.tables_in_db():  
                self.mapping_to_pair=(temp_db_filepath, table_name)
                if log_callback:
                    log_callback(f"[yellow]Created temporary Map {table_name}")
                fm.db.create_connection()    
                fm.map_a_path_to_db(table_name=table_name,
                                    path_to_map=path_to_map,
                                    log_print=log_print, 
                                    progress_bar=progress_bar,
                                    shallow_map=shallow_map,
                                    press_to_continue=press_to_continue,
                                    log_callback=log_callback,
                                    kill_ev=kill_ev,
                                    )
                return True
        return False
    
    def delete_map_from_db(self,selected_db,tablename,log_print=True):
        """Deletes the map from the database"""
        fm=self.cma.get_file_map(selected_db) 
        if fm:
            fm.db.create_connection()
            fm.delete_map(tablename,log_print)
    
    def copy_table_from_to_database(self,dbfrom,table_name_from,db_to,table_name_to):
        log.debug("Entered copy_table_from_to_database ")
        try:
            is_ok, _ =self.map_validation(db_to,table_name_to)
            if not is_ok:
                # ensure the name is unique
                table_name_to=self.cma.format_new_table_name("%_"+table_name_to,"")
            (cloned_db,cloned_map)=self.cma.clone_map((dbfrom,table_name_from),db_to,return_pair=True)
            fm=self.cma.get_file_map(cloned_db)
            if isinstance(fm,FileMapper):
                fm.rename_map(cloned_map,table_name_to)
        except Exception as eee:
            log.debug(f"copy_table_from_to_database ->{eee}")
            return False
        self.refresh_map_size_cache()
        return True
    
    def delete_temporal_database(self):
        (temp_db_filepath, temp_table_name)= self.mapping_to_pair
        was_removed=False
        if temp_db_filepath:
            # remove from register lists
            self.cma.remove_database_file(temp_db_filepath)
            # remove from active directory
            (file_exist, is_file)=self.fm.validate_path_file(temp_db_filepath)
            if file_exist and is_file:
                was_removed=self.fm.delete_file(temp_db_filepath)
        return was_removed
   
    def get_map_info_datamanage(self,a_database)->DataManage:
        fm=self.cma.get_file_map(a_database)
        if isinstance(fm,FileMapper):
            table_list=fm.db.get_data_from_table(fm.mapper_reference_table,'*')
            table_list_size=[]
            #field_list=['id','dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype']
            field_list=fm.db.get_column_list_of_table(fm.mapper_reference_table)+['mapsize']
            for table_info in table_list:
                a_map=table_info[4]
                size_tup= self.get_map_size(a_database,a_map)
                if size_tup is not None:
                    (size, shallow_count, calc_count) = size_tup
                    num_rows=f'{size}'
                    if calc_count:
                        num_rows=f'{size}({calc_count})'
                    if shallow_count:
                        num_rows=f'{size}[{shallow_count}]'
                table_list_size.append(table_info+(num_rows,))
            if len(table_list_size)>0:
                data_manage=DataManage(table_list_size,field_list)
                return data_manage
        return None
        
    # -------------------------------------------------------
    # DB Map Size Cache
    # -------------------------------------------------------    

    def refresh_map_size_cache(self):
        """
        Keeps gui_db_map_size_cache information up to date:
        set a size to None to recalculate the size
        gui_db_map_size_cache:
            {
            database1: {map1:(size, shallow_count, calc_count),
                        map2: (size, shallow_count, calc_count),... },
            database2: {map1:(size, shallow_count, calc_count),
                        map2:(size, shallow_count, calc_count),... }, 
            ....}
        """
        for iii, db in enumerate(self.dbm.databases):
            if isinstance(db,DatabaseInfo):
                database=str(db.database_filepath) # pathlib object
                cache_db=self.gui_db_map_size_cache.get(database)
                if not isinstance(cache_db,dict):
                    #add db to cache
                    self.gui_db_map_size_cache[database]={}
                    cache_db=self.gui_db_map_size_cache.get(database)
                if db in self.get_active_databases_in_dbm():
                    map_list=self.get_maps_in_db(database)
                    if isinstance(cache_db,dict):
                        #remove non existing maps from cache
                        for c_map in list(cache_db.keys()):
                            if c_map and c_map not in map_list:
                                cache_db.pop(c_map)
                        # add or refresh sizes
                        for a_map in map_list:
                            if a_map in cache_db:
                                size_val=cache_db[a_map]
                                if size_val is None:
                                    # refresh size
                                    cache_db[a_map] = self._get_sizes_tuple(database,a_map)
                            else:
                                cache_db[a_map] = self._get_sizes_tuple(database,a_map) 
                    else:
                        # add maps and sizes
                        for a_map in map_list:
                            cache_db[a_map] = self._get_sizes_tuple(database,a_map) 
                else:
                    # Remove unactive database from cache
                    if isinstance(cache_db,dict):
                        self.gui_db_map_size_cache.pop(database)

    def _get_sizes_tuple(self,database,a_map):
        """Returns the size tuple for amount of rows in map, rows with shallow, rows with calc

        Args:
            database (str): database
            a_map (str): map

        Returns:
            tuple: (size, shallow_count, calc_count)
        """
        (shallow_count, calc_count)=self.cma.get_shallow_calc_map_count(database,a_map)
        size = self.cma.get_map_size(database,a_map)
        return size, shallow_count, calc_count

    def get_map_size(self,database:str,a_map:str)->(tuple[int] | None):
        """Searches in cache for a size tuple 

         Args:
            database (str): database
            a_map (str): map

        Returns:
            tuple: (size, shallow_count, calc_count) | None
        """
        database=str(database)
        db_cache=self.gui_db_map_size_cache.get(database)
        size_tup = None
        if isinstance(db_cache,dict):
            size_tup=db_cache.get(a_map)
        return size_tup
            


class LoggerWriter(io.TextIOBase):
    def __init__(self, logger:logging.Logger, level=logging.INFO):
        self.logger = logger
        self.level = level
        self.buffer = ""

    def write(self, text):
        self.buffer += text

        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            if line:
                self.logger.log(self.level, line)

        return len(text)

    def flush(self):
        if self.buffer:
            self.logger.log(self.level, self.buffer)
            self.buffer = ""
    
    def isatty(self): #Accept colors from rich
        return True
    
