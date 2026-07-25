# ask_confirmation_dialog.py

from PyQt6.QtWidgets import (
    QDialog,
    QMessageBox
)

class QtDialogs:

    @staticmethod
    def ask_confirmation(
        message,
        default=False
    ):

        result = QMessageBox.question(
            None,
            "Confirmation",
            message,
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No
        )

        return result == QMessageBox.StandardButton.Yes