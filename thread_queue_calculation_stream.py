'''
F.Garcia
23.02.2025
MD5, SHA1, SHA256 calculating thread.
Is alive meanwhile there is text to stream.
'''
import sys
import os
import threading
import queue
import logging
import time
import re
import hashlib
#import io
from common import *
from datetime import datetime

from class_file_manipulate import FileManipulate
from class_sqlite_database import SQLiteDatabase
from class_data_manage import DataManage
from rich import print
# from rich.progress import Progress
from class_map_progress import MapProgress, RichMapProgress
sys.path.append(os.path.realpath("."))

F_M=FileManipulate()

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
formatter=logging.Formatter('[%(levelname)s] (%(threadName)-10s) %(message)s')
ahandler=logging.StreamHandler()
ahandler.setLevel(logging.INFO)
ahandler.setFormatter(formatter)
log.addHandler(ahandler)
 
class QueueCalcStream(threading.Thread):
    """
        A thread class to buffer and deliver the Gcode for streaming
    """                  
    def __init__(self,db_info:dict,table:str,mount:str,cycle_time:float,kill_event:threading.Event,
                 Pbar_Stream=None,table_column='md5',log_callback=None):
        threading.Thread.__init__(self, name="Stream Calculate thread")        
        if not log_callback:
            self.log_callback=print
            self.use_logger=True
        else:
            self.log_callback=log_callback
            self.use_logger=False

        self.db = SQLiteDatabase(db_info["name"],db_info["encrypt"],db_info["key"],db_info["pwd"])
        self.cycle_time=cycle_time
        self.killer_event = kill_event
        self.table=table
        self.queue_pathfile = queue.Queue()  
        self.queue_id = queue.Queue()   
        self.queue_size = queue.Queue()   
        self.Pbarini=0
        self.Pbarend=100   
        self.pbar_stream=Pbar_Stream 
        self.mount=mount     
        self.d_m=None     
        self.is_data=True
        self.calculation_finished=False    
        self.items_total=0
        self.processing_file=''
        self.table_column=table_column

    
    def calculate_md5(self,file_path):
        """
        Calculate the MD5 hash of a file.
        
        Args:
            file_path (str): The path to the file for which the MD5 hash is calculated.
            
        Returns:
            str: The MD5 sum as a hexadecimal string.
        """
        try:
            md5 = hashlib.md5()
            with open(file_path, 'rb') as f:           
                for chunk in iter(lambda: f.read(4096), b""):
                    md5.update(chunk)  
            return md5.hexdigest()
        except (PermissionError):
            return ':::NoPermission:::'
        except (FileNotFoundError):
            self.log_callback(f"File {file_path} not found.")
            return ':::FileNotFound:::'
            exit(1)

    
    def calculate_sha1(self,file_path):
        """
        Calculate the SHA128 hash of a file.
        
        Args:
            file_path (str): The path to the file for which the MD5 hash is calculated.
            
        Returns:
            str: The SHA128 hash as a string.
        """
        try:
            with open(file_path, 'rb') as f:
                sha1 = hashlib.sha1()
                while chunk := f.read(4096):
                    sha1.update(chunk)  
                return sha1.hexdigest()

        except FileNotFoundError:
            self.log_callback(f"File {file_path} not found.")
            exit(1)

    def calculate_sha256(self,file_path):
        """
        Calculate the SHA256 hash of a file.
        
        Args:
            file_path (str): The path to the file for which the MD5 hash is calculated.
            
        Returns:
            str: The SHA256 hash as a string.
        """
        try:
            with open(file_path, 'rb') as f:
                sha256 = hashlib.sha256()
                while chunk := f.read(4096):
                    sha256.update(chunk)   
                return sha256.hexdigest()

        except FileNotFoundError:
            self.log_callback(f"File {file_path} not found.")
            exit(1)   

    def Pbar_Set_Status(self,Pbar,val):
        """Sets the value of The progress bar. If it is called from QT,can set the object, else will use rich progressbar"""
        if  Pbar!=None and int(val)>=0 and int(val)<=100:   
                Pbar.SetStatus(int(val))
    
    def quit(self):
        self.killer_event.set()        

    def Get_Progress_Percentage(self,sss,Numsss,Perini=0,Perend=100):
        if sss>Numsss:            
            return Perend
        if sss<0 or Numsss<=0:            
            return Perini
        if (Perend-Perini)<=0:
            Per=min(abs(Perini),abs(Perend))              
            return Per 
        Per=round(Perini+(sss/Numsss)*(Perend-Perini),2)        
        return Per   

    def fill_queue_with_files(self):
        """Fills the queue with the filenames"""
        tables=self.db.tables_in_db()
        if self.table not in tables:
            msg=f'{self.table} is not in database!'
            if self.use_logger:
                log.error(msg)
            else:
                self.log_callback(msg)
            self.is_data=False
            return
        data=self.db.get_data_from_table(self.table,'*','md5="***Calculate***"')
        if len(data)==0:
            self.is_data=False
            return
        self.is_data=True
        field_list=self.db.get_column_list_of_table(self.table)
        self.d_m=DataManage(data,field_list)
        self.items_total=len(self.d_m.df['filename'])
        for filepath,filename,an_id,size in zip(self.d_m.df['filepath'],self.d_m.df['filename'],self.d_m.df['id'],self.d_m.df['size']):
            line=os.path.join(self.mount,filepath,filename)
            self.queue_pathfile.put(line)  
            self.queue_id.put(an_id)
            self.queue_size.put(size)
            pass
    
    def calculate_for_next_file_in_queue(self):
        try:        
            line=self.queue_pathfile.get_nowait()
            an_id=self.queue_id.get_nowait()
            size=self.queue_size.get_nowait()
            self.processing_file=line
            size_str=F_M.get_size_str_formatted(size)
            if size > 349175808:
                self.log_callback(f"[yellow]Calculating... {size_str} {line}")
            if self.table_column=='md5':
                md5=self.calculate_md5(line)
                self.db.edit_value_in_table(self.table,an_id,'md5',md5)
            elif self.table_column=='sha1':
                md5=self.calculate_sha1(line)
                self.db.edit_value_in_table(self.table,an_id,'sha1',md5)
            elif self.table_column=='sha256':
                md5=self.calculate_sha256(line)
                self.db.edit_value_in_table(self.table,an_id,'sha256',md5)
            else:
                md5=self.calculate_md5(line)
                self.db.edit_value_in_table(self.table,an_id,'md5',md5)
            if not self.pbar_stream or not self.use_logger:
                self.log_callback(f"{self.items_total-self.queue_id.qsize()}/{self.items_total} ({md5}) ({an_id}) {size_str} {line}")
            else:
                log.info(f"{self.items_total-self.queue_id.qsize()}/{self.items_total} ({md5}) ({an_id}) {size_str} {line}")
        except queue.Empty:                    
            pass    


    def run(self):
        """thread loop"""
        self.log_callback('[green]'+'<'*10+'Successfully Started calculation Thread'+'>'*10)
        count=0
        progress=None
        has_filled_data=False
        progress_bar = self.pbar_stream
        if progress_bar is None:
            progress_bar = RichMapProgress()
        if isinstance(progress_bar, MapProgress):
            progress = progress_bar

        exit_key="ctrl+c"
        if os.name == 'nt':
            exit_key="F12"
        #task1 = progress.add_task(f"[blue]{self.table} [red](Press {exit_key} to Exit)", total=100)
        if progress:
            progress.start(
                100,
                description=f"[blue]{self.table} [red](Press {exit_key} to Exit)",
            )
        try:
            while not self.killer_event.wait(self.cycle_time):
                try:
                    if not has_filled_data and self.queue_pathfile.empty():
                        self.fill_queue_with_files()
                        has_filled_data=True
                    elif has_filled_data and self.queue_pathfile.empty():
                        self.is_data = False
                    if not self.is_data and self.queue_pathfile.empty():
                        self.calculation_finished=True
                        self.killer_event.set()
                        break
                    else:
                        self.calculate_for_next_file_in_queue()

                    count=count+1
                    # print(count)

                    # set progressbar status
                    items_left=self.items_total-self.queue_id.qsize()
                    per=self.Get_Progress_Percentage(items_left,self.items_total,0,100)
                    if not self.pbar_stream:
                        #progress.update(task1, advance=1)
                        if progress:
                            progress.update(
                                current=per,
                                description=f"[blue]{self.table} [red](Press {exit_key} to Exit)",
                            )
                    else:
                        self.Pbar_Set_Status(self.pbar_stream,per)
                except KeyboardInterrupt:
                    self.killer_event.set()
                    msg='User Cancel'
                    if self.use_logger:
                        log.info(msg)
                    else:
                        self.log_callback(msg)
                except Exception as e:
                    self.killer_event.set()
                    msg=f"Stream calculation fatal error! exiting thread!:{e}"
                    if self.use_logger:
                        log.error(msg)
                    else:
                        self.log_callback(msg)
                    raise
        finally:
            if progress:
                progress.stop()

        if self.killer_event.is_set():
            msg="Stream calculation Killing event Detected!"
            if self.use_logger:
                log.info(msg)
            else:
                self.log_callback(msg)
        msg="Stream calculation Ended successfully!"
        if self.use_logger:
            log.info(msg)
        else:
            self.log_callback(msg)
        if self.pbar_stream:
            self.Pbar_Set_Status(self.pbar_stream,100)

        if self.use_logger: # set flag when no logger
            self.killer_event.set()
        #  self.db.print_all_rows(self.table)
        #self.quit() 
    


def main():    
    import keyboard
    kill_ev = threading.Event()
    kill_ev.clear()
        
    cycle_time=0.1
    db_path=os.path.join(F_M.get_app_path(),"db_Files")
    db_name="test_thread.db"
    key_file= None
    pwd=None
    db_path_file=os.path.join(db_path,db_name)
    db_info={"name":db_path_file,"key":key_file,"pwd":pwd,"encrypt":False}
    mount='d:'
    start_datetime=datetime.now()
    tables=['table_test','test2']
    qstream=QueueCalcStream(db_info,tables[0],mount,cycle_time,kill_ev,None)
    qstream.start()
    
    try:
        last_txt=None
        while qstream.is_alive():    
            if os.name=='nt':    
                if keyboard.is_pressed('F12'):
                    kill_ev.set()        
            # txt=qstream.processing_file
            # if txt != last_txt:
            #     print(txt)
            #     last_txt=txt
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    end_datetime=datetime.now()
    print('took',(end_datetime-start_datetime).total_seconds(),' sec')

if __name__ == '__main__':
    main()
