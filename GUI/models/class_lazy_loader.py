import os

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
            
            child.expand = False

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
        

