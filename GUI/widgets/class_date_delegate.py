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
    