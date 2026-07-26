# ask_confirmation_dialog.py

from PyQt6.QtWidgets import (
    QDialog,
    QMessageBox
)

class ConfirmationDialog:

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
        if result not in [QMessageBox.StandardButton.Yes ,
            QMessageBox.StandardButton.No]:
            return default

        return result == QMessageBox.StandardButton.Yes