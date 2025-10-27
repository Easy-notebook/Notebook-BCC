"""
Markdown Renderer
Renders markdown content to terminal-friendly format.
"""

import re
from silantui import ModernLogger
from typing import List



class MarkdownRenderer(ModernLogger):
    """
    Renders markdown content for terminal display.
    """

    def __init__(self, use_colors: bool = True):
        """
        Initialize the renderer.

        Args:
            use_colors: Whether to use ANSI colors
        """
        super().__init__("MarkdownRenderer")
        self.use_colors = use_colors

        # ANSI color codes
        self.colors = {
            'reset': '\033[0m',
            'bold': '\033[1m',
            'dim': '\033[2m',
            'underline': '\033[4m',
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'magenta': '\033[95m',
            'cyan': '\033[96m',
        } if use_colors else {k: '' for k in ['reset', 'bold', 'dim', 'underline', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan']}

    def render(self, markdown_text: str) -> str:
        """
        Render markdown text.

        Args:
            markdown_text: The markdown text to render

        Returns:
            Rendered text
        """
        lines = markdown_text.split('\n')
        rendered_lines = []

        for line in lines:
            rendered_line = self._render_line(line)
            rendered_lines.append(rendered_line)

        return '\n'.join(rendered_lines)

    def _render_line(self, line: str) -> str:
        """Render a single line."""
        # Headers
        if line.startswith('# '):
            return f"{self.colors['bold']}{self.colors['cyan']}{line}{self.colors['reset']}"
        elif line.startswith('## '):
            return f"{self.colors['bold']}{self.colors['blue']}{line}{self.colors['reset']}"
        elif line.startswith('### '):
            return f"{self.colors['bold']}{line}{self.colors['reset']}"

        # Code blocks (inline)
        line = re.sub(r'`([^`]+)`', f"{self.colors['yellow']}\\1{self.colors['reset']}", line)

        # Bold
        line = re.sub(r'\*\*([^*]+)\*\*', f"{self.colors['bold']}\\1{self.colors['reset']}", line)

        # Italic
        line = re.sub(r'\*([^*]+)\*', f"{self.colors['dim']}\\1{self.colors['reset']}", line)

        # Links
        line = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', f"{self.colors['underline']}{self.colors['blue']}\\1{self.colors['reset']}", line)

        return line

    def render_multiline(self, markdown_text: str) -> List[str]:
        """
        Render markdown text and return as list of lines.

        Args:
            markdown_text: The markdown text to render

        Returns:
            List of rendered lines
        """
        rendered = self.render(markdown_text)
        return rendered.split('\n')
