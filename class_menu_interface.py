#!/usr/bin/env python  # shebang for Unix-based systems
#!pythonw        # shebang for Windows systems
from __future__ import print_function, unicode_literals
import os
import sys

from class_mapping_actions import *
from class_backup_actions import BackupActions

import inquirer
import inquirer.errors

# import argparse
# import getpass
# from datetime import datetime
from rich import print

F_M=FileManipulate()

FILE_MAP_LOGO=""">>=========================================<<
||..._____._._........__..__...............||
||..|..___(_).|.___..|..\/..|.__._._.__....||
||..|.|_..|.|.|/._.\.|.|\/|.|/._`.|.'_.\...||
||..|.._|.|.|.|..__/.|.|..|.|.(_|.|.|_).|..||
||..|_|...|_|_|\___|.|_|..|_|\__,_|..__/...||
||................................|_|......||
>>=========================================<<
>>======by FG with coffee and Love=========<<
>>=========================================<<"""

MENU_HEADER=""">>================FILE MAP=================<<
>>======by FG with coffee and Love=========<<
>>=========================================<<
"""
GITHUB="https://github.com/fedetony"
VERSION="v.1.1.333 beta"



class TerminalMenuInterface():
    def __init__(self,file_list:list,password_list:list,key_list:list):
        
        self.ba=BackupActions(file_list,password_list,key_list,self.ask_confirmation)
        self.cma=self.ba.cma   

    @staticmethod
    def ask_confirmation(message:str,default:bool=False)->bool:
        """Asks yes or no question

        Args:
            message (str): question
            default (bool, optional): default answer. Defaults to False.

        Returns:
            bool: True if yes.
        """
        questions = [
        inquirer.Confirm(
            "question",
            message=message,
            default=default
        )]
        answers = inquirer.prompt(questions)
        return answers['question']
            
    def menu_activate_deactivate_databases(self,activate):
        """Menu for Deactivating Databases
        """
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print(MENU_HEADER)
            if activate:
                print("Activate Databases:")
                print("-----------------------")
                ia_list=self.cma.show_active_inactive_databases(False,False)
                if len(ia_list)==0:
                    return '[yellow]All databases are active!!'
                
            else:
                print("Deactivate Databases:")
                print("-----------------------")
                ia_list=self.cma.show_active_inactive_databases(True,True)
                if len(ia_list)==0:
                    return '[yellow]All databases are inactive!!'    
            active_inactive_list=[]
            for _,i_a in ia_list:
                active_inactive_list.append(i_a)
            ch=active_inactive_list+['All','Back']
            menu = [inquirer.List(
                'activate_menu',
                message="Please select",
                choices=ch,
                carousel=False,
                )]
            answers = inquirer.prompt(menu)
            if answers['activate_menu']=='All':
                if activate:
                    self.cma.activate_databases(None)
                else:
                    self.cma.deactivate_databases(None)    
            elif answers['activate_menu']=='Back':
                return ''
            elif answers['activate_menu'] in active_inactive_list:
                if activate:
                    self.cma.activate_databases(answers['activate_menu'])
                else:
                    self.cma.deactivate_databases(answers['activate_menu'])
            else:
                print("Not a valid choice")

    def menu_handle_databases(self):
        """Interactive menu handle databases"""
        msg=''
        ch=['Create New Database File', 
            'Append Database File', 
            'Remove Database File',
            'Activate Database File',
            'Deactivate Database File',
            'Back']
        in_name='handle_db_menu'
        menu = [inquirer.List(
            in_name,
            message="Please select",
            choices=ch,
            carousel=False,
            )]
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print(MENU_HEADER)
            self.cma.show_databases_listed()
            if msg!='':
                print(msg)
            print("---------------------------------")
            answers = inquirer.prompt(menu)
            if answers['handle_db_menu']=='Create New Database File':
                msg=self.menu_create_new_database_file()
            elif answers['handle_db_menu']=='Append Database File': 
                msg=self.menu_append_database_file()
            elif answers['handle_db_menu']=='Remove Database File':         
                msg=self.menu_remove_database_file()   
            elif answers['handle_db_menu']=='Activate Database File':
                msg=self.menu_activate_deactivate_databases(True)
            elif answers['handle_db_menu']=='Deactivate Database File':
                msg=self.menu_activate_deactivate_databases(False)
            elif answers['handle_db_menu']=='Back':
                return ''

    def menu_remove_database_file(self):
        """Removes a database from the file_list
        """
        if len(self.cma.file_list)==0:
            return '[magenta]No databases to remove!'
        answers ={'remove_db_menu':''}
        
        while len(self.cma.file_list)>0:
            
            menu = [inquirer.List(
                'remove_db_menu',
                message="Please select",
                choices=self.cma.file_list+['Select All', 
                        'Back'],
                carousel=False,
                ),
                inquirer.Confirm(
                'remove_all',
                message="You want to remove all?",
                ignore=lambda answers: answers['remove_db_menu'] != 'Select All'
                ),
                inquirer.Confirm(
                'remove_file',
                message=lambda answers: f"You want to remove {answers['remove_db_menu']}?",
                ignore=lambda answers: answers['remove_db_menu'] in ['Select All','Back']
                ),
                ]
            os.system('cls' if os.name == 'nt' else 'clear')
            print(MENU_HEADER)
            self.cma.show_databases_listed()
            print("Remove database from list:")
            print("---------------------------------")
            answers = inquirer.prompt(menu)
            if answers['remove_db_menu']=='Select All':
                if answers['remove_all']:
                    self.cma.deactivate_databases(None)
                    self.cma.file_list.clear()
                    self.cma.password_list.clear()
                    self.cma.key_list.clear()
                    continue
                
            elif answers['remove_db_menu']=='Back':
                return ''
            elif answers['remove_db_menu'] in self.cma.file_list:
                f_r=answers['remove_db_menu']
                if answers['remove_file']:
                    self.cma.deactivate_databases(f_r)
                    self.cma.remove_database_file(f_r)
            else:
                print("Not a valid choice, try again.")
        return ''
        
    def menu_append_database_file(self):
        """Adds a database to the file_list
        """
        dir_available,path_user=self.menu_get_a_directory(False)
        file_available=False
        file_path=''
        if dir_available:
            file_available,file_user=self.menu_get_an_existing_file(path_user,".db")
            if file_available:
                file_path=os.path.join(path_user,file_user)
                self.menu_open_filemap(file_path)
                return ''
            return '[yellow]File Not available!'
        return ''

    def menu_open_filemap(self,file_path):
        """Opens a file map database

        Args:
            file_path (str): Complete path and file name of the database
        """
        keyfile=None
        a_pwd=None
        file_available=False
        if self.ask_confirmation(f"Is {file_path} {A_C.add_ansi('encrypted','hblue')}?"):
            print("-"*5+"Key Directory"+"-"*5)
            dir_available,path_key=self.menu_get_a_directory(False)
            if dir_available:    
                # default_fn=F_M.extract_filename(file_path,False)+'_key.txt'
                file_available,file_key=self.menu_get_an_existing_file(path_key,".txt")
                if file_available:
                    keyfile=os.path.join(path_key,file_key) 
        else:
            file_available=True
        if self.ask_confirmation(f"Is {file_path} {A_C.add_ansi('password protected','hblue')}?"):
            a_pwd=self.cma.ask_password()
        if file_available:
            self.cma.file_list.append(file_path)
            self.cma.password_list.append(a_pwd)
            self.cma.key_list.append(keyfile)
            if self.ask_confirmation(f"{A_C.add_ansi('Activate','hblue')} {file_path}?"):
                self.cma.activate_databases(file_path)

    def menu_clone_map(self):
        """Clones a map into the selected database"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print(MENU_HEADER)
        self.cma.show_databases_listed()
        print("Clone Map:")
        print("---------------------------------")
        print("Select Map to clone")
        db_map_pair=self.menu_select_database_map()
        if db_map_pair:
            selected_db=self.menu_select_database(True)
            if selected_db and selected_db != '': 
                return self.cma.clone_map(db_map_pair,selected_db)
        return ''
        

    def menu_enter_path(self):
        """Asks selection of a directory and returns if the selected path/input is an available directory and the path user input.

        Returns:
            tuple[bool,str]: dir_available, path_user
        """
        input_path = AutocompletePathFile('return string [cyan]ENTER[/cyan], Autofill path/file [cyan]TAB[/cyan], Cancel [cyan]ESC[/cyan]\nOr type complete directory path: ',
                                        F_M.get_app_path(),absolute_path=False,verbose=True,inquire=False).get_input
        path_user = input_path()
        if path_user in ['',None]:
            return False, path_user
        path_user=F_M.fix_separator_in_path(path_user)
        file_exist, is_file = F_M.validate_path_file(path_user)
        if file_exist and not is_file:
            dir_available=True
        elif file_exist and is_file:
            path_user=F_M.extract_path(path_user)
            dir_available=True
        else:
            dir_available=False 
        return dir_available, path_user

    def menu_get_a_directory(self,allow_create_dir=False):
        """Gets a directory from user

        Args:
            allow_create_dir (bool, optional): If does not exit create the dir?. Defaults to False.

        Returns:
            tuple: dir_available, path_user
        """
        path_list=[F_M.get_app_path()]
        for fff in self.cma.file_list:
            a_path=F_M.extract_path(fff)
            if a_path not in path_list:
                path_list.append(a_path) 
        ch=path_list+['Enter Path', 'Back']
        menu = [inquirer.List(
            'dir_select',
            message="Please select",
            choices=ch,
            carousel=False,
            )]
        # menu=[{'type': 'list',
        #     'name': 'dir_select',
        #     'message': 'Please select: (use arrow keys)',
        #     'choices': path_list+['Enter Path', 'Back']
        #     }]
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print(MENU_HEADER)
            print("Select Directory:")
            print("----------")
            answers = inquirer.prompt(menu)
            if answers['dir_select'] in path_list:
                return True, answers['dir_select']
            elif answers['dir_select']=='Enter Path':
                dir_available, path_user=self.menu_enter_a_directory(allow_create_dir)
                if (dir_available, path_user)!=(False,''):
                    return dir_available, path_user
            elif answers['dir_select']=='Back':
                return False,''

    def menu_enter_a_directory(self,allow_create_dir=False):
        """Autocomplete for directory

        Args:
            allow_create_dir (bool, optional): Creates new directory. Defaults to False.

        Returns:
            tuple:  dir_available, path_user
        """
        input_path = AutocompletePathFile('return string [cyan]ENTER[/cyan], Autofill path/file [cyan]TAB[/cyan], Cancel [cyan]ESC[/cyan]\nOr type complete directory path: ',
                                        F_M.get_app_path(),absolute_path=False,verbose=True).get_input
        path_user = input_path()
        if not path_user:
            return False,''
        file_exist, is_file = F_M.validate_path_file(path_user)
        if file_exist and not is_file:
            path_user=F_M.fix_separator_in_path(path_user)
            dir_available=True
        elif file_exist and is_file:
            path_user=F_M.extract_path(path_user)
            path_user=F_M.fix_separator_in_path(path_user)
            dir_available=True
        else:
            dir_available=False
            if allow_create_dir:
                if self.ask_confirmation(f"Path {path_user} does not exist create it?") :
                    try:
                        os.makedirs(path_user)
                        dir_available=True
                    except Exception as eee:
                        print(f'Could not create path directory {path_user}: {eee}')
                        dir_available=False
        return dir_available, path_user


    def menu_get_an_existing_file(self,path, extension=".db"):
        """Gets a file from user selection of files with extension in path folder.

        Args:
            path (str): fath to look for files
            extension (str, optional): None or "" for all files. Defaults to ".db".

        Returns:
            _type_: _description_
        """
        file_available=False
        file_user=None
        database_list=F_M.get_file_list(path,extension)
        ch=database_list+['Enter File', 'Back']
        menu = [inquirer.List(
            'file_select',
            message="Please select",
            choices=ch,
            carousel=False,
            )]
        
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print(MENU_HEADER)
            print("Select File:")
            print("----------")
            
            answers = inquirer.prompt(menu)
            if answers['file_select'] in database_list:
                return True, answers['file_select']
            elif answers['file_select']=='Enter File':
                input_file = AutocompletePathFile('return string [cyan]ENTER[/cyan], Autofill path/file [cyan]TAB[/cyan], Cancel [cyan]ESC[/cyan]\nOr type complete path to file: ',
                                        F_M.get_app_path(),absolute_path=False,verbose=True).get_input
                file_user = input_file()
                if not file_user:
                    continue
                file_exist, is_file = F_M.validate_path_file(file_user)
                if file_exist and not is_file:
                    file_available=False
                elif file_exist and is_file:
                    file_user=F_M.extract_path(file_user)
                    file_available=True
                else:
                    file_available=False
                return file_available, file_user
            elif answers['file_select']=='Back':
                return False,''
        

    def menu_create_new_database_file(self):
        """Create New Database File
        """
        dir_available,path_user=self.menu_get_a_directory(True)
        file_available=False
        if dir_available:
            file_user=input("Enter File name for new DB: ")
            file_user=F_M.clean_filename(file_user)
            file_user=F_M.extract_filename(file_user,False)
            file_path=os.path.join(path_user,file_user+".db")
            file_available=True
        if file_available:
            if not os.path.exists(file_path):
                self.cma.create_filemap_database(file_path)
                return ''
            return f'[yellow]File {file_path} Already Exists!'
        return '[yellow]File Not available!'


    def menu_select_database(self,active):
        """Select a database"""
        ia_list=self.cma.show_active_inactive_databases(active,False)
        active_inactive_list=[]
        selected_db=''
        for _,i_a in ia_list:
            active_inactive_list.append(i_a)
        if len(active_inactive_list)==0:
            return f"[yellow]No {'active' if active else 'inactive'} database to select!!"
        elif len(active_inactive_list)>1:
            ch=active_inactive_list+['Back']
            menu = [inquirer.List(
                'db_select',
                message="Please select",
                choices=ch,
                carousel=False,
                )]
            answers = inquirer.prompt(menu)
            if answers['db_select'] in active_inactive_list:
                return answers['db_select']
            elif answers['db_select']=='Back':
                return ''
        else:
            selected_db=active_inactive_list[0]  
        return selected_db

    def map_validation(self,answers, current):
        """Validates map
        """
        not_allowed = '"/'+"'|><={}[]()" #r'[":$\/\{\}\[\]\|\& \]'
        for char in current:
            if char in not_allowed:
                raise inquirer.errors.ValidationError("", reason=f'Map name does not allow these characters "{str(not_allowed)}".') 
        for a_db in self.cma.active_databases:
            if not self.cma.validate_new_map(current,a_db['file']):
                raise inquirer.errors.ValidationError("", reason=f'Map "{current}" already exists. Please enter a non existing map name')
        return True

    def menu_create_new_map(self):
        """New map"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print(MENU_HEADER)
        print("Create New Map:")
        print("----------")
        selected_db=self.menu_select_database(True)
        if selected_db and selected_db != '':    
            dir_available, path_to_map = self.menu_enter_path()
            if dir_available and path_to_map:
                print(f'[green]Selected path:{path_to_map}')
                print(f'[yellow]Replacements: % (Date_Time), # (Date), ? (Time), & (Dir), ! (Full_Path) ') 
                tablename=self.menu_get_table_name_input()
                tablename=self.cma.format_new_table_name(tablename,path_to_map)
                fm=self.cma.get_file_map(selected_db)
                if tablename not in ['',None]+fm.db.tables_in_db():   
                    shallow=self.ask_confirmation(f"Would you like a {A_C.add_ansi('Shallow','hblue')} map?",False)  
                    fm.db.create_connection()    
                    fm.map_a_path_to_db(tablename,path_to_map,True,shallow_map=shallow)
        return ''

    def menu_delete_map(self):
        """Kill map"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print(MENU_HEADER)
        print("Delete Map:")
        print("----------")
        answers={'table_name':''}
        selected_db=self.menu_select_database(True)
        if selected_db and selected_db != '':
            while True:
                map_list=self.cma.get_maps_in_db(selected_db)
                if len(map_list)==0:
                    return '[yellow] No maps to delete!'
                ch_hints={}
                for a_map in map_list:
                    ch_hints.update({a_map:self.cma.get_map_info_text(selected_db,a_map)})
                ch_hints.update({'Back':'Go Back'})    
                ch=ch_hints.keys()
                menu = [inquirer.List(
                    'map_delete',
                    message="Please select",
                    choices=ch,
                    carousel=False,
                    hints=ch_hints,
                    )]
                answers = inquirer.prompt(menu)
                if answers['map_delete'] == 'Back':
                    return ''
                if answers['map_delete'] not in ['',None]:
                    tablename=answers['map_delete']
                    # path_to_map="D:\Downloads"
                    fm=self.cma.get_file_map(selected_db) 
                    fm.db.create_connection()
                    count=fm.db.get_number_or_rows_in_table(tablename)
                    if self.ask_confirmation(f"Sure to {A_C.add_ansi('delete','hred')} Map {tablename} with {count} elements?"):
                        fm.delete_map(tablename)

    def menu_rename_map(self):
        """rename map"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print(MENU_HEADER)
        print("Rename Map:")
        print("----------")
        answers={'table_name':''}
        selected_db=self.menu_select_database(True)
        if selected_db and selected_db != '':
            while True:
                map_list=self.cma.get_maps_in_db(selected_db)
                if len(map_list)==0:
                    return '[yellow] No maps to rename!'
                ch_hints={}
                for a_map in map_list:
                    ch_hints.update({(a_map,a_map):self.cma.get_map_info_text(selected_db,a_map)})
                ch_hints.update({'Back':'Go Back'})    
                ch=ch_hints.keys()
                menu = [inquirer.List(
                    'map_rename',
                    message="Please select",
                    choices=ch,
                    carousel=False,
                    hints=ch_hints,
                    )]
                answers = inquirer.prompt(menu)
                if answers['map_rename'] == 'Back':
                    return ''
                if answers['map_rename'] not in ['',None]:
                    tablename=answers['map_rename']
                    # path_to_map="D:\Downloads"
                    print(f'[yellow]Replacements: % (Date_Time), # (Date), ? (Time), & (Dir), ! (Full_Path) ') 
                    new_tablename=self.menu_get_table_name_input(tablename)
                    fm=self.cma.get_file_map(selected_db)
                    data=fm.db.get_data_from_table(fm.mapper_reference_table,'*',f"tablename='{tablename}'")
                    #field_list=['id','dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype']
                    path_to_map=os.path.join(data[0][5],data[0][3])
                    new_tablename=self.cma.format_new_table_name(new_tablename,path_to_map)
                    if new_tablename not in ['',None]+fm.db.tables_in_db():
                        fm.db.create_connection()
                        print(f'Renaming Map [yellow]"{tablename}"[/yellow] to [green]"{new_tablename}"')
                        was_renamed=fm.rename_map(tablename,new_tablename)
                        if was_renamed:
                            return f'Renaming success to [green]"{new_tablename}"'
                        print(f'Renaming Failed [red]"{tablename}"')
                        print("-"*33)
                        print("Press any key to continue")
                        print("-"*33)
                        getch()
        return ''

    def menu_get_table_name_input(self,default=None):
        tablename=''
        menu = [inquirer.Text(
                'table_name',
                message="(Leave blank to exit) Type the new table Name",
                default=default,
                validate=self.map_validation,
                )]
        answers = inquirer.prompt(menu)
        if str(answers['table_name']).strip() not in ['',None]:
            tablename=answers['table_name']
        return tablename

    def menu_select_multiple_database_map(self)->list[tuple]:
        """Looks in all databases listed for all maps.

        Returns:
            list[tuple]: list of selected (database,map) tuples. [] if none selected
        """
        db_map_pair_list=self.cma.get_all_maps()
        selected_db_map_pair_list=[]
        if len(db_map_pair_list)>0:
            field_list=['id','dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype']
            str_db_map=''
            # d_m1=DataManage(db_map_pair_list,["db",'Map'])
            # str_db_map=d_m1.get_tabulated_fields(fields_to_tab=None,index=False,justify='left',header=False)
            end_list=[]
            for database,a_map in db_map_pair_list:
                map_info=self.cma.get_map_info(database,a_map)
                if len(map_info)>0:
                    end_list.append(map_info[0]+(database,))
            d_m1=DataManage(end_list,field_list+["db"])
            d_m1.df
            str_db_map=d_m1.get_tabulated_fields(fields_to_tab=['tablename','mount','mappath'],index=False,justify='left',header=False)
            str_list=str_db_map.split('\n')
            map_list=str_list
            choice_hints={}
            default_list=[]
            for txt_ta_m_map,db in zip(str_list,d_m1.df['db']):
                choice_hints.update({(f"{txt_ta_m_map}", f"{txt_ta_m_map}"): f"Map in database: {db}"})
            menu = [inquirer.Checkbox(
                'db_map_select',
                message="Select Maps",
                choices=choice_hints.keys(),
                default=default_list,
                hints=choice_hints,
                )]
            answers = inquirer.prompt(menu)
            # print('got->',answers,'compare to:',map_list)
            for answ_txt in answers['db_map_select']: 
                if answ_txt in map_list:
                    for str_pair,db_map_pair in zip(map_list,db_map_pair_list):
                        if str_pair == answ_txt:
                            selected_db_map_pair_list.append(db_map_pair)
            return selected_db_map_pair_list
        return selected_db_map_pair_list

    def menu_select_database_map(self)->tuple:
        """Looks in all databases listed for all maps.

        Returns:
            tuple: selecte database,map. None if no selected
        """
        db_map_pair_list=self.cma.get_all_maps()
        if len(db_map_pair_list)>0:
            field_list=['id','dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype']
            str_db_map=''
            # d_m1=DataManage(db_map_pair_list,["db",'Map'])
            # str_db_map=d_m1.get_tabulated_fields(fields_to_tab=None,index=False,justify='left',header=False)
            end_list=[]
            for database,a_map in db_map_pair_list:
                map_info=self.cma.get_map_info(database,a_map)
                if len(map_info)>0:
                    end_list.append(map_info[0]+(database,))
                else:
                    print(f"Table {a_map} not in Reference table!!")
                    print("Press any key to continue")
                    A_C.wait_key_press()

            d_m1=DataManage(end_list,field_list+["db"])
            str_db_map=d_m1.get_tabulated_fields(fields_to_tab=['tablename','mount','mappath',"db"],index=False,justify='left',header=False)
            str_list=str_db_map.split('\n')
            map_list=str_list
            #map_list=[]
            # for db_map_pair in db_map_pair_list:
            #     map_list.append(f'Map: {db_map_pair[1]} in DB: {db_map_pair[0]}')
            ch=map_list+['Back']
            menu = [inquirer.List(
                'db_map_select',
                message="Please select",
                choices=ch,
                carousel=False,
                )]
            answers = inquirer.prompt(menu)
            if answers['db_map_select'] == 'Back':
                return None       
            elif answers['db_map_select'] in map_list:
                for str_pair,db_map_pair in zip(map_list,db_map_pair_list):
                    if str_pair == answers['db_map_select']:
                        print(db_map_pair)
                        return db_map_pair
        return None

    def menu_continue_mapping(self):
        """Menu for processing a map"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print(MENU_HEADER)
        print("Continue Mapping:")
        print("----------")
        db_map_pair=self.menu_select_database_map()
        if not db_map_pair:
            return ''
        fm=self.cma.get_file_map(db_map_pair[0])
        data=fm.db.get_data_from_table(db_map_pair[1],'*',f'md5="{MD5_CALC}"')
        if len(data)==0:
            return f"[green]All files in {db_map_pair[1]} are already Mapped"
        msg = fm.remap_map_in_thread_to_db(db_map_pair[1],None,True)
        if msg != "":
            msg= "[magenta]"+msg 
        return msg 

    def menu_process_map(self):
        """Menu for processing a map"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print(MENU_HEADER)
        print("Process Map:")
        print("----------")
        db_map_pair=self.menu_select_database_map()
        if not db_map_pair:
            return ''
        
        choices_hints = {
        "Browse Tree": "Allows browsing the map's tree",
        "Browse Directories": "Allows browsing the map's Folders",
        "Find Duplicates": "Duplicates are files with the same md5 sum, in the same folder but with different names.",
        "Find Repeated": "Repeated are files with the same md5 sum, in any folder within the map.",
        "Search Map": "Search for files in the selected Map",
        "Map Directory Selection": "Make a selection map of selected folders.",
        "Map Files Selection": "Make a selection map of selected Files.",
        "Back": "Go back"}
        ch=list(choices_hints.keys())
        menu = [inquirer.List(
            'map_process',
            message="Please select",
            choices=ch,
            carousel=False,
            hints=choices_hints,
            )]
        while True:
            print("----------")
            answers = inquirer.prompt(menu)
            if answers['map_process'] == 'Back':
                return ''
            elif answers['map_process'] == 'Browse Tree': 
                msg=self.cma.browse_file_directories(db_map_pair,'file')
                if isinstance(msg,str):
                    return msg
            elif answers['map_process'] == 'Find Duplicates': 
                duplicte_list=self.cma.find_duplicates_in_database(db_map_pair[0],db_map_pair[1])
                self.menu_select_from_list_map(duplicte_list,db_map_pair)
            elif answers['map_process'] == 'Find Repeated': 
                repeat_list=self.cma.find_repeated_in_database(db_map_pair[0],db_map_pair[1])
                self.menu_select_from_list_map(repeat_list,db_map_pair)
            elif answers['map_process'] == 'Search Map': 
                fs_list=self.menu_search_in_maps([db_map_pair],True) #set to false to get the file structure list
                # menu_select_from_list_map(repeat_list,db_map_pair)
            elif answers['map_process'] == 'Browse Directories': 
                msg=self.cma.browse_file_directories(db_map_pair,'dir')
                if isinstance(msg,str):
                    return msg
            elif answers['map_process'] == 'Map Directory Selection': 
                msg=self.cma.browse_file_directories(db_map_pair,'dir_multiple')
                if isinstance(msg,str):
                    return msg
                elif isinstance(msg,tuple):
                    node_list,trace_list=msg
                    if len(node_list)>0:
                        selection_name=str(datetime.now()).replace(" ","_").replace("-","").replace(":","").replace(".","")
                        selection_name=selection_name+"_selection"
                        fm=self.cma.get_file_map(db_map_pair[0])
                        where=''
                        for iii,trace in enumerate(trace_list):
                            if iii==0:
                                where=f'filepath LIKE "%{trace}%"'
                            else:
                                where=where+f' OR filepath LIKE "%{trace}%"'
                        cols=fm.db.get_column_list_of_table(db_map_pair[1])
                        datasel=str(cols[1:]).replace("[",'').replace("]",'').replace("'",'')
                        selected_data=fm.db.get_data_from_table(db_map_pair[1],datasel,where)
                        if len(selected_data)>0:
                            fm.map_a_selection(selection_name,db_map_pair[1],selected_data,MAP_TYPES_LIST[1])
                            return f'[green] Following selection maps built:{selection_name}'
                        
            elif answers['map_process'] == 'Map Files Selection': 
                msg=self.cma.browse_file_directories(db_map_pair,'file_multiple')
                if isinstance(msg,str):
                    return msg
                elif isinstance(msg,tuple):
                    selected_db_map_pair, _, data=msg
                    selection_name=str(datetime.now()).replace(" ","_").replace("-","").replace(":","").replace(".","")
                    selection_name=selection_name+"_selection"
                    selections=self.cma.make_selection_maps(selection_name,selected_db_map_pair,data)
                    if selections:
                        return f'[green] Following selection maps built:{selections}'
                    
                        
    def menu_process_selection_map(self):
        """Menu for processing a selection map"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print(MENU_HEADER)
        print("Process Selection Map:")
        print("----------")
        db_map_pair=self.menu_select_database_map()
        if not db_map_pair:
            return ''
        
        choices_hints = {
        "Browse Tree": "Allows browsing the map's tree",
        "Browse Directories": "Allows browsing the map's Folders",
        "Search Map": "Search for files in the selected Map",
        "Add Files to Selection": "You can add files from origin map.",
        "Remove files in Selection": "You can remove files in Selection map.",
        "Selection Map Action": "Do Actions to the files in selection maps",
        "Back": "Go back"}
        ch=list(choices_hints.keys())
        menu = [inquirer.List(
            'map_process',
            message="Please select",
            choices=ch,
            carousel=False,
            hints=choices_hints,
            )]
        while True:
            print("----------")
            answers = inquirer.prompt(menu)
            if answers['map_process'] == 'Back':
                return ''
            elif answers['map_process'] == 'Browse Tree': 
                msg=self.cma.browse_file_directories(db_map_pair,'file')
                if isinstance(msg,str):
                    return msg
            elif answers['map_process'] == 'Find Duplicates': 
                duplicte_list=self.cma.find_duplicates_in_database(db_map_pair[0],db_map_pair[1])
                self.menu_select_from_list_map(duplicte_list,db_map_pair)
            elif answers['map_process'] == 'Find Repeated': 
                repeat_list=self.cma.find_repeated_in_database(db_map_pair[0],db_map_pair[1])
                self.menu_select_from_list_map(repeat_list,db_map_pair)
            elif answers['map_process'] == 'Search Map': 
                fs_list=self.menu_search_in_maps([db_map_pair],True) #set to false to get the file structure list
                # menu_select_from_list_map(repeat_list,db_map_pair)
            elif answers['map_process'] == 'Browse Browse Directories': 
                msg=self.cma.browse_file_directories(db_map_pair,'dir')
                if isinstance(msg,str):
                    return msg

    def menu_search_in_maps(self,selected_db_map_pair_list:list=None,explore=True):
        """Search in Maps"""
        if not selected_db_map_pair_list:
            selected_db_map_pair_list=self.menu_select_multiple_database_map()
        print('selected_db_map_pair_list-->',selected_db_map_pair_list)
        msg=''
        (ans_txt, msg, is_valid)=A_C.get_sql_input()
        print(f'Searching for:{ans_txt}')
        if ans_txt not in ['',None] and is_valid:
            fs_list=[]
            db_map_list=[]
            # data_list=[]
            search=f'{ans_txt} search'
            for db_map_pair in selected_db_map_pair_list:
                where=ans_txt #f"filename LIKE '%{ans_txt}%'"
                # including Id is important
                fs=self.cma.map_to_file_structure(db_map_pair[0],db_map_pair[1],where=where,fields_to_tab=['id'],sort_by=None,ascending=True)
                print(f'Found {len(fs)} in {db_map_pair[1]}')
                if len(fs)>0:
                    fs_list.append(fs.copy())
                    db_map_list.append(db_map_pair)
                    del fs
            if explore:
                if len(fs_list)==0:
                    fs_list=[(f'Nothing Found for {ans_txt}',0)]
                # selected_db_map_pair, selected_id, data=self.cma.explore_one_file_search(search,fs_list,db_map_list)    
                selected_db_map_pair, _, data=self.cma.explore_multiple_file_search(search,fs_list,db_map_list)
                selection_name=str(datetime.now()).replace(" ","_").replace("-","").replace(":","").replace(".","")
                selection_name=selection_name+"_selection"
                selections=self.cma.make_selection_maps(selection_name,selected_db_map_pair,data)
                if selections:
                    return f'[green] Following selection maps built:{selections}'
            else:
                return fs_list     
        return msg
    
    

    def menu_select_from_list_map(self,d_list,db_map_pair,selection_type='repeated'):
        """Menu for Selection
        """
        # os.system('cls' if os.name == 'nt' else 'clear')
        # print(MENU_HEADER)
        print(f"Selecting on {db_map_pair}")
        print("Map Selection:")
        print("----------")
        choices_hints = {
        "Browse/Select Files": "Make a selection",
        # "Remove Duplicates": "Duplicates are files with the same md5 sum, in the same folder but with different names.",
        "Back": "Go back"}
        ch=list(choices_hints.keys())
        menu = [inquirer.List(
            'map_actions',
            message="Please select",
            choices=ch,
            carousel=False,
            hints=choices_hints,
            )]
        answers = inquirer.prompt(menu)
        if answers['map_actions'] == 'Back':
            return ''
        elif answers['map_actions'] == 'Browse/Select Files': 
            amount_per_show=1000
            all_selected=[]
            if len(d_list)<amount_per_show:
                if selection_type=='repeated':
                    selected_items=self.menu_make_selection(d_list,'exlast') #,'none')
                else:
                    selected_items=self.menu_make_selection(d_list,'none')
                if isinstance(selected_items,list):    
                    all_selected=selected_items
                else:
                    return ''
            else:
                lll=int(len(d_list)/amount_per_show) 
                # rrr=len(d_list) % amount_per_show # remainder
                for part in range(lll+1):
                    m_list=self.list_select(d_list,part*amount_per_show,(part+1)*amount_per_show)
                    if selection_type=='repeated':
                        selected_items=self.menu_make_selection(m_list,'exlast') #,'none')
                    else:
                        selected_items=self.menu_make_selection(m_list,'none')
                    
                    if isinstance(selected_items,list):
                        if len(selected_items)==0:
                            if not self.ask_confirmation("Continue Selection?",True):
                                return 'User Cancel'
                        all_selected.append(selected_items)
                    else:
                        return ''
            
            all_id_list=self._get_id_list_from_rem_keep_dict(selected_items,d_list,a_key='all')
            inmap_size=self.cma.get_size_of_file_selection(db_map_pair,all_id_list)
            print(f"Selected {len(all_selected)} items of {len(all_id_list)}")
            rem_id_list=self._get_id_list_from_rem_keep_dict(selected_items,d_list,a_key='remove')
            total_size=self.cma.get_size_of_file_selection(db_map_pair,rem_id_list)
            print(f"Selected for removal {F_M.get_size_str_formatted(total_size,11,False)} from {F_M.get_size_str_formatted(inmap_size,11,False)}")
            print("Press any key to continue")
            A_C.wait_key_press()
            return self.menu_duplicate_removal_confirmation(all_selected,d_list,db_map_pair)

    def _get_id_list_from_rem_keep_dict(self,selected_items,d_list,a_key='remove'):
        """Gets an id list of items in rem,keep dictionary

        Args:
            selected_items (_type_): selected items
            d_list (_type_): duplicate list
            a_key (str, optional): 'remove', 'keep' or 'all'. Defaults to 'remove'.

        Returns:
            list: id list of items with a_key
        """
        rem_keep_dict=self.cma.get_remove_keep_dict(selected_items,d_list)
        id_list=[]
        for _,rem_keep in rem_keep_dict.items():
            id_list=id_list+rem_keep[a_key]
        return id_list


    @staticmethod
    def list_select(a_list:list,from_item:int=None,to_item:int=None):
        if not from_item and not to_item:
            return a_list
        if from_item and not to_item:
            return a_list[from_item:]
        if to_item >= len(a_list):
            to_item=len(a_list)
        if to_item and (not from_item or from_item==0):
            return a_list[:to_item]
        if from_item>=len(a_list):
            return []
        if from_item<0 or to_item<0:
            return a_list
        if from_item==to_item and from_item<len(a_list):
            return [a_list[from_item]]
        if from_item<len(a_list) and to_item>from_item:
            return a_list[from_item:to_item]
        return a_list

    
    def menu_duplicate_removal_confirmation(self,selected_items,duplicte_list,db_map_pair):
        """Confirms removal of selected files

        Args:
            selected_items (list): items user selected
            duplicte_list (lis): list of dictionaries from duplicated files
            db_map_pair (tuple): (database,map)

        Returns:
            str: message
        """
        rem_keep_dict=self.cma.get_remove_keep_dict(selected_items,duplicte_list)
        while len(rem_keep_dict)>0:
            choices_hints = {
            "Remove Selected": "No going back",
            "Selection map Remove/Keep": "Makes a selection map of removed and keep",
            "Cancel": "Cancel"}
            ch=list(choices_hints.keys())
            menu = [inquirer.List(
                'remove_type',
                message="Please select",
                choices=ch,
                carousel=False,
                hints=choices_hints,
                )]
            answers = inquirer.prompt(menu)
            if answers['remove_type'] == 'Cancel':
                return '[yellow]Removal Cancelled'
            elif answers['remove_type'] == 'Selection map Remove/Keep': 
                fm=self.cma.get_file_map(db_map_pair[0])
                name=self.cma.format_new_table_name("%","")
                rem_id_list=self._get_id_list_from_rem_keep_dict(selected_items,duplicte_list,'remove')
                if len (rem_id_list)>0:
                    fm.map_an_id_selection('remove_'+name,db_map_pair[1],rem_id_list,MAP_TYPES_LIST[3])
                keep_id_list=self._get_id_list_from_rem_keep_dict(selected_items,duplicte_list,'keep')
                if len (keep_id_list)>0:
                    fm.map_an_id_selection('keep_'+name,db_map_pair[1],keep_id_list,MAP_TYPES_LIST[4])
            elif answers['remove_type'] == 'Remove Selected': 
                for md5,rem_keep in rem_keep_dict.items():
                    rem=True
                    if len(rem_keep['keep'])==0:
                        print('Marked for removal:...')
                        rem= self.ask_confirmation(f'You aint keeping a copy of any of {len(rem_keep["all"])} files, confirm deletion?')
                    if rem:
                        for an_id in rem_keep['remove']:
                            dupli_dict=self.cma.get_dict_from_id_in_duplicate(an_id,duplicte_list)
                            print(self.cma.remove_file_from_mount_and_map(dupli_dict,db_map_pair))                    
            return ''


    def menu_make_selection(self,duplicte_list,mark='exlast'):
        """Menu to select duplicate files:

        Args:
            duplicte_list (list): list of tuples containing (mapid, dict)
            mark (str, optional): 'last','exlast','first','exfirst' ex = except . Defaults to 'exlast'.
        """
        choice_hints={}
        default_list=[]
        for dup_tup in duplicte_list:
            for iii,dupli_dict in enumerate(dup_tup):
                choice_hints.update({(f"{dupli_dict['filename']}", f"{dupli_dict['id']}"): f"{dupli_dict['md5']} in {dupli_dict['filepath']}"})
                if iii==len(dup_tup)-1 and mark=='last': # last one
                    default_list.append(f"{dupli_dict['id']}")
                elif iii!=len(dup_tup)-1 and mark=='exlast': # except last one
                    default_list.append(f"{dupli_dict['id']}")
                elif iii==0 and mark=='first': # first one
                    default_list.append(f"{dupli_dict['id']}")  
                elif iii!=0 and mark=='exfirst': # except first one
                    default_list.append(f"{dupli_dict['id']}")  
        if len(choice_hints)>0:      
            menu = [
            inquirer.Checkbox(
                "file_selection",
                message="Select files",
                choices=choice_hints.keys(),
                default=default_list,
                hints=choice_hints
            )]
            answers = inquirer.prompt(menu)
            return answers['file_selection']
        else:
            print('[green] There are no duplicates :)')
            return None


    def menu_backup_functions(self):
        """Interactive menu backups"""
        msg=''
        ch=['Map to Backup','Shallow compare Backups','Back']
        in_name='backup'
        menu = [inquirer.List(
            in_name,
            message="Please select",
            choices=ch,
            carousel=False,
            )]
        
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print(MENU_HEADER)
            print("Backup:")
            if not msg in ['',None]:
                print("---------------------------------")
                print(msg)
                msg=''
            print("---------------------------------")
            answers = inquirer.prompt(menu)
            if answers['backup']=='Map to Backup':
                if len(self.cma.active_databases)==0:
                    return '[magenta]There are no active databases![\magenta]'
                db_map_pair=self.menu_select_database_map()
                if not db_map_pair:
                    return ''
                print('Select/create a directory to set the map backup:')
                dir_available, path_user=self.menu_enter_a_directory(True)
                if (dir_available, path_user)!=(False,''):
                    msg = self.ba.map_to_backup(db_map_pair,path_user,True,None)
            elif answers['backup']=='Shallow compare Backups':
                self.menu_shallow_compare_maps(True)
            elif answers['backup']=='Back':
                return ''

    def menu_mapping_functions(self):
        """Interactive menu handle databases"""
        msg=''
        ch=['Create New Map', 'Delete Map','Clone Map','Rename Map','Update Map',
            'Shallow Compare Maps','Deepen Shallow Map','Continue Mapping','Process Map','Search in Maps','Back']
        in_name='mapping'
        menu = [inquirer.List(
            in_name,
            message="Please select",
            choices=ch,
            carousel=False,
            )]
        
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print(MENU_HEADER)
            print("Mapping:")
            print("----------")
            if len(self.cma.active_databases)==0:
                return '[magenta]There are no active databases![\magenta]'
            self.cma.show_maps()
            if not msg in ['',None]:
                print("---------------------------------")
                print(msg)
                msg=''
            print("---------------------------------")
            answers = inquirer.prompt(menu)
            if answers['mapping']=='Create New Map':
                msg=self.menu_create_new_map()
            elif answers['mapping']=='Delete Map': 
                msg=self.menu_delete_map()
            elif answers['mapping']=='Clone Map': 
                msg=self.menu_clone_map()
            elif answers['mapping']=='Rename Map': 
                msg=self.menu_rename_map()
            elif answers['mapping']=='Continue Mapping': 
                msg=self.menu_continue_mapping()
            elif answers['mapping']=='Update Map': 
                msg=self.menu_update_maps()
            elif answers['mapping']=='Shallow Compare Maps': 
                msg=self.menu_shallow_compare_maps()
            elif answers['mapping']=='Deepen Shallow Map': 
                msg=self.menu_deepen_shallow_map()
            elif answers['mapping']=='Process Map':
                msg=self.menu_process_map()
            elif answers['mapping']=='Search in Maps': 
                msg=self.menu_search_in_maps()
            elif answers['mapping']=='Back':
                return ''

    def menu_update_maps(self):
        """Menu update a map"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print(MENU_HEADER)
        print("Update a Map:")
        print("----------")
        db_map_pair=self.menu_select_database_map()
        if db_map_pair:
            return self.cma.update_map(db_map_pair)
        return ''

    def menu_deepen_shallow_map(self):
        """Menu for Shallow Compare two maps"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print(MENU_HEADER)
        print("Deepen Shallow Map:")
        print("----------")
        db_map_pair=self.menu_select_database_map()
        if db_map_pair:
            print(f'Converting {db_map_pair[1]} for calculation...')
            self.cma.shallow_to_deep(db_map_pair)
            fm=self.cma.get_file_map(db_map_pair[0])
            data=fm.db.get_data_from_table(db_map_pair[1],'*',f'md5="{MD5_CALC}"')
            if len(data)==0:
                return f"[green]All files in {db_map_pair[1]} are already Mapped"
            msg = fm.remap_map_in_thread_to_db(db_map_pair[1],None,True)
            if msg != "":
                msg= "[magenta]"+msg 
            return msg
        return ''
    
    def menu_shallow_compare_maps(self,remove_base=False):
        """Menu for Shallow Compare two maps"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print(MENU_HEADER)
        print("Shallow Compare Maps:")
        print("----------")
        db_map_pair_1=self.menu_select_database_map()
        if db_map_pair_1:
            db_map_pair_2=self.menu_select_database_map()
            if not db_map_pair_2:
                return 'No map selected'
            if db_map_pair_1[0]!=db_map_pair_2[0] or db_map_pair_1[1]!=db_map_pair_2[1]:
                map_info_1=self.cma.get_map_info(db_map_pair_1[0],db_map_pair_1[1])
                map_info_2=self.cma.get_map_info(db_map_pair_2[0],db_map_pair_2[1])
                dt_mod_1=map_info_1[0][2]
                dt_mod_2=map_info_2[0][2]
                if datetime.fromisoformat(dt_mod_1) <= datetime.fromisoformat(dt_mod_2):
                    if not remove_base:
                        differences, msg = self.cma.shallow_compare_maps(db_map_pair_1,db_map_pair_2)
                    else:
                        differences, msg, _ = self.ba.shallow_compare_maps_no_base_path(db_map_pair_1,db_map_pair_2,None,None,True)
                else:
                    if not remove_base:
                        differences, msg = self.cma.shallow_compare_maps(db_map_pair_2,db_map_pair_1)   
                    else:
                        differences, msg, _ = self.ba.shallow_compare_maps_no_base_path(db_map_pair_2,db_map_pair_1,None,None,True)
                print(differences['+'])
                print(differences['-']) 
                print(msg)
                print('*'*33)
                print('Press any key to continue ...')
                print('*'*33)
                getch()
                
            else:
                return 'Same map selected'
        else:
            return 'No map selected'
        return ''    

    def main_menu(self):
        """Interactive menu main"""
        msg=''
        ch=['About','Rescan Devices','Handle Databases', 'Mapping', 'Backup', 'Exit']
        menu = [inquirer.List(
            "main_menu",
            message="Please select",
            choices=ch,
            carousel=False,
            )]
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print(MENU_HEADER)
            if msg!='':
                print(msg)
                msg=''
            print("Main Menu:")
            print("----------")
            answers = inquirer.prompt(menu)
            if answers['main_menu']=='Handle Databases':
                msg=self.menu_handle_databases()
            elif answers['main_menu']=='Mapping':
                msg=self.menu_mapping_functions()
            elif answers['main_menu']=='Backup':
                msg=self.menu_backup_functions()
            elif answers['main_menu']=='Rescan Devices':
                msg=self.cma.rescan_database_devices()
            elif answers['main_menu']=='About':
                os.system('cls' if os.name == 'nt' else 'clear')
                print(FILE_MAP_LOGO)
                print(GITHUB)
                print(VERSION)
                print("Press any key to continue")
                getch()
            elif answers['main_menu']=='Exit':
                # Clear the screen and exit program
                os.system('cls' if os.name == 'nt' else 'clear')
                sys.exit(0)

if __name__ == '__main__':
    #main()
    pass
