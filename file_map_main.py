import os
from datetime import datetime
import hashlib

from class_sqlite_database import SQLiteDatabase
from class_file_manipulate import FileManipulate
from class_device_monitor import DeviceMonitor


def calculate_time_elapsed(start_datetime,end_datetime):
    """Calculate the time elapsed between two timestamps"""
    time_elapsed = (end_datetime - start_datetime).total_seconds()
    return time_elapsed


def calculate_md5(file_path):
    """
    Calculate the MD5 hash of a file.
    
    Args:
        file_path (str): The path to the file for which the MD5 hash is calculated.
        
    Returns:
        str: The MD5 sum as a hexadecimal string.
    """
    try:
        with open(file_path, 'rb') as f:
            md5 = hashlib.md5()
            while chunk := f.read(4096):
                md5.update(chunk)
                
            return md5.hexdigest()

    except FileNotFoundError:
        print(f"File {file_path} not found.")
        exit(1)

db_path=os.path.join(FileManipulate.get_app_path(),"db_Files")
db_name="test_files_db.db"
key_file=os.path.join(db_path,FileManipulate.extract_filename(db_name,False)+'_key.txt')
db_path_file=os.path.join(db_path,db_name)
key = None
if not os.path.exists(db_path):
    os.mkdir(db_path)
# #if db exists open and read it
# if os.path.exists(db_path_file):
#     if os.path.exists(key_file):
#         with open(key_file, 'rb') as f:
#             key = f.read()
#         db = SQLiteDatabase(db_path_file,True,key)
#     else:
#         db = SQLiteDatabase(db_path_file,False,None)
# else:
#     # Create new encrypted database
#     db = SQLiteDatabase(db_path_file,False,None,None)
#     key_generated=db.encrypt_db()
#     if key_generated:
#         db.save_key_to_file(key_file)
#         db.decrypt_db()

def map_a_path_to_db(db: SQLiteDatabase,table_name,path_to_map):
    try:
        #if not db.table_exists(table_name):
        db.create_table(table_name,[('dt_data_created', 'DATETIME DEFAULT CURRENT_TIMESTAMP', True),
                                    ('dt_data_modified', 'DATETIME', True),
                                    ('filepath','TEXT',True), 
                                    ('filename','TEXT',True), 
                                    ('md5', 'TEXT', True), 
                                    ('size', 'REAL', True), 
                                    ('dt_file_created','DATETIME',False),
                                    ('dt_file_accessed','DATETIME',False),
                                    ('dt_file_modified','DATETIME',False),
                                    ])
        data=[]
        iii=0
        files_processed=0
        for dirpath, dirnames, filenames in os.walk(path_to_map):
            if files_processed==0:
                last_dirpath=dirpath
            
            for file in filenames:
                dt_data_created=datetime.now()
                joined_file=os.path.join(dirpath,file)
                the_md5=calculate_md5(joined_file)
                the_size=FileManipulate.get_file_size(joined_file)
                dt_data_modified=datetime.now()
                dt_file_a=FileManipulate.get_accessed_date(joined_file)
                dt_file_c=FileManipulate.get_created_date(joined_file)
                dt_file_m=FileManipulate.get_modified_date(joined_file)
                print(f"{files_processed} {dirpath}{os.sep}{file} [{the_md5}]\t{the_size / (1024 * 1024):.2f} MB")
                data.append((dt_data_created,dt_data_modified,dirpath,file,the_md5,the_size,dt_file_c,dt_file_a,dt_file_m))
                iii=iii+1
                if iii>10:
                    print("+"*10)
                    db.insert_data_to_table(table_name,data)
                    data=[]
                    iii=0
                files_processed=files_processed+1
        print("="*10)
        db.insert_data_to_table(table_name,data)
        #db.print_all_rows(table_name)
        
        print(db.get_number_or_rows_in_table(table_name))
    except Exception as e:
        print(f"Error: {e}")
        db.close_connection()

def get_repeated_files(db: SQLiteDatabase,table_name) -> dict[list]:
    """Gets repeated files in map

    Args:
        db (SQLiteDatabase): database
        table_name (_type_): table

    Returns:
        dict[list]: repeated file ids
                    md5sum:[id of files repeated]
    """
    repeated={}
    try:
        data_list=db.get_data_from_table(f"{table_name} ORDER BY md5", "id, md5")
        iii=0
        last_anmd5=None
        last_anid=None
        for anid,anmd5 in data_list:
            if last_anmd5 == anmd5:
                if anmd5 in repeated:
                    rep_list=repeated[anmd5]
                    if isinstance(rep_list,list):
                        rep_list.append(anid)
                        repeated.update({anmd5:rep_list})
                else:
                    repeated.update({anmd5:[last_anid,anid]})
            last_anmd5=anmd5
            last_anid=anid
            iii=iii+1
    except Exception as e:
        print(f"Error: {e}")
        db.close_connection()
    return repeated

def get_repeated_file_multiple_db_tables(db_list: list[SQLiteDatabase],table_name_list: list,column_list:list=['id','md5'],Orderby=1) -> dict[list]:
    """Gets repeated files in map

    Args:
        db (SQLiteDatabase): database
        table_name (_type_): table

    Returns:
        dict[list]: repeated file ids
                    md5sum:[id of files repeated]
    """
    repeated={}
    try:
        data_list=[]
        cols=str(column_list).replace("[","").replace("'","").replace("]","")
        for index,(db,table_name) in enumerate(zip(db_list,table_name_list)):
            data=db.get_data_from_table(f"{table_name} ORDER BY {column_list[Orderby]}", f"{cols}")
            for ddd in data:
                data_list.append((index,)+ddd) # add [db,table] index to tuple

        iii=0
        last_anmd5=None
        last_anid=None
        last_db=None
        for dbtable,anid,anmd5 in data_list:
            if last_anmd5 == anmd5:
                if anmd5 in repeated:
                    rep_list=repeated[anmd5]
                    if isinstance(rep_list,list):
                        rep_list.append((dbtable,anid))
                        repeated.update({anmd5:rep_list})
                else:
                    repeated.update({anmd5:[(last_db,last_anid),(dbtable,anid)]})
            last_anmd5=anmd5
            last_anid=anid
            last_db=dbtable
            iii=iii+1
    except Exception as e:
        print(f"Error: {e}")
        db.close_connection()
    return repeated

def repeated_list_show(repeated_dict,key,db_list: list[SQLiteDatabase],table_name_list: list,db_cols:list=['id','filepath','filename','md5']):
    rep_tup=repeated_dict[key]
    from_txt= str(db_cols).replace("[","").replace("'","").replace("]","")
    info=[]
    for a_db,an_id in rep_tup:
        db=db_list[a_db]
        if isinstance(db,SQLiteDatabase):
            table_name=table_name_list[a_db]
            where= f"id={an_id}"
            data=db.get_data_from_table(table_name,from_txt,where)
            info.append(data)
    return info


start_datetime=datetime.now()
new_map=False
db = SQLiteDatabase(db_path_file,False,None,None)    


if new_map:
    # path_to_map="D:\Downloads"
    path_to_map="C:\\Users\\Tony\\Downloads"
    db.delete_data_from_table("table_test_2")        
    map_a_path_to_db(db,"table_test_2",path_to_map)

# print("repeated files:",get_repeated_files(db,"table_test"))
repeated_dict=get_repeated_file_multiple_db_tables([db,db],["table_test","table_test_2"])
#print("repeated files:",repeated_dict)
key_list=list(repeated_dict.keys())
showing=['id','filepath','filename','md5','size']
print("Show:", repeated_list_show(repeated_dict,key_list[3],[db,db],["table_test","table_test_2"],showing))
print("Show:", repeated_list_show(repeated_dict,key_list[33],[db,db],["table_test","table_test_2"],showing))
print("Show:", repeated_list_show(repeated_dict,key_list[len(key_list)-7],[db,db],["table_test","table_test_2"],showing))

#db.print_all_rows("table_test")
db.close_connection()
end_datetime=datetime.now()
print(f" took {calculate_time_elapsed(start_datetime,end_datetime)} s")

