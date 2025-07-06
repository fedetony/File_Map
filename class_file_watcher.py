"""
File watching functions 
########################
# F.garcia
# creation: 05.02.2025
########################
"""

import os
from datetime import datetime
from rich import print
from class_file_mapper import FileMapper
from class_file_manipulate import FileManipulate
from class_data_manage import DataManage
from class_database_result import DBResult
# from class_backup_actions import BackupActions
# from class_menu_interface import TerminalMenuInterface

# ask_confirmation=TerminalMenuInterface.ask_confirmation

FM=FileManipulate()


class FileWatcher():
    """Class for watching files and paths using mapping functions"""

    def __init__(self):
        files_watch=FM.get_possible_file_list(FM.get_app_path(),"*file_watch*.json")
        self.file_watch_paths=None
        if len(files_watch)>0:
            self.file_watch_paths=files_watch
            self.watch_db_path=FM.extract_path(self.file_watch_paths[0])
            self.watch_db_file=FM.extract_filename(self.file_watch_paths[0],False)+".db"
            self.fm=FileMapper(os.path.join(self.watch_db_path,self.watch_db_file),None,None)
            # self.ba=BackupActions(os.path.join(self.watch_db_path,self.watch_db_file),None,None,ask_confirmation)
        print(self.file_watch_paths)

    def get_watch_tables(self,watch_name:str)->list:
        """Gets a list of tables for the watch_name

        Args:
            watch_name (str): watch

        Returns:
            list: watch table names {watch_name}_FP_{index} for each path in list. 
            Index is congruent to position in "file_list" and "file_list_types" in "watch_name" key.
        """
        db_tables=self.fm.db.tables_in_db()
        watch_tables=[]
        for table_name in db_tables:
            if watch_name+"_FP_" in table_name:
                watch_tables.append(table_name)
        mapped_data=self.fm.db.get_data_from_table(self.fm.mapper_reference_table,'tablename',f"mapname='{watch_name}'")
        for data in mapped_data:
            if data[0] not in watch_tables:
                watch_tables.append(data[0])
        return watch_tables

    @staticmethod
    def get_file_list_types(file_list:list)->list:
        """returns file_list_types 'file','dir','none'

        Args:
            file_list (list): _description_

        Returns:
            list[str]: if exists and is 'file','dir', 'none' if does not exist
        """
        file_list_types=[]
        for f_p_ in file_list:
            file_exist, is_file=FM.validate_path_file(f_p_)
            if file_exist and is_file:
                file_list_types.append('file')
            elif file_exist and not is_file:
                file_list_types.append('dir')
            else:
                file_list_types.append('none')
        return file_list_types

    def make_watch_maps(self,watch_name,file_list,repeat_period_h=24,prompt_if_changed=True,onlymap=True):
        """makes maps for each path/file in file_list in db. If onlymap=False will overwrite the json map with the watch.
            If maps for the same watch exist in db will append the new founded files. 

        Args:
            watch_name (_type_): watch
            file_list (list): list with files or paths to watch
            repeat_period_h (int, optional): set value for checking after, set -1 to check in every run. Defaults to 24.
            prompt_if_changed (bool, optional): when changes are found in a watch prompt. Defaults to True.
            onlymap (bool, optional): When True, generate only in db, else generate in db and in json file. Defaults to True.
        """
        self.fm.map_a_list_of_paths_to_db(watch_name,file_list,True,None,False,False)
        watch_tables=self.get_watch_tables(watch_name)
        watch_dict={}
        file_list_types=self.get_file_list_types(file_list)    
        for watch in watch_tables:
        # self.fm.get_mapping_info_data_from_file(
            # id=0	'dt_map_created'=1	'dt_map_modified'=2	'mappath'=3	'tablename'=4	'mount'=5	'serial'=6	'mapname'=7	'maptype'=8
            map_data=self.fm.db.get_data_from_table(self.fm.mapper_reference_table,'*',f"tablename='{watch}'")
            self.fm.db.edit_value_in_table(self.fm.mapper_reference_table,map_data[0][0],'mapname',watch_name)
            self.fm.db.edit_value_in_table(self.fm.mapper_reference_table,map_data[0][0],'maptype','watch_filepath')
            if onlymap:
                continue # just make the maps
            number_of_watched_files=self.fm.db.get_number_or_rows_in_table(watch)
            # id=0	dt_data_created'=1	'dt_data_modified'=2	'filepath'=3	'filename'=4	'md5'=5	'size'=6
            # 'dt_file_created'=7	'dt_file_accessed'=8	'dt_file_modified'=9
            field_list = self.fm.db.get_column_list_of_table(watch)
            watch_data=self.fm.db.get_data_from_table(watch,'*',None)
            d_m1 = DataManage(watch_data, field_list)
            df=d_m1.get_selected_df(field_list,None,True)    
            aaa={f"{watch_name}":{
                "file_list":file_list,
                "file_list_types":file_list_types,
                "event_list":[] #[["dt","what changed md5"],["dt2","md5"]]
            },
                f"{watch}":{
                "watch_index":int(str(watch).replace(watch_name+"_FP_","")),
                "prompt_if_changed": prompt_if_changed,
                "repeat_period_h": repeat_period_h,
                "filename":df['filename'].to_list(),
                "filepath":df['filename'].to_list(),
                "mappath":map_data[0][3],
                "serial":map_data[0][6],
                "mount":map_data[0][5],
                "md5":df['md5'].to_list(),
                "size":df['size'].to_list(),
                "dt_watch_created":map_data[0][1],
                "dt_watch_modified":map_data[0][2],
                "number_of_watched_files":number_of_watched_files,
                "dt_file_c":df['dt_file_created'].to_list(),
                "dt_file_a":df['dt_file_modified'].to_list(),
                "dt_file_m":df['dt_file_accessed'].to_list(),
                "has_changed":False,
                }}
            watch_dict.update(aaa)
        if not onlymap:
            FM.save_dict_to_json(self.file_watch_paths[0],watch_dict)
    
    def get_watch_active_paths(self,watch_name,log_print=False):
        """gets list active_watch_paths,active_watch_index,for active maps 
            file_list with the correct mount if mount has changed

        Args:
            watch_name (str): watch
            log_print (bool, optional): print not found device. Defaults to False.

        Returns:
            tuple: active_watch_paths,active_watch_index,file_list.
            active_watch_paths->list of paths found active.
            file_list-> 
            active_watch_index contins the index in watch table names {watch_name}_FP_{index}. 
            Index is congruent to position in "file_list".
        """
        watch_tables=self.get_watch_tables(watch_name)
        if len(watch_tables)==0:
            return [],[]
        watch_dict=FM.load_dict_to_json(self.file_watch_paths[0])
        file_list=self.get_item_watch_dict(watch_dict,watch_name,'file_list')
        active_watch_paths=[]
        active_watch_index=[]
        for watch in watch_tables:
            # id=0	'dt_map_created'=1	'dt_map_modified'=2	'mappath'=3	'tablename'=4	'mount'=5	'serial'=6	'mapname'=7	'maptype'=8
            map_data=self.fm.db.get_data_from_table(self.fm.mapper_reference_table,'*',f"tablename='{watch}'")
            watch_index=self.get_item_watch_dict(watch_dict,watch,'watch_index')
            old_mount,f_p_nm=FM.split_filepath_and_mountpoint(file_list[watch_index])
            file_exist, _=FM.validate_path_file(file_list[watch_index])
            if file_exist:
                active_watch_paths.append(os.path.join(old_mount,f_p_nm))
                file_list[watch_index]=os.path.join(old_mount,f_p_nm)
                active_watch_index.append(watch_index)
                continue
            mount, mount_active, mappath_exists = self.fm.check_if_map_device_active(self.fm.db,watch,False)
            if not mount_active:
                if log_print:
                    print(f"Device with serial {map_data[0][6]} is not active!")
                continue
            if not mappath_exists:
                continue
            
            # f_p_nm=self.fm.remove_mount_from_path(file_list[watch_index])
            active_watch_paths.append(os.path.join(mount,f_p_nm))
            file_list[watch_index]=os.path.join(mount,f_p_nm)
            active_watch_index.append(watch_index)
        return active_watch_paths,active_watch_index,file_list

    def remove_watch_from_db(self,watch_name):
        """removes all tables in database for a watch

        Args:
            watch_name (str): watch name
        """
        watch_tables=self.get_watch_tables(watch_name)
        if len(watch_tables)==0:
            return
        for watch_table in watch_tables:
            self.fm.delete_map(watch_table)

    def run_watch_comparison(self,watch_name,onlymap=False):
        """makes a check map of the watched files, compares the files with the check maps and sets events if changes found. 
           Removes the check map before exit.

        Args:
            watch_name (str): watch name
        """
        watch_tables=self.get_watch_tables(watch_name)
        if len(watch_tables)==0:
            return
        watch_dict=FM.load_dict_to_json(self.file_watch_paths[0])
        active_watch_paths,active_watch_index,file_list=self.get_watch_active_paths(watch_name)
        # create check tables
        watch_name_check=watch_name+"_check"
        self.make_watch_maps(watch_name_check,file_list,-1,None,True)
        watch_check_tables=self.get_watch_tables(watch_name_check)
        for watch,watch_ch in zip(watch_tables,watch_check_tables):
            # id=0	'dt_map_created'=1	'dt_map_modified'=2	'mappath'=3	'tablename'=4	'mount'=5	'serial'=6	'mapname'=7	'maptype'=8
            map_data=self.fm.db.get_data_from_table(self.fm.mapper_reference_table,'*',f"tablename='{watch}'")
            watch_index=self.get_item_watch_dict(watch_dict,watch,'watch_index')
            active_fp=None
            for awi,a_path in zip(active_watch_index,active_watch_paths):
                if watch_index == awi:
                    active_fp=a_path
                    break
            if active_fp:
                mount,_=FM.split_filepath_and_mountpoint(active_fp)
                mount_active=True
                mappath_exists=True
            else:
                mount, mount_active, mappath_exists = self.fm.check_if_map_device_active(self.fm.db,watch,False)
            if not mount_active:
                print(f"Device with serial {map_data[0][6]} is not active!")
                continue
            if not mappath_exists:
                print(f"[magenta]Path {os.path.join(mount,map_data[0][3])} does not Exist!")
                watch_dict=self.add_event_to_watch_dict(watch_dict,watch_name,[str(datetime.now()),watch,'filepath','main path not_found|deleted|moved'])
                watch_dict=self.set_item_watch_dict(watch_dict,watch,'has_changed',True)
                if not FM.save_dict_to_json(self.file_watch_paths[0],watch_dict):
                    print(f'[red]Error: {self.file_watch_paths[0]} could not be saved!')
                continue
            
            if watch_index not in active_watch_index:
                continue
            # number_of_watched_files=self.fm.db.get_number_or_rows_in_table(watch)
            # field_list = self.fm.db.get_column_list_of_table(watch)
            # watch_data=self.fm.db.get_data_from_table(watch,'*',None)
            # # d_m1 = DataManage(watch_data, field_list)
            # # df=d_m1.get_selected_df(field_list,None,True)
            db_result = DBResult(self.fm.db.describe_table_in_db(watch))
            db_result.set_values(self.fm.db.get_data_from_table(watch, "*",None))
            db_result_ch = DBResult(self.fm.db.describe_table_in_db(watch_ch))
            db_result_ch.set_values(self.fm.db.get_data_from_table(watch_ch, "*",None))
            if len(db_result.dbr) > 0:            
                # # id=0	dt_data_created'=1	'dt_data_modified'=2	'filepath'=3	'filename'=4	'md5'=5	'size'=6
                 # # 'dt_file_created'=7	'dt_file_accessed'=8	'dt_file_modified'=9
                for dbr,dbr_ch in zip(db_result.dbr,db_result_ch.dbr):
                    comp_dict=db_result.compare_nodes(dbr,dbr_ch,'==')
                    print(comp_dict)
                    has_changed=False
                    if not comp_dict['dt_file_created']:
                        watch_dict=self.add_event_to_watch_dict(watch_dict,watch_name,[str(datetime.now()),watch,'dt_file_created',f'{dbr.filename} replaced'])
                        watch_dict=self.set_item_watch_dict(watch_dict,watch,'has_changed',True)
                        has_changed=True
                    if not comp_dict['dt_file_modified']:
                        watch_dict=self.add_event_to_watch_dict(watch_dict,watch_name,[str(datetime.now()),watch,'dt_file_modified',f'{dbr.filename} exchanged'])
                        watch_dict=self.set_item_watch_dict(watch_dict,watch,'has_changed',True)    
                        has_changed=True
                    if not comp_dict['filename'] and comp_dict['md5']:
                        watch_dict=self.add_event_to_watch_dict(watch_dict,watch_name,[str(datetime.now()),watch,'filename',f'{dbr.filename} renamed'])
                        watch_dict=self.set_item_watch_dict(watch_dict,watch,'has_changed',True) 
                        has_changed=True
                    if not comp_dict['md5']:
                        watch_dict=self.add_event_to_watch_dict(watch_dict,watch_name,[str(datetime.now()),watch,'md5', f'{dbr.filename} content'])
                        watch_dict=self.set_item_watch_dict(watch_dict,watch,'has_changed',True)    
                        has_changed=True
                    if not comp_dict['size'] and comp_dict['md5']:
                        watch_dict=self.add_event_to_watch_dict(watch_dict,watch_name,[str(datetime.now()),watch,'size',f'{dbr.filename} resized'])
                        watch_dict=self.set_item_watch_dict(watch_dict,watch,'has_changed',True) 
                        has_changed=True
                    if not comp_dict['filepath']:
                        watch_dict=self.add_event_to_watch_dict(watch_dict,watch_name,[str(datetime.now()),watch,'filepath',f'{dbr.filepath} deleted|moved'])
                        watch_dict=self.set_item_watch_dict(watch_dict,watch,'has_changed',True) 
                        has_changed=True
                    if has_changed and not onlymap:
                        if not FM.save_dict_to_json(self.file_watch_paths[0],watch_dict):
                            print(f'[red]Error: {self.file_watch_paths[0]} could not be saved!')
                    # file_info=self.fm.get_mapping_info_data_from_file(mount,dbr.filepath,dbr.filename,False,"",False)
                    # if dbr.tablename == table_name:
                    #     table_indexed = True
                    #     an_id = dbr.id
                    #     breaks
            # Need to have a file_list and db to be in active_databases to use -> will show in mapping :S
            # self.ba.deep_compare((self.fm.db_file,watch),(self.fm.db_path_file,watch_ch),None,None,True)
        print(f"Events: {self.get_item_watch_dict(watch_dict,watch_name,'event_list')}")

        
        
        # remove check tables
        self.remove_watch_from_db(watch_name_check)
    
    @staticmethod
    def add_event_to_watch_dict(watch_dict:dict,watch_name:str,new_event:list)->dict:
        """Adds event to the dictionary

        Args:
            watch_name (str): name
            watch_dict (dict): dictionary with watch information
            new_event (list): event list with changes of file/dict

        Returns:
            dict: watch_dict with added event
        """
        if watch_name in watch_dict.keys():
            event_list=watch_dict[f"{watch_name}"]["event_list"]
            if isinstance(event_list,list):
                event_list.append(new_event)
                watch_dict[f"{watch_name}"].update({"event_list":event_list})
        return watch_dict
    
    @staticmethod
    def _reset_events_in_watch_dict(watch_dict:dict,watch_name:str)->dict:
        """Resets the event_list on the dictionary"""
        if watch_name in watch_dict.keys():
            watch_dict[f"{watch_name}"]["event_list"]=[]
        return watch_dict
    
    def reset_events(self,watch_name:str):
        """Resets the event_list on the json file

        Args:
            watch_name (str): watch events to be reset
        """
        watch_tables=self.get_watch_tables(watch_name)
        if len(watch_tables)==0:
            return
        watch_dict=FM.load_dict_to_json(self.file_watch_paths[0])
        self._reset_events_in_watch_dict(watch_dict,watch_name)
        if not FM.save_dict_to_json(self.file_watch_paths[0],watch_dict):
            print(f'[red]Error: {self.file_watch_paths[0]} could not be saved!')


    @staticmethod
    def set_item_watch_dict(watch_dict:dict,watch:str,item:str,new_value)->dict:
        """Edits an item value on the watch dictionary

        Args:
            watch (str): watch to change item
            item (str): item in watch: prompt_if_changed,
            repeat_period_h ,filename, filepath, mappath ,serial ,mount ,md5 ,size ,dt_watch_created ,dt_watch_modified,
            number_of_watched_files ,dt_file_c ,dt_file_a ,dt_file_m ,has_changed
            watch_dict (dict): watch dictionary
            new_value (any): new value

        Returns:
            dict: modified watch_dict
        """
        if watch in watch_dict.keys():
            wd=watch_dict[watch]
            if isinstance(wd,dict):
                if item in wd.keys():
                    watch_dict[watch].update({item:new_value})
        return watch_dict
    
    @staticmethod
    def get_item_watch_dict(watch_dict:dict,watch:str,item:str):
        """gets an item value on the watch dictionary

        Args:
            watch (str): watch to change item
            item (str): item in watch: prompt_if_changed,
            repeat_period_h ,filename, filepath, mappath ,serial ,mount ,md5 ,size ,dt_watch_created ,dt_watch_modified,
            number_of_watched_files ,dt_file_c ,dt_file_a ,dt_file_m ,has_changed
            watch_dict (dict): watch dictionary
            

        Returns:
            any: value
        """
        if watch in watch_dict.keys():
            wd=watch_dict[watch]
            if isinstance(wd,dict):
                if item in wd.keys():
                    return wd[item]
        return None


# Example usage
if __name__ == "__main__":
    FW=FileWatcher()
    file_list=['D:\\test\\TestodePrueba.txt','D:\\test']
    # FW.make_watch_maps("watch_test",file_list,24,True,False)
    FW.reset_events("watch_test")
    FW.run_watch_comparison("watch_test")
    