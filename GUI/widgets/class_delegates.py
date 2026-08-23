# class_date_delegate.py
from PyQt6 import QtCore, QtGui, QtWidgets 
from PyQt6.QtWidgets import *
from datetime import datetime


class DateDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(
        self,
        parent=None,
        output_format="%d %b %Y %H:%M",
    ):
        super().__init__(parent)

        self.output_format = output_format

    def displayText(self, value, locale):
        if value is None:
            return ""

        text = str(value)
        try:
            d_t=datetime.fromisoformat(text)
        except ValueError:
            return text
        return d_t.strftime(self.output_format)
    
class ColoredTextDelegate(QtWidgets.QStyledItemDelegate):
     
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter, option, index):
        painter.save()

        # Let Qt draw selection/background/focus normally
        if option.state & QtWidgets.QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        text = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
        if text is None:
            painter.restore()
            return

        # Example: split your text however you need
        if "[" in text:
            main_text, extra = text.split("[", 1)
            extra = "[" + extra
            use_shallow=True
        elif "(" in text:
            main_text, extra = text.split("(", 1)
            extra = "(" + extra
            use_shallow=False
        else:
            main_text = text
            extra = ""
            use_shallow=None

        document = QtGui.QTextDocument()
        document.setDefaultFont(option.font)
        c1="#ac34db"
        c2="#27ae60"
        c3="#dbca34"
        c4="#e67e22"
        c5="#3498db"
        if use_shallow is None:
            html = (
                f'<span style="color:{c2};">{main_text}</span>'
                f'<span style="color:{c3};">{extra}</span>'
            )
        elif use_shallow:
            html = (
                f'<span style="color:{c5};">{main_text}</span>'
                f'<span style="color:{c1};">{extra}</span>'
            )
        else:
            html = (
                f'<span style="color:{c5};">{main_text}</span>'
                f'<span style="color:{c4};">{extra}</span>'
            )

        document.setHtml(html)

        painter.translate(option.rect.topLeft())

        document.drawContents(
            painter,
            QtCore.QRectF(
                0,
                0,
                option.rect.width(),
                option.rect.height(),
            ),
        )

        painter.restore()

class ItemTypeDelegate(QStyledItemDelegate):

    def __init__(
        self,
        icons: dict,
        itemtype_column: int,
        parent=None
    ):
        super().__init__(parent)
        self.item_icons = icons
        self.itemtype_column = itemtype_column

    def paint(self, painter, option, index):
        item_type = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
        icon = self.item_icons.get(str(item_type).lower())
        if icon is not None and not icon.isNull():
            option = QStyleOptionViewItem(option)
            option.icon = icon

        super().paint(painter, option, index)



class ActiveMapDelegate(QStyledItemDelegate):

    ACTIVE_COLOR = QtGui.QColor("#27AE60")
    ACTIVE_FONT = QtGui.QFont("", -1, QtGui.QFont.Weight.Bold)

    def __init__(self, fmap, mount_column, serial_column, parent=None):
        super().__init__(parent)
        self.fmap = fmap
        self.mount_column = mount_column
        self.serial_column = serial_column

    def paint(self, painter, option, index):
        mount_index = index.siblingAtColumn(self.mount_column)
        serial_index = index.siblingAtColumn(self.serial_column)

        mount = str(
            mount_index.data(QtCore.Qt.ItemDataRole.DisplayRole) or ""
        )
        serial = str(
            serial_index.data(QtCore.Qt.ItemDataRole.DisplayRole) or ""
        )

        if self.is_active(mount, serial):
            option = QStyleOptionViewItem(option)
            option.palette.setColor(
                QtGui.QPalette.ColorRole.Text,
                self.ACTIVE_COLOR
            )
            option.font = QtGui.QFont(option.font)
            option.font.setBold(True)

        super().paint(painter, option, index)

    def is_active(self, mount, serial):
        for device_mount, device_serial in self.fmap.device_monitor.devices:
            if mount == str(device_mount) and serial == str(device_serial):
                return True

        return False
