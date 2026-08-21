# class_explorer_config.py
from dataclasses import dataclass

from typing import Callable, Any
from models.class_style_provider import (
    DefaultExplorerStyle,
    DefaultTreeStyle,
)

from models.class_enums_definitions import SelectionByTypeMode, SelectionMode, CheckBoxMode
from models.class_action_provider import (DefaultFileActionProvider)
from models.class_lazy_loader import LazyLoaderProvider

@dataclass
class ExplorerConfig:
    # tree behavior
    lazy_loading: bool = True
    lazy_loader: Callable| LazyLoaderProvider | None = None
    # ui
    show_path_edit: bool = True
    show_context_menu: bool = True
    show_label: bool = True
    # selection
    selection_by_type_mode: SelectionByTypeMode = (SelectionByTypeMode.ANY)
    checkbox_mode: CheckBoxMode = (CheckBoxMode.CHECKBOX)
    selection_mode: SelectionMode = (SelectionMode.MULTI)
    # providers
    provider = None
    # styles
    explorer_style = DefaultExplorerStyle()
    tree_style = DefaultTreeStyle()
    # actions
    action_provider = DefaultFileActionProvider()
    # root node
    root_node = None
