import os

from class_backup_actions import *
from class_file_mapper import FileMapper
from class_file_manipulate import FileManipulate

FM = FileManipulate()

class ForwardDBStructurer:
    """
    Builds a file-structure representation directly from a database map.

    Unlike ``FileStructurer``, which operates on an already-loaded
    ``pandas.DataFrame`` and can therefore process an entire map at once,
    this class queries the database only for the requested path.

    This is useful for large maps where loading the complete map would be
    unnecessarily expensive. For example, a database map may contain
    hundreds of thousands of files, while the caller may only require the
    structure of one directory.

    The class uses the database map's mount point and stored ``filepath``
    values to locate files and directories below a requested filesystem
    path. The returned paths are converted into the project's file-structure
    dictionary format using ``FileMapper`` structure helpers.

    Typical flow::

        database map
            |
            +-- get_dirs_in_db_path()
            |
            +-- get_files_in_db_path()
            |
            +-- path_to_file_structure_dict()
            |
            +-- merge_file_structure_dicts()
            |
            +-- resulting file structure

    Attributes:
        fm (FileMapper):
            FileMapper instance providing database access and path utilities.

        db_map_pair (tuple):
            Pair identifying the database and map being queried.
            Expected format is ``(database, map)``.

        ba (BackupActions):
            BackupActions instance used to access the common map manager.

        cma:
            Reference to the common map manager obtained from ``ba.cma``.
    """

    def __init__(self, fm: FileMapper, db_map_pair, ba: BackupActions):
        """
        Initialize a database-backed file structure builder.

        Args:
            fm (FileMapper):
                FileMapper instance used for database access and path
                manipulation.

            db_map_pair (tuple):
                Database/map pair identifying the map to query.
                Expected format is ``(database, map)``.

            ba (BackupActions):
                BackupActions instance providing access to the common map
                manager.
        """
        self.fm = fm
        self.db_map_pair = db_map_pair
        self.ba = ba
        self.cma = self.ba.cma

    def build_struct(
        self,
        path,
        in_tup: bool = True,
        selected_fields: list = None
    ):
        """
        Build a file-structure dictionary for a specific database path.

        Only the requested path is queried. The complete database map is not
        loaded into memory, making this method suitable for large maps.

        Direct child directories are queried separately from direct files.
        Each returned path is converted into the standard file-structure
        representation and merged into the resulting structure.

        Args:
            path (str):
                Filesystem path for which the structure should be generated.

            in_tup (bool, optional):
                Controls the representation of files.

                If ``True``, files are represented as tuples containing
                ``(filename, size)`` and optionally additional selected
                fields.

                If ``False``, only the filename is included.

                Defaults to ``True``.

            selected_fields (list, optional):
                Additional database fields to include in the file tuple.
                ``filename`` and ``size`` are always included when
                ``in_tup`` is ``True``.

                Fields that do not exist in the map are ignored.

        Returns:
            dict:
                File-structure dictionary containing the requested path
                and its direct files and directories.

        Example:
            A path containing::

                MyDocuments/file1.txt
                MyDocuments/folder1/file2.txt

            may produce a structure equivalent to::

                {
                    "MyDocuments": [
                        "file1.txt",
                        {
                            "folder1": [
                                "file2.txt"
                            ]
                        }
                    ]
                }
        """
        if not path.strip():
            return {}
        dirs = self.get_dirs_in_db_path(path,self.db_map_pair,self.fm)
        files = self.get_files_in_db_path(path,self.db_map_pair,self.fm,in_tup, selected_fields) 

        result = []
        struct={}
        for dirname in dirs:
            full_path=os.path.join(path,dirname)
            full_path=FM.fix_separator_in_path(full_path)
            dir_struct=FM.path_to_file_structure_dict(full_path,None,False)
            struct=FM.merge_file_structure_dicts(struct,dir_struct)

        for file_tup in files:
            full_path=FM.fix_separator_in_path(path)
            file_struct=FM.path_to_file_structure_dict(full_path,file_tup,False)
            struct=FM.merge_file_structure_dicts(struct,file_struct)
        
        return struct
    
    def get_full_mount_path_of_map(self, database, a_map):
        """
        Return the filesystem path represented by a database map.

        The path is constructed from the map's mount point and mapped path.

        Args:
            database:
                Database identifier.

            a_map:
                Map identifier/name.

        Returns:
            str:
                Combined mount and mapped path.

                Returns an empty string if map information cannot be
                retrieved.
        """
        try:
            map_info=self.cma.get_map_info(database,a_map)
            # mount= 5 mappath = 3
            mount_path_of_map=os.path.join(map_info[0][5],map_info[0][3])
            return mount_path_of_map
        except:
            pass
        return ""
    
    def get_mount_of_map(self, database, a_map) -> str:
        """
        Return the mount point associated with a database map.

        The mount point is the filesystem root from which the map's
        ``filepath`` values are interpreted.

        Examples of mount points include::

            /
            C:\\
            D:\\

        Args:
            database:
                Database identifier.

            a_map:
                Map identifier/name.

        Returns:
            str:
                Map mount point, or an empty string if the map information
                cannot be retrieved.
        """

        try:
            map_info=self.cma.get_map_info(database,a_map)
            # mount= 5 mappath = 3
            return map_info[0][5]
        except:
            pass
        return ""
    
    def get_files_in_db_path(
        self,
        path,
        db_map_pair,
        fm: FileMapper,
        in_tup=True,
        selected_fields=None
        ):
        """
        Return files directly contained in a database path.

        The database stores the directory portion of a file separately from
        its filename. This method queries rows whose normalized ``filepath``
        exactly matches the requested path.

        Therefore, files in descendant directories are not returned.

        For example, given::

            User/MyDocuments/file1.txt
            User/MyDocuments/folder1/file2.txt

        querying ``User/MyDocuments`` returns only ``file1.txt``.

        Path separators stored in the database are normalized to ``/`` in
        the SQL expression so that maps created on different operating
        systems can be queried consistently.

        Args:
            path (str):
                Filesystem path to query.

            db_map_pair (tuple):
                Database/map pair identifying the map to query.

            fm (FileMapper):
                FileMapper used for database access and path utilities.

            in_tup (bool, optional):
                If ``True``, return file information as tuples beginning with
                ``(filename, size)``. If ``False``, return filenames only.

            selected_fields (list, optional):
                Additional database fields to append to each tuple.
                Unknown fields are ignored.

        Returns:
            list:
                List of filenames or file tuples.

        Notes:
            The query is intentionally restricted to an exact ``filepath``
            match. Using ``LIKE path + '%'`` here would also return files
            belonging to descendant directories.
        """

        ext_path = path
        # remove end separator
        if path and path[-1] in ["/", "\\", os.sep]:
            ext_path = path[:-1]

        mount = self.get_mount_of_map(db_map_pair[0], db_map_pair[1])
        if not mount:
            return []
        # Remove mount to find path in filepath
        if mount in ["/", "\\", os.sep]:
            ext_path = ext_path[1:]
        else:
            ext_path = ext_path.replace(mount, "")
        a_map = db_map_pair[1]
        # ---------------------------
        # Direct files
        # ---------------------------

        where = ("(replace(filepath, '\\', '/') = " + fm.db.quotes(ext_path)+")")
        data_files = fm.db.get_data_from_table(a_map, "*", where)
        
        if not data_files:
            return []
        
        fields = fm.db.get_column_list_of_table(a_map)
        
        file_list=[]
        for info in data_files:
            info_dict=fm.data_to_field_dict(fields,info)
            if not info_dict:
                continue
            # db_id = info_dict["id"]
            # filepath = info_dict["filepath"]
            filename = info_dict["filename"]
            size = info_dict["size"]
            # ch_full_path=os.path.join(mount,filepath)
            # ch_filepath=os.path.join(ch_full_path,filename)
            if in_tup:
                file_tup=(filename,size)
                if isinstance(selected_fields,list):
                    for field in selected_fields:
                        if field in fields and field not in ["filename","size"]:
                            file_tup += (info_dict.get(field),)
            else:
                file_tup = filename
            file_list.append(file_tup)
        return file_list
            
    def get_dirs_in_db_path(
        self,
        path,
        db_map_pair,
        fm: FileMapper
        ):
        """
        Return the unique direct child directories of a database path.

        Directories are not stored as separate database records. They are
        inferred from the ``filepath`` values of files contained somewhere
        below the requested path.

        For example, if the database contains::

            User/MyDocuments/file1.txt
            User/MyDocuments/folder1/file2.txt
            User/MyDocuments/folder1/folder2/file3.txt
            User/MyDocuments/folder2/file4.txt

        querying ``User/MyDocuments`` returns::

            ["folder1", "folder2"]

        while querying ``User/MyDocuments/folder1`` returns::

            ["folder2"]

        The SQL query extracts the first path component following the
        requested path. ``DISTINCT`` removes duplicates caused by multiple
        files existing below the same directory.

        This allows directories to be reconstructed without loading all
        database rows into Python.

        Args:
            path (str):
                Filesystem path whose direct child directories should be
                returned.

            db_map_pair (tuple):
                Database/map pair identifying the map to query.

            fm (FileMapper):
                FileMapper used for database access and path manipulation.

        Returns:
            list:
                Unique names of direct child directories.

        Notes:
            Empty directories cannot be discovered because the database map
            contains file records only. A directory is considered present
            when at least one mapped file exists somewhere below it.
        """

        ext_path = FM.fix_separator_in_path(path,add_sep_start=True) 
        mount = self.get_mount_of_map(db_map_pair[0], db_map_pair[1])
        if not mount:
            return []
        # Remove mount to find path in filepath
        if mount in ["/", "\\", os.sep]:
            ext_path = ext_path[1:]
        else:
            ext_path = ext_path.replace(mount, "")
        a_map = db_map_pair[1]
        # ---------------------------
        # Direct directories
        # ---------------------------
        where_dirs = (
            "replace(filepath, '\\', '/') LIKE "
            + fm.db.quotes(ext_path + "%")
        )

        relative_expr = (
            "substr("
            "replace(filepath, '\\', '/'), "
            + str(len(ext_path) + 1)
            + ")"
        )

        dirname_expr = (
            "CASE "
            "WHEN instr(" + relative_expr + ", '/') > 0 "
            "THEN substr(" + relative_expr + ", 1, instr(" + relative_expr + ", '/') - 1) "
            "ELSE " + relative_expr + " "
            "END"
        )
        #data = fm.db.get_data_from_table(a_map, "*")

        data_dirs = fm.db.get_data_from_table(a_map,f"DISTINCT {dirname_expr}", where_dirs)
        if not data_dirs:
            return []
        dirs_list=[]
        for path_part_tup in data_dirs:
            dirname=path_part_tup[0]
            if not dirname:
                continue
            dirs_list.append(dirname)
        return dirs_list
    #-----------------------------------------------------------------
    # # filestructure functions
    #-----------------------------------------------------------------
    # use with 
    # # self.fmap.fm.path_to_file_structure_dict() # for file_structure
    # # self.fmap.fm.merge_file_structure_lists
    # or filestructurer
    def get_structure_node(self, structure, path):
        """
        Locate a node in a file-structure dictionary.

        Traverses the project's nested dictionary/list file-structure
        representation according to the supplied path.

        Args:
            structure (dict | list):
                File-structure object to search.

            path (str):
                Path to locate within the structure.

        Returns:
            Any | None:
                The structure node corresponding to ``path``, or ``None``
                when the path does not exist.
        """
        path_list = FM.path_to_list(path)
        current = structure
        for part in path_list:
            if isinstance(current, dict):
                if part not in current:
                    return None
                current = current[part]
            elif isinstance(current, list):
                found = False
                for item in current:
                    if isinstance(item, dict) and part in item:
                        current = item[part]
                        found = True
                        break
                if not found:
                    return None
            else:
                return None
        return current
    
    def get_structure_children(self, contents):
        """
        Return the immediate children represented by a file-structure node.

        Files are identified by strings or tuples, while directories are
        represented by dictionaries.

        Args:
            contents (list):
                Contents of a file-structure node.

        Returns:
            list:
                List of ``(name, type)`` pairs where ``type`` is either
                ``"file"`` or ``"dir"``.
        """
        entries = []
        if not isinstance(contents, list):
            return entries
        for item in contents:
            if isinstance(item, (str|tuple)):
                # File
                entries.append((item, "file"))

            elif isinstance(item, dict):
                # Directory
                for name in item:
                    entries.append((name, "dir"))

        return entries


    
