#!/usr/bin/env python  # shebang for Unix-based systems
#!pythonw        # shebang for Windows systems

import os
import sys
import argparse
import getpass
from datetime import datetime
import hashlib

from class_sqlite_database import SQLiteDatabase
from class_file_manipulate import FileManipulate
from class_device_monitor import DeviceMonitor
from class_file_mapper import FileMapper

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

MENU_HEADER="""
>>================FILE MAP=================<<
>>======by FG with coffee and Love=========<<
>>=========================================<<
"""
__version__="v.1.1.333 beta"

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
    
    
    # Ask for user input for name
    # name = input("Enter your name: ")
    # Print the name without prompting for password or using keyfile
    # print(f"And your name is {name}")
    print(file_list,password_list,key_list)
    main_menu()

def activate_databases(db_file_name=None):
    """Activates all databases in file_list using the key. Will prompt for password if DB is password protected.
    """
    for file,pwd,keyf in zip(file_list,password_list,key_list):
        if not db_file_name or db_file_name==file:
            is_active=False
            for adb in active_databases:
                if adb['file']==file:
                    is_active=True
                    break
            if not is_active:
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
        print(MENU_HEADER)
        if activate:
            print("\nActivate Databases:")
            print("-----------------------")
            ia_list=show_active_inactive_databases(False,True)
        else:
            
            print("\nDeactivate Databases:")
            print("-----------------------")
            ia_list=show_active_inactive_databases(True,True)
        if len(ia_list)>0:
            print("*. ALL")
        else:
            break    
        print("X. Back")
        choice = input("Enter your choice (1-N): ")
        is_valid,is_digit=is_choice_valid(choice,1,len(ia_list),["*","X","x"])
        if choice == '*':
            if activate:
                activate_databases(None)
            else:
                deactivate_databases(None)    
        elif choice in ["X","x"]:
            break
        elif is_valid and is_digit:
            for lll in ia_list:
                if int(choice)-1 == lll[0]:
                    if activate:
                        activate_databases(lll[1])
                    else:
                        deactivate_databases(lll[1])
        else:
            print("Not a valid choice")

def is_choice_valid(choice:str,minval:int,maxval:int,others:list[str]=None) -> tuple[bool]:
    """Evaluates menu choice

    Args:
        choice (str): input choice
        minval (int): minimum numeric value
        maxval (int): maximum numeric value
        others (list[str],Optional): other choice string posibilities as ["*","X","x"]. Default None.
    Returns:
        tuple[bool]: (is valid choice, is digit)
    """
    try:
        if others and choice in others:
            return True,False
        if choice.isdigit() and int(choice) >= minval and int(choice) <= maxval:
            return True ,True
        return False,True
    except (TypeError,ValueError):
        return False, False

def menu_handle_databases():
    """Interactive menu handle databases"""
    os.system('cls' if os.name == 'nt' else 'clear')
    while True:
        print(MENU_HEADER)
        show_databases_listed()
        print("---------------------------------")
        print("\nEdit Active File Map Databases:")
        print("1. Create New Database File")
        print("2. Append Database File")
        print("3. Remove Database File")
        print("4. Activate Database File")
        print("5. Deactivate Database File")
        print("X. Back")
        
        choice = input("Enter your choice (1-N): ")
        if choice == '1':
            create_new_database_file()
        elif choice == '2': 
            append_database_file()
        elif choice == '3':         
            menu_remove_database_file()   
        elif choice == '4':
            menu_activate_deactivate_databases(True)
        elif choice == '5':
            menu_activate_deactivate_databases(False)
       
        elif choice in ["X","x"]:
            break

def show_databases_listed():
    """prints databases listed
    """
    print("File Map Databases listed:")
    for iii,(file,pwd,keyf) in enumerate(zip(file_list,password_list,key_list)):
        print(f"{iii+1}. {file} {'(pwd)' if pwd else ''} {keyf} {'ACTIVE' if is_database_active(file) else ''}")

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
                print(f"{iii+1}. {a_db['file']} {'(pwd)' if a_db['haspassword'] else ''} {a_db['keyfile']}")
            ai_list.append([iii,a_db['file']])
    else:
        if do_print:
            print("Inactive Databases:")
        for iii,(file,pwd,keyf) in enumerate(zip(file_list,password_list,key_list)):
            if not is_database_active(file):
                if do_print:
                    print(f"{iii+1}. {file} {'(pwd)' if pwd else ''} {keyf}")
                ai_list.append([iii,file])
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


def menu_remove_database_file():
    """Removes a database from the file_list
    """
    while len(file_list)>0:
        show_databases_listed()
        print(f"*. Select All")
        print(f"X. Back")
        
        choice=input("Enter selection to remove from list: ")
        if choice in ["*"]:
            if input("Remove all databases? y/n: ") in ['y','Y','yes','Yes','YES']:
                deactivate_databases(None)
                file_list.clear()
                password_list.clear()
                key_list.clear()
                continue
            
        elif choice in ["X","x"]:
            break
        else:
            try:
                val=int(choice)
                if val<len(file_list) and val>0:
                    f_r=file_list[val-1]
                    if input(f"Remove {f_r} database? y/n: ") in ['y','Y','yes','Yes','YES']:
                        deactivate_databases(f_r)
                        f_list=file_list.copy()
                        for iii,fn in enumerate(f_list):
                            if fn==f_r:
                                file_list.remove(iii)
                                password_list.remove(iii)
                                key_list.remove(iii)
                                break
            except (TypeError, ValueError):
                print("Not a valid choice, try again.")

    
def append_database_file():
    """Adds a database to the file_list
    """
    print(f" File Map path: {FileManipulate.get_app_path()}")
    dir_available=False
    file_available=False
    file_path=''
    path_user=input("Enter complete path of DB (Enter to use File Map path): ")
    if not path_user or path_user.strip()=="":
        path_user=FileManipulate.get_app_path()
        dir_available=True
    else:
        if FileManipulate.validate_path(path_user):
            dir_available=True
        else:
            print("Path does not exist") 
    if dir_available:
        file_user=input("Enter File name of DB: ")
        file_user=FileManipulate.extract_filename(file_user,False)
        file_path=os.path.join(path_user,file_user+".db")
        file_available=True
    if file_available:
        if not os.path.exists(file_path):
            if input("File does not exist create it? y/n: ") in ['y','Y','yes','Yes','YES']:
                create_filemap_database(file_path)
        else:
            open_filemap(file_path)

def open_filemap(file_path):
    """Opens a file map database

    Args:
        file_path (str): Complete path and file name of the database
    """
    keyfile=None
    a_pwd=None
    can_open=True
    if input(f"Is {file_path} encrypted? y/n: ") in ['y','Y','yes','Yes','YES']:
        print(f"db path: {FileManipulate.extract_path(file_path)}")
        path_key=input("Enter complete path for new DB (Enter to use db path): ")
        if not path_key or path_key.strip()=="":
            path_key=FileManipulate.extract_path(file_path)
        if os.path.exists(path_key):    
            default_fn=kf=FileManipulate.extract_filename(file_path,False)+'_key.txt'
            file_key=input(f"Enter DB filename (Enter to use {default_fn} path): ")
            if not file_key or file_key=='':
                keyfile=os.path.join(path_key,default_fn)
            else:
                keyfile=os.path.join(path_key,file_key)
            if not os.path.exists(keyfile):
                print(f"File {keyfile} does not exist!")
                can_open=False    
        else:
            print("Path does not exist!")
            can_open=False
    if input(f"Is {file_path} password protected? y/n: ") in ['y','Y','yes','Yes','YES']:
        a_pwd=ask_password()
    if can_open:
        file_list.append(file_path)
        password_list.append(keyfile)
        key_list.append(a_pwd)

def create_new_database_file():
    """Create New Database File
    """
    print(f" File Map path: {FileManipulate.get_app_path()}")
    dir_available=False
    file_available=False
    file_path=''
    path_user=input("Enter complete path for new DB (Enter to use File Map path): ")
    if not path_user or path_user.strip()=="":
        path_user=FileManipulate.get_app_path()
        dir_available=True
    else:
        
        if FileManipulate.validate_path(path_user):
            dir_available=True
        else:
            if input("Path does not exist create it? y/n: ") in ['y','Y','yes','Yes','YES']:
                try:
                    os.makedirs(path_user)
                    dir_available=True
                except Exception as eee:
                    print(f'Could not create path directory {path_user}: {eee}')
                    path_user=FileManipulate.get_app_path()
    if dir_available:
        file_user=input("Enter File name for new DB: ")
        file_user=FileManipulate.clean_filename(file_user)
        file_user=FileManipulate.extract_filename(file_user,False)
        file_path=os.path.join(path_user,file_user+".db")
        file_available=True
    if file_available:
        if not os.path.exists(file_path):
            create_filemap_database(file_path)

def create_filemap_database(file_path):
    """Creates a new File Map database

    Args:
        file_path (str): Path and filename of new database
    """
    if input("Encrypt Database? y/n: ") in ['y','Y','yes','Yes','YES']:
        path=FileManipulate.extract_path(file_path)
        kf=FileManipulate.extract_filename(file_path,False)+'_key.txt'
        keyfile=os.path.join(path,kf)
        print(f'New keyfile will be set to: {keyfile}')
        print("Warning: If you erase, or loose the file, you will not be able to access the database anymore!")
    else:
        keyfile=None
    if input("Set Database password? y/n: ") in ['y','Y','yes','Yes','YES']:
        a_pwd=''
        while True:
            a_pwd=ask_password("New password for:")
            r_pwd=ask_password("Repeat password for:")
            if not a_pwd or a_pwd=='':
                a_pwd=None
                print("Setting no password")
                continue
            if a_pwd != r_pwd:
                print("Passwords did not match, try again!")
            else:
                continue
    else:
        a_pwd=None
    fm=FileMapper(file_path,keyfile,a_pwd)
    fm.close()
    file_list.append(file_path)
    password_list.append(keyfile)
    key_list.append(a_pwd)

def main_menu():
    """Interactive menu main"""
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(MENU_HEADER)
        print("\nMain Menu:")
        print("1. Handle Databases")
        print("2. Browse databases")
        print("3. Add File")
        print("4. Add password to file")
        print("5. Add key file to file")
        print("6. Exit")
        
        choice = input("Enter your choice (1-6): ")
        
        if choice == "1":
            menu_handle_databases()
            # Clear the screen and display menu 2

            # os.system('cls' if os.name == 'nt' else 'clear')
            # print(MENU_HEADER)
            # print("\nMenu 2:")  
            # while choice not in ["X","x"]:
            #     print("Select File to print:")
            #     for i, file in enumerate(file_list):
            #         print(f"{i+1}. {file}")
            #     print(f"X. Back")
            #     choice=-1
            #     choice = input("Enter your choice (1-N): ")
            #     if choice.isdigit() and int(choice) > 0 and int(choice) <= len(file_list):
            #         # Print the selected file
            #         print(f"{file_list[int(choice)-1]}")
            #     else:
            #         print("Invalid choice. Please try again. X to go back")
        elif choice == "2":
            # Clear the screen and display menu 3
            os.system('cls' if os.name == 'nt' else 'clear')
            print(MENU_HEADER)
            print("\nMenu 3:")
            print("Select File to inspect:")
            for i, file in enumerate(file_list):
                print(f"{i+1}. {file}")
            choice = input("Enter your choice (1-N): ")
            
            if choice == "X":
                # Go back to main menu
                continue
            elif choice.isdigit() and int(choice) > 0 and int(choice) <= len(file_list):
                # Inspect the selected file
                print(f"inspect_files {[int(choice)-1]}")
            else:
                print("Invalid choice. Please try again.")
        elif choice == "3":
            # Clear the screen and display menu 4
            os.system('cls' if os.name == 'nt' else 'clear')
            print(MENU_HEADER)
            print("\nMenu 4:")
            print("Enter File :")
            for i, file in enumerate(file_list):
                print(f"{i+1}. {file}")
            choice = input("Enter your choice (1-N): ")
            
            if choice == "X":
                # Go back to main menu
                continue
            elif choice.isdigit() and int(choice) > 0 and int(choice) <= len(file_list):
                file = file_list[int(choice)-1]
                print("Enter name of File to add :")
                for i, a in enumerate(file_list):
                    if a == file:
                        print(f"{i+1}. {a}")
                        choice = input("This file already exists. Enter another file name (or press X to go back): ")
                        if choice == "X":
                            continue
                else:
                    # Add the new file
                    print(f"{file} added successfully.")
            else:
                print("Invalid choice. Please try again.")
        elif choice == "4":
            # Clear the screen and display menu 5
            os.system('cls' if os.name == 'nt' else 'clear')
            print("\nMenu 5:")
            print("Select File to add password to:")
            for i, file in enumerate(file_list):
                print(f"{i+1}. {file}")
            choice = input("Enter your choice (1-N): ")
            
            if choice == "X":
                # Go back to main menu
                continue
            elif choice.isdigit() and int(choice) > 0 and int(choice) <= len(file_list):
                file = file_list[int(choice)-1]
                print("Enter password for", file, ":")
                password = input()
                # add_passwords[file] = password
                print(f"Password added successfully.")
            else:
                print("Invalid choice. Please try again.")
        elif choice == "5":
            # Clear the screen and display menu 6
            os.system('cls' if os.name == 'nt' else 'clear')
            print("\nMenu 6:")
            print("Select File to add key file to:")
            for i, file in enumerate(file_list):
                print(f"{i+1}. {file}")
            choice = input("Enter your choice (1-N): ")
            
            if choice == "X":
                # Go back to main menu
                continue
            elif choice.isdigit() and int(choice) > 0 and int(choice) <= len(file_list):
                file = file_list[int(choice)-1]
                print("Enter key file for", file, ":")
                key_file = input()
                # add_key_files[file] = key_file
                print(f"Key file added successfully.")
            else:
                print("Invalid choice. Please try again.")
        elif choice == "6":
            # Clear the screen and exit program
            os.system('cls' if os.name == 'nt' else 'clear')
            sys.exit(0)
	
def main_debug():
    db_path=os.path.join(FileManipulate.get_app_path(),"db_Files")
    db_name="test_files_db.db"
    key_file= None#os.path.join(db_path,FileManipulate.extract_filename(db_name,False)+'_key.txt')
    db_path_file=os.path.join(db_path,db_name)

    start_datetime=datetime.now()
    file_list.append(db_path_file)
    password_list.append(None)
    key_list.append(key_file)
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
