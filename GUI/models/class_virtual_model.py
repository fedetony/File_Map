from PyQt6.QtCore import Qt, QAbstractItemModel, QModelIndex


class VirtualNode:
    def __init__(self, name, parent=None):
        self.name = name
        self.children: list[VirtualNode] = []
        self.parent = parent


class VirtualModel(QAbstractItemModel):
    def __init__(self, backend=None):
        super().__init__()
        self.backend = backend  # your engine (plug later)
        self.root = VirtualNode("ROOT")

    # --- basic tree plumbing ---

    def rowCount(self, parent):
        node = parent.internalPointer() if parent.isValid() else self.root
        return len(node.children)

    def columnCount(self, parent):
        return 1

    def index(self, row, col, parent):
        if not self.hasIndex(row, col, parent):
            return QModelIndex()
        parent_node = parent.internalPointer() if parent.isValid() else self.root
        if row < 0 or row >= len(parent_node.children):
            return QModelIndex()
        child = parent_node.children[row]
        return self.createIndex(row, col, child)

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        node = index.internalPointer()
        parent = node.parent
        if parent is None or parent == self.root:
            return QModelIndex()
        grandparent = parent.parent
        row = grandparent.children.index(parent)
        return self.createIndex(row, 0, parent)

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            node = index.internalPointer()
            return node.name

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsDropEnabled
        return (
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsEditable
            | Qt.ItemFlag.ItemIsDragEnabled
            | Qt.ItemFlag.ItemIsDropEnabled
        )

    # --- rename ---

    def setData(self, index, value, role):
        if role == Qt.ItemDataRole.EditRole and index.isValid():
            node = index.internalPointer()
            node.name = value
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
            # TODO: call backend rename hook here if needed
            return True
        return False

    # --- create folder ---

    def insert_folder(self, parent_index, name: str):
        parent_node = parent_index.internalPointer() if parent_index.isValid() else self.root
        new_node = VirtualNode(name, parent_node)
        row = len(parent_node.children)
        self.beginInsertRows(parent_index, row, row)
        parent_node.children.append(new_node)
        self.endInsertRows()
        # TODO: backend hook for "create directory" in virtual map

    # --- delete node ---

    def remove_node(self, index):
        if not index.isValid():
            return
        node = index.internalPointer()
        parent = node.parent
        if parent is None:
            return
        row = parent.children.index(node)
        parent_index = self.createIndex(parent.children.index(node.parent) if parent.parent else 0, 0, parent)
        self.beginRemoveRows(parent_index, row, row)
        parent.children.pop(row)
        self.endRemoveRows()
        # TODO: backend hook for "delete" in virtual map

    # --- path helper ---

    def filePath(self, index):
        if not index.isValid():
            return "/"
        node = index.internalPointer()
        parts = []
        while node and node.parent:
            parts.append(node.name)
            node = node.parent
        return "/" + "/".join(reversed(parts))

    # --- JSON save/load (structure only) ---

    def to_dict(self, node=None):
        if node is None:
            node = self.root
        return {
            "name": node.name,
            "children": [self.to_dict(c) for c in node.children],
        }

    def from_dict(self, data, parent=None):
        if parent is None:
            self.root = VirtualNode(data["name"])
            parent = self.root
        for child_data in data.get("children", []):
            child = VirtualNode(child_data["name"], parent)
            parent.children.append(child)
            self.from_dict(child_data, child)
        # TODO: emit layoutChanged when used
