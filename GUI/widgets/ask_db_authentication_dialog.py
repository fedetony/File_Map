from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QCheckBox,
    QPushButton,
    QHBoxLayout,
)


class DatabaseAuthTypeDialog(QDialog):
    """Ask the user which authentication the database uses."""

    def __init__(self, database_name, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Database Authentication")
        self.create_ui(database_name)

    def create_ui(self, database_name):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"Database: {database_name}"))
        layout.addWidget(QLabel("Select the authentication used by this database:"))

        self.password_check = QCheckBox("Password")
        self.keyfile_check = QCheckBox("SHA256 Key File")

        layout.addWidget(self.password_check)
        layout.addWidget(self.keyfile_check)

        buttons = QHBoxLayout()

        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)

        ok = QPushButton("Continue")
        ok.clicked.connect(self.accept)

        buttons.addStretch()
        buttons.addWidget(cancel)
        buttons.addWidget(ok)

        layout.addLayout(buttons)

    def values(self):
        return (
            self.password_check.isChecked(),
            self.keyfile_check.isChecked(),
        )