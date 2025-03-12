#!/usr/bin/env python  # shebang for Unix-based systems
#!pythonw        # shebang for Windows systems
from __future__ import print_function, unicode_literals

import os
import getpass

from datetime import datetime
from rich import print

from class_file_manipulate import FileManipulate
from class_file_mapper import *
from class_data_manage import DataManage
from class_file_explorer import *


F_M=FileManipulate()

class MappingActions():
    def __init__(self,file_list:list,password_list:list,key_list:list,ask_confirmation):
        self.ask_confirmation=ask_confirmation
        self.file_list=file_list
        self.password_list=password_list
        self.key_list=key_list
        self.active_databases=[]
    
    @staticmethod
    def calculate_time_elapsed(start_datetime:datetime,end_datetime:datetime)->float:
        """Calculate the time elapsed between two timestamps"""
        time_elapsed = (end_datetime - start_datetime).total_seconds()
        return time_elapsed
    
    def activate_databases(self,db_file_name=None):
        """Activates all databases in file_list using the key. Will prompt for password if DB is password protected.
        """
        for file,pwd,keyf in zip(self.file_list,self.password_list,self.key_list):
            if not db_file_name or db_file_name==file:
                if not self.is_database_active(file):
                    the_ppp=None
                    if pwd:
                        the_ppp =self.ask_password()
                    try:
                        fm=FileMapper(file,keyf,the_ppp)
                        self.active_databases.append({'file':file,'keyfile':keyf,'haspassword':pwd,'mapdb':fm})
                    except Exception as eee:
                        print(f"Could not activate {file}: {eee}")
    
    @staticmethod
    def ask_password(prompt):
        """Prompts the user for a password and returns it."""
        while True:
            password = getpass.getpass(f"Enter your {prompt} password (or leave blank to skip): ")
            if not password or password.strip() == "":
                return None
            else:
                return password

    def is_database_active(self,db_file_name:str)->bool:
        """True if database active

        Args:
            db_file_name (str): Database

        Returns:
            bool: True if database active
        """
        is_active=False
        for a_db in self.active_databases:
            if db_file_name==a_db['file']:
                is_active=True
                break
        return is_active

    def deactivate_databases(self,db_file_name=None):
        """Deactivate active databases, closes db connection.

        Args:
            db_file_name (str, optional): deactivate specific database, if None, removes all. Defaults to None.
        """
        active_dbs=self.active_databases.copy()
        for iii,a_db in enumerate(active_dbs):
            if not db_file_name or db_file_name==a_db['file']:
                fm=a_db['mapdb']
                if isinstance(fm,FileMapper):
                    fm.close()
                self.active_databases.pop(iii)
            
    def show_databases_listed(self):
        """prints databases listed
        """
        print("File Map Databases listed:")
        for iii,(file,pwd,keyf) in enumerate(zip(self.file_list,self.password_list,self.key_list)):
            print(f"\t{iii+1}. {file} {'[yellow](pwd)[/yellow]' if pwd else '()'} {keyf} {'[green]ACTIVE[/green]' if is_database_active(file) else '[magenta]NOT ACTIVE[/magenta]'}")

    def show_active_inactive_databases(self,show_active:bool=True,do_print=True):
        """Prints databases listed
        Args:
            show_active (bool, optional): active if True, inactive if False. Defaults to True.
            do_print (bool, optional): print info

        Returns:
            _type_: list of active/inactive databases [index,Database File]
        """
        ai_list=[]
        if show_active:
            if do_print:
                print("Active Databases:")
            for iii,a_db in enumerate(self.active_databases):
                #'keyfile','haspassword'
                if do_print:
                    print(f"\t{iii+1}. {a_db['file']} {'(pwd)' if a_db['haspassword'] else ''} {a_db['keyfile']}")
                ai_list.append([iii,a_db['file']])
        else:
            if do_print:
                print("Inactive Databases:")
            iii=0
            for file,pwd,keyf in zip(self.file_list,self.password_list,self.key_list):
                if not self.is_database_active(file):
                    if do_print:
                        print(f"\t{iii+1}. {file} {'(pwd)' if pwd else ''} {keyf}")
                    ai_list.append([iii,file])
                    iii=iii+1
        return ai_list

    def is_database_active(self,db_file_name:str)->bool:
        """True if database active

        Args:
            db_file_name (str): Database

        Returns:
            bool: True if database active
        """
        is_active=False
        for a_db in self.active_databases:
            if db_file_name==a_db['file']:
                is_active=True
                break
        return is_active

    def remove_database_file(self,filename):
        """Removes a file from lists

        Args:
            filename (str): file to remove
        """
        if filename in self.file_list:
            f_list=self.file_list.copy()
            for iii,fn in enumerate(f_list):
                if fn==filename:
                    self.file_list.pop(iii)
                    self.password_list.pop(iii)
                    self.key_list.pop(iii)
                    break
    
    def create_filemap_database(self,file_path):
        """Creates a new File Map database

        Args:
            file_path (str): Path and filename of new database
        """
        if self.ask_confirmation("Encrypt Database?"):
            path=F_M.extract_path(file_path)
            kf=F_M.extract_filename(file_path,False)+'_key.txt'
            keyfile=os.path.join(path,kf)
            print(f'New keyfile will be set to: {keyfile}')
            print("Warning: If you erase, or loose the file, you will not be able to access the database anymore!")
        else:
            keyfile=None
        if self.ask_confirmation("Set Database password?"):
            a_pwd=''
            while True:
                a_pwd=self.ask_password("New password for:")
                if not a_pwd or a_pwd=='':
                    a_pwd=None
                    print("Setting no password")
                    break
                r_pwd=self.ask_password("Repeat password for:")
                if a_pwd != r_pwd:
                    print("Passwords did not match, try again!")
                else:
                    break
        else:
            a_pwd=None
        fm=FileMapper(file_path,keyfile,a_pwd)
        fm.close()
        self.file_list.append(file_path)
        self.password_list.append(a_pwd)
        self.key_list.append(keyfile)



    def validate_new_map(self,new_table_name,database):
        """Check if New table name is Correct"""
        fm=self.get_file_map(database)
        return fm.validate_new_map_name(new_table_name)

    @staticmethod
    def format_new_table_name(tablename:str,path_to_map:str)->str:
        """Replaces the charater for the respective string: 
        % (Date_Time), # (Date), ? (Time), & (Dir), ! (Full_Path)

        Args:
            tablename (str): new map name
            path_to_map (str): path to map directory

        Returns:
            str: formatted string
        """
        tablename=tablename.replace('/','')
        tablename=tablename.replace('\\','')
        tablename=tablename.replace(' ','_')
        if '%' in tablename:
            dt=datetime.now().strftime("%Y%m%d_%H%M%S")
            tablename=tablename.replace('%',dt)
        if '&' in tablename:
            p_p=F_M.extract_parent_path(path_to_map,True)
            dp=path_to_map.replace(p_p,'')
            tablename=tablename.replace('&',dp)
            tablename=tablename.replace('/','')
            tablename=tablename.replace('\\','')
        if '#' in tablename:
            dt=datetime.now().strftime("%Y%m%d")
            tablename=tablename.replace('#',dt)
        if '?' in tablename:
            dt=datetime.now().strftime("%H%M%S")
            tablename=tablename.replace('?',dt)
        if '!' in tablename:
            dp=path_to_map.replace(":",'')
            tablename=tablename.replace('!',dp)
            tablename=tablename.replace('/','_')
            tablename=tablename.replace('\\','_')
            tablename=tablename.replace(' ','_')
        return tablename

    def get_maps_in_db(self,database):
        """Gets maps in database

        Args:
            database (str): database

        Returns:
            list: list of map's (table names)
        """
        fm=self.get_file_map(database)
        tables=fm.db.tables_in_db()
        referenced_tables=fm.get_referenced_attribute('tablename')
        # print(referenced_tables)
        maps=[]
        for ttt in tables:
            if ttt not in [fm.mapper_reference_table,'sqlite_sequence']:
                maps.append(ttt)
        for ref_map in referenced_tables:
            if ref_map not in maps:
                maps.append(ref_map)
        return maps
    
    def get_file_map(self,dbfile) -> FileMapper:
        """Returns the File Map object for database

        Args:
            dbfile (str): path and filename of db

        Returns:
            FileMapper: File map object
        """
        for a_db in self.active_databases:
            if a_db['file'] == dbfile:
                return a_db['mapdb']
        return None

    def get_map_info_text(self,a_database,a_map):
        """Gets a string with the Map information

        Args:
            a_database (str): database
            a_map (str): map/table name

        Returns:
            str: tabulated string with
            'Date Time Created','Table Name','Serial','Mount','Map Path','Items'
        """
        map_info_str=''
        fm=self.get_file_map(a_database)
        if isinstance(fm,FileMapper):
            table_list=fm.db.get_data_from_table(fm.mapper_reference_table,'*')
            table_list_size=[]
            for table_info in table_list:
                #field_list=['id','dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype']
                if a_map==table_info[4]:
                    table_list_size.append(table_info+(fm.db.get_number_or_rows_in_table(a_map),))
            if len(table_list_size)>0:
                field_list=['id','Date Time Created','Date Time Modified','Map Path','Table Name','Mount','Serial','Map Name','Map Type']+['Items']
                data_manage=DataManage(table_list_size,field_list)
                map_info_str=data_manage.get_tabulated_fields(fields_to_tab=[field_list[1],field_list[4],field_list[6],field_list[5],field_list[3],'Items'],header=False,index=False,justify='left')
        return map_info_str

    def get_map_info_dict(self,a_database:str,a_map:str)->dict:
        """Gets a dictionary with the Map reference information
    
        Args:
            a_database (str): database
            a_map (str): map/table name

        Returns:
            dict: with format
            {
            'id': {0: int},
            'dt_map_created': {0: 'YYYY-MM-DD HH:mm:SS.uS'},
            'dt_map_modified': {0: 'YYYY-MM-DD HH:mm:SS.uS'},
            'mappath': {0: '\\path\\of\\map'},
            'tablename': {0: 'tablename'},
            'mount': {0: 'mount/point'},
            'serial': {0: 'XXXXXXXX'},
            'mapname': {0: ''},
            'maptype': {0: 'type of map'}
            }
        """
        map_info_dict={}
        fm=self.get_file_map(a_database)
        if isinstance(fm,FileMapper):
            table_list=fm.db.get_data_from_table(fm.mapper_reference_table,'*',f'tablename="{a_map}"')
            if len(table_list)>0:
                #field_list=['id','dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype']
                field_list=fm.db.get_column_list_of_table(fm.mapper_reference_table)
                data_manage=DataManage(table_list,field_list)
                map_info_dict=data_manage.df.to_dict()
        return map_info_dict

    def show_maps(self):
        """Prints Map information
        """
        for iii,a_db in enumerate(self.active_databases):
            fm=a_db['mapdb']
            if isinstance(fm,FileMapper):
                print(f"{iii+1}. [yellow]Maps in {a_db['file']}:")
                table_list=fm.db.get_data_from_table(fm.mapper_reference_table,'*')
                table_list_size=[]
                for table_info in table_list:
                    #field_list=['id','dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype']
                    data=fm.db.get_data_from_table(table_info[4],'*',f'md5="{MD5_CALC}"')
                    shallow_data=fm.db.get_data_from_table(table_info[4],'*',f'md5="{MD5_SHALLOW}"')
                    num_rows=str(fm.db.get_number_or_rows_in_table(table_info[4]))
                    if len(data)>0:
                        num_rows=f'{num_rows}({len(data)})'
                    if len(shallow_data)>0:
                        num_rows=f'{num_rows}[{len(shallow_data)}]'
                    table_list_size.append(table_info+(num_rows,))
                if len(table_list_size)>0:
                    field_list=['id','Date Time Created','Date Time Modified','Map Path','Table Name','Mount','Serial','Map Name','Map Type']+['Items']
                    data_manage=DataManage(table_list_size,field_list)
                    print(data_manage.get_tabulated_fields(fields_to_tab=[field_list[1],field_list[4],field_list[6],field_list[5],field_list[3],'Items'],index=True,justify='left'))

    def get_all_maps(self):
        """Finds all maps in all loaded databases

        Returns:
            list: list of (database,map name)
        """
        output=[]
        for database in self.file_list:
            maps=[]
            try:
                maps=self.get_maps_in_db(database)
                for mmm in maps:
                    output.append((database,mmm))
            except:
                pass
        return output

    def get_map_info(self,database,a_map):
        """returns the map table information

        Args:
            database (str): database
            a_map (str): Table name

        Returns:
            list(tuple): information on reference table
        """
        fm=self.get_file_map(database)
        return fm.db.get_data_from_table(fm.mapper_reference_table,'*',f"tablename='{a_map}'")

    @staticmethod
    def search_maps_for(selected_db_map_pair_list,column,search):
        fs_list=[]
        for db_map_pair in selected_db_map_pair_list:
            where=f"filename LIKE '%{search}%'"
            fs=map_to_file_structure(db_map_pair[0],db_map_pair[1],where=where,fields_to_tab=None,sort_by=None,ascending=True)
            print('here',len(fs))
            if len(fs)>0:
                fs_list.append(fs.copy())
                del fs
        return fs_list


    def remove_file_from_mount_and_map(self,dupli_dict,db_map_pair):   
        print("$"*50,'\nRemoving->',dupli_dict,' in ',db_map_pair ) 
        
        # check mount exist
        fm=self.get_file_map(db_map_pair[0])
        mount, mount_active, mappath_exists=fm.check_if_map_device_active(fm.db,db_map_pair[1],False)
        print("Check result:", mount, mount_active, mappath_exists)
        # get file name and path 
        if mount_active and mappath_exists:
            filepath=os.path.join(mount,dupli_dict['filepath'],dupli_dict['filename'])
            print(filepath)
        else:
            return 'Cant find {}'
        # # try to remove file
        # was_removed=False
        # if os.path.exists(filepath):
        #     was_removed=F_M.delete_file(filepath)
        # #if was removed -> remove from db,map
        # if was_removed:
        #     fm.db.delete_data_from_table(db_map_pair[1],f'id={dupli_dict['id']}')
        # Find in all maps with the file in the same db
        matching_list=[]
        for (a_db,a_map) in self.get_all_maps():
            #if a_map !=db_map_pair[1]:
                where=f"filepath='{dupli_dict['filepath']}' AND filename='{dupli_dict['filename']}' AND md5='{dupli_dict['md5']}'"
                matches=fm.db.get_data_from_table(a_map,"*",where)
                if len(matches)>0:
                    matching_list.append((a_db,a_map)+matches[0])
                    # print('match found',a_map,matches)
        print('match found',matching_list)
        return ''

    @staticmethod
    def get_dict_from_id_in_duplicate(an_id:int,duplicte_list):
        for dup_tup in duplicte_list:
            for dupli_dict in dup_tup:
                if an_id == dupli_dict['id']:
                    return dupli_dict

    def map_to_file_structure(self,database,a_map,where=None,fields_to_tab:list[str]=None,sort_by:list=None,ascending:bool=True)->dict:
        """Generates a file structure from map information

        Args:
            database (str): database
            a_map (str): table in database
            where (_type_, optional): sql filter for the database search. Defaults to None.
            fields_to_tab (list[str], optional): Additional information to 'filename' and 'size' from map into file tuple. Defaults to None.
            sort_by (list, optional): Dataframe sorting. Defaults to None.
            ascending (bool, optional): AScending descending order for sorting. Defaults to True.

        Returns:
            dict: file structure
        """
        if a_map in self.get_maps_in_db(database):
            fm=self.get_file_map(database)
            table_size=fm.db.get_number_or_rows_in_table(a_map)
            if table_size > 10000:
                print(f'[red]Map {a_map} has {table_size} items, is too big to load into a single file structure!')
                if not self.ask_confirmation("You want to continue?"):
                    return {}
            return fm.map_to_file_structure(a_map,where,fields_to_tab,sort_by,ascending)
        return {}

    def shallow_compare_maps(self,db_map_pair_1,db_map_pair_2):
        """Compare two maps using tabulated data. Compares: 
            "dt_file_modified","size","filename","filepath"
            Assumes db_map_pair_1 is the oldest.
            Gives lists of differences and ids in the respective database.
            (-_id): ids removed/changed in db_map_pair_1
            (+_id): ids changed in db_map_pair_2

        Args:
            db_map_pair_1 (_type_): database map pair to compare
            db_map_pair_2 (_type_): database map pair to compare

        Returns:
            tuple(dict,str): differences dictionary, message
            differences={'+':[],'-':[],'+_id':[],'-_id':[],'diff_fs':[]}
            'diff_fs' list of tuples (db_map_pair)+(+/-),(* data)
        """
        fm_1=self.get_file_map(db_map_pair_1[0])
        fm_2=self.get_file_map(db_map_pair_2[0])
        # field list in map
        # id=0	dt_data_created'=1	'dt_data_modified'=2	'filepath'=3	'filename'=4	'md5'=5	'size'=6	
        # 'dt_file_created'=7	'dt_file_accessed'=8	'dt_file_modified'=9
        if isinstance(fm_1,FileMapper) and isinstance(fm_2,FileMapper):
            def fix_separators(path:str):
                """Sets same separator format for comparison"""
                return F_M.fix_separator_in_path(F_M.fix_path_separators(path),True)
            field_list=["dt_file_modified","size","filename","filepath"]
            what=", ".join(field_list)
            table_list_1=fm_1.db.get_data_from_table(db_map_pair_1[1],what)
            if len(table_list_1)>0:
                # field_list= fm_1.db.get_column_list_of_table(db_map_pair_1[1])
                data_manage_1=DataManage(table_list_1,field_list)
                # text1=data_manage_1.get_tabulated_fields(None,header=False,index=False,justify='right').splitlines(keepends=False)
                data_manage_1.df['filepath'] = data_manage_1.df['filepath'].apply(fix_separators)
                data_manage_1.df['size'] = data_manage_1.df['size'].apply(int)#F_M.get_size_str_formatted)
                text1=data_manage_1.get_tab_separated_fields(None,sort_by=['filepath','filename'],separator=',',header=False,index=False).splitlines(keepends=False)
            else:
                return {} , f"No data in {db_map_pair_1}"
            table_list_2=fm_2.db.get_data_from_table(db_map_pair_2[1],what)
            if len(table_list_2)>0:
                
                # field_list=fm_2.db.get_column_list_of_table(db_map_pair_2[1])
                data_manage_2=DataManage(table_list_2,field_list)
                data_manage_2.df['filepath'] = data_manage_2.df['filepath'].apply(fix_separators)
                data_manage_2.df['size'] = data_manage_2.df['size'].apply(int)#F_M.get_size_str_formatted)
                # text2=data_manage_2.get_tabulated_fields(None,header=False,index=False,justify='right').splitlines(keepends=False)
                text2=data_manage_2.get_tab_separated_fields(None,sort_by=['filepath','filename'],separator=',',header=False,index=False).splitlines(keepends=False)
            else:
                return {} , f"No data in {db_map_pair_2}"
            diff = difflib.Differ()
            result = list(diff.compare(text1, text2))
            comp_list=[]
            differences={'+':[],'-':[],'+_id':[],'-_id':[],'diff_fs':[]}
            for line in result:
                if line.startswith('+'):
                    comp_list.append(line)#A_C.add_ansi(line,'hgreen'))
                    differences.update({'+':differences['+']+[line]})
                elif line.startswith('-'):
                    comp_list.append(line)#A_C.add_ansi(line,'hred'))
                    differences.update({'-':differences['-']+[line]})
                elif line.startswith('?'):
                    pass
                else:
                    comp_list.append(line)   
            # get indexes
            for added in differences['+']:
                added=added[2:]
                addsep=added.split(',')
                fp=fm_2.db.quotes('%'+addsep[3][1:-1]+'%')
                where=f"size = {addsep[1]} AND dt_file_modified = {fm_2.db.quotes(addsep[0])} AND filename = {fm_2.db.quotes(addsep[2])} AND filepath LIKE {fp}"
                id_list_2=fm_2.db.get_data_from_table(db_map_pair_2[1],'*',where)
                if len(id_list_2)>0:
                    differences.update({'+_id':differences['+_id']+[id_list_2[0][0]]})
                    differences.update({'diff_fs':differences['diff_fs']+[tuple(db_map_pair_2)+('+',)+id_list_2[0]]})
            for added in differences['-']:
                added=added[2:]
                addsep=added.split(',')
                fp=fm_1.db.quotes('%'+addsep[3][1:-1]+'%')
                where=f"size = {addsep[1]} AND dt_file_modified = {fm_2.db.quotes(addsep[0])} AND filename = {fm_2.db.quotes(addsep[2])} AND filepath LIKE {fp}"
                id_list_1=fm_1.db.get_data_from_table(db_map_pair_1[1],'*',where)
                if len(id_list_1)>0:
                    differences.update({'-_id':differences['-_id']+[id_list_1[0][0]]})
                    differences.update({'diff_fs':differences['diff_fs']+[tuple(db_map_pair_1)+('-',)+id_list_1[0]]})
            
            # print(differences)
            return differences , f"Found {len(differences['+_id'])} (+) changes and {len(differences['-_id'])} (-) changes!"
            
        return {} , 'No Filemap found!'

    def shallow_compare_maps_fs(self,db_map_pair_1,db_map_pair_2):
        """Compare two maps using file structures, just compares formatted size path and filename.
            Not very precise 

        Args:
            db_map_pair_1 (_type_): database map pair to compare
            db_map_pair_2 (_type_): database map pair to compare

        Returns:
            tuple(dict,str): differences dictionary, message
            differences={'+':[],'-':[]}
        """
        fs_1=None
        fs_1=self.map_to_file_structure(db_map_pair_1[0],db_map_pair_1[1],where=None,fields_to_tab=None,sort_by=None,ascending=True)
        if len(fs_1)==0:
            return {} , f"No data in {db_map_pair_1}"
        fs_2=None
        fs_2=self.map_to_file_structure(db_map_pair_2[0],db_map_pair_2[1],where=None,fields_to_tab=None,sort_by=None,ascending=True)
        if len(fs_2)==0:
            return {} , f"No data in {db_map_pair_2}"
        # field list in map
        # id=0	dt_data_created'=1	'dt_data_modified'=2	'filepath'=3	'filename'=4	'md5'=5	'size'=6	
        # 'dt_file_created'=7	'dt_file_accessed'=8	'dt_file_modified'=9
        # Map info
        # id=0	'dt_map_created'=1	'dt_map_modified'=2	'mappath'=3	'tablename'=4	'mount'=5	'serial'=6	'mapname'=7	'maptype'=8
        f_e_1=FileExplorer(None,None,fs_1)
        f_e_2=FileExplorer(None,None,fs_2)
        text1=f_e_1.get_tree_view_string(None,my_style_size).splitlines(keepends=False)
        text2=f_e_2.get_tree_view_string(None,my_style_size).splitlines(keepends=False)
        diff = difflib.Differ()
        result = list(diff.compare(text1, text2))
        comp_list=[]
        differences={'+':[],'-':[]}
        for line in result:
            if line.startswith('+'):
                comp_list.append(line)#A_C.add_ansi(line,'hgreen'))
                differences.update({'+':differences['+']+[line]})
            elif line.startswith('-'):
                comp_list.append(line)#A_C.add_ansi(line,'hred'))
                differences.update({'-':differences['-']+[line]})
            elif line.startswith('?'):
                pass
            else:
                comp_list.append(line)   
        
        # print('\n'.join(comp_list))
        # print(differences)
        return differences , ''
        
    @staticmethod
    def get_remove_keep_dict(selected_items,duplicte_list):
        """Makes a dictionary with the remove and keep files from selection
        {'md5sum': {'all': [id1,... idN], 'remove': [id1], 'keep': [id2]}}
        """
        rem_keep_dict={}
        for dup_tup in duplicte_list:
            remove=[]
            keep=[]
            all_ids=[]
            # add all to keep
            for dupli_dict in dup_tup:
                all_ids.append(dupli_dict['id'])
            the_md5=dup_tup[0]['md5']
            for s_item in selected_items:
                if int(s_item) in all_ids: 
                    if int(s_item) in all_ids:
                        remove.append(int(s_item))
            for kkk in all_ids:
                if kkk not in remove:
                    keep.append(kkk) 
            rem_keep_dict.update({the_md5:{'all':all_ids,'remove':remove,'keep':keep}})
        return rem_keep_dict    
    
    def find_duplicates_in_database(self,database,a_map):
        """Returs a list of tuple with the dictionaries of file information of each repeated file.
            Duplicates are the files in the same folder,with different file names but with the same md5 sum.

            Args:
                database (str): database
                tablename (str): table in database

            Returns:
                list: list of tuples, each dictionary in the tuple contains the duplicate files
                [({Dupfileinfo1},{Dupfileinfo2}..{DupfileinfoN}), ...({DupfileinfoX1},{DupfileinfoX2}..{DupfileinfoXN})]
        """
        fm=self.get_file_map(database)
        return fm.find_duplicates(a_map)

    def find_repeated_in_database(self,database,a_map):
        """Returs a list of tuple with the dictionaries of file information of each repeated file.
        Repeated are files with the same md5 sum, in any folder within the map. 

            Args:
                database (str): database
                tablename (str): table in database

            Returns:
                list: list of tuples, each dictionary in the tuple contains the duplicate files
                [({Dupfileinfo1},{Dupfileinfo2}..{DupfileinfoN}), ...({DupfileinfoX1},{DupfileinfoX2}..{DupfileinfoXN})]
        """
        fm=self.get_file_map(database)
        return fm.find_repeated(a_map)

    def rescan_database_devices(self):
        new_active=None
        for iii,a_db in enumerate(self.active_databases):
            fm=a_db['mapdb']
            if isinstance(fm,FileMapper) and iii==0:
                fm.look_for_active_devices()
                new_active=fm.active_devices
            elif isinstance(fm,FileMapper) and iii>0:
                fm.active_devices=new_active    
        return '[green]Devices Refreshed'        


if __name__ == '__main__':
    #main()
    pass