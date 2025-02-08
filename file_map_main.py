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


def calculate_time_elapsed(start_datetime,end_datetime):
    """Calculate the time elapsed between two timestamps"""
    time_elapsed = (end_datetime - start_datetime).total_seconds()
    return time_elapsed

# db_path=os.path.join(FileManipulate.get_app_path(),"db_Files")
# db_name="test_files_db.db"
# key_file= None#os.path.join(db_path,FileManipulate.extract_filename(db_name,False)+'_key.txt')
# db_path_file=os.path.join(db_path,db_name)
# fm=FileMapper(db_path_file,key_file,None)

# start_datetime=datetime.now()
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
# end_datetime=datetime.now()
# print(f" took {calculate_time_elapsed(start_datetime,end_datetime)} s")

def ask_password(prompt):
    """Prompts the user for a password and returns it."""
    while True:
        password = getpass.getpass(f"Enter your {prompt} password (or leave blank to skip): ")
        if not password or password.strip() == "":
            continue
        else:
            return password
    

def main():
    parser = argparse.ArgumentParser(description="Example program")
    parser.add_argument("files", nargs="+", help="Enter one or several Files to process")
    parser.add_argument("-p", "--password",required=False, nargs="+", type=int, default=None, help="File number to prompt for Password for password protected files (default: None)")
    parser.add_argument("-k", "--keyfile", required=False,  nargs="+", type=str, default=None, help="For each File enter Path to keyfile for decryption, Enter None if not Encrypted.")
    
    args = parser.parse_args()
    file_list=[]
    password_list=[]
    key_list=[]
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
                        #password_list[iii]=True
                        # Comment remove when debugged and works
                        password_list[iii]=ask_password(file)

    if args.keyfile:
        if len(file_list) != len(args.keyfile):
            raise AttributeError(f"Wrong amount of KeyFiles entered: Files: {len(file_list)} != Key Files: {len(args.keyfile)}")  
        for iii,(file,a_kf) in enumerate(zip(file_list,args.keyfile)):
            if str(a_kf).strip() in ['None','none','NONE','No','N','n','no']: 
                key_list[iii]=None 
            else:      
                key_list[iii]=str(a_kf).strip()
    
    
    # Ask for user input for name
    name = input("Enter your name: ")
    # Print the name without prompting for password or using keyfile
    print(f"And your name is {name}")
    print(file_list,password_list,key_list)


def menu(file_list,password_list,key_list):
    while True:
        print("\nMain Menu:")
        print("1. Print files")
        print("2. Inspect files")
        print("3. Add File")
        print("4. Add password to file")
        print("5. Add key file to file")
        print("6. Exit")
        
        choice = input("Enter your choice (1-6): ")
        
        if choice == "1":
            # Clear the screen and display menu 2
            os.system('cls' if os.name == 'nt' else 'clear')
            print("\nMenu 2:")
            print("Select File to print:")
            for i, file in enumerate(file_list):
                print(f"{i+1}. {file}")
            choice = input("Enter your choice (1-N): ")
            
            if choice == "X":
                # Go back to main menu
                continue
            elif choice.isdigit() and int(choice) > 0 and int(choice) <= len(file_list):
                # Print the selected file
                print(f"{file_list[int(choice)-1]}")
            else:
                print("Invalid choice. Please try again.")
        elif choice == "2":
            # Clear the screen and display menu 3
            os.system('cls' if os.name == 'nt' else 'clear')
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
	

if __name__ == '__main__':
    main()