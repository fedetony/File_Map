#!/usr/bin/env python  # shebang for Unix-based systems
#!pythonw        # shebang for Windows systems
from __future__ import print_function, unicode_literals

import os
import sys
import argparse
import getpass
from datetime import datetime
from rich import print

from class_sqlite_database import SQLiteDatabase
from class_file_manipulate import FileManipulate
from class_device_monitor import DeviceMonitor
from class_file_mapper import *
from class_autocomplete_input import AutocompletePathFile
from class_data_manage import DataManage
from class_file_explorer import *


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
__version__="v.1.1.333 beta"


import inquirer

F_M=FileManipulate()

def calculate_time_elapsed(start_datetime,end_datetime):
    """Calculate the time elapsed between two timestamps"""
    time_elapsed = (end_datetime - start_datetime).total_seconds()
    return time_elapsed

def ask_password(prompt):
    """Prompts the user for a password and returns it."""
    while True:
        password = getpass.getpass(f"Enter your {prompt} password (or leave blank to skip): ")
        if not password or password.strip() == "":
            return None
        else:
            return password
        
file_list=[]
password_list=[]
key_list=[]
active_databases=[]

def main():
    """Argument parser function for File Map

    Raises:
        AttributeError: Wrong number of files or keys.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print(FILE_MAP_LOGO)
    parser = argparse.ArgumentParser(description=f"File Map {__version__}")
    parser.add_argument("files", required=False,  nargs="+", type=str, help="Enter one or several File Map Database Files to process")
    parser.add_argument("-p", "--password",required=False, nargs="+", type=int, default=None, help="File number to prompt for Password for password protected files. Usage -p (1-N) (default: None)")
    parser.add_argument("-k", "--keyfile", required=False,  nargs="+", type=str, default=None, help="For each File enter Path to keyfile for decryption, Enter None if not Encrypted.")
    
    args = parser.parse_args()
    
    for file in args.files:
        file_list.append(file)
        password_list.append(None)
        key_list.append(None)
    
    # Prompt for passwords for files that require them
    if args.password:
        for a_pwd in args.password:
            for iii,file in enumerate(file_list):
                if a_pwd == iii+1:
                    if not password_list[iii]: 
                        #Here store true, and prompt for password next time you need it
                        password_list[iii]=True
                        # Comment remove when debugged and works
                        # password_list[iii]=ask_password(file)

    if args.keyfile:
        if len(file_list) != len(args.keyfile):
            raise AttributeError(f"Wrong amount of KeyFiles entered: Files: {len(file_list)} != Key Files: {len(args.keyfile)}")  
        for iii,(file,a_kf) in enumerate(zip(file_list,args.keyfile)):
            if str(a_kf).strip() in ['None','none','NONE','No','N','n','no']: 
                key_list[iii]=None 
            else:      
                key_list[iii]=str(a_kf).strip()

    #print(file_list,password_list,key_list)
    activate_databases(None)
    main_menu()
    

def activate_databases(db_file_name=None):
    """Activates all databases in file_list using the key. Will prompt for password if DB is password protected.
    """
    for file,pwd,keyf in zip(file_list,password_list,key_list):
        if not db_file_name or db_file_name==file:
            if not is_database_active(file):
                the_ppp=None
                if pwd:
                    the_ppp =ask_password()
                try:
                    fm=FileMapper(file,keyf,the_ppp)
                    active_databases.append({'file':file,'keyfile':keyf,'haspassword':pwd,'mapdb':fm})
                except Exception as eee:
                    print(f"Could not activate {file}: {eee}")

def deactivate_databases(db_file_name=None):
    """Deactivate active databases, closes db connection.

    Args:
        db_file_name (str, optional): deactivate specific database, if None, removes all. Defaults to None.
    """
    active_dbs=active_databases.copy()
    for iii,a_db in enumerate(active_dbs):
        if not db_file_name or db_file_name==a_db['file']:
            fm=a_db['mapdb']
            if isinstance(fm,FileMapper):
                fm.close()
            active_databases.pop(iii)
            
def menu_activate_deactivate_databases(activate):
    """Menu for Deactivating Databases
    """
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(MENU_HEADER)
        if activate:
            print("Activate Databases:")
            print("-----------------------")
            ia_list=show_active_inactive_databases(False,False)
            if len(ia_list)==0:
                return '[yellow]All databases are active!!'
            
        else:
            print("Deactivate Databases:")
            print("-----------------------")
            ia_list=show_active_inactive_databases(True,True)
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
                activate_databases(None)
            else:
                deactivate_databases(None)    
        elif answers['activate_menu']=='Back':
            return ''
        elif answers['activate_menu'] in active_inactive_list:
            if activate:
                activate_databases(answers['activate_menu'])
            else:
                deactivate_databases(answers['activate_menu'])
        else:
            print("Not a valid choice")

def menu_handle_databases():
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
        show_databases_listed()
        if msg!='':
            print(msg)
        print("---------------------------------")
        answers = inquirer.prompt(menu)
        if answers['handle_db_menu']=='Create New Database File':
            msg=menu_create_new_database_file()
        elif answers['handle_db_menu']=='Append Database File': 
            msg=menu_append_database_file()
        elif answers['handle_db_menu']=='Remove Database File':         
            msg=menu_remove_database_file()   
        elif answers['handle_db_menu']=='Activate Database File':
            msg=menu_activate_deactivate_databases(True)
        elif answers['handle_db_menu']=='Deactivate Database File':
            msg=menu_activate_deactivate_databases(False)
        elif answers['handle_db_menu']=='Back':
            return ''

def show_databases_listed():
    """prints databases listed
    """
    print("File Map Databases listed:")
    for iii,(file,pwd,keyf) in enumerate(zip(file_list,password_list,key_list)):
        print(f"\t{iii+1}. {file} {'[yellow](pwd)[/yellow]' if pwd else '()'} {keyf} {'[green]ACTIVE[/green]' if is_database_active(file) else '[magenta]NOT ACTIVE[/magenta]'}")

def show_active_inactive_databases(show_active:bool=True,do_print=True):
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
        for iii,a_db in enumerate(active_databases):
            #'keyfile','haspassword'
            if do_print:
                print(f"\t{iii+1}. {a_db['file']} {'(pwd)' if a_db['haspassword'] else ''} {a_db['keyfile']}")
            ai_list.append([iii,a_db['file']])
    else:
        if do_print:
            print("Inactive Databases:")
        iii=0
        for file,pwd,keyf in zip(file_list,password_list,key_list):
            if not is_database_active(file):
                if do_print:
                    print(f"\t{iii+1}. {file} {'(pwd)' if pwd else ''} {keyf}")
                ai_list.append([iii,file])
                iii=iii+1
    return ai_list

def is_database_active(db_file_name:str)->bool:
    """True if database active

    Args:
        db_file_name (str): Database

    Returns:
        bool: True if database active
    """
    is_active=False
    for a_db in active_databases:
        if db_file_name==a_db['file']:
            is_active=True
            break
    return is_active

def remove_database_file(filename):
    """Removes a file from lists

    Args:
        filename (str): file to remove
    """
    if filename in file_list:
        f_list=file_list.copy()
        for iii,fn in enumerate(f_list):
            if fn==filename:
                file_list.pop(iii)
                password_list.pop(iii)
                key_list.pop(iii)
                break


def menu_remove_database_file():
    """Removes a database from the file_list
    """
    if len(file_list)==0:
        return '[magenta]No databases to remove!'
    answers ={'remove_db_menu':''}
    
    while len(file_list)>0:
        
        menu = [inquirer.List(
            'remove_db_menu',
            message="Please select",
            choices=file_list+['Select All', 
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
        show_databases_listed()
        print("Remove database from list:")
        print("---------------------------------")
        answers = inquirer.prompt(menu)
        if answers['remove_db_menu']=='Select All':
            if answers['remove_all']:
                deactivate_databases(None)
                file_list.clear()
                password_list.clear()
                key_list.clear()
                continue
            
        elif answers['remove_db_menu']=='Back':
            return ''
        elif answers['remove_db_menu'] in file_list:
            f_r=answers['remove_db_menu']
            if answers['remove_file']:
                deactivate_databases(f_r)
                remove_database_file(f_r)
        else:
            print("Not a valid choice, try again.")
    return ''
    
def menu_append_database_file():
    """Adds a database to the file_list
    """
    dir_available,path_user=menu_get_a_directory(False)
    file_available=False
    file_path=''
    if dir_available:
        file_available,file_user=get_an_existing_file(path_user,".db")
        if file_available:
            file_path=os.path.join(path_user,file_user)
            open_filemap(file_path)
            return ''
        return '[yellow]File Not available!'
    return ''

def open_filemap(file_path):
    """Opens a file map database

    Args:
        file_path (str): Complete path and file name of the database
    """
    keyfile=None
    a_pwd=None
    file_available=False
    if ask_confirmation(f"Is {file_path} encrypted?"):
        print("-"*5+"Key Directory"+"-"*5)
        dir_available,path_key=menu_get_a_directory(False)
        if dir_available:    
            # default_fn=F_M.extract_filename(file_path,False)+'_key.txt'
            file_available,file_key=get_an_existing_file(path_key,".txt")
            if file_available:
                keyfile=os.path.join(path_key,file_key) 
    else:
        file_available=True
    if ask_confirmation(f"Is {file_path} password protected?"):
        a_pwd=ask_password()
    if file_available:
        file_list.append(file_path)
        password_list.append(a_pwd)
        key_list.append(keyfile)
        if ask_confirmation(f"Activate {file_path}?"):
            activate_databases(file_path)

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

def menu_enter_path():
    """Asks selection of a directory and returns if the selected path/input is an available directory and the path user input.

    Returns:
        tuple[bool,str]: dir_available, path_user
    """
    input_path = AutocompletePathFile('return string [cyan]ENTER[/cyan], Autofill path/file [cyan]TAB[/cyan], Cancel [cyan]ESC[/cyan]\nOr type complete directory path: ',
                                      F_M.get_app_path(),absolute_path=False,verbose=True,inquire=False).get_input
    path_user = input_path()
    if path_user in ['',None]:
        return False, path_user
    if not path_user.endswith(os.sep):
        path_user=path_user+os.sep
    file_exist, is_file = F_M.validate_path_file(path_user)
    if file_exist and not is_file:
        dir_available=True
    elif file_exist and is_file:
        path_user=F_M.extract_path(path_user)
        dir_available=True
    else:
        dir_available=False 
    return dir_available, path_user

def menu_get_a_directory(allow_create_dir=False):
    """Gets a directory from user

    Args:
        allow_create_dir (bool, optional): If does not exit create the dir?. Defaults to False.

    Returns:
        tuple: dir_available, path_user
    """
    path_list=[F_M.get_app_path()]
    for fff in file_list:
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
            input_path = AutocompletePathFile('return string [cyan]ENTER[/cyan], Autofill path/file [cyan]TAB[/cyan], Cancel [cyan]ESC[/cyan]\nOr type complete directory path: ',
                                      F_M.get_app_path(),absolute_path=False,verbose=True).get_input
            path_user = input_path()
            if not path_user:
                continue
            file_exist, is_file = F_M.validate_path_file(path_user)
            if file_exist and not is_file:
                dir_available=True
            elif file_exist and is_file:
                path_user=F_M.extract_path(path_user)
                dir_available=True
            else:
                dir_available=False
                if allow_create_dir:
                    if ask_confirmation(f"Path {path_user} does not exist create it?") :
                        try:
                            os.makedirs(path_user)
                            dir_available=True
                        except Exception as eee:
                            print(f'Could not create path directory {path_user}: {eee}')
                            dir_available=False
            return dir_available, path_user
        elif answers['dir_select']=='Back':
            return False,''

def get_an_existing_file(path, extension=".db"):
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
        elif answers['dir_select']=='Back':
            return False,''
    

def menu_create_new_database_file():
    """Create New Database File
    """
    dir_available,path_user=menu_get_a_directory(True)
    file_available=False
    if dir_available:
        file_user=input("Enter File name for new DB: ")
        file_user=F_M.clean_filename(file_user)
        file_user=F_M.extract_filename(file_user,False)
        file_path=os.path.join(path_user,file_user+".db")
        file_available=True
    if file_available:
        if not os.path.exists(file_path):
            create_filemap_database(file_path)
            return ''
        return f'[yellow]File {file_path} Already Exists!'
    return '[yellow]File Not available!'

def create_filemap_database(file_path):
    """Creates a new File Map database

    Args:
        file_path (str): Path and filename of new database
    """
    if ask_confirmation("Encrypt Database?"):
        path=F_M.extract_path(file_path)
        kf=F_M.extract_filename(file_path,False)+'_key.txt'
        keyfile=os.path.join(path,kf)
        print(f'New keyfile will be set to: {keyfile}')
        print("Warning: If you erase, or loose the file, you will not be able to access the database anymore!")
    else:
        keyfile=None
    if ask_confirmation("Set Database password?"):
        a_pwd=''
        while True:
            a_pwd=ask_password("New password for:")
            if not a_pwd or a_pwd=='':
                a_pwd=None
                print("Setting no password")
                break
            r_pwd=ask_password("Repeat password for:")
            if a_pwd != r_pwd:
                print("Passwords did not match, try again!")
            else:
                break
    else:
        a_pwd=None
    fm=FileMapper(file_path,keyfile,a_pwd)
    fm.close()
    file_list.append(file_path)
    password_list.append(a_pwd)
    key_list.append(keyfile)

def menu_select_database(active):
    """Select a database"""
    ia_list=show_active_inactive_databases(active,False)
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


def validate_new_map(new_table_name,database):
    """Check if New table name is Correct"""
    fm=get_file_map(database)
    return fm.validate_new_map_name(new_table_name)

def map_validation(answers, current):
    """Validates map
    """
    not_allowed = '"/'+"'|><={}[]()" #r'[":$\/\{\}\[\]\|\& \]'
    for char in current:
        if char in not_allowed:
            raise inquirer.errors.ValidationError("", reason=f'Map name does not allow these characters "{str(not_allowed)}".') 
    for a_db in active_databases:
        if not validate_new_map(current,a_db['file']):
            raise inquirer.errors.ValidationError("", reason=f'Map "{current}" already exists. Please enter a non existing map name')
    return True

def menu_create_new_map():
    """New map"""
    os.system('cls' if os.name == 'nt' else 'clear')
    print(MENU_HEADER)
    print("Create new Map:")
    print("----------")
    selected_db=menu_select_database(True)
    if selected_db and selected_db != '':    
        dir_available, path_to_map = menu_enter_path()
        if dir_available and path_to_map:
            print(f'[green]Selected path:{path_to_map}')
            print(f'[yellow]Replacements: % (Date_Time), # (Date), ? (Time), & (Dir), ! (Full_Path) ') 
            tablename=menu_get_table_name_input()
            tablename=format_new_table_name(tablename,path_to_map)
            fm=get_file_map(selected_db)
            if tablename not in ['',None]+fm.db.tables_in_db():     
                fm.db.create_connection()
                fm.map_a_path_to_db(tablename,path_to_map,True)
    return ''

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

def get_maps_in_db(database):
    """Gets maps in database

    Args:
        database (str): database

    Returns:
        list: list of map's (table names)
    """
    fm=get_file_map(database)
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

def menu_delete_map():
    """Kill map"""
    os.system('cls' if os.name == 'nt' else 'clear')
    print(MENU_HEADER)
    print("Delete Map:")
    print("----------")
    answers={'table_name':''}
    selected_db=menu_select_database(True)
    if selected_db and selected_db != '':
        while True:
            map_list=get_maps_in_db(selected_db)
            if len(map_list)==0:
                return '[yellow] No maps to delete!'
            ch_hints={}
            for a_map in map_list:
                ch_hints.update({a_map:get_map_info_text(selected_db,a_map)})
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
                fm=get_file_map(selected_db) 
                fm.db.create_connection()
                count=fm.db.get_number_or_rows_in_table(tablename)
                if ask_confirmation(f"Sure to delete Map {tablename} with {count} elements?"):
                    fm.delete_map(tablename)

def menu_rename_map():
    """rename map"""
    os.system('cls' if os.name == 'nt' else 'clear')
    print(MENU_HEADER)
    print("Rename Map:")
    print("----------")
    answers={'table_name':''}
    selected_db=menu_select_database(True)
    if selected_db and selected_db != '':
        while True:
            map_list=get_maps_in_db(selected_db)
            if len(map_list)==0:
                return '[yellow] No maps to rename!'
            ch_hints={}
            for a_map in map_list:
                ch_hints.update({(a_map,a_map):get_map_info_text(selected_db,a_map)})
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
                new_tablename=menu_get_table_name_input()
                fm=get_file_map(selected_db)
                data=fm.db.get_data_from_table(fm.mapper_reference_table,'*',f"tablename='{tablename}'")
                #field_list=['id','dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype']
                path_to_map=os.path.join(data[0][5],data[0][3])
                new_tablename=format_new_table_name(new_tablename,path_to_map)
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

def menu_get_table_name_input():
    tablename=''
    menu = [inquirer.Text(
            'table_name',
            message="(Leave blank to exit) Type the new table Name",
            validate=map_validation,
            )]
    answers = inquirer.prompt(menu)
    if str(answers['table_name']).strip() not in ['',None]:
        tablename=answers['table_name']
    return tablename
    
def get_file_map(dbfile) -> FileMapper:
    """Returns the File Map object for database

    Args:
        dbfile (str): path and filename of db

    Returns:
        FileMapper: File map object
    """
    for a_db in active_databases:
        if a_db['file'] == dbfile:
            return a_db['mapdb']
    return None

def get_map_info_text(a_database,a_map):
    """Gets a string with the Map information

    Args:
        a_database (str): database
        a_map (str): map/table name

    Returns:
        str: tabulated string with
        'Date Time Created','Table Name','Serial','Mount','Map Path','Items'
    """
    map_info_str=''
    fm=get_file_map(a_database)
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

def get_map_info_dict(a_database:str,a_map:str)->dict:
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
    fm=get_file_map(a_database)
    if isinstance(fm,FileMapper):
        table_list=fm.db.get_data_from_table(fm.mapper_reference_table,'*',f'tablename="{a_map}"')
        if len(table_list)>0:
            #field_list=['id','dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype']
            field_list=fm.db.get_column_list_of_table(fm.mapper_reference_table)
            data_manage=DataManage(table_list,field_list)
            map_info_dict=data_manage.df.to_dict()
    return map_info_dict

def show_maps():
    """Prints Map information
    """
    for iii,a_db in enumerate(active_databases):
        fm=a_db['mapdb']
        if isinstance(fm,FileMapper):
            print(f"{iii+1}. Maps in {a_db['file']}:")
            table_list=fm.db.get_data_from_table(fm.mapper_reference_table,'*')
            table_list_size=[]
            for table_info in table_list:
                #field_list=['id','dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype']
                data=fm.db.get_data_from_table(table_info[4],'*',f'md5="{MD5_CALC}"')
                num_rows=str(fm.db.get_number_or_rows_in_table(table_info[4]))
                if len(data)>0:
                    num_rows=f'{num_rows}({len(data)})'
                table_list_size.append(table_info+(num_rows,))
            if len(table_list_size)>0:
                field_list=['id','Date Time Created','Date Time Modified','Map Path','Table Name','Mount','Serial','Map Name','Map Type']+['Items']
                data_manage=DataManage(table_list_size,field_list)
                print(data_manage.get_tabulated_fields(fields_to_tab=[field_list[1],field_list[4],field_list[6],field_list[5],field_list[3],'Items'],index=True,justify='left'))

def get_all_maps():
    """Finds all maps in all loaded databases

    Returns:
        list: list of (database,map name)
    """
    output=[]
    for database in file_list:
        maps=[]
        try:
            maps=get_maps_in_db(database)
            for mmm in maps:
                output.append((database,mmm))
        except:
            pass
    return output

def get_map_info(database,a_map):
    """returns the map table information

    Args:
        database (str): database
        a_map (str): Table name

    Returns:
        list(tuple): information on reference table
    """
    fm=get_file_map(database)
    return fm.db.get_data_from_table(fm.mapper_reference_table,'*',f"tablename='{a_map}'")

def menu_select_multiple_database_map()->list[tuple]:
    """Looks in all databases listed for all maps.

    Returns:
        list[tuple]: list of selected (database,map) tuples. [] if none selected
    """
    db_map_pair_list=get_all_maps()
    selected_db_map_pair_list=[]
    if len(db_map_pair_list)>0:
        field_list=['id','dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype']
        str_db_map=''
        # d_m1=DataManage(db_map_pair_list,["db",'Map'])
        # str_db_map=d_m1.get_tabulated_fields(fields_to_tab=None,index=False,justify='left',header=False)
        end_list=[]
        for database,a_map in db_map_pair_list:
            map_info=get_map_info(database,a_map)
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

def menu_select_database_map()->tuple:
    """Looks in all databases listed for all maps.

    Returns:
        tuple: selecte database,map. None if no selected
    """
    db_map_pair_list=get_all_maps()
    if len(db_map_pair_list)>0:
        field_list=['id','dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype']
        str_db_map=''
        # d_m1=DataManage(db_map_pair_list,["db",'Map'])
        # str_db_map=d_m1.get_tabulated_fields(fields_to_tab=None,index=False,justify='left',header=False)
        end_list=[]
        for database,a_map in db_map_pair_list:
            map_info=get_map_info(database,a_map)
            end_list.append(map_info[0]+(database,))
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

def menu_continue_mapping():
    """Menu for processing a map"""
    os.system('cls' if os.name == 'nt' else 'clear')
    print(MENU_HEADER)
    print("Continue Mapping:")
    print("----------")
    db_map_pair=menu_select_database_map()
    if not db_map_pair:
        return ''
    fm=get_file_map(db_map_pair[0])
    data=fm.db.get_data_from_table(db_map_pair[1],'*',f'md5="{MD5_CALC}"')
    if len(data)==0:
        return f"[green]All files in {db_map_pair[1]} are already Mapped"
    fm.remap_map_in_thread_to_db(db_map_pair[1],None,True)
    return ''

def menu_process_map():
    """Menu for processing a map"""
    os.system('cls' if os.name == 'nt' else 'clear')
    print(MENU_HEADER)
    print("Process Map:")
    print("----------")
    db_map_pair=menu_select_database_map()
    if not db_map_pair:
        return ''
    
    choices_hints = {
    "Print Tree": "Tree",
    "Find Duplicates": "Duplicates are files with the same md5 sum, in the same folder but with different names.",
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
        elif answers['map_process'] == 'Print Tree': 
            print('Tree') #db_map_pair)
            fs=None
            fs=map_to_file_structure(db_map_pair[0],db_map_pair[1],where=None,fields_to_tab=None,sort_by=None,ascending=True)
            if len(fs)>0:
                f_e=FileExplorer(None,None,fs)
                _=f_e.browse_files(my_style_expand_size)
            else: 
                return 'No items in Map'
        elif answers['map_process'] == 'Find Duplicates': 
            duplicte_list=find_duplicates_in_database(db_map_pair[0],db_map_pair[1])
            menu_duplicates_actions(duplicte_list,db_map_pair)

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

def menu_search_in_maps():
    #"Find in Map": "Input a word to be searched alon the files",
    selected_db_map_pair_list=menu_select_multiple_database_map()
    print('selected_db_map_pair_list-->',selected_db_map_pair_list)
    menu = [inquirer.Text(
        'search_text',
        message="(Leave blank to exit) Type the text to search the maps",
        )]
    answers = inquirer.prompt(menu)
    ans_txt=str(answers['search_text']).strip()
    print(ans_txt)
    if ans_txt not in ['',None]:
        fs_list=[]
        for db_map_pair in selected_db_map_pair_list:
            where=f"filename LIKE '%{ans_txt}%'"
            fs=map_to_file_structure(db_map_pair[0],db_map_pair[1],where=where,fields_to_tab=None,sort_by=None,ascending=True)
            print('here',len(fs))
            if len(fs)>0:
                fs_list.append(fs.copy())
                del fs
        if len(fs_list)==0:
            fs_list=[(f'Nothing Found for {ans_txt}',0)]
        f_e=FileExplorer(None,None,{f'{ans_txt} search':fs_list})
        _=f_e.browse_files(my_style_expand_size)        
    return ''

def menu_duplicates_actions(duplicte_list,db_map_pair):
    """Menu for duplicate actions
    """
    # os.system('cls' if os.name == 'nt' else 'clear')
    # print(MENU_HEADER)
    print("Duplictes in Map actions:")
    print("----------")
    choices_hints = {
    "Browse Duplicate Files": "",
    "Remove Duplicates": "Duplicates are files with the same md5 sum, in the same folder but with different names.",
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
    elif answers['map_actions'] == 'Browse Duplicate Files': 
        selected_items=menu_duplicate_select(duplicte_list,'none')
    elif answers['map_actions'] == 'Remove Duplicates': 
        selected_items=menu_duplicate_select(duplicte_list)
        if isinstance(selected_items,list):
            if len(selected_items)>0:
                return menu_duplicate_removal_confirmation(selected_items,duplicte_list,db_map_pair)
            else:
                return '[magenta]No duplicates Selected'
        else:
            return ''

def menu_duplicate_removal_confirmation(selected_items,duplicte_list,db_map_pair):
    """Confirms removal of selected files

    Args:
        selected_items (list): items user selected
        duplicte_list (lis): list of dictionaries from duplicated files
        db_map_pair (tuple): (database,map)

    Returns:
        str: message
    """
    rem_keep_dict=get_remove_keep_dict(selected_items,duplicte_list)
    while len(rem_keep_dict)>0:
        choices_hints = {
        "Remove 1 by 1": "No going back",
        "Skip": "Skip removal",
        "Remove All":"Prompt only when no files to keep!",
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
        elif answers['remove_type'] == 'Remove 1 by 1': 
            selected_items=menu_duplicate_select(duplicte_list,'none')
            print('Tree') 
        elif answers['remove_type'] == 'Remove All': 
            for md5,rem_keep in rem_keep_dict.items():
                rem=True
                if len(rem_keep['keep'])==0:
                    print('Marked for removal:...')
                    rem= ask_confirmation(f'You aint keeping a copy of any of {len(rem_keep["all"])} files?')
                if rem:
                    for an_id in rem_keep['remove']:
                        dupli_dict=get_dict_from_id_in_duplicate(an_id,duplicte_list)
                        print(remove_file_from_mount_and_map(dupli_dict,db_map_pair))                    
        return ''

def remove_file_from_mount_and_map(dupli_dict,db_map_pair):   
    print("$"*50,'\nRemoving->',dupli_dict,' in ',db_map_pair ) 
    
    # check mount exist
    fm=get_file_map(db_map_pair[0])
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
    for (a_db,a_map) in get_all_maps():
        #if a_map !=db_map_pair[1]:
            where=f"filepath='{dupli_dict['filepath']}' AND filename='{dupli_dict['filename']}' AND md5='{dupli_dict['md5']}'"
            matches=fm.db.get_data_from_table(a_map,"*",where)
            if len(matches)>0:
                matching_list.append((a_db,a_map)+matches[0])
                # print('match found',a_map,matches)
    print('match found',matching_list)
    return ''

def get_dict_from_id_in_duplicate(an_id:int,duplicte_list):
     for dup_tup in duplicte_list:
        for dupli_dict in dup_tup:
            if an_id == dupli_dict['id']:
                return dupli_dict


def map_to_file_structure(database,a_map,where=None,fields_to_tab:list[str]=None,sort_by:list=None,ascending:bool=True)->dict:
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
    if a_map in get_maps_in_db(database):
        fm=get_file_map(database)
        table_size=fm.db.get_number_or_rows_in_table(a_map)
        if table_size > 10000:
            print(f'[red]Map {a_map} has {table_size} items, is too big to load into a single file structure!')
            if not ask_confirmation("You want to continue?"):
                return {}
        return fm.map_to_file_structure(a_map,where,fields_to_tab,sort_by,ascending)
    return {}

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
    
    

def menu_duplicate_select(duplicte_list,mark='exlast'):
    """Menu to select duplicate files:

    Args:
        duplicte_list (list): list of tuples containing (mapid, dict)
        mark (str, optional): _description_. Defaults to 'exlast'.
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
            elif iii==0 and mark=='first': # last one
                default_list.append(f"{dupli_dict['id']}")  
            elif iii!=0 and mark=='exfirst': # last one
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
        
def find_duplicates_in_database(database,a_map):
    """Returs a list of tuple with the dictionaries of file information of each repeated file.
        Duplicates are the files in the same folder,with different file names but with the same md5 sum.

        Args:
            database (str): database
            tablename (str): table in database

        Returns:
            list: list of tuples, each dictionary in the tuple contains the duplicate files
            [({Dupfileinfo1},{Dupfileinfo2}..{DupfileinfoN}), ...({DupfileinfoX1},{DupfileinfoX2}..{DupfileinfoXN})]
    """
    fm=get_file_map(database)
    return fm.find_duplicates(a_map)
    # repeated_dict=fm.get_repeated_files(fm.db,a_map)
    # showing=['id','filepath','filename','md5','size']
    # key_list=list(repeated_dict.keys())
    # filelist=[]
    # for a_key in key_list:
    #     print(a_key)
    #     fm.re
    #     filelist.append(fm.repeated_list_show(repeated_dict,a_key,[fm.db],[a_map],showing))
    #     # d_m1=DataManage(file_list,showing)
    # return filelist


def menu_mapping_functions():
    """Interactive menu handle databases"""
    msg=''
    ch=['Create New Map', 'Delete Map','Rename Map','Continue Mapping', 'Process Map','Search in Maps','Back']
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
        if len(active_databases)==0:
            return '[magenta]There are no active databases![\magenta]'
        show_maps()
        if not msg in ['',None]:
            print("---------------------------------")
            print(msg)
            msg=''
        print("---------------------------------")
        answers = inquirer.prompt(menu)
        if answers['mapping']=='Create New Map':
            msg=menu_create_new_map()
        elif answers['mapping']=='Delete Map': 
            msg=menu_delete_map()
        elif answers['mapping']=='Rename Map': 
            msg=menu_rename_map()
        elif answers['mapping']=='Continue Mapping': 
            msg=menu_continue_mapping()
        elif answers['mapping']=='Process Map':
            msg=menu_process_map()
        elif answers['mapping']=='Search in Maps': 
            msg=menu_search_in_maps()
        elif answers['mapping']=='Back':
            return ''

def main_menu():
    """Interactive menu main"""
    msg=''
    ch=['Handle Databases', 'Mapping', 'Exit']
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
            msg=menu_handle_databases()
        elif answers['main_menu']=='Mapping':
            msg=menu_mapping_functions()
        elif answers['main_menu']=='Exit':
            # Clear the screen and exit program
            os.system('cls' if os.name == 'nt' else 'clear')
            sys.exit(0)
	
def main_debug():
    db_path=os.path.join(F_M.get_app_path(),"db_Files")
    db_name="test_files_db.db"
    key_file= None#os.path.join(db_path,F_M.extract_filename(db_name,False)+'_key.txt')
    db_path_file=os.path.join(db_path,db_name)

    start_datetime=datetime.now()
    file_list.append(db_path_file)
    password_list.append(None)
    key_list.append(key_file)
    activate_databases(None)
    main_menu()
    # fm=FileMapper(db_path_file,key_file,None)
    # new_map=True
    # #db = SQLiteDatabase(db_path_file,False,None,None)    

    # tablename="table_test_2"

    # if new_map:
    #     # path_to_map="D:\Downloads"
    #     path_to_map="C:\\Users\\Tony\\Downloads"
    #     print(fm.db.table_exists(tablename))
    #     if fm.db.table_exists(tablename):
    #         fm.delete_map(fm.db,tablename)      
    #     print(fm.db.table_exists(tablename))
    #     print(fm.db.table_exists('Cow'))  
    #     fm.map_a_path_to_db(fm.db,tablename,path_to_map,True)

    # # print("repeated files:",get_repeated_files(db,"table_test"))
    # repeated_dict=fm.get_repeated_files(fm.db,tablename)
    # #print("repeated files:",repeated_dict)
    # key_list=list(repeated_dict.keys())

    # showing=['id','filepath','filename','md5','size']
    # filelist3=fm.repeated_list_show(repeated_dict,key_list[33],[fm.db],[tablename],showing)
    # print("Show:", filelist3)
    # mount, mount_active, mappath_exists=fm.check_if_map_device_active(fm.db,tablename,False)
    # print("Check result:", mount, mount_active, mappath_exists)

    # if mount_active and mappath_exists:
    #     for item in filelist3:
    #         print(os.path.join(mount,item[1],item[2]))

    # fm.db.close_connection()
    end_datetime=datetime.now()
    print(f" took {calculate_time_elapsed(start_datetime,end_datetime)} s")

if __name__ == '__main__':
    #main()
    main_debug()
