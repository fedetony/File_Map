# class_tree_node.py

class TreeNode:
    """
    Generic tree node.

    Compatible with the existing TreeViewer architecture.
    Qt-independent.
    """
    _next_id = 0
    def __init__(self, name):
        # identification
        self.id = TreeNode._next_id
        TreeNode._next_id += 1
        
        self.name = name
        # hierarchy
        self.parent = None
        self.children = []
        # type
        self.i_am = ""          # "file" / "dir"
        # metadata
        self.info = None
        self.size = None
        self.default = None
        # selection
        self.selected = False
        self.selected_children = False
        self.selectable = True
        self.selected_count = 0
        # future filtering support
        self.hidden = False
        self.locked = False
        # lazy loading
        self.loaded = False
        # visual state
        self.expand = None
        # depth in tree
        self.level = 0
        # optional full path cache
        self.path = None
        # database mapping
        self.db = None
        self.map = None
        self.db_id = None
        self.i_exist = None
        # file mapping
        self.mount = None
        self.serial = None
        self.itempath = None
        self.quantity = 0
        self.num_files = None
        self.num_dirs = None

    # ---------------------------------------------------
    # hierarchy helpers
    # ---------------------------------------------------

    def add_child(self, child):
        child.parent = self
        child.level = self.level + 1
        self.children.append(child)

    def remove_child(self, child):
        if child in self.children:
            self.children.remove(child)
            child.parent = None

    def child(self, row):
        try:
            return self.children[row]
        except IndexError:
            return None

    def child_count(self):
        return len(self.children)

    def row(self):
        if self.parent is None:
            return 0

        try:
            return self.parent.children.index(self)
        except ValueError:
            return 0

    # ---------------------------------------------------
    # path helpers
    # ---------------------------------------------------

    def get_bloodline(self) -> list:
        """
        Returns root -> self nodes.
        """

        nodes = []

        node = self

        while node is not None:
            nodes.append(node)
            node = node.parent

        nodes.reverse()

        return nodes

    # ---------------------------------------------------
    # serialization
    # ---------------------------------------------------

    def to_dict(self):

        return {
            "id": self.id,
            "name": self.name,
            "type": self.i_am,
            "selected": self.selected,
            "selected_children": self.selected_children,
            "children": [
                child.to_dict()
                for child in self.children
            ]
        }

    # ---------------------------------------------------

    def __repr__(self):

        return (
            f"TreeNode("
            f"id={self.id}, "
            f"name='{self.name}', "
            f"type='{self.i_am}')"
        )

class TreeManager:

    def __init__(self,root:TreeNode):

        self.root = root
        self.nodes_by_id = {}
        self.all_nodes = []
        self.register_subtree(root)
    
    def check_node(self,node:TreeNode)->bool:
            return isinstance(node,TreeNode)

    def get_full_path(self,node:TreeNode, sep="/"):
        if not self.check_node(node): return
        bloodline = node.get_bloodline()
        return sep.join(
            anode.name
            for anode in bloodline
            if anode.parent is not None
        )

    # ---------------------------------------------------
    # selection helpers
    # ---------------------------------------------------

    def set_selected(self, node:TreeNode, value):
        if not self.check_node(node): return
        if node.locked or not node.selectable:
            return
        old = node.selected
        node.selected = value
        if old == value:
            return
        if value:
            self.propagate_selected_up(node)
        else:
            self.propagate_unselected_up(node)

    def select_descendants(self, node:TreeNode, state: bool):
        if not self.check_node(node): return
        node.selected = state
        for child in node.children:
            self.select_descendants(child, state)
    
    def has_selected_descendants(self,node:TreeNode):
        if not self.check_node(node): return
        for child in node.children:
            if child.selected:
                return True
            if child.selected_children:
                return True
        return False
    
    def propagate_selected_up(self,node:TreeNode):
        if not self.check_node(node): return
        parent = node.parent
        while parent:
            parent.selected_count += 1
            parent.selected_children = True

            parent = parent.parent
    
    def propagate_unselected_up(self,node:TreeNode):
        if not self.check_node(node): return
        parent = node.parent
        while parent:
            parent.selected_count -= 1
            parent.selected_children = (parent.selected_count > 0)
            parent = parent.parent

    def update_selected_children(self,node:TreeNode)->bool:
        """
        Recalculate subtree selection state.

        Call from leaves upward.
        """
        if not self.check_node(node): return False
        has_selected = False
        for child in node.children:
            self.update_selected_children(child)
            if child.selected:
                has_selected = True
            if child.selected_children:
                has_selected = True

        node.selected_children = has_selected
        return has_selected
    
    def clear_selected_children(self,node:TreeNode):
        if not self.check_node(node): return
        node.selected_children = False
        for child in node.children:
            self.clear_selected_children(child)

    def mark_bloodline(self,node:TreeNode):
        if not self.check_node(node): return
        anode = node.parent
        while anode:
            anode.selected_children = True
            anode = anode.parent

    # ---------------------------------------------------
    # traversal
    # ---------------------------------------------------

    # def walk(self):
    #     yield self
    #     for child in self.children:
    #         yield from child.walk()

    # def find_by_id(self, node_id):

    #     for node in self.walk():

    #         if node.id == node_id:
    #             return node

    #     return None
    
    def register_node(self, node:TreeNode):
        if not self.check_node(node): return
        self.nodes_by_id[node.id] = node
        if node not in self.all_nodes:
            self.all_nodes.append(node)

    def register_subtree(self, node:TreeNode):
        if not self.check_node(node): return
        self.register_node(node)
        for child in node.children:
            self.register_subtree(child)
    
    def expand_subtree(self, node:TreeNode):
        if not self.check_node(node): return
        if node.i_am == "dir":
            node.expand = True
        for child in node.children:
            self.expand_subtree(child)
    
    def collapse_subtree(self, node:TreeNode):
        if not self.check_node(node): return
        if node.i_am == "dir":
            node.expand = False
        for child in node.children:
            self.collapse_subtree(child)
    
    def toggle_subtree(self, node:TreeNode):
        if not self.check_node(node): return
        self.toggle_selection(node)
        for child in node.children:
            self.toggle_subtree(child)
    
    def remove_node_by_id(self, node_id: int):
        node = self.get_node_by_id(node_id)
        if node is None:
            return False
        return self.remove_node(node)

    def remove_node(self, node: TreeNode):
        if not self.check_node(node): return False
        # remove subtree first
        for child in list(node.children):
            self.remove_node(child)

        # detach from parent
        if node.parent:
            try:
                node.parent.children.remove(node)
            except ValueError:
                pass
        self.nodes_by_id.pop(node.id, None)

        if node in self.all_nodes:
            self.all_nodes.remove(node)
        return True
    
    def add_child(self, parent:TreeNode, child:TreeNode):
        if not self.check_node(parent): return
        if not self.check_node(child): return
        child.parent = parent
        child.level = parent.level + 1

        parent.children.append(child)

        self.register_node(child)
    
    def get_node_by_id(self, node_id:int) -> TreeNode | None:
        return self.nodes_by_id.get(node_id)
    
    def get_nodes_by_attribute(self, attribute:str, value)-> list[TreeNode] :
        result = []
        for node in self.nodes_by_id.values():
            if hasattr(node, attribute):
                if getattr(node, attribute) == value:
                    result.append(node)
        return result
    
    def set_node_attribute(self, node_id:int, attribute:str, value):
        node = self.get_node_by_id(node_id)
        if node is None:
            return False

        if not hasattr(node,attribute):
            return False
        setattr(node, attribute, value)

        return True
    
    def set_selected_by_id(self, node_id:int, selected:bool):
        node = self.get_node_by_id(node_id)
        self.set_selected( node, selected)
    
    def get_selected_nodes(self):
        return self.get_nodes_by_attribute("selected",True)
    
    def get_expanded_nodes(self):
        return self.get_nodes_by_attribute("expanded",True)
    
    def get_locked_nodes(self):
        return self.get_nodes_by_attribute("locked",True)
    
    def get_selected_ids(self):
        return [node.id for node in self.get_selected_nodes()]
    
    def get_expanded_ids(self):
        return [node.id for node in self.get_expanded_nodes()]
    
    def get_locked_ids(self):
        return [node.id for node in self.get_locked_nodes()]
    
    def get_node_path_by_id(self, node_id:int,sep: str = "/"):
        node = self.get_node_by_id(node_id)
        if node is None:
            return ""
        return self.get_full_path(node,sep)
    
    def select_subtree(self, node: TreeNode, selected: bool):
        if not self.check_node(node): return
        self.select_descendants(node, selected)
        if selected:
            self.mark_bloodline(node)
        else:
            self.propagate_unselected_up(node)
    
    def select_siblings(self, node: TreeNode, state: bool):
        if not self.check_node(node): return
        if node.parent is None:
            return
        for child in node.parent.children:
                self.set_selected(child,state)
    
    def select_bloodline(self, node: TreeNode, state: bool):
        if not self.check_node(node): return
        bl=node.get_bloodline()
        for anode in bl[1:]:
            if anode.selectable and not anode.locked:
                self.set_selected(anode,state)
    
    def toggle_selection(self,node: TreeNode):
        if not self.check_node(node): return
        selected=node.selected
        self.set_selected(node,not selected)
    
    def lock_node(self, node: TreeNode):
        if not self.check_node(node): return
        node.locked = True

    def unlock_node(self, node: TreeNode):
        if not self.check_node(node): return
        node.locked = False
    
    def find_node_from_path(
        self,
        path_list: list[str], 
        start_node: TreeNode | None = None
        ) -> TreeNode | None:
        if start_node is None:
            start_node = self.root
        current = start_node
        for part in path_list:
            found = None
            for child in current.children:
                if child.name == part:
                    found = child
                    break
            if found is None:
                return current
            current = found
        return current
    
    def find_child_name_by_id(self, node_id: int, child_name: str)->int:
        """"""
        parent = self.get_node_by_id(node_id)
        if parent is None:
            return None

        for child in parent.children:

            if child.name == child_name:
                return child.id
        return None
    
    def find_child_name(self, node: TreeNode, child_name: str)->TreeNode:
        if not self.check_node(node): return None
        for child in node.children:
            if child.name == child_name:
                return child
        return None
    
    