#!/usr/bin/env python  # shebang for Unix-based systems
#!pythonw        # shebang for Windows systems
# from __future__ import print_function, unicode_literals

import os
import argparse

from class_menu_interface import *
from class_mapping_actions import *
        


def main():
    """Argument parser function for File Map

    Raises:
        AttributeError: Wrong number of files or keys.
    """
    file_list=[]
    password_list=[]
    key_list=[]
    os.system('cls' if os.name == 'nt' else 'clear')
    print(FILE_MAP_LOGO)
    parser = argparse.ArgumentParser(description=f"File Map {VERSION}")
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
    menu=TerminalMenuInterface(file_list,password_list,key_list)
    menu.cma.activate_databases(None)
    menu.main_menu()
 

def main_debug():
    file_list=[]
    password_list=[]
    key_list=[]
    db_path=os.path.join(F_M.get_app_path(),"db_Files")
    db_name="test_files_db.db"
    key_file= None#os.path.join(db_path,F_M.extract_filename(db_name,False)+'_key.txt')
    db_path_file=os.path.join(db_path,db_name)

    start_datetime=datetime.now()
    file_list.append(db_path_file)
    password_list.append(None)
    key_list.append(key_file)
    try:
        menu=TerminalMenuInterface(file_list,password_list,key_list)
        menu.cma.activate_databases(None)
        menu.main_menu()
        end_datetime=datetime.now()
        print(f" took {MappingActions.calculate_time_elapsed(start_datetime,end_datetime)} s")
    except KeyboardInterrupt:
        print(FILE_MAP_LOGO)
        print("bye bye!")
    

if __name__ == '__main__':
    db_path=os.path.join(F_M.get_app_path(),"db_Files")
    db_name="test_files_db.db"
    if os.path.exists(os.path.join(db_path,db_name)):
        main_debug()
    else:
        main()
