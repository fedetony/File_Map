import os
from controllers.class_filemap_cli_manager import FileMapCliManager,FileMapper,SQLiteDatabase,DataManage

from controllers.class_tree_node_manager import TreeNode,TreeManager
from PyQt6.QtGui import QIcon
from models.class_enums_definitions import SelectionByTypeMode, SelectionMode, CheckBoxMode


class LazyLoaderProvider:
    """
    Base class.
    Override in descendants.
    """
    defaults = []
    locked = []
    hidden = []
    blank = []
    tree_manager=None

    selectionbytypemode=SelectionByTypeMode.ANY
    selectionmode=SelectionMode.MULTI
    checkboxmode=CheckBoxMode.CHECKBOX
    
    def set_selectionbytypemode(self,selectionbytypemode:SelectionByTypeMode):
        self.selectionbytypemode=selectionbytypemode
    
    def set_selectionmode(self,selectionmode:SelectionMode):
        self.selectionmode=selectionmode
    
    def set_checkboxmode(self,checkboxmode:CheckBoxMode):
        self.checkboxmode=checkboxmode
    
    def set_defaults(self,default_list:list):
        self.defaults=default_list
    
    def set_hidden(self,hidden_list:list):
        self.hidden=hidden_list
    
    def set_blank(self,blank_list:list):
        self.blank=blank_list
    
    def set_locked(self,locked_list:list):
        self.locked=locked_list
    
    def set_tree_manager(self,tree_manager:TreeManager):
        self.tree_manager=tree_manager

    def lazy_loader(self,node:TreeNode):
        return

class DatabaseLazyLoader(LazyLoaderProvider):
    """
    Database explorer 
    Default 
    """
    def set_filemap(self,fmap):        
        if isinstance(fmap,FileMapCliManager):
            self.fmap = fmap
        else:
            self.fmap = None

    def lazy_loader(self, node: TreeNode):
        success, bl = self._load_children(node)
        if success is not True:
            return
        
        #set selectability of children
        for child in node.children:
            if not isinstance(child,TreeNode):
                continue
            if child.i_am == "dir":
                self._dir_selection(child)
            elif child.i_am == "file":
                self._file_selection(child)
            
            if child.expand is None: 
                child.expand = False

            if child.id in self.locked:
                child.locked = True
            else:
                child.locked = False

            # Set defaults
            if child.id in self.defaults:
                child.default = True    
            else:
                child.default = None # No defaults for lazy db explorer
            
            # Set if item is selected
            if child.default and child.selectable:
                child.selected = True
            else:
                child.selected = False

            child.level=len(bl)
        
        # Set selectability
        node.selectable = self._node_selectable(node)
        # mark loaded
        node.loaded = True
    
    def _get_fm(self,node:TreeNode)->FileMapper:
        fm=None
        if node.i_am == "root":
            return fm
        elif node.i_am == "database":
            database = node.info
            fm=self.fmap.cma.get_file_map(database)
        elif node.i_am == "map":
            db_map_pair = node.info
            fm=self.fmap.cma.get_file_map(db_map_pair[0])
        else:
            bl=node.get_bloodline()
            if bl and len(bl)>2: #root->db->map
                db_map_pair = bl[2].info
                fm=self.fmap.cma.get_file_map(db_map_pair[0])                
        return fm
    
    def _get_db_map_pair(self,node:TreeNode)->tuple[str]:
        db_map_pair=None
        if node.i_am == "root":
            return db_map_pair
        elif node.i_am == "database":
            database = node.info
            db_map_pair = None
        elif node.i_am == "map":
            return node.info
        else:
            bl=node.get_bloodline()
            if bl and len(bl)>2: #root->db->map
                return bl[2].info
        return db_map_pair

    def _set_files_children_in_path(self, path, db_map_pair, fm: FileMapper,node: TreeNode):
        ext_path = path
        # remove end separator
        if path[-1] in ["/", "\\", os.sep]:
            ext_path = path[:-1]

        mount = self.fmap.get_mount_of_map(db_map_pair[0], db_map_pair[1])
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
        
        data = fm.db.get_data_from_table(a_map, "*")

        where = ("(replace(filepath, '\\', '/') = " + fm.db.quotes(ext_path)+")")
        data_files = fm.db.get_data_from_table(a_map, "*", where)
        
        if not data_files:
            return
        # field_list=fm.db.get_column_list_of_table(db_map_pair[1])
        # dm=DataManage(data_files,field_list)
        # df=dm.get_selected_df(fields_to_tab=None,sort_by=None,ascending=True)
        # for db_id,filename,size,filepath,info in zip(df['id'],df['filename'],df['size'],df['filepath'],data_files):

        # # field list in map
        # # id=0	dt_data_created'=1	'dt_data_modified'=2	'filepath'=3	'filename'=4	'md5'=5	'size'=6	
        # # 'dt_file_created'=7	'dt_file_accessed'=8	'dt_file_modified'=9
        
        fields = fm.db.get_column_list_of_table(a_map)
        
        for info in data_files:
            info_dict=fm.data_to_field_dict(fields,info)
            if not info_dict:
                continue
            db_id = info_dict["id"]
            filepath = info_dict["filepath"]
            filename = info_dict["filename"]
            size = info_dict["size"]

            ch_full_path=os.path.join(mount,filepath)
            ch_filepath=os.path.join(ch_full_path,filename)
            # set child
            ch_node=TreeNode(filename) #sets name
            ch_node.i_am ="file"
            ch_node.size = size
            ch_node.path=ch_full_path
            ch_node.i_exist=os.path.exists(ch_filepath)
            ch_node.db_id=db_id
            ch_node.db=node.db
            ch_node.map=node.map
            ch_node.info=info
            ch_node.loaded=True
            #----------------
            node.add_child(ch_node)

    def _set_dir_children_in_path(self, path, db_map_pair, fm: FileMapper,node: TreeNode):
        ext_path = self.fmap.fm.fix_separator_in_path(path,add_sep_start=True) 
        mount = self.fmap.get_mount_of_map(db_map_pair[0], db_map_pair[1])
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


        data = fm.db.get_data_from_table(a_map, "*")

        data_dirs = fm.db.get_data_from_table(a_map,f"DISTINCT {dirname_expr}", where_dirs)
        if not data_dirs:
            return
        for path_part_tup in data_dirs:
            dirname=path_part_tup[0]
            if not dirname:
                continue
            db_id = None
            filepath = os.path.join(ext_path,dirname)
            size = 0

            ch_full_path=os.path.join(mount,filepath)
            
            # set child
            ch_node=TreeNode(dirname) #sets name
            ch_node.i_am ="dir"
            ch_node.size = size
            ch_node.path=ch_full_path
            ch_node.i_exist=os.path.exists(ch_full_path)
            ch_node.db_id=db_id
            ch_node.db=node.db
            ch_node.map=node.map
            ch_node.info=None
            ch_node.loaded=False
            #-------------------------
            node.add_child(ch_node)


    def _load_children(self, node: TreeNode):
        try:
            bl = node.get_bloodline()
            db_map_pair = self._get_db_map_pair(node)
            if not db_map_pair:
                return None, None
            fm = self._get_fm(node)
            if not fm:
                return None, None
            # Already loaded
            if node.loaded:
                return True, bl

            if not node.path and node.i_am not in ("database", "root"):
                # set a path if lacking one
                path = os.path.join(*[n.name for n in bl[1:]])
                if os.path.exists(path):
                    node.i_exist = True
                node.path = path

            # Directories first, then files ;)
            self._set_dir_children_in_path(
                node.path, db_map_pair, fm, node)

            self._set_files_children_in_path(
                node.path, db_map_pair, fm, node)

            return True, bl
        except Exception:
            return None, None


    def _node_selectable(self,node:TreeNode):
        if self.checkboxmode == CheckBoxMode.NO_CHECKBOX:
            return False
        
        if self.selectionbytypemode == SelectionByTypeMode.ANY:
            return True
        
        if node.i_am == "file":
            if self.selectionbytypemode in (
                    SelectionByTypeMode.DIRS_ONLY,
                    ) :
                return False
            else:
                return True
        if node.i_am in ("dir","folder"):
            if self.selectionbytypemode in (
                    SelectionByTypeMode.FILES_ONLY,
                    ) :
                return False
            else:
                return True
            
        if node.i_am not in ("dir","folder","file"):
            if self.selectionbytypemode in (
                    SelectionByTypeMode.FILES_DIRS_ONLY,
                    ) :
                return False
            else:
                return True
        
        # if node.i_am =="map":
        #     if self.selectionbytypemode ==  SelectionByTypeMode.MAP:
        #         return True
        
        # if node.i_am =="root":
        #     if self.selectionbytypemode ==  SelectionByTypeMode.ROOT:
        #         return True
            
        return True

    def _dir_selection(self,child:TreeNode):
        child.i_am = "dir"
        child.selectable = self._node_selectable(child)
        # Hidden or blank
        # True -> will appear disabled, None -> will appear the space blank,
        if child.id in self.hidden:
            child.hidden = True
        elif child.id in self.blank:
            child.hidden = True # Don't blank folders
        else:
            child.hidden = False
    
    def _file_selection(self,child:TreeNode):
        child.i_am = "file"
        child.selectable = self._node_selectable(child)
        # Hidden or blank
        # True -> will appear disabled, None -> will appear the space blank,
        if child.id in self.hidden:
            child.hidden = True
        elif child.id in self.blank:
            child.hidden = None
        else:
            child.hidden = False
    
    #-----------------------------------------------------------------
    # # filestructure functions
    #-----------------------------------------------------------------
    # use with 
    # # self.fmap.fm.path_to_file_structure_dict() # for file_structure
    # # self.fmap.fm.merge_file_structure_lists
    # or filestructurer
    
    # def _get_structure_node(self, structure, path):
    #     path_list = self.fmap.fm.path_to_list(path)
    #     current = structure
    #     for part in path_list:
    #         if isinstance(current, dict):
    #             if part not in current:
    #                 return None
    #             current = current[part]
    #         elif isinstance(current, list):
    #             found = False
    #             for item in current:
    #                 if isinstance(item, dict) and part in item:
    #                     current = item[part]
    #                     found = True
    #                     break
    #             if not found:
    #                 return None
    #         else:
    #             return None
    #     return current
    
    # def _get_structure_children(self, contents):
    #     entries = []
    #     if not isinstance(contents, list):
    #         return entries
    #     for item in contents:
    #         if isinstance(item, (str|tuple)):
    #             # File
    #             entries.append((item, "file"))

    #         elif isinstance(item, dict):
    #             # Directory
    #             for name in item:
    #                 entries.append((name, "dir"))

    #     return entries
        

class ActiveFELazyLoader(LazyLoaderProvider):
    """
    File explorer 
    Default 
    """

    def lazy_loader(self,node:TreeNode):
        entries, bl =self._load_entries(node)
        if not isinstance(entries, list):
            return
        
        #Add children
        for entry in entries:
            full = os.path.join(node.path, entry)
            child = TreeNode(entry)
            child.path = full
            if os.path.isdir(full):
                self._dir_selection(child)
            else:
                self._file_selection(child)
            
            #child.expand = False

            if child.id in self.locked:
                child.locked = True
            else:
                child.locked = False
            
            child.info = None

            if child.i_am == "file":
                try:
                    child.size = os.path.getsize(full)
                except:
                    child.size = -1
            else:
                child.size = 0

            # Set defaults
            if child.id in self.defaults:
                child.default = True    
            else:
                child.default = None # No defaults for default explorer
            
            # Set if item is selected
            if child.default and child.selectable:
                child.selected = True
            else:
                child.selected = False

            child.level=len(bl)
            child.loaded=False
            # add child node
            node.add_child(child)
        
        # Set selectability
        node.selectable = self._node_selectable(node)
        # mark loaded
        node.loaded = True
    
    def _load_entries(self,node:TreeNode):
        try:
            bl=node.get_bloodline()
            if not node.path:
                path = os.path.join(*[n.name for n in bl[1:]])
                if os.path.exists(path):
                    node.path=path
                else:
                    return None, None
            entries = os.listdir(node.path)
            return entries, bl
        except Exception:
            pass
        return None, None

    def _node_selectable(self,node:TreeNode):
        if self.checkboxmode == CheckBoxMode.NO_CHECKBOX:
            return False
        
        if self.selectionbytypemode == SelectionByTypeMode.ANY:
            return True
        
        if node.i_am == "file":
            if self.selectionbytypemode in (
                    SelectionByTypeMode.DIRS_ONLY,
                    ) :
                return False
            else:
                return True
        if node.i_am in ("dir","folder"):
            if self.selectionbytypemode in (
                    SelectionByTypeMode.FILES_ONLY,
                    ) :
                return False
            else:
                return True
            
        if node.i_am not in ("dir","folder","file"):
            if self.selectionbytypemode in (
                    SelectionByTypeMode.FILES_DIRS_ONLY,
                    ) :
                return False
            else:
                return True
        
        # if node.i_am =="map":
        #     if self.selectionbytypemode ==  SelectionByTypeMode.MAP:
        #         return True
        
        # if node.i_am =="root":
        #     if self.selectionbytypemode ==  SelectionByTypeMode.ROOT:
        #         return True
            
        return True

    def _dir_selection(self,child:TreeNode):
        child.i_am = "dir"
        child.selectable = self._node_selectable(child)
        # Hidden or blank
        # True -> will appear disabled, None -> will appear the space blank,
        if child.id in self.hidden:
            child.hidden = True
        elif child.id in self.blank:
            child.hidden = True # Don't blank folders
        else:
            child.hidden = False
    
    def _file_selection(self,child:TreeNode):
        child.i_am = "file"
        child.selectable = self._node_selectable(child)
        # Hidden or blank
        # True -> will appear disabled, None -> will appear the space blank,
        if child.id in self.hidden:
            child.hidden = True
        elif child.id in self.blank:
            child.hidden = None
        else:
            child.hidden = False
        

