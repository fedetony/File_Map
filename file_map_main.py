import os
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

db_path=os.path.join(FileManipulate.get_app_path(),"db_Files")
db_name="test_files_db.db"
key_file= None#os.path.join(db_path,FileManipulate.extract_filename(db_name,False)+'_key.txt')
db_path_file=os.path.join(db_path,db_name)
fm=FileMapper(db_path_file,key_file,None)

start_datetime=datetime.now()
new_map=True
#db = SQLiteDatabase(db_path_file,False,None,None)    

tablename="table_test_2"

if new_map:
    # path_to_map="D:\Downloads"
    path_to_map="C:\\Users\\Tony\\Downloads"
    print(fm.db.table_exists(tablename))
    if fm.db.table_exists(tablename):
        fm.delete_map(fm.db,tablename)      
    print(fm.db.table_exists(tablename))
    print(fm.db.table_exists('Cow'))  
    fm.map_a_path_to_db(fm.db,tablename,path_to_map,True)

# print("repeated files:",get_repeated_files(db,"table_test"))
repeated_dict=fm.get_repeated_files(fm.db,tablename)
#print("repeated files:",repeated_dict)
key_list=list(repeated_dict.keys())
showing=['id','filepath','filename','md5','size']
print("Show:", fm.repeated_list_show(repeated_dict,key_list[3],[fm.db],[tablename],showing))

fm.db.close_connection()
end_datetime=datetime.now()
print(f" took {calculate_time_elapsed(start_datetime,end_datetime)} s")

