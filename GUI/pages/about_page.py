# about_page.py
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
)


class AboutPage(QWidget):

    def __init__(
        self,
        parent=None,
        icon_path=None,
        author="Your Name",
        version="1.0",
        creation_date="2025",
        github="github.com",
        copyright_text=""
    ):

        super().__init__(parent)

        self.icon_path = icon_path

        self.author = author
        self.version = version
        self.creation_date = creation_date
        self.github = github
        self.copyright_text = copyright_text

        self.create_ui()


    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def create_ui(self):

        layout = QVBoxLayout(
            self
        )

        layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )


        # Icon

        self.icon_label = QLabel()

        self.icon_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )


        if self.icon_path:

            pixmap = QPixmap(
                self.icon_path
            )

            pixmap = pixmap.scaled(
                160,
                160,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            self.icon_label.setPixmap(
                pixmap
            )


        layout.addWidget(
            self.icon_label
        )


        # Main text

        year = datetime.now().strftime(
            "%Y"
        )


        html = f"""
        <div align="center">

        <h1 style="
        font-size:220%;
        color:#d00000;
        ">
        Programmed with coffee & love ❤️
        </h1>


        <h2 style="
        color:#202020;
        ">
        File Mapping Tool
        </h2>


        <p style="
        font-size:120%;
        ">
        by <b>{self.author}</b>
        </p>


        <p>
        Version: <b>{self.version}</b>
        </p>


        <p>
        Creation date: {self.creation_date}
        </p>


        <p>
        <a href="{self.github}">
        {self.github}
        </a>
        </p>


        <hr>


        <small>
        {self.copyright_text.replace("<year>", year)}
        </small>


        </div>
        """


        self.info = QLabel()

        self.info.setTextFormat(
            Qt.TextFormat.RichText
        )

        self.info.setOpenExternalLinks(
            True
        )

        self.info.setText(
            html
        )

        self.info.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )


        layout.addWidget(
            self.info
        )


        # Button

        buttons = QHBoxLayout()

        buttons.addStretch()


        self.website_button = QPushButton(
            "Visit Project"
        )


        self.website_button.clicked.connect(
            self.open_project
        )


        buttons.addWidget(
            self.website_button
        )


        buttons.addStretch()


        layout.addLayout(
            buttons
        )


        layout.addStretch()


    # --------------------------------------------------
    # Actions
    # --------------------------------------------------

    def open_project(self):

        import webbrowser

        webbrowser.open(
            self.github
        )


    # --------------------------------------------------
    # Lifecycle
    # --------------------------------------------------

    def activate(self):

        pass


    def deactivate(self):

        pass