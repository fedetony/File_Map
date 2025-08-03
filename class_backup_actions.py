

#!/usr/bin/env python  # shebang for Unix-based systems
#!pythonw        # shebang for Windows systems
from __future__ import print_function, unicode_literals

import os
# import getpass

# from datetime import datetime
from rich import print

from class_mapping_actions import *
# from class_file_manipulate import FileManipulate
from class_file_mapper import *
# from class_data_manage import DataManage
# from class_file_explorer import *
from class_dataframe_compare import DataFrameCompare


#F_M=FileManipulate()

class BackupActions():
    def __init__(self,file_list:list,password_list:list,key_list:list,ask_confirmation):
        
        self.ask_confirmation=ask_confirmation
        self.file_list=file_list
        self.password_list=password_list
        self.key_list=key_list
        self.cma=MappingActions(file_list,password_list,key_list,self.ask_confirmation)

    @staticmethod
    def _get_file_info(src_item):
        """File information on item"""
        return (F_M.extract_filename(src_item),F_M.get_file_size(src_item),F_M.get_accessed_date(src_item),F_M.get_modified_date(src_item),F_M.get_created_date(src_item))
        
    def map_to_backup(self,db_map_pair,end_path,shallow=True,where=None,keep_changed=None,keep_removed=None):
        """ If end_path exists and has information then Makes actual map of end path.
            Compares with Map, Additions are added, Substractions are renamed.
        """
        scr_is_active,scr_mount = self.verify_map_device_active(db_map_pair)
        if not scr_is_active or not scr_mount:
            return "[red] Source Device not available!"
        path_has_info, _ = self.verify_path_has_information(end_path)

        if not path_has_info:
            map_info=self.cma.get_map_info(db_map_pair[0],db_map_pair[1])
            # id=0	'dt_map_created'=1	'dt_map_modified'=2	'mappath'=3	'tablename'=4	'mount'=5	'serial'=6	'mapname'=7	'maptype'=8
            scr_folder=os.path.join(scr_mount,map_info[0][3])
            print(f"Copying information from {scr_folder} to {end_path}")
            was_copied=F_M.copy_folder(scr_folder,end_path,True)
            if was_copied and self.ask_confirmation("Do you want to map the new Backup?",True):
                tablename=self.cma.format_new_table_name("%!",db_map_pair[1])
                fm=self.cma.get_file_map(db_map_pair[0])
                return fm.map_a_path_to_db(tablename,end_path,True,shallow_map=shallow)
            return "" 
        if keep_changed is None:
            keep_changed=self.ask_confirmation(f"Would you like to {A_C.add_ansi('keep changed files','yellow')}?",True)
        if keep_removed is None:
            keep_removed=self.ask_confirmation(f"Would you like to {A_C.add_ansi('keep old deleted files','yellow')}?",True)
        return self.map_existing_path_compare_do_action(db_map_pair,end_path,keep_changed,keep_removed,shallow,where)
    
    def verify_map_device_active(self,db_map_pair):
        """Verifies the device availability
        """
        fm=self.cma.get_file_map(db_map_pair[0])
        mount, mount_active, mappath_exists =fm.check_if_map_device_active(fm.db,db_map_pair[1],True)
        if mount_active and mappath_exists:
            return True, mount
        return False, None
    
    def verify_path_has_information(self,end_path):
        """Verifies the path has files or folders
        """
        path_has_info=False
        fs=None
        if os.path.exists(end_path):
            print("Analyzing end path")
            fs=F_M.get_file_structure_from_active_path(end_path,'Backup',{},True,self._get_file_info,True)
            if len(fs['Backup'])>0:
                path_has_info=True
                print(f"Path {end_path} has information!")
        return path_has_info, fs

    def selection_map_to_backup(self,db_map_pair,end_path,shallow=True,where=None,keep_changed=None,keep_removed=None):
        """ If end_path exists and has information then Makes actual map of end path.
            Compares with Map, Additions are added, Substractions are renamed.
        """
        scr_is_active,scr_mount = self.verify_map_device_active(db_map_pair)
        if not scr_is_active or not scr_mount:
            return "[red] Source Device not available!"
        path_has_info, fs = self.verify_path_has_information(end_path)
        fm=self.cma.get_file_map(db_map_pair[0])
        if not path_has_info:
            map_info=self.cma.get_map_info(db_map_pair[0],db_map_pair[1])
            scr_folder=os.path.join(scr_mount,map_info[0][3])
            # id=0	'dt_map_created'=1	'dt_map_modified'=2	'mappath'=3	'tablename'=4	'mount'=5	'serial'=6	'mapname'=7	'maptype'=8
            data_list=fm.db.get_data_from_table(db_map_pair[1],"*",where)
            if len(data_list)==0:
                return "No data to backup"
            field_list=fm.db.get_column_list_of_table(db_map_pair[1])
            dm=DataManage(data_list,field_list)
            print(f"Copying information from {scr_folder} to {end_path}")
            was_copied=False
            for iii,(filepath,filename) in enumerate(zip(dm.df['filepath'],dm.df['filename'])):
                scr_file = os.path.join(scr_mount,filepath,filename)
                end_file = scr_file.replace(scr_folder,end_path)
                if F_M.copy_file(scr_file,end_file):
                    print(f"{iii} [green]Copied {end_file}[/green] ")
                else:
                    print(f"{iii} [red]Could not copy {scr_file}[/red] ")
            if was_copied and self.ask_confirmation("Do you want to map the new Backup?",True):
                tablename=self.cma.format_new_table_name("%!",db_map_pair[1])
                fm=self.cma.get_file_map(db_map_pair[0])
                suc_msg=fm.map_a_path_to_db(tablename,end_path,True,shallow_map=shallow)
                return suc_msg
            return ""
        if keep_changed is None:
            keep_changed=self.ask_confirmation(f"Would you like to {A_C.add_ansi('keep changed files','yellow')}?",True)
        if keep_removed is None:
            keep_removed=self.ask_confirmation(f"Would you like to {A_C.add_ansi('keep old deleted files','yellow')}?",True)
        return self.map_existing_path_compare_do_action(db_map_pair,end_path,keep_changed,keep_removed,shallow,where)
        
    def backup_compare(self,db_map_pair,where=None):
        """Maps actual base path and compares with backup map"""
        shallow=False # map needs md5 to calculate actions
        scr_is_active,scr_mount = self.verify_map_device_active(db_map_pair)
        if not scr_is_active or not scr_mount:
            return "[red] Source Device not available!"
        map_info=self.cma.get_map_info(db_map_pair[0],db_map_pair[1])
        scr_folder=os.path.join(scr_mount,map_info[0][3])
        fm=self.cma.get_file_map(db_map_pair[0])
        fm.db.create_connection()
        tablename=self.cma.format_new_table_name("%_!",db_map_pair[1])
        suc_msg=fm.map_a_path_to_db(tablename,scr_folder,True,shallow_map=shallow,press_to_continue=False)
        if fm.db.table_exists(tablename) and "Successfully" in suc_msg:
            # [end_mount,end_path_nm]=F_M.split_filepath_and_mountpoint(end_path)
            db_map_pair_1=(db_map_pair[0],tablename)
            db_map_pair_2=db_map_pair
            str_actions,_=self.deep_compare(db_map_pair_1,db_map_pair_2,where,where,show_as_action=False)
            print(str_actions)
            if not self.ask_confirmation(f"Do you want to {A_C.add_ansi(f'keep {tablename} map','cyan')}?",False):
                fm.delete_map(tablename,True)
    
    def deep_compare(self,db_map_pair_1,db_map_pair_2,where1,where2,show_as_action=False):
        """Makes a deep comparison of the maps"""
        _,action_dict=self.identify_differences(db_map_pair_1,db_map_pair_2,where1,where2)
        # (index=0, db_map_pair=1, (mappath,mount)=2, identification=3,'+/-'=4, data=5)
        str_actions=self.show_actions(action_dict,True,True,show_as_action)
        return str_actions,action_dict

    def map_existing_path_compare_do_action(self,db_map_pair,end_path,keep_changed,keep_removed,shallow,where=None):
        """Makes a map of end_path, compares to map in db map pair and performs actions on differences

        Args:
            db_map_pair (tuple): database map pair
            end_path (str): path to make backup
            keep_changed (bool): _description_
            keep_removed (bool): _description_
            shallow (bool): _description_
            where (str, optional): map filter. Defaults to None.
        """
         # make new map of end path
        fm=self.cma.get_file_map(db_map_pair[0])
        fm.db.create_connection()
        tablename=self.cma.format_new_table_name("%!",db_map_pair[1])
        suc_msg=fm.map_a_path_to_db(tablename,end_path,True,shallow_map=shallow,press_to_continue=False)
        if fm.db.table_exists(tablename) and "Successfully" in suc_msg:
            # [end_mount,end_path_nm]=F_M.split_filepath_and_mountpoint(end_path)
            db_map_pair_1=(db_map_pair[0],tablename)
            db_map_pair_2=db_map_pair
            str_actions,action_dict=self.deep_compare(db_map_pair_1,db_map_pair_2,where,where,show_as_action=True)
            
            print('*'*33+'FILE ACTIONS'+'*'*33)
            print('*'*33+'************'+'*'*33)
            print(f"[yellow] Following actions will be performed:[/yellow]\n{str_actions}")
            
            if self.ask_confirmation(f"Do you want to {A_C.add_ansi('do actions','cyan')}?",False):
                if not self.do_actions(action_dict,keep_changed,keep_removed):
                    suc_msg="Not all actions were performed!!" 
            # if not self.ask_confirmation(f"Do you want {A_C.add_ansi('to keep',
            # 'cyan')} the Backup Map {A_C.add_ansi(tablename,'yellow')}?",True):    
            fm.delete_map(tablename,False)      
            return suc_msg   
        return suc_msg
    
    def has_file_structure_changed(self,db_map_pair:tuple,file_structure:dict,where:str=None):
        
        fs1=self.cma.map_to_file_structure(db_map_pair[0],db_map_pair[1],where,None,None,True)
        fs2=file_structure
        differences , _ = self.cma.shallow_compare_two_fs(fs1,fs2)
        print(differences)
        if len(differences['+'])>0 or len(differences['-'])>0:
            return True
        return False
        # fm=self.cma.get_file_map(db_map_pair[0])
        # data_list=fm.db.get_data_from_table(db_map_pair[1],"*",where)
        # if len(data_list)==0:
        #     return None
        # field_list=fm.db.get_column_list_of_table(db_map_pair[1])
        # dm=DataManage(data_list,field_list)
        # for iii,(filepath,filename) in enumerate(zip(dm.df['filepath'],dm.df['filename'])):
        #     pass        

    
    def show_actions(self,action_dict:dict,keep_changed:bool,keep_removed:bool,show_as_action:bool=True) ->str:
        """Return string of actions to be performed

        Args:
            action_dict (dict): action dictionary with {'action':[(from,to)]} 
            keep_changed (bool): when is a file changed, overwrite it or make a copy.
            keep_removed (bool): if a file was removed, keep the old file.
        Returns:
            str: String with actions
        """
        str_p=''
        iii=1
        for action_key, act_from_to_list in action_dict.items():   
            # 'data changed', 'file renamed', 'file moved', 'added file', or 'removed file'
            for act_from_to in act_from_to_list:
                (from_file,to_file)=act_from_to
                if action_key in ['file renamed', 'file moved']:
                    # Rename file
                    if show_as_action:
                        str_p=str_p+f'{iii} [green]Move/Rename[/green] {from_file} -> {to_file}'+'\n'
                    else:
                         str_p=str_p+f'{iii} {from_file} [yellow]was Moved/Renamed to[/yellow] {to_file}'+'\n'
                    iii += 1
                if action_key == 'added file':
                    # add file
                    if show_as_action:
                        str_p=str_p+f'{iii} [green]Copy[/green] {from_file} -> {to_file}'+'\n'
                    else:
                        str_p=str_p+f'{iii} {to_file} [green]has been added [/green]'+'\n'
                    iii += 1
                if action_key == 'data changed':
                    # Data changed
                    if show_as_action:
                        if keep_changed:
                            fn=F_M.extract_filename(to_file,True)
                            to_file_mod=to_file.replace(fn,"_old_"+str(datetime.now().date())+fn)
                            str_p=str_p+f'{iii} [green]Rename[/green] {to_file} -> {to_file_mod}'+'\n'
                            str_p=str_p+f'[green]then copy[/green] {from_file} -> {to_file}'+'\n'
                            iii += 1
                        else:
                            str_p=str_p+f'{iii} [magenta]Copy replacing[/magenta] {from_file} -> {to_file}'+'\n'
                            iii += 1
                    else:
                        str_p=str_p+f'{iii} {from_file} [magenta] data changed [/magenta] {to_file}'+'\n'
                        iii += 1
                if action_key == 'removed file':
                    # Rename file
                    if show_as_action:
                        if not keep_removed:
                            str_p=str_p+f'{iii} [red]Permanently remove[/red] {to_file}'+'\n'
                            iii += 1
                        else:
                            str_p=str_p+f'{iii} [green]Keeping[/green] {to_file}'+'\n'
                            iii += 1
                    else:
                        str_p=str_p+f'{iii} {to_file} [red]has been removed [/red] '+'\n'
                        iii += 1
        return str_p
                        
    def do_actions(self,action_dict:dict,keep_changed:bool,keep_removed:bool):
        """Actions to files

        Args:
            action_dict (dict): action dictionary with {'action':[(from,to)]} 
            keep_changed (bool): when is a file changed, overwrite it or make a copy.
            keep_removed (bool): if a file was removed, keep the old file.

        Returns:
            bool: all actions performed
        """
        did_actions=True
        for action_key, act_from_to_list in action_dict.items():   
            # 'data changed', 'file renamed', 'file moved', 'added file', or 'removed file'
            for act_from_to in act_from_to_list:
                (from_file,to_file)=act_from_to
                if action_key in ['file renamed', 'file moved']:
                    # Rename file
                    if not F_M.move_file(from_file,to_file):
                        print(f"Could not change {from_file}")
                        did_actions=False
                if action_key == 'added file':
                    # add file            
                    if not F_M.copy_file(from_file,to_file):
                        print(f"Could not copy {from_file}")
                        did_actions=False          
                if action_key == 'data changed':
                    # Data changed
                    if keep_changed:
                        fn=F_M.extract_filename(to_file,True)
                        to_file_mod=to_file.replace(fn,"_old_"+str(datetime.now().date())+fn)
                        # print('move',to_file,' -> ',to_file_mod)
                        if F_M.move_file(to_file,to_file_mod):
                            print(f"Could not modify {to_file} to {to_file_mod}")
                            did_actions=False
                        # print('copy',from_file,' -> ',to_file)
                        if not F_M.copy_file(from_file,to_file):
                            print(f"Could not copy {from_file}")
                            did_actions=False
                    else:
                        # print('copy replace ',from_file,' -> ',to_file)
                        if not F_M.copy_file(from_file,to_file):
                            print(f"Could not replace changed file {from_file}")  
                            did_actions=False  
                if action_key == 'removed file':
                    # Rename file
                    if not keep_removed:
                        # print('remove',' -> ',to_file)
                        if not F_M.delete_file(to_file):
                            print(f"Could not replace changed file {to_file}") 
                            did_actions=False
        return did_actions

    def identify_differences(self,db_map_pair_1,db_map_pair_2,where_1=None,where_2=None):
        """Compares two maps and gets the changes identified as:
            identification='data changed', 'file renamed', 'file moved', 'added file', or 'removed file'
            
        Args:
            db_map_pair_1 (tuple): database map pair 1
            db_map_pair_2 (tuple): database map pair 2
            where_1 (str, optional): filter for db_map_pair_1. Defaults to None.
            where_2 (str, optional): filter for db_map_pair_2. Defaults to None.

        Returns:
            list[tuple], dict: (index, db_map_pair, (mappath,mount), identification,'+/-',data), action dictionary
        """
        fm1=self.cma.get_file_map(db_map_pair_1[0])
        fm2=self.cma.get_file_map(db_map_pair_2[0])
        differences, msg, diff_info= self.shallow_compare_maps_no_base_path(db_map_pair_1,db_map_pair_2,where_1,where_2,remove_temp=False)
        if len(differences)==0:
            print(msg)
            return [], {}
        ((name_1,mappath_1,mount_1),(name_2,mappath_2,mount_2))=diff_info
        field_list=fm1.db.get_column_list_of_table(db_map_pair_1[1])
        data_list_p = []
        for an_id in differences['+_id']:           
            data_list_p = data_list_p + fm2.db.get_data_from_table(db_map_pair_2[1], "*", f"id={an_id}")
        data_list_m = []
        # Calculate md5 of the differences if not already
        self.cma.shallow_to_deep(db_map_pair_1,differences['-_id'])
        self.cma.shallow_to_deep(db_map_pair_2,differences['+_id'])
        _ = fm1.remap_map_in_thread_to_db(db_map_pair_1[1],None,False)
        _ = fm2.remap_map_in_thread_to_db(db_map_pair_2[1],None,False)
        for an_id in differences['-_id']:     
            data_list_m = data_list_m + fm1.db.get_data_from_table(db_map_pair_1[1], "*", f"id={an_id}")
        identified=[]
        already_id_p=[]
        already_id_m=[]
        index=0
        action_dict={'data changed':[], 'file renamed':[], 'file moved':[], 'added file':[], 'removed file':[]}
        for ppp,plus_d in enumerate(data_list_p):
            for mmm,minus_d in enumerate(data_list_m):
                # data changed but same filename
                # id=0,dt_data_created'=1,'dt_data_modified'=2,'filepath'=3,'filename'=4,'md5'=5,'size'=6	
                # md5 different same name
                if minus_d[5] != plus_d[5] and minus_d[4] == plus_d[4]:
                    identified.append((index, db_map_pair_1,(mappath_1,mount_1),'data changed','-',minus_d))
                    identified.append((index, db_map_pair_2,(mappath_2,mount_2),'data changed','+',plus_d))
                    already_id_m.append(mmm)
                    already_id_p.append(ppp)
                    to_file=os.path.join(mount_1,minus_d[3],minus_d[4])
                    from_file=os.path.join(mount_2,plus_d[3],plus_d[4])
                    act_list=action_dict['data changed']
                    act_list.append((from_file,to_file))
                    action_dict.update({'data changed':act_list})
                    index += 1
                # same md5 different name
                elif minus_d[5] == plus_d[5] and minus_d[4] != plus_d[4]:
                    identified.append((index, db_map_pair_1,(mappath_1,mount_1),'file renamed','-',minus_d))
                    identified.append((index, db_map_pair_2,(mappath_2,mount_2),'file renamed','+',plus_d))
                    already_id_m.append(mmm)
                    already_id_p.append(ppp)
                    from_file=os.path.join(mount_1,minus_d[3],minus_d[4])
                    to_file=os.path.join(mount_1,minus_d[3],plus_d[4])
                    act_list=action_dict['file renamed']
                    act_list.append((from_file,to_file))
                    action_dict.update({'file renamed':act_list})
                    index += 1
                # same md5 and same name
                elif minus_d[5] == plus_d[5] and minus_d[4] == plus_d[4]:
                    identified.append((index ,db_map_pair_1,(mappath_1,mount_1),'file moved','-',minus_d))
                    identified.append((index, db_map_pair_2,(mappath_2,mount_2),'file moved','+',plus_d))
                    already_id_m.append(mmm)
                    already_id_p.append(ppp)
                    from_file=os.path.join(mount_1,minus_d[3],minus_d[4])
                    path=str(plus_d[3]).replace(mappath_2,mappath_1)
                    to_file=os.path.join(mount_2,path,plus_d[4])
                    act_list=action_dict['file moved']
                    act_list.append((from_file,to_file))
                    action_dict.update({'file moved':act_list})
                    index += 1
        for ppp,plus_d in enumerate(data_list_p):
            if ppp not in already_id_p:
                identified.append((index, db_map_pair_2,(mappath_2,mount_2),'added file','+',plus_d))
                from_file=os.path.join(mount_2,plus_d[3],plus_d[4])
                to_file=str(from_file).replace(os.path.join(mount_2,mappath_2),os.path.join(mount_1,mappath_1))
                act_list=action_dict['added file']
                act_list.append((from_file,to_file))
                action_dict.update({'added file':act_list})
                index += 1
        for mmm,minus_d in enumerate(data_list_m):
            if mmm not in already_id_m:
                identified.append((index, db_map_pair_1,(mappath_1,mount_1),'removed file','-',minus_d))
                from_file=None
                to_file=os.path.join(mount_1,minus_d[3],minus_d[4])
                act_list=action_dict['removed file']
                act_list.append((from_file,to_file))
                action_dict.update({'removed file':act_list})
                index += 1

        print(f"Identified {index} changes")            
        
        # Remove temp maps
        fm2.delete_map(name_2,False)
        fm1.delete_map(name_1,False) 
        return identified, action_dict


    def shallow_compare_maps_no_base_path(self,db_map_pair_1,db_map_pair_2,where_1=None,where_2=None,remove_temp=True):
        """makes shallow compare of two maps without the base path. This allows to compare folders 

        Args:
            db_map_pair_1 (tuple): database map pair
            db_map_pair_2 (tuple): database map pair
            where_1 (str): filter for db_map_pair_1
            where_2 (str): filter for db_map_pair_2
            remove_temp (bool, optional): remove the temporal maps after compare. Defaults to True.

        Returns:
            tuple: differences, msg, diff_info
            diff_info =((name1,mappath1,mount1),(name2,mappath2,mount2))
        """
        fm1=self.cma.get_file_map(db_map_pair_1[0])
        fm2=self.cma.get_file_map(db_map_pair_2[0])
        name_1=f"__temp__{db_map_pair_1[1]}"
        mappath,mount=self._remove_base_path_map_(name_1,db_map_pair_1,where_1)
        name_2=f"__temp__{db_map_pair_2[1]}"
        mappath_end,mount_end=self._remove_base_path_map_(name_2,db_map_pair_2,where_2)
        differences, msg = self.cma.shallow_compare_maps((db_map_pair_1[0],name_1),(db_map_pair_2[0],name_2))
        if remove_temp:
            fm1.delete_map(name_1,False)
            fm2.delete_map(name_2,False)
            diff_info = tuple()
        else:
            diff_info = ((name_1,mappath,mount),(name_2,mappath_end,mount_end))
        return differences, msg, diff_info
            
    def _remove_base_path_map_(self,table_name:str,db_map_pair:tuple,where:str=None):  
        """Maps a copy of the map or selection taking the base part of the path out

        Args:
            table_name (str): New name for the map
            db_map_pair (tuple): map to take the info
            where (str, optional): filter options. Defaults to None.
        Returns:
            str: map path, mount
        """
        fm=self.cma.get_file_map(db_map_pair[0]) 
        cols=fm.db.get_column_list_of_table(db_map_pair[1])
        datasel=str(cols[1:]).replace("[",'').replace("]",'').replace("'",'')
        data_list=fm.db.get_data_from_table(db_map_pair[1],datasel,where)
        #field_list=['dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype']
        mod_data=[]
        # path of map
        map_info=self.cma.get_map_info(db_map_pair[0],db_map_pair[1])
        mappath=map_info[0][3]
        for d_t in data_list:
            modd_t=list(d_t)
            # modd_t[2]=F_M.fix_path_separators(modd_t[2])
            modd_t[2]=str(modd_t[2]).replace(mappath,'')
            mod_data.append(tuple(modd_t))
        fm.map_a_selection(table_name,db_map_pair[1],mod_data,MAP_TYPES_LIST[2])
        return mappath, map_info[0][5]
    
    def remove_selection_files_from_mount(self,db_map_pair,remove_from_origin:bool=True,where:str=None):   
        """Removes a file and its map reference"""
        map_info=self.cma.get_map_info(db_map_pair[0],db_map_pair[1])
        if map_info[0][8] in [MAP_TYPES_LIST[0],MAP_TYPES_LIST[2]]:
            return f"{db_map_pair[1]} is not a selection map!"
        origin_map=map_info[0][7] 
        if map_info[0][8]==MAP_TYPES_LIST[5]: # Sorted Maps 
            origin_map=db_map_pair[1]
        if (db_map_pair[0],origin_map) not in self.cma.get_maps_by_type([MAP_TYPES_LIST[0],MAP_TYPES_LIST[2],MAP_TYPES_LIST[5]]):
            return f"Can't find {(db_map_pair[0],origin_map)} origin map!"
        # check mount exist
        fm=self.cma.get_file_map(db_map_pair[0])
        mount, mount_active, mappath_exists=fm.check_if_map_device_active(fm.db,db_map_pair[1],False)
        print("Device check result:", mount, mount_active, mappath_exists)
        data_list=fm.db.get_data_from_table(db_map_pair[1],'*',where)
        # get file name and path 
        if len(data_list)==0:
            return "No data to remove!"
        if not mount_active or not mappath_exists:
            return f'Mount point {mount} is not available'
        msg=''
        # field list in map
        # id=0	dt_data_created'=1	'dt_data_modified'=2	'filepath'=3	'filename'=4	'md5'=5	'size'=6	
        # 'dt_file_created'=7	'dt_file_accessed'=8	'dt_file_modified'=9
        if not self.ask_confirmation(f"{A_C.add_ansi('Permanently Remove','hred')} {len(data_list)} files?",False):
            return f'User Cancel'
        for data in data_list:
            filepath=os.path.join(mount,data[3],data[4])
            print(f'Removing File: {filepath} and data in {db_map_pair}')
            # try to remove file
            was_removed=False
            if os.path.exists(filepath):
                was_removed=F_M.delete_file(filepath)
            #if was removed -> remove from db,map
            if was_removed:
                fm.db.delete_data_from_table(db_map_pair[1],f"id={data[0]}")
                if remove_from_origin:
                    wh_ori=f"filename={fm.db.quotes(data[4])} AND md5='{data[5]}' AND size={data[6]}"
                    fipa=fm.db.quotes(str(data[3]).replace('\\','%').replace('/','%'))
                    wh_ori+=f" AND filepath LIKE {fipa}"
                    id_list=fm.db.get_data_from_table(origin_map,"id",wh_ori)
                    if len(id_list)==1:
                        fm.db.delete_data_from_table(db_map_pair[1],f"id={id_list[0][0]}")
                    else:
                        msg=msg+f'[red]\t({wh_ori}) was not Removed in Origin!!\n'
            if not was_removed:
                msg=msg + f'[red]\t({data[0]}) {filepath} was not Removed!!\n'
        return msg

    def compare_two_maps(self,db_map_pair_1,db_map_pair_2,where1=None,where2=None,show_statistic=False): 
        """compares two maps or parts of the maps

        Args:
            db_map_pair_1 (tuple): db map pair 1
            db_map_pair_2 (tuple): db map pair 2
            where1 (_type_, optional): filter for map 1. Defaults to None.
            where2 (_type_, optional): filter for map 2. Defaults to None.
            show_statistic (bool, optional):Print statistics dictionary. Defaults to False.

        Returns:
            tuple(pd.Dataframe,dict): Datafame with unique "md5","ids_on_a","ids_on_b":list of ids, Source: "A","B" or "A&B", 'num_ids_a','num_ids_b': Number of ids in each.
                                        and statistic dictionary. 
                                        md5_c class.
        """
        fm1=self.cma.get_file_map(db_map_pair_1[0])
        data_list1=fm1.db.get_data_from_table(db_map_pair_1[1],"*",where1)
        if len(data_list1)==0:
            return None,None
        fm2=self.cma.get_file_map(db_map_pair_2[0])
        data_list2=fm2.db.get_data_from_table(db_map_pair_2[1],"*",where2)
        if len(data_list2)==0:
            return None,None
        field_list=fm1.db.get_column_list_of_table(db_map_pair_1[1])
        dm1=DataManage(data_list1,field_list)
        dm2=DataManage(data_list2,field_list)
        #pass only md5 for speed
        fields=["id", "md5"]
        md5_c=DataFrameCompare(dm1.get_selected_df(fields),dm2.get_selected_df(fields))
        df_compare=md5_c.compare_a_b("md5")
        statistic=md5_c.generate_comparison_stats(df_compare)
        if show_statistic:
            print(statistic)
        return df_compare,statistic,md5_c
    
        

