# class_db_tree_viewer.py

from PyQt6 import QtCore, QtWidgets
import os

from class_sqlite_database import *
from class_backup_actions import BackupActions
from class_file_manipulate import FileManipulate
from class_data_manage import DataManage
from class_file_structurer import FileStructurer

FM=FileManipulate()

from class_LogHandler import LM
log=LM.get_logger_with_handler("DBTreeModel","debug",True,None)

class DBTreeNode:
    """
    Lightweight tree node used by DBTreeModel.

    The node only stores the minimum information required to
    represent an item in the tree. Database access is delegated
    to DBTreeModel through the db_map_key and id_in_map references.

    A node may represent:
        - root
        - database
        - map
        - folder
        - file

    Children are loaded on demand when a node is expanded.
    """

    def __init__(
        self,
        node_id,
        name,
        file="",
        path="",
        parent=None,
        node_type="folder",
        db_map_key=None,
        id_in_map=None,
        size=0
    ):
        self.node_id = node_id
        self.name = name
        self.file = file
        self.path = path
        self.parent = parent
        self.node_type = node_type
        # external references
        self.db_map_key = db_map_key       # identifies database map/table pair
        self.id_in_map = id_in_map        # file row id if exists
        self.size = size
        self.children = []
        self.loaded = False
        self.children_count = None
        self.is_dir = node_type in (
            "folder",
            "dir",
            "map",
            "database",
            "root"
        )
        self.is_expandable = node_type in (
            "database",
            "map",
            "folder",
            "dir",
            "root"
        )
    def get_node_id_bloodline(self) -> list[int]:
        """
        Returns the trace of node ids from the tree root to this node.

        Returns:
            list[int]:
                Ordered list of node ids beginning at the root node and
                ending with this node.

        Example:
            [0, 5, 18, 41]
        """
        trace = []
        node = self
        while node is not None:
            trace.append(node.node_id)
            node = node.parent
        trace.reverse()          # root -> me
        return trace
    
    def get_node_bloodline(self) -> list:
        """
        Returns the trace of node objects from the tree root
        to this node.

        Returns:
            list[DBTreeNode]:
                Ordered list of nodes beginning at the root node and
                ending with this node.
        """
        trace = []
        node = self
        while node is not None:
            trace.append(node)
            node = node.parent
        trace.reverse()
        return trace

class DBTreeRegistry:
    """
    Registry relating tree nodes to database/map pairs.

    A database may contain multiple maps (tables). Rather than
    storing database objects inside every node, nodes only keep
    a db_map_key which can be resolved through this registry.

    This avoids duplicated references and keeps DBTreeNode
    independent of the database implementation.
    """
    def __init__(self):
        self.databases = {}
        self.maps = {}

    def register_db_map(self, db_map_key, db, map):
        """Register a database map pair

        Args:
            db_map_key (int): index of pair
            db (str): database path/to/filename.db
            map (str): table in database
        """
        idx_db=self._get_db_index(db)
        if idx_db is None:
            self._add_database(self._new_db_index(),db)
        self._add_map(db_map_key,idx_db,map)
    
    def unregister_db_map(self, db_map_key):
        """
        Removes a database/map association.

        If no remaining maps reference the database, the database
        entry is also removed from the registry.

        Args:
            db_map_key (int):
                Registered database/map key.
        """
        if db_map_key in self.maps.keys():
            md=self.maps.pop(db_map_key)
            # see if db is in other maps
            for rmp in self.maps.values():
                if rmp["db"] == md["db"]:
                    return
            # remove db if not found
            self.databases.pop(md["db"])
    
    def _new_db_index(self) -> int:
        """
        Returns the next available internal database index.

        Returns:
            int:
                Unused database registry index.
        """
        idx=0
        while idx in self.databases.keys():
            idx+=1
        return idx
    
    def _get_db_index(self, db) -> int | None:
        """
        Finds the registry index for a database.

        Args:
            db (str):
                Database filename or path.

        Returns:
            int | None:
                Database registry index or None if not registered.
        """
        for idx, adb in self.databases.items():
            if adb == db:
                return idx
        return None
    
    def number_of_pairs(self):
        return len(self.maps)
    
    def number_of_databases(self):
        return len(self.databases)

    def _add_database(self, key, db:str):
        """Path and filename of database"""
        self.databases[key]=db

    def _add_map(self, map_key, db_key, table):
        """
        Registers a map belonging to a registered database.

        Args:
            map_key (int):
                External map identifier.

            db_key (int):
                Internal database registry index.

            table (str):
                Database table containing the map.
        """
        self.maps[map_key]={
            "db":db_key,
            "table":table
        }

    def _get_db(self,db_key)->str:
        return self.databases.get(db_key,None)

    def get_db_map_pair(self,map_key)->str:
        md=self.maps.get(map_key,None)
        if not md:
            return None
        return (self._get_db(md["db"]), md["table"])

class DBTreeModel(QtCore.QAbstractItemModel):
    def __init__(self, db_map_pairs:list[tuple], ba:BackupActions, parent=None ):
        """
        Qt model implementing a lazy-loading tree view of one or more
        database maps.

        Each root child represents a database/map pair. Folder contents
        are only queried from the database when expanded, allowing very
        large maps to be browsed efficiently.

        Args:
            db_map_pairs (list[tuple]):
                List containing (database_path, table_name) pairs.

            ba (BackupActions):
                BackupActions instance used to retrieve map information
                and file data.

            parent:
                Optional Qt parent object.
        """
        super().__init__(parent)
        self.db_map_registry=DBTreeRegistry()
        self.node_id_map={}
        self.node_id=-1
        self.root=DBTreeNode(self._new_node_id(),"DB-Map Pairs",node_type="root")
        self.node_id_map[self.root.node_id] = self.root
        self.ba=ba
        self.cma=ba.cma
        for idx,db,map_name in enumerate(db_map_pairs):
            if db not in self.cma.active_databases:
                continue
            db_name=FM.extract_filename(db,True)
            self.db_map_registry.register_db_map(idx,db,map_name)
            db_map_node=DBTreeNode(
                node_id=self._new_node_id(),
                name=f"{map_name} @({db_name})",
                file="",
                path="",
                node_type="map",
                parent=self.root,
                db_map_key=idx,
                id_in_map=None,
                size=0
                )
            self.root.children.append(db_map_node)
            self.node_id_map[db_map_node.node_id] = db_map_node

    # ---------------------------------------------------------
    # Qt required functions
    # ---------------------------------------------------------
    def columnCount(self,parent=QtCore.QModelIndex()):
        """
        Returns the number of columns displayed by the tree view.

        Columns:
            0 -> Name
            1 -> Type
            2 -> Size
        """
        return 3

    def headerData(self, section, orientation, role ):
        """
        Returns the horizontal column headers shown by the tree view.
        """
        if role != QtCore.Qt.ItemDataRole.DisplayRole:
            return None

        if orientation == QtCore.Qt.Orientation.Horizontal:
            headers=[
                "Name",
                "Type",
                "Size"
            ]

            if section < len(headers):
                return headers[section]
        return None

    def index(self, row, column, parent):
        """
        Creates a QModelIndex for the requested child node.

        Qt calls this whenever it needs to display or navigate the tree.
        """
        if not self.hasIndex(row,column,parent):
            return QtCore.QModelIndex()

        parent_node=self.node_from_index(parent)

        if parent_node is None:
            parent_node=self.root

        if row < len(parent_node.children):
            child=parent_node.children[row]
            return self.createIndex(row, column, child)

        return QtCore.QModelIndex()

    def parent(self,index):
        """
        Returns the QModelIndex of a node's parent.

        Required by Qt to navigate the tree hierarchy.
        """
        if not index.isValid():
            return QtCore.QModelIndex()
        node=index.internalPointer()
        if node is None:
            return QtCore.QModelIndex()
        parent=node.parent

        if parent is None or parent == self.root:
            return QtCore.QModelIndex()
        grand = parent.parent

        if grand is None:
            return QtCore.QModelIndex()

        row = grand.children.index(parent)
        return self.createIndex(row, 0, parent)
        # return self.createIndex(parent.children.index(node), 0, parent)

    def rowCount(self, parent):
        """
        Returns the number of visible children for a node.

        For expandable nodes that have not yet been loaded,
        the number of children is obtained directly from the
        database without creating child nodes.
        """
        node=self.node_from_index(parent)
        if node is None:
            node=self.root

        if not node.is_dir:
            return 0

        # Important:
        # Qt asks this before expanding
        #
        # Return database count,
        # but do not load objects
        if not node.loaded:
            return self.count_children(node)

        return len(node.children)

    def data(self, index, role):
        """
        Returns the data displayed by the tree view.

        Columns:
            0 -> Name
            1 -> File / Folder
            2 -> File size
        """
        if not index.isValid():
            return None
        node=index.internalPointer()
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if index.column()==0:
                return node.name
            if index.column()==1:
                return ("Folder" if node.is_dir else "File")
            if index.column()==2:
                if node.is_dir:
                    return ""
                return str(node.size)
        return None

    # ---------------------------------------------------------
    # Lazy loading
    # ---------------------------------------------------------
    def hasChildren(self,index):
        """
        Returns True if the node has children.

        This method queries the database without loading the
        child nodes into memory.
        """
        node=self.node_from_index(index)
        if node is None:
            node=self.root
        if not node.is_dir:
            return False
        return self.count_children(node)>0

    def canFetchMore(self,index):
        """
        Returns True if the node supports lazy loading and its
        children have not yet been loaded.
        """
        node=self.node_from_index(index)
        if node is None:
            node=self.root
        return ( node.is_dir and not node.loaded )

    def fetchMore(self,index):
        """
        Loads child nodes into the model.

        Qt calls this when an expandable node is opened for the
        first time.
        """
        node=self.node_from_index(index)
        if node is None:
            node=self.root
        if node.loaded:
            return
        rows=self.load_children(node)
        if isinstance(rows,list) and len(rows)==0:
            node.loaded=True
            return
        self.beginInsertRows(index, 0, len(rows)-1 )

        for idx,r in enumerate(rows):
            # "id","filename","filepath","size","info","node_type","is_dir"
            # "name":name,
            # "id_in_map": None,
            # "filename":None,
            # "filepath":folder,
            # "size":tot_size,
            # "info":None,
            # "node_type":"folder",
            # "is_dir":True,
            # "parent":node.index,
            # "db_map_key":node.db_map_key,
            child=DBTreeNode(
                node_id=self._new_node_id(),
                name=r["name"],
                file=r["filename"],
                path=r["filepath"],
                parent=node,
                node_type=r["node_type"],
                db_map_key=node.db_map_key,
                id_in_map=r["id_in_map"],
                size=r.get("size",0),
            )
            node.children.append(child)
            self.node_id_map[child.node_id] = child
        node.loaded=True
        self.endInsertRows()

    # ---------------------------------------------------------
    # Database interface
    # ---------------------------------------------------------
    def count_children(self,node:DBTreeNode):
        """
        Counts the direct children of a node.

        Only immediate children are counted. No DBTreeNode
        objects are created.

        Args:
            node (DBTreeNode):
                Parent node.

        Returns:
            int:
                Number of immediate children.
        """
        if node.node_type == "root":
            return len(node.children)
        db_map_pair=self.db_map_registry.get_db_map_pair(node.db_map_key)
        info_dict=self.cma.get_map_info_dict(db_map_pair[0],db_map_pair[1])
        fm=self.cma.get_file_map(db_map_pair[0])
        if node.node_type=="map":
            # On table
            # id=0	dt_data_created'=1	'dt_data_modified'=2	'filepath'=3	'filename'=4	'md5'=5	'size'=6
            # 'dt_file_created'=7	'dt_file_accessed'=8	'dt_file_modified'=9            
            mappath= info_dict['mappath']
            data_list=fm.db.get_data_from_table(db_map_pair[1],'COUNT(*)',f"filepath = '{mappath}'")

        elif node.node_type in ["folder","dir"]:

            data_list=fm.db.get_data_from_table(db_map_pair[1],'COUNT(*)',f"filepath = '{node.path}'")

        else:
            return 0
        
        if len(data_list) > 0:
                if len(data_list[0]) > 0:
                    return data_list[0][0] # list[tuple]
        return 0

    def load_children(self,node:DBTreeNode):
        """
        Loads the direct contents of a node from the database.

        Files are added directly from database records.

        Folders are reconstructed by analysing descendant file
        paths and extracting the first directory level below
        the current node.

        Only one directory level is returned. Subfolders are
        loaded later when expanded.

        Args:
            node (DBTreeNode):
                Parent node.

        Returns:
            list[dict]:
                List of dictionaries describing the child nodes.
        """
        if node.node_type == "root":
            return []
        db_map_pair=self.db_map_registry.get_db_map_pair(node.db_map_key)
        # info_dict
        # id=0 'dt_map_created'=1 'dt_map_modified'=2 'mappath'=3 'tablename'=4 'mount'=5 'serial'=6
        # 'mapname'=7 'maptype'=8
        info_dict=self.cma.get_map_info_dict(db_map_pair[0],db_map_pair[1])
        if len(info_dict) == 0:
            log.error(f"Could not find database or map {db_map_pair}")
            return []
        fm=self.cma.get_file_map(db_map_pair[0])
       
        if node.node_type=="map":
            mainpath = info_dict['mappath']
            node_type="map"
        else:
            mainpath = node.path
                
        data_list=fm.db.get_data_from_table(db_map_pair[1],'*',f"filepath = '{mainpath}'")        
        # add Files
        # On table
            # id=0	dt_data_created'=1	'dt_data_modified'=2	'filepath'=3	'filename'=4	'md5'=5	'size'=6
            # 'dt_file_created'=7	'dt_file_accessed'=8	'dt_file_modified'=9
        # dbr.set_values(data_list)

        result=[]
        for row in data_list:
            result.append(
                {
                    "name":row[4],
                    "id_in_map":row[0],
                    "filename":row[4],
                    "filepath":row[3],
                    "size":row[6],
                    "info":row,
                    "node_type":"file",
                    "is_dir":False,
                    "parent":node.node_id,
                    "db_map_key":node.db_map_key,
                }
            )
        # add folders
        base = FM.remove_separator_in_path_end(mainpath)
        where = (
            f"(filepath LIKE '{base}\\%' "
            f"OR filepath LIKE '{base}/%') "
            f"AND filepath != '{base}'"
        )
        data_list=fm.db.get_data_from_table(db_map_pair[1],'*',where)
        # field list in map
        # id=0	dt_data_created'=1	'dt_data_modified'=2	'filepath'=3	'filename'=4	'md5'=5	'size'=6
        # 'dt_file_created'=7	'dt_file_accessed'=8	'dt_file_modified'=9
        field_list = fm.db.get_column_list_of_table(db_map_pair[1])
        
        try:
            d_m1 = DataManage(data_list, field_list)
        except ValueError:
            # No folders found
            return result
        df=d_m1.get_selected_df()
        FS=FileStructurer(df)
        df=FS.add_depth_to_df(df)
        min_depth = FS.get_min_depth(df)
        # For rows at min depth, extract path_n and truncate filepath
        df=FS.add_splitted_path_n_df(df,min_depth)
        folders=list(df["filepath"].unique())
        for folder in folders:
            df_dir = df[df["filepath"] == folder] #->has all children ids
            tot_size=sum(df_dir["size"])
            parpath = FM.remove_separator_in_path_end(folder)
            # after no separator extract_filename returns the path
            name=FM.extract_filename(parpath,with_extension=False)
            result.append(
                {
                    "name":name,
                    "id_in_map": None,
                    "filename":None,
                    "filepath":folder,
                    "size":tot_size,
                    "info":None,
                    "node_type":"folder",
                    "is_dir":True,
                    "parent":node.node_id,
                    "db_map_key":node.db_map_key,
                }
            )
        return result
    # ---------------------------------------------------------
    def _new_node_id(self):
        """
        Returns a new unique node identifier.

        Node ids remain stable during the lifetime of the model
        and allow fast lookup through node_id_map.
        """
        self.node_id += 1
        return self.node_id

    def node_from_node_id(self,node_id:int):
        """
        Returns the node associated with a node id.

        Args:
            node_id (int):
                Internal node identifier.

        Returns:
            DBTreeNode | None:
                Matching node or None if not found.
        """
        return self.node_id_map.get(node_id)

    def node_from_index(self,index):
        """
        Converts a QModelIndex into its corresponding DBTreeNode.

        Returns:
            DBTreeNode | None
        """
        if index.isValid():
            return index.internalPointer()
        return None

# =============================================================
# Widget wrapper
# =============================================================
class DBTreeView(QtWidgets.QTreeView):
    """
    Tree view for browsing one or more database/map pairs.

    The widget displays the contents of one or more mapped directories
    stored in SQLite databases. Children are loaded lazily when a node
    is expanded.

    Args:
        db_map_pairs (list[tuple]):
            List of (database_path, table_name) pairs to display.

        ba (BackupActions):
            BackupActions instance used by the model to access the
            CommonMapActions object and database contents.

        parent (QWidget | None, optional):
            Parent widget.
    """

    def __init__(
        self,
        db_map_pairs: list[tuple],
        ba: BackupActions,
        parent=None
    ):
        super().__init__(parent)

        self.ba = ba
        self.db_map_pairs = db_map_pairs

        self.model_obj = DBTreeModel(
            db_map_pairs=db_map_pairs,
            ba=ba,
            parent=self
        )

        self.setModel(self.model_obj)

        # Performance
        self.setUniformRowHeights(True)

        # Preserve database order
        self.setSortingEnabled(False)

        # Load folders only when expanded
        self.expanded.connect(self.on_expand)

        # Nice defaults
        self.setAlternatingRowColors(True)
        self.setAnimated(True)
        self.setExpandsOnDoubleClick(True)

        # Optional
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )
        self.header().setSectionResizeMode(
            0,
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )

    def on_expand(self, index):
        """
        Loads the children of a node when it is expanded.

        Qt requests the row count before expansion. The actual child
        nodes are created here only when required.
        """
        if self.model_obj.canFetchMore(index):
            self.model_obj.fetchMore(index)
    
    @property
    def tree_model(self) -> DBTreeModel:
        """Returns the underlying tree model."""
        return self.model_obj


# db = SQLiteDatabase("my_maps.db")

# tree = DBTreeView(
#     db,
#     "map_table"
# )

# tree.show()

