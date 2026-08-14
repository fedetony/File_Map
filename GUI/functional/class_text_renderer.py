

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
        Detect likely Rich markup.

        Rich allows tags such as:

            [blue]Mapping...
            [red]Warning
            [green]Complete

        without explicit closing tags.
        """
        if "[" not in text or "]" not in text:
            return False

        # Explicit Rich closing tag
        if "[/" in text:
            return True

        # Common Rich opening tag.
        # Avoid treating ordinary "[text]" as markup.
        return any(
            text.startswith(f"[{tag}]")
            for tag in (
                "black",
                "red",
                "green",
                "yellow",
                "blue",
                "magenta",
                "cyan",
                "white",
                "bold",
                "dim",
                "italic",
                "underline",
                "strike",
                "blink",
                "reverse",
            )
        )

    def ansi_to_html(self, text):
        """
        Convert terminal ANSI colors to HTML.
        """
        return self.ansi_converter.convert(text, full=False)

    # def rich_to_html(self, text):
    #     """
    #     Convert Rich markup into HTML.
    #     """
    #     self.console.clear()
    #     self.console.print(text, markup=True)
    #     return self.console.export_html(inline=True)
    def rich_to_html(self, text):
        """
        Convert arbitrary Rich markup into compact inline HTML suitable for Qt.
        Rich handles the parsing and styling.
        """
        if not text:
            return ""

        rich_text = self.console.render_str(
            str(text),
            markup=True,
        )

        if not rich_text.plain:
            return ""

        parts = []
        pos = 0

        for span in sorted(
            rich_text.spans,
            key=lambda span: (span.start, span.end),
        ):

            if span.start > pos:
                parts.append(
                    html.escape(rich_text.plain[pos:span.start])
                )

            content = html.escape(
                rich_text.plain[span.start:span.end]
            )

            css = self._rich_style_to_css(span.style)

            if css:
                content = (
                    f'<span style="{css}">'
                    f'{content}'
                    f'</span>'
                )

            parts.append(content)
            pos = max(pos, span.end)

        if pos < len(rich_text.plain):
            parts.append(
                html.escape(rich_text.plain[pos:])
            )

        return "".join(parts)

    def _rich_style_to_css(self, style):
        """
        Convert a Rich style string into Qt-compatible CSS.
        """

        if not style:
            return ""

        styles = style.split()
        css = []

        colors = {
            "black": "#000000",
            "red": "#ff0000",
            "green": "#00ff00",
            "yellow": "#ffff00",
            "blue": "#0000ff",
            "magenta": "#ff00ff",
            "cyan": "#00ffff",
            "white": "#ffffff",

            "bright_black": "#808080",
            "bright_red": "#ff5555",
            "bright_green": "#55ff55",
            "bright_yellow": "#ffff55",
            "bright_blue": "#5555ff",
            "bright_magenta": "#ff55ff",
            "bright_cyan": "#55ffff",
            "bright_white": "#ffffff",
        }

        for item in styles:

            if item in colors:
                css.append(
                    f"color: {colors[item]};"
                )

            elif item == "bold":
                css.append(
                    "font-weight: bold;"
                )

            elif item == "italic":
                css.append(
                    "font-style: italic;"
                )

            elif item == "underline":
                css.append(
                    "text-decoration: underline;"
                )

            elif item == "strike":
                css.append(
                    "text-decoration: line-through;"
                )

        return " ".join(css)
    

    def rich_text_to_html(self, text):
        """
        Convert a Rich Text object into HTML.
        """
        self.console.clear()
        self.console.print(text)
        return self.console.export_html() #inline=True)