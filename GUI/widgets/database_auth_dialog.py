# database_auth_dialog.py

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QHBoxLayout
)


class DatabaseAuthDialog(QDialog):

    def __init__(
        self,
        database_name,
        need_password=False,
        need_key=False,
        parent=None
    ):
        super().__init__(parent)

        self.setWindowTitle("Database Authentication")

        self.password = None
        self.key_file = None

        self.need_password = need_password
        self.need_key = need_key

        self.create_ui(database_name)


    def create_ui(self, database_name):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Database: {database_name}"))

        if self.need_password:
            self.password_edit = QLineEdit()
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.password_edit.setPlaceholderText("Password")
            layout.addWidget(self.password_edit)

        if self.need_key:
            row = QHBoxLayout()
            self.key_edit = QLineEdit()
            browse = QPushButton("Browse")
            browse.clicked.connect(self.select_key)
            row.addWidget(self.key_edit)
            row.addWidget(browse)
            layout.addLayout(row)
        ok = QPushButton("Continue")
        ok.clicked.connect(self.accept)
        layout.addWidget(ok)

    def select_key(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select SHA256 Key File",
            filter="Text files (*.txt)")
        if filename:
            self.key_edit.setText(filename)

    def values(self):
        password = None
        key = None
        if self.need_password:
            password = self.password_edit.text()
        if self.need_key:
            key = self.key_edit.text()
        return password, key