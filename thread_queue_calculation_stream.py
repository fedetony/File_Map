'''
F.Garcia
23.02.2025
MD5, SHA1, SHA256 calculating thread.
Is alive meanwhile there is text to stream.
'''
import os
import sys
import threading
import queue
import logging
import hashlib

from common import *
from class_file_manipulate import FileManipulate
from class_sqlite_database import SQLiteDatabase
from class_map_progress import MapProgress, RichMapProgress
from rich import print

sys.path.append(os.path.realpath("."))

F_M = FileManipulate()

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

if not log.handlers:
    formatter = logging.Formatter(
        '[%(levelname)s] (%(threadName)-10s) %(message)s'
    )
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)
    log.addHandler(handler)


class QueueCalcStream(threading.Thread):
    """
    Background thread for calculating file hashes and updating the database.
    """

    CHUNK_SIZE = 1024 * 1024       # 1 MB file read chunks
    DB_BATCH_SIZE = 100            # database updates per SQL command

    def __init__(
        self,
        db_info: dict,
        table: str,
        mount: str,
        cycle_time: float,
        kill_event: threading.Event,
        Pbar_Stream=None,
        table_column='md5',
        log_callback=None
    ):
        super().__init__(name="Stream Calculate thread")

        self.log_callback = log_callback or print
        self.use_logger = log_callback is None

        self.db = SQLiteDatabase(
            db_info["name"],
            db_info["encrypt"],
            db_info["key"],
            db_info["pwd"]
        )

        self.cycle_time = cycle_time
        self.killer_event = kill_event
        self.table = table
        self.mount = mount
        self.table_column = table_column
        self.pbar_stream = Pbar_Stream

        self.queue = queue.Queue()

        self.is_data = True
        self.calculation_finished = False
        self.items_total = 0
        self.processing_file = ''

    # ------------------------------------------------------------------
    # Hashing
    # ------------------------------------------------------------------

    def calculate_hash(self, file_path):
        """Calculate the requested hash using large read chunks."""
        try:
            hasher = {
                'md5': hashlib.md5,
                'sha1': hashlib.sha1,
                'sha256': hashlib.sha256,
            }.get(self.table_column, hashlib.md5)()

            with open(file_path, 'rb') as f:
                while not self.killer_event.is_set():
                    chunk = f.read(self.CHUNK_SIZE)
                    if not chunk:
                        break
                    hasher.update(chunk)

            if self.killer_event.is_set():
                return None

            return hasher.hexdigest()

        except PermissionError:
            return ':::NoPermission:::'

        except FileNotFoundError:
            self.log_callback(f"File {file_path} not found.")
            return ':::FileNotFound:::'

        except OSError as e:
            self.log_callback(f"Error reading {file_path}: {e}")
            return ':::ReadError:::'

    # ------------------------------------------------------------------
    # Progress
    # ------------------------------------------------------------------

    def Pbar_Set_Status(self, Pbar, val):
        if Pbar is not None and 0 <= int(val) <= 100:
            Pbar.SetStatus(int(val))

    def Get_Progress_Percentage(self, current, total, Perini=0, Perend=100):
        if current > total:
            return Perend

        if current < 0 or total <= 0:
            return Perini

        return round(Perini + (current / total) * (Perend - Perini),2)

    # ------------------------------------------------------------------
    # Queue
    # ------------------------------------------------------------------

    def fill_queue_with_files(self):
        """Load files requiring calculation into the work queue."""

        tables = self.db.tables_in_db()
        if self.table not in tables:
            msg = f'{self.table} is not in database!'

            if self.use_logger:
                log.error(msg)
            else:
                self.log_callback(msg)

            self.is_data = False
            return

        data = self.db.get_data_from_table(
            self.table,'filepath, filename, id, size', 
            f'{self.table_column}="***Calculate***"')

        if not data:
            self.is_data = False
            self.items_total = 0
            return

        self.is_data = True
        self.items_total = len(data)

        for filepath, filename, an_id, size in data:
            if self.killer_event.is_set():
                return

            full_path = os.path.join(self.mount, filepath, filename)
            self.queue.put((full_path, an_id, size))

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------

    def update_database_batch(self, updates):
        """
        Update a batch of hashes using one SQL UPDATE statement.

        updates:
            [(id, hash), (id, hash), ...]
        """

        if not updates:
            return

        # CASE id
        case_parts = []

        # IDs used by the WHERE clause
        ids = []

        for an_id, hash_value in updates:
            case_parts.append(
                f"WHEN {an_id} THEN {self.db.quotes(hash_value)}"
            )
            ids.append(str(an_id))

        sql = f"""
            UPDATE {self.table}
            SET {self.table_column} =
                CASE id
                    {' '.join(case_parts)}
                END
            WHERE id IN ({','.join(ids)})
        """

        self.db.send_sql_command(sql)

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------

    def calculate_for_next_file(self, pending_updates):
        """Calculate one file and append its result to the DB batch."""

        try:
            file_path, an_id, size = self.queue.get_nowait()
        except queue.Empty:
            return False

        if self.killer_event.is_set():
            return False

        self.processing_file = file_path
        size_str = F_M.get_size_str_formatted(size)

        if size > 349175808:
            self.log_callback(
                f"[yellow]Calculating... {size_str} {file_path}[/yellow]"
            )
            size_str = f"[red]{size_str}[/red]"

        hash_value = self.calculate_hash(file_path)

        if hash_value is None:
            return False

        pending_updates.append((an_id, hash_value))

        processed = self.items_total - self.queue.qsize()

        self.log_callback(
            f"[cyan]{processed}[/cyan]/"
            f"[green]{self.items_total}[/green] "
            f"([yellow]{hash_value}[/yellow]) "
            f"({an_id}) "
            f"{size_str} "
            f"{file_path}"
        )

        return True

    # ------------------------------------------------------------------
    # Control
    # ------------------------------------------------------------------

    def quit(self):
        self.killer_event.set()

    # ------------------------------------------------------------------
    # Main thread
    # ------------------------------------------------------------------

    def run(self):
        self.log_callback(
            '[green]' +
            '<' * 10 +
            'Successfully Started calculation Thread' +
            '>' * 10
        )

        progress = None
        progress_bar = self.pbar_stream

        if progress_bar is None:
            progress_bar = RichMapProgress()

        if isinstance(progress_bar, MapProgress):
            progress = progress_bar

        exit_key = "F12" if os.name == 'nt' else "ctrl+c"

        if progress:
            progress.start(
                100,
                description=(
                    f"[blue]{self.table} "
                    f"[red](Press {exit_key} to Exit)"
                )
            )

        pending_updates = []

        try:
            # ----------------------------------------------------------
            # Load work
            # ----------------------------------------------------------

            self.fill_queue_with_files()

            if not self.is_data:
                self.calculation_finished = True
                return

            # ----------------------------------------------------------
            # Process files continuously
            # ----------------------------------------------------------

            while not self.killer_event.is_set():

                # Calculate one file.
                #
                # This also:
                #   - gets the next file from the queue
                #   - shows the >333 MB message
                #   - calculates the hash
                #   - adds the result to pending_updates
                #   - prints the per-file result
                #
                if not self.calculate_for_next_file(pending_updates):
                    break

                # ------------------------------------------------------
                # Write DB every DB_BATCH_SIZE files
                # ------------------------------------------------------

                if len(pending_updates) >= self.DB_BATCH_SIZE:
                    self.update_database_batch(pending_updates)
                    pending_updates.clear()

                # ------------------------------------------------------
                # Progress
                # ------------------------------------------------------

                processed = (self.items_total - self.queue.qsize())

                per = self.Get_Progress_Percentage(
                    processed, self.items_total)

                if self.pbar_stream:
                    self.Pbar_Set_Status(self.pbar_stream, per)

                elif progress:
                    progress.update(
                        current=per,
                        description=(
                            f"[blue]{self.table} "
                            f"[red](Press {exit_key} to Exit)"
                        )
                    )

            # ----------------------------------------------------------
            # Write remaining DB updates
            # ----------------------------------------------------------

            if not self.killer_event.is_set() and pending_updates:
                self.update_database_batch(pending_updates)
                pending_updates.clear()

            self.calculation_finished = True

        except KeyboardInterrupt:
            self.killer_event.set()

            msg = 'User Cancel'

            if self.use_logger:
                log.info(msg)
            else:
                self.log_callback(msg)

        except Exception as e:
            self.killer_event.set()

            msg = (
                f"Stream calculation fatal error! "
                f"exiting thread!: {e}"
            )

            if self.use_logger:
                log.exception(msg)
            else:
                self.log_callback(msg)

        finally:
            self.db.close_connection()
            if progress:
                progress.stop()

        # --------------------------------------------------------------
        # Finished / killed
        # --------------------------------------------------------------

        if self.killer_event.is_set():
            msg = "Stream calculation Killing event Detected!"

            if self.use_logger:
                log.info(msg)
            else:
                self.log_callback(msg)

        else:
            msg = "Stream calculation Ended successfully!"

            if self.use_logger:
                log.info(msg)
            else:
                self.log_callback(msg)

        if self.pbar_stream:
            self.Pbar_Set_Status(
                self.pbar_stream,
                100
            )
def main():    
    import keyboard
    import time
    from datetime import datetime
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
