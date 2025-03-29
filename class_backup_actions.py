

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
        
    def map_to_backup(self,db_map_pair,end_path,shallow=True,where=None,keep_changed=True,keep_removed=True):
        """ If end_path exists and has information then Makes actual map of end path.
            Compares with Map, Additions are added, Substractions are renamed.
        """
        path_has_info=False
        if os.path.exists(end_path):
            print("Analyzing end path")
            fs=F_M.get_file_structure_from_active_path(end_path,'Backup',{},True,self._get_file_info,True)
            if len(fs['Backup'])>0:
                path_has_info=True
                print(f"Path {end_path} has information!")

        if not path_has_info:
            map_info=self.cma.get_map_info(db_map_pair[0],db_map_pair[1])
            # id=0	'dt_map_created'=1	'dt_map_modified'=2	'mappath'=3	'tablename'=4	'mount'=5	'serial'=6	'mapname'=7	'maptype'=8
            scr_folder=os.path.join(map_info[0][5],map_info[0][3])
            print(f"Copying information from {scr_folder} to {end_path}")
            was_copied=F_M.copy_folder(scr_folder,end_path,True)
            if was_copied and self.ask_confirmation("Do you want to map the new Backup?",True):
                tablename=self.cma.format_new_table_name("%!",db_map_pair[1])
                fm=self.cma.get_file_map(db_map_pair[0])
                suc_msg=fm.map_a_path_to_db(tablename,end_path,True,shallow_map=shallow)
        else:
            # make new map of end path
            fm=self.cma.get_file_map(db_map_pair[0])
            fm.db.create_connection()
            tablename=self.cma.format_new_table_name("%!",db_map_pair[1])
            suc_msg=fm.map_a_path_to_db(tablename,end_path,True,shallow_map=shallow)
            if fm.db.table_exists(tablename) and "Successfully" in suc_msg:
                # [end_mount,end_path_nm]=F_M.split_filepath_and_mountpoint(end_path)
                db_map_pair_1=(db_map_pair[0],tablename)
                db_map_pair_2=db_map_pair
                _,action_dict=self.identify_differences(db_map_pair_1,db_map_pair_2,where,where)
                # (index=0, db_map_pair=1, (mappath,mount)=2, identification=3,'+/-'=4, data=5)
                
                # rename old first
                
                for action_key, act_from_to_list in action_dict.items():
                    
                    # 'data changed', 'file renamed', 'file moved', 'added file', or 'removed file'
                    for act_from_to in act_from_to_list:
                        (from_file,to_file)=act_from_to
                        if action_key in ['file renamed', 'file moved']:
                            # Rename file
                            print('move',from_file,' -> ',to_file)
                            # if not F_M.move_file(from_file,to_file):
                            #     print(f"Could not change {from_file}")
                        if action_key == 'added file':
                            # add file
                            print('copy',from_file,' -> ',to_file)
                            # if not F_M.copy_file(from_file,to_file):
                            #     print(f"Could not copy {from_file}")
                        
                        if action_key == 'data changed':
                            # Data changed
                            if keep_changed:
                                fn=F_M.extract_filename(to_file,True)
                                to_file_mod=to_file.replace(fn,"_old_"+str(datetime.now().date())+fn)
                                print('move',to_file,' -> ',to_file_mod)
                                # if F_M.move_file(to_file,to_file_mod):
                                #     print(f"Could not modify {to_file} to {to_file_mod}")
                                print('copy',from_file,' -> ',to_file)
                                # if not F_M.copy_file(from_file,to_file):
                                #     print(f"Could not copy {from_file}")
                            else:
                                print('copy replace ',from_file,' -> ',to_file)
                                # if not F_M.copy_file(from_file,to_file):
                                #     print(f"Could not replace changed file {from_file}")    
                        
                        if action_key == 'removed file':
                            # Rename file
                            if not keep_removed:
                                print('remove',' -> ',to_file)
                                # if not F_M.delete_file(to_file):
                                #     print(f"Could not replace changed file {to_file}")        
                    
                fm.delete_map(tablename) # FOR TESTING FAST        
            else:
                return suc_msg
        return ""

    def identify_differences(self,db_map_pair_1,db_map_pair_2,where_1=None,where_2=None):
        """Compares two maps and gets the changes identified as:
            identification='data changed', 'file renamed', 'file moved', 'added file', or 'removed file'
            
        Args:
            db_map_pair_1 (tuple): database map pair 1
            db_map_pair_2 (tuple): database map pair 2
            where_1 (str, optional): filter for db_map_pair_1. Defaults to None.
            where_2 (str, optional): filter for db_map_pair_2. Defaults to None.

        Returns:
            list[tuple]: (index, db_map_pair, (mappath,mount), identification,'+/-',data)
        """
        fm1=self.cma.get_file_map(db_map_pair_1[0])
        fm2=self.cma.get_file_map(db_map_pair_2[0])
        differences, msg, diff_info= self.shallow_compare_maps_no_base_path(db_map_pair_1,db_map_pair_2,where_1,where_2,remove_temp=False)
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
        fm2.delete_map(name_2)
        fm1.delete_map(name_1) 
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
            fm1.delete_map(name_1)
            fm2.delete_map(name_2)
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