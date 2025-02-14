#!/usr/bin/env python  # shebang for Unix-based systems
#!pythonw        # shebang for Windows systems
from __future__ import print_function, unicode_literals

import os
import sys
import re
import argparse
import getpass
from datetime import datetime
from rich import print
import hashlib

from class_sqlite_database import SQLiteDatabase
from class_file_manipulate import FileManipulate
from class_device_monitor import DeviceMonitor
from class_file_mapper import FileMapper
from class_autocomplete_input import AutocompletePathFile
from class_data_manage import DataManage


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




from pprint import pprint
from PyInquirer import style_from_dict, Token, prompt
from PyInquirer import Validator, ValidationError, Separator


style = style_from_dict({
    Token.QuestionMark: '#E91E63 bold',
    Token.Selected: '#673AB7 bold',
    Token.Instruction: '',  # default
    Token.Answer: '#2196f3 bold',
    Token.Question: '',
})

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
        menu=[{'type': 'list',
        'name': 'activate_menu',
        'message': 'Please select: (Use arrow keys)',
        'choices': active_inactive_list+['All','Back']
        }]   
        answers = prompt(menu, style=style)
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
    menu=[{'type': 'list',
        'name': 'handle_db_menu',
        'message': 'Please select: (use arrow keys)',
        'choices': ['Create New Database File', 
                    'Append Database File', 
                    'Remove Database File',
                    'Activate Database File',
                    'Deactivate Database File',
                    'Back']
        }]
    msg=''
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(MENU_HEADER)
        show_databases_listed()
        if msg!='':
            print(msg)
        print("---------------------------------")
        answers = prompt(menu, style=style)
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
        return '[magenta]No databases to remove![\magenta]'
    answers ={'remove_db_menu':''}
    while len(file_list)>0:
        menu=[{'type': 'list',
        'name': 'remove_db_menu',
        'message': 'Please select: (Use arrow keys)',
        'choices': file_list+['Select All', 
                    'Back']
        },
        {'type': 'confirm',
        'name': 'remove_all',
        'message': 'You want to remove all?',
        'default': False,
        'when': lambda answers: answers['remove_db_menu'] == 'Select All'
        },
        {'type': 'confirm',
        'name': 'remove_file',
        'message': f"You want to remove {answers['remove_db_menu']}?",
        'default': False,
        'when': lambda answers: answers['remove_db_menu'] in file_list
        }
        ]
        os.system('cls' if os.name == 'nt' else 'clear')
        print(MENU_HEADER)
        show_databases_listed()
        print("Remove database from list:")
        print("---------------------------------")
        answers = prompt(menu, style=style)
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
    {
        'type': 'confirm',
        'name': 'question',
        'message': message,
        'default': default
    }]
    answers = prompt(questions, style=style)
    return answers['question']

def menu_enter_path():
    """Asks selection of a directory and returns if the selected path/input is an available directory and the path user input.

    Returns:
        tuple[bool,str]: dir_available, path_user
    """
    input_path = AutocompletePathFile('return string [cyan]ENTER[/cyan], Autofill path/file [cyan]TAB[/cyan], Cancel [cyan]ESC[/cyan]\nOr type complete directory path: ',
                                      F_M.get_app_path(),absolute_path=False,verbose=True).get_input
    path_user = input_path()
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
    menu=[{'type': 'list',
        'name': 'dir_select',
        'message': 'Please select: (use arrow keys)',
        'choices': path_list+['Enter Path', 'Back']
        }]
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(MENU_HEADER)
        print("Select Directory:")
        print("----------")
        answers = prompt(menu, style=style)
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
    menu=[{'type': 'list',
        'name': 'file_select',
        'message': 'Please select: (use arrow keys)',
        'choices': database_list+['Enter File', 'Back']
        }]
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(MENU_HEADER)
        print("Select File:")
        print("----------")
        answers = prompt(menu, style=style)
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
        menu=[{'type': 'list',
        'name': 'db_select',
        'message': 'Please select: (use arrow keys)',
        'choices': active_inactive_list+['Back']
        }]
        answers = prompt(menu, style=style)
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
    tables=fm.db.tables_in_db()
    if new_table_name in tables:
        return False
    return True

class MapValidator(Validator):
    def validate(self, document):
        for a_db in active_databases:
            if not validate_new_map(document.text,a_db['file']):
                raise ValidationError(
                message=f'Map "{document.text}" already exists. Please enter a non existing map name',
                cursor_position=len(document.text))  # Move cursor to end

def menu_create_new_map():
    """New map"""
    os.system('cls' if os.name == 'nt' else 'clear')
    print(MENU_HEADER)
    print("Create new Map:")
    print("----------")
    answers={'table_name':''}
    selected_db=menu_select_database(True)
    if selected_db and selected_db != '':
        menu=[{
        'type': 'input',
        'name': 'table_name',
        'message': 'Enter table name',
        'validate': MapValidator
        },
        ]   
        answers = prompt(menu, style=style)
        if answers['table_name'] not in ['',None]:
            tablename=answers['table_name']
            # path_to_map="D:\Downloads"
            dir_available, path_to_map = menu_enter_path()
            if dir_available and path_to_map:
                fm=get_file_map(selected_db) 
                fm.db.create_connection()
                fm.map_a_path_to_db(tablename,path_to_map,True)

def get_maps_in_db(database):
    """Gets maps in database

    Args:
        database (str): database

    Returns:
        list: list of map's (table names)
    """
    fm=get_file_map(database)
    tables=fm.db.tables_in_db()
    maps=[]
    for ttt in tables:
        if isinstance(ttt,tuple):
            if len(ttt)>0:
                if ttt[0] not in [fm.mapper_reference_table,'sqlite_sequence']:
                    maps.append(ttt[0])
    return maps

def delete_map():
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
            menu=[{'type': 'list',
            'name': 'map_delete',
            'message': 'Please select: (use arrow keys)',
            'choices': map_list+['Back']
            }]
            answers = prompt(menu, style=style)
            if answers['map_delete'] == 'Back':
                return ''
            if answers['map_delete'] not in ['',None]:
                tablename=answers['map_delete']
                # path_to_map="D:\Downloads"
                fm=get_file_map(selected_db) 
                fm.db.create_connection()
                count=fm.db.get_number_or_rows_in_table(tablename)
                if ask_confirmation(f"Sure to delete Map [magenta]{tablename}[\magenta] with [magenta]{count}[\magenta] elements?"):
                    fm.delete_map(tablename)

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


def show_maps():
    """Prints Map information
    """
    for iii,a_db in enumerate(active_databases):
        fm=a_db['mapdb']
        if isinstance(fm,FileMapper):
            print(f"{iii+1}. Maps in {a_db['file']}:")
            table_list=fm.db.get_data_from_table(fm.mapper_reference_table,'*')
            jjj=0
            if len(table_list)>0:
                # print('\t(id','dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype)')
                #field_list=['id','dt_map_created','dt_map_modified','mappath','tablename','mount','serial','mapname','maptype']
                field_list=['id','Date Time Created','Date Time Modified','Map Path','Table Name','Mount','Serial','Map Name','Map Type']
                data_manage=DataManage(table_list,field_list)
                print(data_manage.get_tabulated_fields(fields_to_tab=[field_list[1],field_list[4],field_list[6],field_list[5],field_list[3]],index=True,justify='left'))
            # for table in table_list:
            #     print(f"\t{jjj+1}. {table}")
            #     jjj=jjj+1

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
        menu=[{'type': 'list',
        'name': 'db_map_select',
        'message': 'Please select: (use arrow keys)',
        'choices': map_list+['Back']
        }]
        answers = prompt(menu, style=style)
        if answers['db_map_select'] == 'Back':
            return None       
        elif answers['db_map_select'] in map_list:
            for str_pair,db_map_pair in zip(map_list,db_map_pair_list):
                if str_pair == answers['db_map_select']:
                    print(db_map_pair)
                    return db_map_pair
    return None

def process_map():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(MENU_HEADER)
    print("Process Map:")
    print("----------")
    db_map_pair=menu_select_database_map()
    if not db_map_pair:
        return ''
    menu=[{'type': 'list',
        'name': 'map_process',
        'message': 'Please select: (use arrow keys)',
        'choices': ['Print Tree','Find Duplicates','Back']
        }]
    while True:
        print("----------")
        answers = prompt(menu, style=style)
        if answers['map_process'] == 'Back':
            return ''
        elif answers['map_process'] == 'Print Tree': 
            print(db_map_pair)
        elif answers['map_process'] == 'Find Duplicates': 
            duplicte_list=find_duplicates(db_map_pair[0],db_map_pair[1])
            menu_duplicate_select(duplicte_list)


def menu_duplicate_select(duplicte_list):
    choice_list=[]
    for dup_tup in duplicte_list:
        for iii,dupli_dict in enumerate(dup_tup):
            if iii==0:
                choice_list.append(Separator(f"{dupli_dict['md5']} in {dupli_dict['filepath']}"))
                choice_list.append({
                'name': f"{dupli_dict['filename']}",
                'checked': True,
                })
            else:    
                choice_list.append({
                'name': f"{dupli_dict['filename']}",
                'checked': False,
                })
    menu = [{
        'type': 'checkbox',
        'message': 'Select files',
        'name': 'file_selection',
        'choices': choice_list
        }]
    answers = prompt(menu, style=style)
    print(answers)
        
def find_duplicates(database,a_map):
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
    menu=[{'type': 'list',
        'name': 'mapping',
        'message': 'Please select: (use arrow keys)',
        'choices': ['Create New Map', 'Delete Map', 'Process Map','Back']
        }]
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(MENU_HEADER)
        print("Mapping:")
        print("----------")
    
        if len(active_databases)==0:
            return '[magenta]There are no active databases![\magenta]'
        show_maps()
        print("---------------------------------")
        answers = prompt(menu, style=style)
        if answers['mapping']=='Create New Map':
            menu_create_new_map()
        elif answers['mapping']=='Delete Map': 
            delete_map()
        elif answers['mapping']=='Process Map': 
            process_map()
        elif answers['mapping']=='Back':
            return ''

def main_menu():
    """Interactive menu main"""
    msg=''
    menu=[{'type': 'rawlist',
        'name': 'main_menu',
        'message': 'Please select:',
        'choices': ['Handle Databases', 'Mapping', 'Exit']
        }]
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(MENU_HEADER)
        if msg!='':
            print(msg)
            msg=''
        print("Main Menu:")
        print("----------")
        answers = prompt(menu, style=style)
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
