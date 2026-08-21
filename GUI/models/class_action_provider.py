# class_action_provider.py

from dataclasses import dataclass, field
from typing import Callable, Any
from controllers.class_tree_node_manager import TreeNode,TreeManager
from PyQt6.QtGui import QIcon

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
            ExplorerAction(
                text=None,
                shortcut="Tab",
                callback=widget.autocomplete
            )
        ]
        return global_actions

