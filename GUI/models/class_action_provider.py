# class_action_provider.py

from dataclasses import dataclass, field
from typing import Callable, Any
from controllers.class_tree_node_manager import TreeNode,TreeManager
from PyQt6.QtGui import QIcon
from functional.class_icons import Icons
import os
from class_file_manipulate import FileManipulate
FM = FileManipulate()
from widgets.class_file_dialogs import *

@dataclass
class ExplorerAction:
    text: str
    callback: Callable[..., Any] | None = None
    shortcut: str | None = None
    icon: QIcon | None = None
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    enabled: bool | Callable = True
    visible: bool | Callable = True
    separator_before: bool = False
    tip: str | None = None
    checkable: bool = False
    checked: bool | Callable = False

class TreeActionProvider:
    """
    Base class.
    Override in descendants.
    """
    parent_widget=None
    def set_parent_widget(self,parent_widget):
        self.parent_widget=parent_widget

    def get_actions(self, node: TreeNode, tree_manager: TreeManager) -> list[ExplorerAction]:
        return []

    def get_global_actions(self,widget) -> list: 
        return []
    
    def execute_action( self, node, action: ExplorerAction):
          if action.callback:
            action.callback(
                *action.args,
                **action.kwargs
            )

class DefaultFileActionProvider(TreeActionProvider):

    def get_actions(self, node: TreeNode, tree_manager: TreeManager) -> list[ExplorerAction]:
        actions = []
        actions.extend([
            ExplorerAction(
                text=f"Select {node.name}",
                callback=tree_manager.set_selected,
                args=(node, True)
            ),

            ExplorerAction(
                text = f"Deselect {node.name}",
                callback = tree_manager.set_selected,
                args = (node, False)
            ),

            ExplorerAction(
                text = f"Select all in {node.parent.name}",
                callback = tree_manager.select_siblings,
                args = (node, True),
                separator_before=True
            ),

            ExplorerAction(
                text = f"Deselect all in {node.parent.name}",
                callback = tree_manager.select_siblings,
                args = (node, False),
                #visible=lambda node: node.i_am == "file", # Callable example
            ),

            ])
        
        return actions
    
    def get_global_actions(self,widget):
        global_actions= [
            ExplorerAction(
                text=None,
                shortcut="Space",
                callback=widget.toggle_current_nodes
            ),
            # ExplorerAction(
            #     text=None,
            #     shortcut="Tab",
            #     callback=widget.autocomplete
            # )
        ]
        return global_actions

class SearchFileActionProvider(TreeActionProvider):
    icons=Icons()
    max_depth_count = 100

    def _reveal_in_explorer(self,node: TreeNode):
        full_path = node.path
        (file_exist, is_file)=FM.validate_path_file(full_path)
        reveal=False
        # if file_exist and is_file:
        #     full_path=FM.extract_path(full_path)
        #     reveal=True
        # elif file_exist and not is_file:
        #     reveal=True
        if file_exist:
            reveal=True
        if reveal:
            a_diag = Dialogs()
            a_diag.explore(full_path,select=True)
    
    def _copy_path(self,node: TreeNode):
        """Copy the current node's path to the clipboard."""
        full_path = node.path
        if node.i_am == "file":
            full_path = os.path.join(full_path,node.name)
        elif node.i_am == "database":
            full_path = str(node.info)
        elif node.i_am == "map":
            full_path = str(node.info)
        QtWidgets.QApplication.clipboard().setText(full_path)
    
    def _expand_tree(self,node: TreeNode, count = 0 ):
        "Expand all nodes under the node"
        if count > self.max_depth_count:
            return count
        if self.parent_widget:
            if hasattr(self.parent_widget,"expand_node"):
                if node.i_am == "dir":
                    if not node.loaded:
                        count += 1
                    self.parent_widget.expand_node(node)
                    for child in node.children:
                        count = self._expand_tree(child,count)
        return count
    
    def _collapse_tree(self,node: TreeNode):
        "Expand all nodes under the node"
        if self.parent_widget:
            if hasattr(self.parent_widget,"collapse_node"):
                self.parent_widget.collapse_node(node)
                for child in node.children:
                    self._collapse_tree(child)
    
    def _select_tree(self,node: TreeNode, tree_manager: TreeManager, selected=True, count=0):
        "Expand all nodes under the node"
        if self.parent_widget:
            if hasattr(self.parent_widget,"expand_node"):
                if node.i_am == "dir":
                    if count>self.max_depth_count:
                        return count
                    if not node.loaded:
                        count += 1
                    self.parent_widget.expand_node(node)
                    
                    for child in node.children:
                        count = self._select_tree(child,
                                                  tree_manager,
                                                  selected=selected,
                                                  count=count)
                elif node.i_am == "file":
                    tree_manager.set_selected(node,selected)     
        return count       

    def get_actions(self, node: TreeNode, tree_manager: TreeManager) -> list[ExplorerAction]:
        actions = []
        files_dirs_visible = (node.i_am in ("file","dir"))
        actions.extend([
            ExplorerAction(
                text=f"Reveal in explorer {node.name}",
                callback=self._reveal_in_explorer,
                args=(node,),
                icon=self.icons.icon('reveal'),
                visible=lambda node:(node.i_am in ("file","dir") and node.i_exist),
            ),

            ExplorerAction(
                text = f"Copy {node.name} path to Clipboard",
                callback=self._copy_path,
                args=(node,),
                icon=self.icons.icon('clipboard'),
            ),

            ExplorerAction(
                text = f"Expand all in {node.name}|first {self.max_depth_count}(⏳ may take time ⌛)",
                callback = self._expand_tree,
                args = (node,0),
                icon=self.icons.icon('expand'),
                tip="⏳ Warning: This may take a long time depending on the number of items in the tree ⌛" ,
                visible=lambda node:(node.i_am in ("dir","map","database")),
                separator_before=True,
            ),

            ExplorerAction(
                text = f"Collapse all in {node.name}",
                callback = self._collapse_tree,
                icon=self.icons.icon('collapse'),
                visible=lambda node:(node.i_am in ("dir","map","database")),
                args = (node,),
                
            ),
            ExplorerAction(
                text = f"Select all in {node.name}",
                callback = self._select_tree,
                args = (node, tree_manager, True, 0),
                icon=self.icons.icon('select'),
                visible=lambda node:(node.i_am in ("dir","map","database")),
                separator_before=True,
            ),

            ExplorerAction(
                text = f"Deselect all in {node.name}",
                callback = self._select_tree,
                icon=self.icons.icon('unselect'),
                args = (node, tree_manager, False, 0),
                visible=lambda node:(node.i_am in ("dir","map","database")),
            ),

            # ExplorerAction(
            #     text = f"Deselect all in {node.parent.name}",
            #     callback = tree_manager.toggle_subtree,
            #     icon=self.icons.icon('toggle'),
            #     args = (node, False),
            #     visible=lambda node: (node.i_am in ("file","dir")), # Callable example
            # ),

            ])
        
        return actions
    
    def get_global_actions(self,widget):
        global_actions= [
            ExplorerAction(
                text=None,
                shortcut="Space",
                callback=widget.toggle_current_nodes
            ),
            # Do NOT install Tab as a global shortcut here.
            # Tab is context-sensitive and is handled by the widget
            # that currently owns keyboard focus (e.g. editor/search).
            # A global Tab shortcut causes those widgets to fight over Tab.
            #
            # ExplorerAction(
            #     text=None,
            #     shortcut="Tab",
            #     callback=widget.autocomplete
            # )
        ]
        return global_actions

