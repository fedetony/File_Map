

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
        """Detect likely Rich markup anywhere in the text."""
        if "[" not in text or "]" not in text:
            return False

        # Explicit closing markup
        if "[/" in text:
            return True

        # Opening/style markup, including combinations such as
        # [bold red] or [italic green]
        return any(
            f"[{tag}" in text
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


    def rich_to_html(self, text):
        """
        Convert Rich markup into compact inline HTML.

        Supports both explicit closing tags and Rich's implicit
        style continuation, for example:

            [green]Hello
            [green]Hello[/green]
            [green]Hi [red]there [white]again
        """
        if not text:
            return ""

        rich_text = self.console.render_str(
            str(text),
            markup=True,
        )

        plain = rich_text.plain

        if not plain:
            return ""

        # Every span boundary is a point where the active style
        # can change.
        boundaries = {0, len(plain)}

        for span in rich_text.spans:
            boundaries.add(span.start)
            boundaries.add(span.end)

        boundaries = sorted(boundaries)

        parts = []

        for start, end in zip(boundaries, boundaries[1:]):
            if start >= end:
                continue

            content = html.escape(plain[start:end])

            # Find all styles active for this section.
            styles = [
                str(span.style)
                for span in rich_text.spans
                if span.start <= start and span.end >= end
            ]

            if styles:
                css = self._rich_style_to_css(
                    " ".join(styles)
                )

                if css:
                    content = (
                        f'<span style="{css}">'
                        f'{content}'
                        f'</span>'
                    )

            parts.append(content)

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
                css.append(f"color: {colors[item]};")

            elif item == "bold":
                css.append("font-weight: bold;")

            elif item == "italic":
                css.append("font-style: italic;")

            elif item == "underline":
                css.append("text-decoration: underline;")

            elif item == "strike":
                css.append("text-decoration: line-through;")

        return " ".join(css)

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

    def rich_text_to_html(self, text):
        """
        Convert a Rich Text object into HTML.
        """
        self.console.clear()
        self.console.print(text)
        return self.console.export_html() #inline=True)