import os
import threading
from collections import Counter, defaultdict

from class_sqlite_database import SQLiteDatabase, sqlite3
#from controllers.class_filemap_cli_manager import FileMapCliManager

from class_file_mapper import MD5_CALC, MD5_SHALLOW

LOG_AFTER = 5
LOG_AFTER_TOP = 50

class RepeatedDuplicateSearch:
    """SQL-backed search for repeated files and duplicates.

    Source databases are opened and managed by FileMapCliManager.
    Search data and result references are stored in a temporary database.

    Result descriptor:
        {
            "database": temporary_database_path,
            "table": result_table_name,
            "groups_table": result_groups_table_name,
            "mode": mode,
            "db_map_pair_list": original_db_map_pair_list,
        }
    """

    BATCH_SIZE = 1000

    def __init__(self, fmap):
        self.fmap = fmap

    @staticmethod
    def _check_cancel(kill_ev):
        if kill_ev and kill_ev.is_set():
            raise InterruptedError("Repeated/duplicate search cancelled")

    @staticmethod
    def _quote(db:SQLiteDatabase, name):
        return db.quote_identifier(name)

    def search(
        self,
        db_map_pair_list,
        mode,
        progress_bar=None,
        log_callback=None,
        kill_ev: threading.Event | None = None,
    ):
        """ Search selected database maps for repeated files or duplicates.
            Creates a temporary database containing three tables: 
                worktable: (id, md5, dbmapindex, idin_db, filepath, filename) 
            Working occurrences used for MD5 grouping and classification.

            groupstable: (groupid, md5, occurrence_count) 
                One row per matching group, identifying its MD5 and number of matched file occurrences.

            resulttable: (groupid, dbmapindex, idindb) 
                Compact references to original file records, allowing the GUI lazy loader to retrieve 
                full file information on demand.

            The search processes maps individually, batches inserts, groups occurrences by MD5, 
            and classifies matches according to mode. Source database records are not modified.

            Args: 
                dbmappairlist (list[tuple]): Selected (databasepath, mapname) pairs. 
                    Their list positions become dbmapindex values. 
                mode (str): 'repeated' or 'duplicates'. 
                progressbar (optional): Progress reporting interface. 
                logcallback (optional): Callback for status messages. 
                killev (threading.Event | None): Cancellation event.

            Returns: 
                dict | None: Temporary database path, result table name, groups table name, 
                search mode, and original database/map pairs; None if cancelled.

            Raises: 
                ValueError: Invalid mode or missing required source columns. 
                RuntimeError: Temporary database creation or source map access fails. """
        mode = mode.lower()

        if mode not in {"repeated", "duplicates"}:
            raise ValueError(
                "mode must be 'repeated' or 'duplicates'"
            )

        if not db_map_pair_list:
            return None

        log = log_callback or print
        temp_db_path = None
        temp_db = None

        try:
            # --------------------------------------------------
            # Create the temporary database through fmap.
            # --------------------------------------------------
            source_path, source_table = db_map_pair_list[0]

            temp_db_path = self.fmap._create_temporal_database(
                source_path,
                source_table,
                log_callback=log,
            )

            if not temp_db_path:
                raise RuntimeError(
                    "Could not create the temporary search database"
                )

            temp_fm = self.fmap.cma.get_file_map(temp_db_path)

            if not temp_fm:
                raise RuntimeError(
                    "Could not open the temporary search database"
                )

            temp_db = temp_fm.db

            # Use unique names to avoid collisions with the mapper's
            # own table and any other tables in the temporary database.
            suffix = self.fmap._get_timestamp()

            work_table = f"search_occurrences_{suffix}"
            result_table = f"search_results_{suffix}"
            groups_table = f"search_groups_{suffix}"

            qwork = self._quote(temp_db, work_table)
            qresult = self._quote(temp_db, result_table)
            qgroups = self._quote(temp_db, groups_table)

            cursor = temp_db.conn.cursor()

            try:
                cursor.executescript(f"""
                    CREATE TABLE {qwork} (
                        id INTEGER PRIMARY KEY,
                        md5 TEXT NOT NULL,
                        db_map_index INTEGER NOT NULL,
                        id_in_db INTEGER NOT NULL,
                        filepath TEXT,
                        filename TEXT
                    );

                    CREATE TABLE {qgroups} (
                        group_id INTEGER PRIMARY KEY,
                        md5 TEXT NOT NULL,
                        occurrence_count INTEGER NOT NULL
                    );

                    CREATE TABLE {qresult} (
                        group_id INTEGER NOT NULL,
                        db_map_index INTEGER NOT NULL,
                        id_in_db INTEGER NOT NULL,
                        PRIMARY KEY (
                            group_id,
                            db_map_index,
                            id_in_db
                        )
                    );
                """)

                temp_db.conn.commit()

            finally:
                cursor.close()

            # --------------------------------------------------
            # Read one source map at a time and populate the
            # working table.
            # --------------------------------------------------
            total = len(db_map_pair_list)

            if progress_bar:
                progress_bar.start(total, "Indexing file occurrences")

            for pair_index, (source_db, table_name) in enumerate(db_map_pair_list):
                self._check_cancel(kill_ev)

                source_fm = self.fmap.cma.get_file_map(source_db)
                if not source_fm:
                    raise RuntimeError(f"Could not open database/map: {source_db}, {table_name}")

                db = source_fm.db
                required = {"id", "md5", "filepath", "filename"}
                available = set(db.get_column_list_of_table(table_name))
                missing = required - available
                if missing:
                    raise ValueError(f"Table {table_name} is missing columns: {sorted(missing)}")

                columns = ", ".join(self._quote(db, column)
                    for column in ("id", "md5", "filepath", "filename"))

                sql = (
                    f"SELECT {columns} "
                    f"FROM {self._quote(db, table_name)} "
                    f"ORDER BY {self._quote(db, 'md5')}"
                )

                rows = db.get_data_sql_command(sql)

                insert_sql = f"""
                    INSERT INTO {qwork}
                    (md5, db_map_index, id_in_db, filepath, filename)
                    VALUES (?, ?, ?, ?, ?)
                """

                batch = []

                for record_id, md5, filepath, filename in rows:
                    self._check_cancel(kill_ev)

                    # Deep maps should already have been filtered by
                    # the caller. Do not treat placeholders as hashes.
                    if not md5 or md5 in {MD5_CALC, MD5_SHALLOW}:
                        continue

                    batch.append((
                        md5,
                        pair_index,
                        record_id,
                        filepath,
                        filename,
                    ))

                    if len(batch) >= self.BATCH_SIZE:
                        temp_db.conn.executemany(insert_sql, batch)
                        temp_db.conn.commit()
                        batch.clear()

                if batch:
                    temp_db.conn.executemany(insert_sql, batch)
                    temp_db.conn.commit()

                log(f"Indexed map {pair_index + 1}/{total}: {table_name}")

                if progress_bar:
                    progress_bar.update(
                        current=pair_index + 1,
                        description="Indexing file occurrences")

            # The bulk load is complete; build indexes for classification.
            temp_db.conn.executescript(f"""
                CREATE INDEX idx_{suffix}_md5
                    ON {qwork}(md5);

                CREATE INDEX idx_{suffix}_map_path_name
                    ON {qwork}(db_map_index, filepath, filename);
            """)
            temp_db.conn.commit()

            # --------------------------------------------------
            # Classify one MD5 group at a time.
            # --------------------------------------------------
            self._check_cancel(kill_ev)

            cursor = temp_db.conn.cursor()

            try:
                cursor.execute(f"""
                    SELECT md5, db_map_index, id_in_db, filepath, filename
                    FROM {qwork}
                    ORDER BY md5, db_map_index, id_in_db
                """)

                group_id = 0
                current_md5 = None
                records = []
                iii = 0
                num_files = 0
                stats={}

                def flush_group(md5, group_records):
                    nonlocal group_id
                    nonlocal num_files
                    num_files += 1
                    
                    if len(group_records) < 2:
                        return
                    matched = self._classify_group(group_records, mode)
                    if len(matched) < 2:
                        return
                    group_id += 1
                    temp_db.conn.execute(
                        f"""
                        INSERT INTO {qgroups}
                            (group_id, md5, occurrence_count)
                        VALUES (?, ?, ?)
                        """,
                        (group_id, md5, len(matched)),
                    )

                    temp_db.conn.executemany(
                        f"""
                        INSERT INTO {qresult}
                            (group_id, db_map_index, id_in_db)
                        VALUES (?, ?, ?)
                        """,
                        [
                            (group_id, map_index, record_id)
                            for map_index, record_id in matched
                        ],
                    )
                    nonlocal iii
                    nonlocal stats
                    
                    iii += 1
                    len_r = len(matched)
                    if not stats.get(len_r):
                        stats[len_r] = (1, md5)
                    else:
                        num, _ =stats.get(len_r)
                        stats[len_r] = (num + 1, md5)
                    if len_r>LOG_AFTER:
                        lr=f"[cyan]{len_r}[/cyan]" if len_r<LOG_AFTER_TOP else f"[red]{len_r}[/red]"
                        log(f"[green]{iii}.[/green] [yellow]{md5}[/yellow] -> Found {lr} {mode} matches!")
                
                
                for md5, map_index, record_id, filepath, filename in cursor:
                    self._check_cancel(kill_ev)

                    if current_md5 is not None and md5 != current_md5:
                        flush_group(current_md5, records)
                        records = []

                        # Commit completed groups periodically.
                        if group_id and group_id % 100 == 0:
                            temp_db.conn.commit()

                    current_md5 = md5
                    records.append((
                        map_index,
                        record_id,
                        filepath,
                        filename,
                    ))

                if current_md5 is not None:
                    flush_group(current_md5, records)
                    

                temp_db.conn.commit()
                log("[yellow]"+"-"*33)
                log(f"[yellow]Summary:")
                for occur,(num,mmm) in stats.items():
                    if occur == 1:
                        log(f"Found [magenta]{num}[/magenta] non {mode} files!")
                        continue
                    occ=f"[cyan]{occur}[/cyan]" if occur<LOG_AFTER_TOP else f"[red]{occur}[/red]"
                    mddddd=""
                    if num == 1:
                        mddddd=f"-> [yellow]{mmm}[/yellow]"
                    log(f"[magenta]{num}[/magenta] groups of {occ} {mode} were found! {mddddd}")
                log("[yellow]"+"-"*33)

            finally:
                cursor.close()

            log(f"[yellow]Search complete: [magenta]{iii}[/magenta] matching groups in [green]{num_files}[/green] files")

            return {
                "database": temp_db_path,
                "table": result_table,
                "groups_table": groups_table,
                "mode": mode,
                "db_map_pair_list": db_map_pair_list,
            }

        except InterruptedError:
            log("Repeated/duplicate search cancelled")
            return None

        finally:
            if progress_bar:
                progress_bar.stop()

    @staticmethod
    def _classify_group(records, mode):
        """Return references participating in at least one match.

        records:
            [(map_index, record_id, filepath, filename), ...]

        The original file paths are compared as stored. This method
        does not reconstruct absolute paths.
        """
        matched = set()

        if mode == "duplicates":
            # Duplicate: same map, same stored folder, different name.
            by_folder = defaultdict(list)

            for map_index, record_id, filepath, filename in records:
                by_folder[(map_index, filepath)].append(
                    (map_index, record_id, filename)
                )

            for folder_records in by_folder.values():
                if len(folder_records) < 2:
                    continue

                name_counts = Counter(
                    filename
                    for _, _, filename in folder_records
                )

                total = len(folder_records)

                for map_index, record_id, filename in folder_records:
                    if total > name_counts[filename]:
                        matched.add((map_index, record_id))

        else:
            # Repeated: different stored folders AND different names.
            # This mirrors the original filepath/filename comparison.
            paths = Counter(filepath for _, _, filepath, _ in records)
            names = Counter(filename for _, _, _, filename in records)
            path_name = Counter(
                (filepath, filename)
                for _, _, filepath, filename in records
            )

            total = len(records)

            for map_index, record_id, filepath, filename in records:
                # Inclusion-exclusion: is there at least one other
                # occurrence with both a different path and name?
                candidates = (
                    total
                    - paths[filepath]
                    - names[filename]
                    + path_name[(filepath, filename)]
                )

                if candidates > 0:
                    matched.add((map_index, record_id))

        return matched
    
    def repeated_duplicates_search_result(self, search_dict):
        """
        Load repeated/duplicate search results from the temporary database.

        Table schemas:
            groups_table:
                (group_id, md5, occurrence_count)

            result_table:
                (group_id, db_map_index, id_in_db)

        Returns:
            dict: Ordered mapping:
                md5 -> [(db_map_index, id_in_db), ...]
        """
        import sqlite3

        if not isinstance(search_dict, dict):
            raise TypeError("search_dict must be a dictionary")

        temp_db_path = search_dict.get("database")
        result_table = search_dict.get("table")
        groups_table = search_dict.get("groups_table")
        mode = search_dict.get("mode")

        if not all((temp_db_path, result_table, groups_table)):
            raise ValueError(
                "Search results require database, table and groups_table"
            )

        if mode not in {"repeated", "duplicates"}:
            raise ValueError(
                "mode must be 'repeated' or 'duplicates'"
            )

        self.db_map_pair_list = search_dict.get("db_map_pair_list") or []
        self.mode = mode

        def quote_identifier(name):
            return '"' + name.replace('"', '""') + '"'

        result_sql = quote_identifier(result_table)
        groups_sql = quote_identifier(groups_table)

        # Use the existing FileMapper connection.
        temp_fm = self.fmap.cma.get_file_map(temp_db_path)

        if not temp_fm:
            raise RuntimeError(
                f"Could not open temporary database: {temp_db_path}"
            )

        db = temp_fm.db
        conn = db.conn

        # Preserve the connection's existing transaction/lifecycle.
        previous_row_factory = conn.row_factory

        try:
            conn.row_factory = sqlite3.Row

            # Read groups in their explicit comparison order.
            groups = {}

            group_rows = conn.execute(
                f"""
                SELECT group_id, md5
                FROM {groups_sql}
                ORDER BY group_id
                """
            )

            for row in group_rows:
                groups[row["md5"]] = []

            # Join occurrences to their MD5 groups.
            # The result table deliberately stores IDs, not MD5 values.
            result_rows = conn.execute(
                f"""
                SELECT
                    g.md5,
                    r.db_map_index,
                    r.id_in_db
                FROM {result_sql} AS r
                INNER JOIN {groups_sql} AS g
                    ON r.group_id = g.group_id
                ORDER BY
                    g.group_id,
                    r.db_map_index,
                    r.id_in_db
                """
            )

            for row in result_rows:
                groups[row["md5"]].append(
                    (
                        row["db_map_index"],
                        row["id_in_db"],
                    )
                )

        finally:
            conn.row_factory = previous_row_factory

        return groups





# from collections import defaultdict
# import threading

# from class_sqlite_database import SQLiteDatabase
# from controllers.class_filemap_cli_manager import FileMapCliManager

# class RepeatedDuplicateSearch:
#     """
#     Finds repeated files or duplicates across selected database/table pairs.

#     Result format:
#         {
#             md5: [
#                 (db_map_pair_index, record_id),
#                 ...
#             ]
#         }

#     db_map_pair_index refers to the ORIGINAL input list, including
#     entries skipped because their maps are not searchable.
#     """

#     COLUMNS = ("id", "md5", "filepath", "filename")

#     def __init__(self, log_callback=None):
#         self.log = log_callback or print

#     def search(
#         self,
#         fmap:FileMapCliManager,
#         db_map_pair_list,
#         mode,
#         progress_bar=None,
#         kill_ev: threading.Event | None = None,
#     ):
#         self.fmap=fmap
#         mode = mode.lower()

#         if mode not in {"repeated", "duplicates"}:
#             raise ValueError(
#                 "mode must be 'repeated' or 'duplicates'"
#             )

#         # md5 -> candidate records
#         candidates = defaultdict(list)

#         total = len(db_map_pair_list)

#         if progress_bar:
#             progress_bar.start(
#                 total,
#                 "Indexing repeated/duplicate candidates",
#             )

#         try:
#             for pair_index, (a_db, table_name) in enumerate(
#                 db_map_pair_list
#             ):
#                 fm=self.fmap.cma.get_file_map(a_db)
#                 if not fm:
#                     continue
#                 db = fm.db
#                 if kill_ev and kill_ev.is_set():
#                     return {}

#                 columns = ", ".join(
#                     db.quote_identifier(column)
#                     for column in self.COLUMNS
#                 )

#                 sql = (
#                     f"SELECT {columns} "
#                     f"FROM {db.quote_identifier(table_name)} "
#                     f"ORDER BY {db.quote_identifier('md5')}"
#                 )

#                 rows = db.get_data_sql_command(sql)

#                 for record_id, md5, filepath, filename in rows:
#                     if not md5:
#                         continue

#                     candidates[md5].append({
#                         "ref": (pair_index, record_id),
#                         "filepath": filepath,
#                         "filename": filename,
#                     })

#                 if progress_bar:
#                     progress_bar.update(
#                         current=pair_index + 1,
#                         description="Indexing repeated/duplicate candidates",
#                     )

#             result = {}

#             for md5, records in candidates.items():
#                 if kill_ev and kill_ev.is_set():
#                     return result

#                 if len(records) < 2:
#                     continue

#                 # Preserve the existing algorithm's anchor-record
#                 # matching behaviour.
#                 anchor = records[0]
#                 matches = [anchor["ref"]]

#                 for record in records[1:]:
#                     same_path = (
#                         record["filepath"] == anchor["filepath"]
#                     )
#                     same_name = (
#                         record["filename"] == anchor["filename"]
#                     )

#                     if mode == "duplicates":
#                         matched = same_path and not same_name
#                     else:
#                         matched = not same_path and not same_name

#                     if matched:
#                         matches.append(record["ref"])

#                 if len(matches) > 1:
#                     result[md5] = matches

#             return result

#         finally:
#             if progress_bar:
#                 progress_bar.stop()