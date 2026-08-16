# FileMap Cli Manager
import io
import logging
from typing import Callable, Any
from contextlib import redirect_stdout
from datetime import datetime

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

    def Create_new_filemap_database(self,database_filepath, 
                    ask_for_pwd=False, log_callback=None)->str:
        """Creates a valid database with referencemap based on the selected_db and table_name. 
            Both used to have a temporary folder with prefix="__filemap__",suffix=table_name
            and database_name: selected_db +"_temp.db"

        Args:
            
            log_callback (_type_, optional): logging callback to log print. Defaults to None.

        Returns:
            str: database filepath
        """
        # if you wanted encrypted call
        if ask_for_pwd:
            self.cma.create_filemap_database(database_filepath) #this asks for pwd
            fm = self.cma.get_file_map(database_filepath)
        else:
            fm=FileMapper(database_filepath,None,None,False) 
            if not isinstance(fm,FileMapper):
                if log_callback:
                    log_callback(f"[red]Error creating database @ {database_filepath}")
                return None
            self.cma.file_list.append(database_filepath)
            self.cma.password_list.append(None)
            self.cma.key_list.append(None)
        self.cma.activate_databases(database_filepath)
        if log_callback:
            log_callback(f"[yellow]Created database @ {database_filepath}")
        # Add dummy table to generate a reference index map
        table_name="dummy"
        temp_folder=FM.extract_path(database_filepath)
        temp_table_name=self.cma.format_new_table_name("___"+self._get_timestamp()+"___"+table_name,temp_folder)
        was_indexed=fm.add_table_to_mapper_index(temp_table_name,temp_folder,None)
        if was_indexed:
            if log_callback:
                log_callback(f"[green]Valid index {fm.db.table_exists(fm.mapper_reference_table)}")
            fm.delete_map(temp_table_name)
            self.cma.deactivate_databases(database_filepath)
            return database_filepath
        return None

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
    def rename_map(self,database,a_map,new_mapename):
        selected_db=database
        map_list=self.cma.get_maps_in_db(selected_db)
        if len(map_list)==0:
            log.warning('[yellow] No maps to rename!')
            return False
        if a_map not in map_list:
            log.warning(f'[yellow]{a_map} is not in database!')
            return False
        info_txt=self.cma.get_map_info_text(selected_db,a_map)    
        fm=self.cma.get_file_map(selected_db)
        if not fm:
            return False
        data=fm.db.get_data_from_table(fm.mapper_reference_table,'*',f"tablename='{a_map}'")
        #field_list=['id','dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype']
        path_to_map=os.path.join(data[0][5],data[0][3])
        new_tablename=self.cma.format_new_table_name(new_mapename,path_to_map)
        is_ok,msg=self.map_validation(database,new_tablename)
        if not is_ok:
            log.warning(msg)
            return False
        fm.db.create_connection()
        log.info(f'Renaming Map [yellow]"{a_map}"[/yellow] to [green]"{new_tablename}"')
        was_renamed=fm.rename_map(a_map,new_tablename)
        if was_renamed:
            log.info(f'Renaming success to [green]"{new_tablename}"')
            return True
        log.warning(f'Renaming Failed [red]"{a_map}"')
        return False


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
        """Returns a list of maps in the database"""
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
            if not isinstance(fm,FileMapper):
                if log_callback:
                    log_callback(f"[red]Error creating database @ {temp_db_filepath}")
                return False
            self.cma.file_list.append(temp_db_filepath)
            self.cma.password_list.append(None)
            self.cma.key_list.append(None)
            self.cma.activate_databases(temp_db_filepath)
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
    
    def _create_temporal_database(self,selected_db,table_name,log_callback=None)->str:
        """Creates a temporal database based on the selected_db and table_name. 
            Both used to have a temporary folder with prefix="__filemap__",suffix=table_name
            and database_name: selected_db +"_temp.db"

        Args:
            selected_db (str): reference db_name
            table_name (str): reference table_name
            log_callback (_type_, optional): logging callback to log print. Defaults to None.

        Returns:
            str: temporary database filepath
        """
        temp_folder=FM.get_temp_directory_path(prefix="__filemap__",suffix=table_name)
        temp_db=FM.extract_filename(selected_db,False)+"_temp.db"
        
        temp_db_filepath=os.path.join(temp_folder,temp_db)
        # if you wanted encrypted call
        # self.cma.create_filemap_database(temp_db_filepath) #this asks for pwd

        # creates new database and assigns mapper
        fm=FileMapper(temp_db_filepath,None,None,False) 
        if not isinstance(fm,FileMapper):
            if log_callback:
                log_callback(f"[red]Error creating database @ {temp_db_filepath}")
            return None
        self.cma.file_list.append(temp_db_filepath)
        self.cma.password_list.append(None)
        self.cma.key_list.append(None)
        self.cma.activate_databases(temp_db_filepath)
        if log_callback:
            log_callback(f"[yellow]Created temporary database @ {temp_db_filepath}")
        temp_table_name=self.cma.format_new_table_name(
            "___"+self._get_timestamp()+"__"+table_name,temp_folder)
        was_indexed=fm.add_table_to_mapper_index(temp_table_name,temp_folder,None)
        if was_indexed:
            if log_callback:
                log_callback("[green]Valid index")
        else: 
            return None
        if log_callback:
            log_callback(f"[yellow]Has reference table: {fm.db.table_exists(fm.mapper_reference_table)}")
        return temp_db_filepath
            
    def deepen_shallow_map(self,database,
                        table_name: str,
                        path_to_map: str,
                        progress_bar: Callable | None = None,
                        press_to_continue: bool = False,
                        log_callback: Callable | None = None,
                        kill_ev: threading.Event | None = None
                        ):
        """Menu for Shallow Compare two maps 

        Returns: 
            (is_ok, is_finished, can_replace)"""
        is_ok = False
        is_finished = False
        can_replace = False
        if not database or not table_name:
            return is_ok, is_finished, can_replace
        db_map_pair=(database,table_name)
        if log_callback:
            log_callback(f'Converting {db_map_pair[1]} for calculation...')
        self.cma.shallow_to_deep(db_map_pair,None,progress_bar,kill_ev=kill_ev)
        if kill_ev.is_set():
            log_callback('[yellow]Conversion Cancelled...')
            return is_ok, is_finished, can_replace
        if log_callback:
            log_callback(f'Conversion Finished for {db_map_pair[1]}')
        fm=self.cma.get_file_map(db_map_pair[0])
        if not fm:
            return is_ok, is_finished, can_replace
        data=fm.db.get_data_from_table(db_map_pair[1],'COUNT(*)',f'md5="{MD5_CALC}"')
        if len(data)==0 or data[0][0]==0:
            is_ok=True 
            is_finished=True
            if log_callback:
                log_callback("[green]"+"*"*15+" NOTHING TO DO "+"*"*15)
                log_callback(f"[green]All files in {db_map_pair[1]} are already Mapped")
                log_callback("[green]"+"*"*45)
                return is_ok, is_finished, can_replace
        if log_callback:
            log_callback(f"[magenta]Deepening {data[0][0]} shallow files in {db_map_pair[1]}!")
        # Create temporal database
        temp_db_filepath=self._create_temporal_database(db_map_pair[0],db_map_pair[1],log_callback=log_callback)
        temp_table_name=self.cma.format_new_table_name(table_name,path_to_map)
        is_ok,msg=self.map_validation(temp_db_filepath,temp_table_name)
        if  is_ok:  
            self.mapping_to_pair=(temp_db_filepath, temp_table_name)
            temp_map_pair = self.mapping_to_pair
            fm_temp = self.cma.get_file_map(temp_map_pair[0])
            # fm_temp.add_table_to_mapper_index(temp_map_pair,)

            if log_callback:
                log_callback(f"[yellow]Created temporary Map {temp_table_name}")
            
            if log_callback:
                log_callback(f"[yellow]Copying map to temporary database: {db_map_pair[1]} -> {temp_map_pair[1]}")
            was_copied=self.copy_table_from_to_database(db_map_pair[0],db_map_pair[1],
                                             temp_map_pair[0],temp_map_pair[1],log_callback)
            if not was_copied:
                if log_callback:
                    log_callback(f"[red]Error copying table {db_map_pair[1]} to {temp_map_pair[1]}")
                return False, False, False
            
            if log_callback:
                log_callback(f"[cyan]Starting Deep calculation @ {temp_map_pair[1]}")

                log_callback(f"Debug -> Ref table of {fm_temp.db_path_file}:")
                log_callback(f"{fm_temp.db.get_data_from_table(fm_temp.mapper_reference_table)}")
                
                log_callback(f"[cyan]Debug -> Table Exists {fm_temp.db.table_exists(temp_map_pair[1])}")
                log_callback(f"[cyan]Debug -> {fm_temp.check_if_map_device_active(fm_temp.db,temp_map_pair[1],False)}")
            msg = fm_temp.remap_map_in_thread_to_db(table_name = temp_map_pair[1],
                                            progress_bar = progress_bar,
                                            wait_for_key_press = press_to_continue,
                                            log_callback = log_callback,
                                            kill_ev = kill_ev)
            is_ok=True 
            if msg: 
                if log_callback:
                    log_callback(f"[magenta]{msg}")
                is_finished = False
            else:
                if log_callback:
                    log_callback("[green]Successfuly Finished deepening!")
                is_finished = not kill_ev.is_set()

            can_replace = True
            return is_ok, is_finished, can_replace
            # # copy back to db in worker
            
        return False, False, False
    
    def replace_map_from_temporal_db(self, to_db_map_pair, log_callback=None):
        """Replace a map in the target database with a temporary map."""

        target_db, target_map = to_db_map_pair
        source_db, source_map = self.mapping_to_pair

        fm = self.cma.get_file_map(target_db)
        if not fm:
            if log_callback:
                log_callback(f"[red]Inactive Database {target_db}[/red]")
            return False

        map_list = self.cma.get_maps_in_db(target_db)
        if target_map not in map_list:
            if log_callback:
                log_callback(
                    f"[red]Map {target_map} is not in "
                    f"database {target_db}[/red]"
                )
            return False

        # Copy source map into target DB under a temporary name        
        temp_name = self.cma.format_new_table_name(
            self._get_timestamp()+"_" + source_map,"")

        can_replace = self.copy_table_from_to_database(
            source_db, source_map,
            target_db, temp_name, log_callback )

        if not can_replace:
            if log_callback:
                log_callback(
                    f"[red]Error copying temporary table "
                    f"{source_map} to {target_db}[/red]"
                )
            return False
        
        # Rename existing target map out of the way
        temp_original_name = self.cma.format_new_table_name(
            self._get_timestamp()+"_" + target_map,"")
        was_original_renamed = self.rename_map(
            target_db, target_map, temp_original_name)

        if not was_original_renamed:
            # The new temporary table exists but the original
            # table was not renamed. Clean up the temporary table.
            self.delete_map_from_db(target_db, temp_name)

            if log_callback:
                log_callback(
                    f"[red]Could not rename original map {target_map}[/red]")
            return False
        # Rename new temporary map to the real map name
        was_temp_renamed = self.rename_map(target_db, temp_name, target_map)

        if not was_temp_renamed:
            # Try to restore the original map.
            restored = self.rename_map(target_db, temp_original_name, target_map)

            if log_callback:
                if restored:
                    log_callback(
                        f"[yellow]Could not install new map. "
                        f"Original map {target_map} was restored.[/yellow]"
                    )
                else:
                    log_callback(
                        f"[red]CRITICAL: Could not install new map "
                        f"or restore original map {target_map}.[/red]"
                    )
            return False
        # New map is now active. Remove old map.
        deleted = self.delete_map_from_db(target_db, temp_original_name)
        if not deleted:
            if log_callback:
                log_callback(
                    f"[yellow]Map {target_map} was replaced, "
                    f"but the old map could not be deleted: "
                    f"{temp_original_name}[/yellow]"
                )

            # Replacement itself succeeded.
            self._clear_map_size(target_db, target_map)
            return True
        
        # Success
        self._clear_map_size(target_db, target_map)

        return True
    
    def get_full_mount_path_of_map(self,database,a_map):
        try:
            map_info=self.cma.get_map_info(database,a_map)
            # mount= 5 mappath = 3
            mount_path_of_map=os.path.join(map_info[0][5],map_info[0][3])
            return mount_path_of_map
        except:
            pass
        return ""
        
    
    def delete_map_from_db(self,selected_db,tablename,log_print=True):
        """Deletes the map from the database"""
        fm=self.cma.get_file_map(selected_db) 
        if fm:
            fm.db.create_connection()
            fm.delete_map(tablename,log_print)
    
    def copy_table_from_to_database(self,db_from, table_name_from, db_to, table_name_to,log_callback=None):
        if log_callback:
            log_callback("Entered copy_table_from_to_database ")
            log_callback(f"    From {self.fm.extract_filename(db_from)}, {table_name_from}")
            log_callback(f"    To   {self.fm.extract_filename(db_to)}, {table_name_to}")
        try:
            is_ok, _ =self.map_validation(db_to,table_name_to)
            if not is_ok:
                # ensure the name is unique
                table_name_to=self.cma.format_new_table_name(
                    self._get_timestamp()+"_"+table_name_to,"")
            if log_callback:
                log_callback("Cloning...")
            self.cma.activate_databases(db_to)
            self.cma.activate_databases(db_from)
            (cloned_db,cloned_map)=self.cma.clone_map((db_from,table_name_from),db_to,return_pair=True)
            if cloned_db is None or cloned_map is None:
                msg=self.cma.clone_map((db_from,table_name_from),db_to,return_pair=False)
                if log_callback:
                    log_callback("[red]Error Cloning ..")    
                    log_callback(f"[red]{msg}")    
                return False
            fm=self.cma.get_file_map(cloned_db)
            if log_callback:
                log_callback("Cloned Finished..")
            if isinstance(fm,FileMapper):
                fm.rename_map(cloned_map,table_name_to)
        except Exception as eee:
            if log_callback:
                log_callback(f"[red]Error copy_table_from_to_database -> {eee}")
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
    
    def _clear_map_size(self,database:str,a_map:str):
        """Searches in cache for a size tuple 
            sets it to None if found
        """
        database=str(database)
        db_cache=self.gui_db_map_size_cache.get(database)
        db_cache[a_map] = None
    
    @staticmethod
    def _get_timestamp():
        return datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            


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
    
