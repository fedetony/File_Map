

from rich.console import Console
from rich.text import Text
from rich.markup import render
from ansi2html import Ansi2HTMLConverter


from ansi2html import Ansi2HTMLConverter
from rich.console import Console
from rich.text import Text
import html


class TextRenderer:
    """
    Converts text output from different sources into HTML suitable for Qt widgets.

    Supported inputs:
        - ANSI escape sequences (terminal colors)
        - Rich markup strings
        - Rich Text objects
        - Plain text

    Output:
        - HTML string compatible with QTextEdit/QLabel/etc.
    """

    ANSI_MARKER = "\033["

    def __init__(self):
        self.ansi_converter = Ansi2HTMLConverter(inline=True)
        self.console = Console(record=True, color_system="truecolor")

    def to_html(self, value) -> str:
        """
        Convert any supported text format into HTML.
        """

        if value is None:
            return ""

        # Rich Text object
        if isinstance(value, Text):
            return self.rich_text_to_html(value)

        # Convert everything else to string
        text = str(value)

        # ANSI terminal colors
        if self.has_ansi(text):
            return self.ansi_to_html(text)

        # Rich markup
        if self.has_rich_markup(text):
            return self.rich_to_html(text)

        # Normal text
        return html.escape(text)


    def has_ansi(self, text):
        """
        Detect ANSI escape sequences.
        """
        return self.ANSI_MARKER in text


    def has_rich_markup(self, text):
        """
        Basic detection of Rich markup.

        Avoids treating normal text like:
        'Database [test]'
        as markup.
        """
        return (
            "[" in text
            and "]" in text
            and "[/" in text)

    def ansi_to_html(self, text):
        """
        Convert terminal ANSI colors to HTML.
        """
        return self.ansi_converter.convert(text, full=False)

    def rich_to_html(self, text):
        """
        Convert Rich markup into HTML.
        """
        self.console.clear()
        self.console.print(text, markup=True)
        return self.console.export_html(inline=True)

    def rich_text_to_html(self, text):
        """
        Convert a Rich Text object into HTML.
        """
        self.console.clear()
        self.console.print(text)
        return self.console.export_html(inline=True)