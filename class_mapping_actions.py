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
            print(f"\t{iii+1}. {file} {'[yellow](pwd)[/yellow]' if pwd else '()'} {keyf} {'[green]ACTIVE[/green]' if self.is_database_active(file) else '[magenta]NOT ACTIVE[/magenta]'}")

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

    def show_maps(self,where:str=None):
        """Prints Map information
        """
        for iii,a_db in enumerate(self.active_databases):
            fm=a_db['mapdb']
            if isinstance(fm,FileMapper):
                print(f"{iii+1}. [yellow]Maps in {a_db['file']}:")
                table_list=fm.db.get_data_from_table(fm.mapper_reference_table,'*',where)
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
                    print(data_manage.get_tabulated_fields(fields_to_tab=[field_list[1],field_list[4],field_list[6],field_list[5],field_list[3],'Items',field_list[8]],index=True,justify='left'))

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

    def get_maps_by_type(self,type_list=None,in_list=True):
        """Finds all maps of specific types (or not of specific types) in all loaded databases

        Args:
            type_list (_type_, optional): list of databases types. Defaults to None.
            in_list (bool, optional): If true will return types in list, in False returns the inverse types of list. Defaults to True.
        
        Returns:
            list: list of (database,map name)
        """
        all_db_map_pair_list=self.get_all_maps()
        if not type_list:
            return all_db_map_pair_list
        output=[]
        for db_map_pair in all_db_map_pair_list:
            map_info=self.get_map_info(db_map_pair[0],db_map_pair[1])
            maptype=map_info[0][8]
            if maptype in type_list and in_list:
                output.append(db_map_pair)
            if maptype not in type_list and not in_list:
                output.append(db_map_pair)
        return output

    def get_size_of_file_selection(self,db_map_pair,id_list:list=None):
        """Calculates the total size in bytes of a map, or selected ids on the map

        Args:
            db_map_pair (tuple): database map pair
            id_list (list, optional): list of ids to use. Defaults to None.

        Returns:
            int: size in bytes
        """
        fm=self.get_file_map(db_map_pair[0])
        id_size_list=fm.db.get_data_from_table(db_map_pair[1],"id, size",None)
        use_all=True
        if isinstance(id_list,list):
            if len(id_list)>0:
                use_all=False
        total_size=0
        if use_all:
            for (_,a_size) in id_size_list:
                if a_size>=0:
                    total_size=total_size+a_size
        else:
            for (an_id,a_size) in id_size_list:
                if a_size>=0 and an_id in id_list:
                    total_size=total_size+a_size
        return total_size
            
    def remove_file_from_mount_and_map(self,dupli_dict,db_map_pair):   
        """Removes a file and its map reference"""
        # check mount exist
        fm=self.get_file_map(db_map_pair[0])
        mount, mount_active, mappath_exists=fm.check_if_map_device_active(fm.db,db_map_pair[1],False)
        print("Check result:", mount, mount_active, mappath_exists)
        # get file name and path 
        if mount_active and mappath_exists:
            filepath=os.path.join(mount,dupli_dict['filepath'],dupli_dict['filename'])
            print(f'Removing File: {filepath} and data in {db_map_pair}')
        else:
            return f'Mount point {mount} is not available'
        # try to remove file
        was_removed=False
        if os.path.exists(filepath):
            was_removed=F_M.delete_file(filepath)
        #if was removed -> remove from db,map
        if was_removed:
            fm.db.delete_data_from_table(db_map_pair[1],f"id={dupli_dict['id']}")
        if not was_removed:
            return f'[red] ({dupli_dict["id"]}) {filepath} was not Removed!!'
        return ''

    @staticmethod
    def get_dict_from_id_in_duplicate(an_id:int,duplicte_list):
        """Gets dictionary for an id value"""
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

    def shallow_to_deep(self,db_map_pair,id_list:list=None):
        """Convert Shallow map into a calculation Map can be done for specific ids

        Args:
            db_map_pair (tuple): database map pair
            id_list (list): list of ids to select. Defaults to None 
        """
        fm=self.get_file_map(db_map_pair[0])
        data_np=fm.db.get_data_from_table(db_map_pair[1],"*",f"md5={fm.db.quotes(MD5_SHALLOW)}")
        data=[]
        if id_list:
            for a_row in data_np:
                if a_row[0] in id_list:
                    data.append(a_row)
        else:
            data=data_np
        for iii,a_row in enumerate(data):
            A_C.print_cycle(iii,len(data))
            fm.db.edit_value_in_table(db_map_pair[1],a_row[0],'md5',MD5_CALC)

    def shallow_compare_maps(self,db_map_pair_1:tuple,db_map_pair_2:tuple):
        """Compare two maps using tabulated data. Compares: 
            "dt_file_modified","size","filename","filepath"
            Assumes db_map_pair_1 is the oldest.
            Gives lists of differences and ids in the respective database.
            (-_id): ids removed/changed in db_map_pair_1
            (+_id): ids changed in db_map_pair_2

        Args:
            db_map_pair_1 (tuple): database map pair to compare
            db_map_pair_2 (tuple): database map pair to compare

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
                text1=data_manage_1.get_tab_separated_fields(None,sort_by=['filepath','filename'],separator='|',header=False,index=False).splitlines(keepends=False)
            else:
                return {} , f"No data in {db_map_pair_1}"
            table_list_2=fm_2.db.get_data_from_table(db_map_pair_2[1],what)
            if len(table_list_2)>0:
                
                # field_list=fm_2.db.get_column_list_of_table(db_map_pair_2[1])
                data_manage_2=DataManage(table_list_2,field_list)
                data_manage_2.df['filepath'] = data_manage_2.df['filepath'].apply(fix_separators)
                data_manage_2.df['size'] = data_manage_2.df['size'].apply(int)#F_M.get_size_str_formatted)
                # text2=data_manage_2.get_tabulated_fields(None,header=False,index=False,justify='right').splitlines(keepends=False)
                text2=data_manage_2.get_tab_separated_fields(None,sort_by=['filepath','filename'],separator='|',header=False,index=False).splitlines(keepends=False)
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
                addsep=added.split('|')
                fp=fm_2.db.quotes('%'+addsep[len(addsep)-1][1:-1]+'%')
                where=f"size = {addsep[1]} AND dt_file_modified = {fm_2.db.quotes(addsep[0])} AND filename = {fm_2.db.quotes(addsep[2])} AND filepath LIKE {fp}"
                id_list_2=fm_2.db.get_data_from_table(db_map_pair_2[1],'*',where)
                if len(id_list_2)>0:
                    differences.update({'+_id':differences['+_id']+[id_list_2[0][0]]})
                    differences.update({'diff_fs':differences['diff_fs']+[tuple(db_map_pair_2)+('+',)+id_list_2[0]]})
            for added in differences['-']:
                added=added[2:]
                addsep=added.split('|')
                fp=fm_1.db.quotes('%'+addsep[len(addsep)-1][1:-1]+'%')
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
        return self.shallow_compare_two_fs(fs_1,fs_2)
    
    def shallow_compare_two_fs(self,fs_1,fs_2):
        """Compare two file structures, just compares formatted size path and filename.
            Not very precise 

        Args:
            db_map_pair_1 (_type_): database map pair to compare
            db_map_pair_2 (_type_): database map pair to compare

        Returns:
            tuple(dict,str): differences dictionary, message
            differences={'+':[],'-':[]}
        """
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
                if isinstance(s_item,str): 
                    if int(s_item) in all_ids:
                        remove.append(int(s_item))
                if isinstance(s_item,list): 
                    for an_sitem in s_item:
                        if int(an_sitem) in all_ids:
                            remove.append(int(an_sitem))
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

    def browse_file_directories(self,db_map_pair,browse_type='file',where=None):
        """browse files or directories

        Args:
            db_map_pair (tuple): database map pair
            type (srt): Type of browsing 'file', 'dir', 'file_multiple', 'dir_multiple'. Default 'file'

        Returns:
            str,Treenode,list[TreeNode],tuple: msg (str) 
                                                or treenode
                                                or list of selected treeNodes.
                                                or 
        """
        # print('Tree') #db_map_pair)
        fs=None
        fs=self.map_to_file_structure(db_map_pair[0],db_map_pair[1],where=where,fields_to_tab=['id'],sort_by=None,ascending=True)
        if len(fs)>0:
            f_e=FileExplorer(None,None,fs)
            if browse_type=='dir':
                return f_e.browse_folders(my_style_dir_expand_size,f"Browsing directories of {A_C.add_ansi(db_map_pair[1],'cyan')}")
            elif browse_type=='file':
                return f_e.browse_files(my_style_expand_size,True,f"Browsing tree of {A_C.add_ansi(db_map_pair[1],'cyan')}")
            elif browse_type=='dir_multiple':
                node_list=f_e.select_multiple_folders(my_style_dir_expand_size,None,f"Browse and select directories from {A_C.add_ansi(db_map_pair[1],'cyan')}")
                trace_list=[]
                for node in node_list:
                    trace=f_e.t_v.trace_path(node,[0],True)
                    trace_list.append(os.sep.join(trace))
                return node_list,trace_list
            elif browse_type=='file_multiple':
                return self.explore_multiple_file_search(f"Browse and select files from {A_C.add_ansi(db_map_pair[1],'cyan')}",[fs],[db_map_pair])
                # return f_e.select_multiple_files(my_style_file_expand_size,None,f"Browse and select files from {A_C.add_ansi(db_map_pair[1],'cyan')}",False)
            
        else: 
            return 'No items in Map'
        return None

    def edit_selection_map(self,database,a_map):
        map_info=self.get_map_info(database,a_map)
        if map_info[0][8] in [MAP_TYPES_LIST[0],MAP_TYPES_LIST[2]]:
            return f"{a_map} is not a selection map!"
        origin_map=map_info[0][7] 
        if (database,origin_map) not in self.get_maps_by_type([MAP_TYPES_LIST[0],MAP_TYPES_LIST[2]]):
            return f"Can't find {(database,origin_map)} origin map!"
        fm=self.get_file_map(database)
        fn_fp=fm.db.get_data_from_table(a_map,'filename, filepath')
        name_list=[]
        parent_list=[]
        for d_tup in fn_fp:
            name_list.append(d_tup[0])
            parent_list.append(d_tup[1])
            # # get the last path from the path
            # parent=os.path.split(d_tup[1])
            # if parent[1]=='':
            #     parent=os.path.split(parent[0])
            # parent_list.append(parent[1])
        fs=None
        fs=self.map_to_file_structure(database,origin_map,None,fields_to_tab=['id'],sort_by=None,ascending=True)
        if len(fs)>0:

            selected_db_map_pair, _, data=self.explore_multiple_file_search(f"Browse and select files from {A_C.add_ansi(a_map,'cyan')}",[fs],[(database,origin_map)],name_list,parent_list)
            # selection_name=str(datetime.now()).replace(" ","_").replace("-","").replace(":","").replace(".","")
            if len(selected_db_map_pair)>0:
                new_data=[]
                for ddd in data:
                    new_data=new_data+ddd
                fm.db.delete_data_from_table(a_map)
                if fm.db.insert_data_to_table(a_map,new_data):
                    return f"{a_map} has been edited!"
        return ""

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

    def explore_one_file_search(self,search,fs_list:list,db_map_list:list)->tuple:
        """Uses file explorer to select a file from a search.

        Args:
            search (_type_): main node name to show
            fs_list (list): list of file structures from search. 
                Id must be included in filestructure! 
            db_map_list (list): correspondant db_map_pair list

        Returns:
            tuple: selected_db_map_pair, selected_id, selection data
        """
        selected_db_map_pair=None
        selected_id=None 
        data=None
        f_e=FileExplorer(None,None,{search:fs_list})
        selected_node=f_e.browse_files(my_style_expand_size,allow_dir_selection=False,prompt="Browse and select a File")   
        if selected_node.level not in [0,1]: # search, db_map
            #  get the db_map_pair and id of selection.
            b_l=selected_node.get_bloodline()
            for iii,node in enumerate(f_e.t_v.main_node.children):
                if node.id in b_l:
                    selected_db_map_pair=db_map_list[iii]
                    break
            # directories do not have an id in map, and no info on file_structure so not allowing to select directories
            selected_id=selected_node.info[2]
            fm=self.get_file_map(selected_db_map_pair[0])
            data=fm.db.get_data_from_table(selected_db_map_pair[1],"*",f'id={selected_id}')
        # else: # only used if allow_dir_selection=True
        #     if not self.ask_confirmation("Not valid selection, do you want to exit?",True):
        #         selected_db_map_pair, selected_id, data = self.explore_one_file_search(search,fs_list,db_map_list)
        return selected_db_map_pair, selected_id, data
    
    def make_selection_maps(self,selection_name,db_map_pair_list,data_list:list[list]):
        """Selection maps, one for each db map pair.

        Args:
            selection_name (str): selection name
            db_map_pair_list (list(tuple)): Lists of databases and maps
            data_list (list[list]): data list matching length of db_map_pair_list
        Returns:
            list: list of selection map names
        """
        if not db_map_pair_list or not data_list:
            return None
        selections=[]
        if len(db_map_pair_list)>0 and len(db_map_pair_list)==len(data_list):
            set_dbmap_pairs=set(db_map_pair_list)
            data_same_dbmap=[]
            for iii,db_map_pair in enumerate(list(set_dbmap_pairs)):
                selections.append(f"{selection_name}_{iii}")
                same_data=[]
                for s_db_m_p,s_ddd in zip(db_map_pair_list,data_list):
                    if db_map_pair == s_db_m_p:
                        same_data.append(s_ddd[0]) # just the tuple
                data_same_dbmap.append(same_data)   
            for s_db_m_p,s_ddd,s_name in zip(list(set_dbmap_pairs),data_same_dbmap,selections):
                fm=self.get_file_map(s_db_m_p[0])
                fm.map_a_selection(s_name,s_db_m_p[1],s_ddd)
                
        return selections

    def explore_multiple_file_search(self,search,fs_list:list,db_map_list:list,name_list:list=None,parent_list:list=None)->tuple:
        """Uses file explorer to select a file from a search.

        Args:
            search (str): main node name to show
            fs_list (list): list of file structures from search. 
                Id must be included in filestructure! 
            db_map_list (list): correspondant db_map_pair list
            name_list(list,optional): Preselceted name list, Default None
            parent_list (list,optional): Preselceted parent list, Default None

        Returns:
            tuple[list]: selected_db_map_pair, selected_id, selection data
        """
        selected_db_map_pair_list=[]
        selected_id_list=[]
        data=[]
        f_e=FileExplorer(None,None,{search:fs_list})
        f_e.set_selected_lists(name_list,parent_list,[0,1])
        selected_node_list=f_e.select_multiple_files(my_style_file_expand_size,None,prompt="Browse and select Files",allow_dir_selection=False)  
        for selected_node in  selected_node_list:
            if selected_node.level not in [0,1]: # search, db_map
                #  get the db_map_pair and id of selection.
                b_l=selected_node.get_bloodline()
                for iii,node in enumerate(f_e.t_v.main_node.children):
                    if node.id in b_l:
                        selected_db_map_pair=db_map_list[iii]
                        selected_db_map_pair_list.append(selected_db_map_pair)
                        break
                # directories do not have an id in map, and no info on file_structure so not allowing to select directories
                selected_id_list.append(selected_node.info[2])
                fm=self.get_file_map(selected_db_map_pair[0]) #last appended to list
                cols=fm.db.get_column_list_of_table(selected_db_map_pair[1])
                datasel=str(cols[1:]).replace("[",'').replace("]",'').replace("'",'')
                data.append(fm.db.get_data_from_table(selected_db_map_pair[1],datasel,f'id={selected_node.info[2]}'))
            
        return selected_db_map_pair_list, selected_id_list, data

    def rescan_database_devices(self):
        """scans for devices when you have a drive connected or disconnected

        Returns:
            str: message
        """
        new_active=None
        for iii,a_db in enumerate(self.active_databases):
            fm=a_db['mapdb']
            if isinstance(fm,FileMapper) and iii==0:
                fm.look_for_active_devices()
                new_active=fm.active_devices
            elif isinstance(fm,FileMapper) and iii>0:
                fm.active_devices=new_active    
        return '[green]Devices Refreshed'

    def clone_map(self,db_map_pair:tuple,selected_db:str,return_pair:bool=False):
        """Clones a map in the database"""
        map_info=self.get_map_info(db_map_pair[0],db_map_pair[1])
        mappath=map_info[0][3]
        newtablename=f"%{db_map_pair[1]}_clone"
        table_name=self.format_new_table_name(newtablename,mappath)
        new_map_info=tuple()
        for iii,item in enumerate(map_info[0]):
            if iii==0:
                pass
            elif iii==2:
                new_map_info=new_map_info+(str(datetime.now()),)
            elif iii==4:
                new_map_info=new_map_info+(table_name,)
            else:
                new_map_info=new_map_info+(item,)
        fm=self.get_file_map(selected_db)   
        if not fm.db.table_exists(table_name):
            was_indexed=fm.db.insert_data_to_table(fm.mapper_reference_table,[new_map_info]) 
            if was_indexed:
                # same db
                if selected_db == db_map_pair[0]:
                    fm.db.clone_table(db_map_pair[1],table_name)
                    return f'Successfully cloned {db_map_pair[1]} to {table_name} in {db_map_pair[0]}' 
                else:
                    fmfrom=self.get_file_map(db_map_pair[0])
                    cols=fmfrom.db.get_column_list_of_table(db_map_pair[1])
                    datasel=str(cols[1:]).replace("[",'').replace("]",'').replace("'",'')
                    all_data=fmfrom.db.get_data_from_table(db_map_pair[1],datasel)
                    fm.db.create_table(table_name,[('dt_data_created', 'DATETIME DEFAULT CURRENT_TIMESTAMP', True),
                                        ('dt_data_modified', 'DATETIME', True),
                                        ('filepath','TEXT',True), 
                                        ('filename','TEXT',True), 
                                        ('md5', 'TEXT', True), 
                                        ('size', 'REAL', True), 
                                        ('dt_file_created','DATETIME',False),
                                        ('dt_file_accessed','DATETIME',False),
                                        ('dt_file_modified','DATETIME',False),
                                        ])
                    if fm.db.insert_data_to_table(table_name,all_data):
                        newdb_map_pair=(selected_db,table_name)
                        if return_pair:
                            return newdb_map_pair
                        return f'Successfully cloned {db_map_pair} to {newdb_map_pair}'  
            return "Unable to Index Table!"    
        return f"Table exists {table_name}"
        



    def update_map(self,db_map_pair:tuple):
        """Updates a map

        Args:
            db_map_pair (tuple): database and map pair

        Returns:
            str: message
        """
        map_info_1=self.get_map_info(db_map_pair[0],db_map_pair[1])
        # field list in map
        # id=0	dt_data_created'=1	'dt_data_modified'=2	'filepath'=3	'filename'=4	'md5'=5	'size'=6	
        # 'dt_file_created'=7	'dt_file_accessed'=8	'dt_file_modified'=9
        # Map info
        # id=0	'dt_map_created'=1	'dt_map_modified'=2	'mappath'=3	'tablename'=4	'mount'=5	'serial'=6	'mapname'=7	'maptype'=8
        mappath=map_info_1[0][3]
        new_tablename=db_map_pair[1]+'_update'
        # check mount exist
        fm=self.get_file_map(db_map_pair[0])
        mount, mount_active, mappath_exists=fm.check_if_map_device_active(fm.db,db_map_pair[1],False)
        print("Check result:", mount, mount_active, mappath_exists)
        # get file name and path 
        filepath=None
        if mount_active and mappath_exists:
            filepath=os.path.join(mount,mappath)
            print(filepath)
        if not filepath:
            return f'Mount or device is not active for {db_map_pair}'
        # Make a shallow map
        try:
            if not fm.db.table_exists(new_tablename):
                fm.map_a_path_to_db(new_tablename,filepath,True,None,shallow_map=True)
            db_map_pair_1=db_map_pair
            db_map_pair_2=(db_map_pair[0],new_tablename)
            differences, msg = self.shallow_compare_maps(db_map_pair_1,db_map_pair_2)
            # Delete the shallow map
            print(differences['+'])
            print(differences['-']) 
            print(msg)
            found_differences=False
            for _,value in differences.items():
                if len(value)>0:
                    found_differences=True
                    break
            if not found_differences:
                # delete shallow map
                fm.delete_map(new_tablename)
                return msg
            if not self.ask_confirmation(f"Replace differences in map {db_map_pair[1]}?",False):
                return '[yellow] Map not Updated! Delete map manually or restart update to use map'
            data_to_add=[]
            for item in differences['diff_fs']:
                if item[2]=='+':
                    ddd=tuple()
                    for iii in range(4,len(item)):
                        if item[iii] == MD5_SHALLOW:
                            ddd=ddd+(MD5_CALC,)
                        else:    
                            ddd=ddd+(item[iii],)
                    data_to_add.append(ddd)
                if item[2]=='-':
                    ddd=tuple()
                    where=f'id = {item[3]}'
                    fm.db.delete_data_from_table(db_map_pair[1],where)    
            fm.db.insert_data_to_table(db_map_pair[1],data_to_add)
            # update data modified
            fm.db.edit_value_in_table(fm.mapper_reference_table,map_info_1[0][0],'dt_data_modified',datetime.now())
            # delete shallow map
            fm.delete_map(new_tablename)
            # start thread
            msg = fm.remap_map_in_thread_to_db(db_map_pair[1],None,True)
        except (KeyboardInterrupt,ValueError,TypeError) as eee:
            print(f'Something Wrong:{eee}')
            fm.delete_map(new_tablename)
        return msg


if __name__ == '__main__':
    #main()
    pass