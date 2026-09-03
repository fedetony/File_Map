# class_style_provider.py
from enum import Enum, auto
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QIcon
from controllers.class_tree_node_manager import TreeNode
from class_file_manipulate import FileManipulate
FM=FileManipulate()

TEXT_ICONS = {
    "database": "🗄️",
    "map":      "🗺️",
    "dir":      "📁",
    "file":     "📄",
}
class NodeVisualState(Enum):
    NORMAL = auto()
    SELECTED = auto()
    BLOODLINE = auto()
    LOCKED = auto()
    HIDDEN = auto()
    EXIST = auto()

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
        
        if node.i_exist:
            return NodeVisualState.EXIST

        return NodeVisualState.NORMAL

class ExportTreeStyle:

    def text(self, node: TreeNode) -> str:
        return node.name

    def branch(self, node: TreeNode, is_last: bool) -> str:
        return "└── " if is_last else "├── "

    def indent(self, node: TreeNode, is_last: bool) -> str:
        return "    " if is_last else "│   "
    
    def indent_prefix(self, node: TreeNode, is_last: bool) -> str:
        return ""
    
    def indent_postfix(self, node: TreeNode, is_last: bool) -> str:
        return ""

#####################################
# Default Styles
#####################################
class DefaultExportStyle(ExportTreeStyle):
    def text(self, node: TreeNode) -> str:
        txt=""
        if node.i_am in ("file","dir") and isinstance(node.size,(int | float)):
            node_size_txt=FM.get_size_str_formatted(node.size,33,True)
            node_size_txt=node_size_txt.replace(".00 By"," Bytes").strip()
            txt += f"{node_size_txt} ─ "
        txt += node.name
        if node.i_am == "dir" and len(node.children)==0:
            txt += '─¤'  # ‡ • † × · ¤ ▶
        return txt

    def branch(self, node, is_last):
        if node.i_am == "root":
            return "• " 
        if node.i_am == "database":
            return "‡── " 
        if node.i_am == "map":
            return "▶── " 
        if node.i_am == "dir":
            return "└── " if is_last else "├── "
        return "└─ " if is_last else "├─ "

    def indent(self, node: TreeNode, is_last: bool) -> str:
        if node.i_am == "root":
            return "  "
        return "    " if is_last else "│   "
    
    def indent_prefix(self, node: TreeNode, is_last: bool) -> str:
        if node.i_am == "root":
            return ""
        return "↓"
    
    def indent_postfix(self, node: TreeNode, is_last: bool) -> str:
        return ""

class DefaultExplorerStyle(TreeStyle):

    def text(self, node:TreeNode):

        prefix = ""

        if node.locked:
            prefix += "🔒•"

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
            node_size_txt=node_size_txt.replace(".00 By"," Bytes").strip()
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

class DBSelectionTreeStyle(TreeStyleProvider):
    """
    Selection tree style
    """
    def get_style(self, node:TreeNode, role:Qt.ItemDataRole):
        state= self.get_node_state(node)

        if role == Qt.ItemDataRole.ForegroundRole:
            # -------------------------------------------------
            # Structural nodes
            # -------------------------------------------------
            if node.i_am == "root":
                return QColor("#7A8F82")       # muted sage

            if node.i_am == "database":
                return QColor("#D6A84F")       # warm amber/gold

            if node.i_am == "map":
                if node.i_exist:
                    return QColor("#d1ce22")   # existing map - green
                else:
                    return QColor("#B07A5A")   # missing map - muted orange/brown
            
            # LOCKED always wins
            if state == NodeVisualState.LOCKED:
                if node.i_exist:
                    return QColor("#6F8F7A")   # muted green-gray
                else:
                    return QColor("#8A8F98")   # neutral gray

            # Selected
            if state == NodeVisualState.SELECTED:
                if node.i_exist:
                    return QColor("#14B163")   # strong green
                else:
                    return QColor("#3B82F6")   # blue

            # Bloodline
            if state == NodeVisualState.BLOODLINE:
                if node.i_exist:
                    return QColor("#32B4DB")   # cyan
                else:
                    return QColor("#60A5FA")   # light blue


        if role == Qt.ItemDataRole.FontRole: 
            font = QFont("Consolas")
            #font.setPointSize(10)

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

class DBSelectionExplorerStyle(TreeStyle):

    def text(self, node:TreeNode):
        node_size_txt=""
        if node.i_am in ["file","dir"] and isinstance(node.size,(int | float)):
            node_size_txt=FM.get_size_str_formatted(node.size,10,True)
            node_size_txt=node_size_txt.replace(".00 By"," Bytes")

        prefix = ""
        if node.i_exist:
            prefix += "✓"
        else:
            prefix += "-"

        if node.locked:
            prefix += "🔒"

        if node.i_am == "dir":
            return f"{prefix}{node_size_txt}📁 {node.name}"

        return f"{prefix}{node_size_txt}📄 {node.name}"

    def tooltip(self, node:TreeNode)->str:
        txt = [
            f"Name : {'🔒' if node.locked else ''} {node.name}",
            f"ID   : {node.id}",
            f"Type : {node.i_am}"
        ]

        if node.path:
            if node.i_exist:
                txt.append(f"Path : ✓ {node.path}")
            else:
                txt.append(f"Path : ✗ {node.path}")

        if node.i_am in ["file","dir"] and isinstance(node.size,(int | float)):
            node_size_txt=FM.get_size_str_formatted(node.size,10,True)
            node_size_txt=node_size_txt.replace(".00 By"," Bytes").strip()
            txt.append(f"Size : {node_size_txt}")

        return "\n".join(txt)

    def icon(self, node)-> QIcon | None:
        return None    
