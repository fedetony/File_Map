# class_style_provider.py
from enum import Enum, auto
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QIcon
from controllers.class_tree_node_manager import TreeNode
from class_file_manipulate import FileManipulate
FM=FileManipulate()

class NodeVisualState(Enum):
    NORMAL = auto()
    SELECTED = auto()
    BLOODLINE = auto()
    LOCKED = auto()
    HIDDEN = auto()

class TreeStyle:
    # Base to be overwritten
    def text(self, node:TreeNode):
        return node.name

    def tooltip(self, node):
        return None

    def foreground(self, node):
        return None

    def background(self, node):
        return None

    def font(self, node):
        return None

    def icon(self, node):
        return None

class TreeStyleProvider:
    # Base to be overwritten
    def get_style(self, node:TreeNode, role):
        return None
    
    def get_node_state(self,node:TreeNode):

        if node.locked:
            return NodeVisualState.LOCKED

        if node.selected:
            return NodeVisualState.SELECTED

        if node.selected_children:
            return NodeVisualState.BLOODLINE

        return NodeVisualState.NORMAL
#####################################
# Default Styles
#####################################
class DefaultExplorerStyle(TreeStyle):

    def text(self, node:TreeNode):

        prefix = ""

        if node.locked:
            prefix += "🔒▶"

        if node.i_am == "dir":
            return f"{prefix}📁 {node.name}"

        return f"{prefix}{node.name}"

    def tooltip(self, node)->str:
        txt = [
            f"Name : {node.name}",
            f"ID   : {node.id}",
            f"Type : {node.i_am}"
        ]

        if node.path:
            txt.append(f"Path : {node.path}")

        if node.i_am == "file" and isinstance(node.size,(int | float)):
            node_size_txt=FM.get_size_str_formatted(node.size,33,True)
            node_size_txt=node_size_txt.replace(".00 By"," By").strip()
            txt.append(f"Size : {node_size_txt}")

        return "\n".join(txt)

    def icon(self, node)-> QIcon | None:
        return None    

class DefaultTreeStyle(TreeStyleProvider):
    """
    DisplayRole         -> str
    ToolTipRole         -> str
    StatusTipRole       -> str
    WhatsThisRole       -> str

    DecorationRole      -> QIcon | QPixmap

    ForegroundRole      -> QColor | QBrush
    BackgroundRole      -> QColor | QBrush

    FontRole            -> QFont

    TextAlignmentRole   -> Qt.AlignmentFlag

    CheckStateRole      -> Qt.CheckState

    SizeHintRole        -> QSize

    UserRole+N          -> anything
    """
    def get_style(self, node:TreeNode, role:Qt.ItemDataRole):
        state= self.get_node_state(node)

        if role == Qt.ItemDataRole.ForegroundRole: #-> QColor / QBrush
            if state in (NodeVisualState.SELECTED, NodeVisualState.BLOODLINE):
                if state == NodeVisualState.SELECTED:
                    return QColor(0,180,0)

                if state == NodeVisualState.BLOODLINE:
                    return QColor(50,120,255)
            else:
                if state == NodeVisualState.LOCKED:
                    return QColor("gray")

        if role == Qt.ItemDataRole.FontRole: 
            font = QFont()

            if state in (
                NodeVisualState.SELECTED,
                NodeVisualState.BLOODLINE
            ):
                font.setBold(True)

            if state == NodeVisualState.LOCKED:
                font.setItalic(True)

            return font
        
        if role == Qt.ItemDataRole.UserRole:
            return node.id
        if role == Qt.ItemDataRole.UserRole + 1:
            return node.path

        return None
#######################################
# Example Theme
#####################################
class MyDarkTheme(TreeStyleProvider):
    # Example
    def get_style(self,node,state,role):

        if role == Qt.ItemDataRole.ForegroundRole:

            if state == NodeVisualState.SELECTED:
                return QColor("#7FFF00")

            if state == NodeVisualState.BLOODLINE:
                return QColor("#FFAA00")
    # In settings you can add
    # model.style_provider = MyDarkTheme()
    # model.layoutChanged.emit()

class OrangeTheme(TreeStyleProvider):

    def get_style(self, node, role):
        state = self.get_node_state(node)
        if role == Qt.ItemDataRole.ForegroundRole:
            if state == NodeVisualState.SELECTED:
                return QColor("lime")

            if state == NodeVisualState.BLOODLINE:
                return QColor("orange")

        if role == Qt.ItemDataRole.FontRole:
            font = QFont()
            if state != NodeVisualState.NORMAL:
                font.setBold(True)

            return font