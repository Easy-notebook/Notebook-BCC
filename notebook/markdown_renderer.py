"""
Markdown Renderer
Renders markdown content to terminal-friendly format.
Supports error and image rendering in standard markdown.
"""

import re
from silantui import ModernLogger
from typing import List, Dict, Any



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
        in_code_block = False
        code_block_type = None

        for line in lines:
            # Track code blocks
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                if in_code_block:
                    # Extract code block type (e.g., 'error', 'python', etc.)
                    code_block_type = line.strip()[3:].strip()
                    if code_block_type == 'error':
                        rendered_lines.append(f"{self.colors['red']}{self.colors['bold']}Error:{self.colors['reset']}")
                        continue
                else:
                    code_block_type = None
                    continue

            # Render error code block lines with red color
            if in_code_block and code_block_type == 'error':
                rendered_lines.append(f"{self.colors['red']}{line}{self.colors['reset']}")
            # Render other code block lines
            elif in_code_block:
                rendered_lines.append(f"{self.colors['yellow']}{line}{self.colors['reset']}")
            # Regular markdown lines
            else:
                rendered_line = self._render_line(line)
                rendered_lines.append(rendered_line)

        return '\n'.join(rendered_lines)

    def _render_line(self, line: str) -> str:
        """Render a single line."""
        # Headers - only match if # is at the very start and followed by space
        # This prevents matching code comments like "# Load data"
        stripped_line = line.lstrip()
        if stripped_line.startswith('# ') and line.startswith('#'):
            return f"{self.colors['bold']}{self.colors['cyan']}{line}{self.colors['reset']}"
        elif stripped_line.startswith('## ') and line.startswith('##'):
            return f"{self.colors['bold']}{self.colors['blue']}{line}{self.colors['reset']}"
        elif stripped_line.startswith('### ') and line.startswith('###'):
            return f"{self.colors['bold']}{line}{self.colors['reset']}"

        # Images: ![alt text](url)
        # Special rendering for images with distinctive formatting
        image_pattern = r'!\[([^\]]*)\]\(([^\)]+)\)'
        if re.search(image_pattern, line):
            def replace_image(match):
                alt_text = match.group(1) or 'Image'
                url = match.group(2)
                # Extract image ID if present
                image_id_match = re.search(r'#([^\s>]+)', url)
                if image_id_match:
                    image_id = image_id_match.group(1)
                    return f"{self.colors['cyan']}{self.colors['bold']}[📊 {alt_text} (#{image_id})]{self.colors['reset']}"
                else:
                    return f"{self.colors['cyan']}{self.colors['bold']}[📊 {alt_text}]{self.colors['reset']}"
            line = re.sub(image_pattern, replace_image, line)

        # Code blocks (inline)
        line = re.sub(r'`([^`]+)`', f"{self.colors['yellow']}\\1{self.colors['reset']}", line)

        # Bold
        line = re.sub(r'\*\*([^*]+)\*\*', f"{self.colors['bold']}\\1{self.colors['reset']}", line)

        # Italic
        line = re.sub(r'\*([^*]+)\*', f"{self.colors['dim']}\\1{self.colors['reset']}", line)

        # Links (but not images, which were already handled)
        line = re.sub(r'(?<!\!)\[([^\]]+)\]\(([^\)]+)\)', f"{self.colors['underline']}{self.colors['blue']}\\1{self.colors['reset']}", line)

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

    def render_error(self, error_data: Dict[str, Any]) -> str:
        """
        Render error data to standard markdown format.

        Args:
            error_data: Error dictionary with 'name', 'message', and 'traceback'

        Returns:
            Rendered error in markdown format

        Example:
            Input: {"name": "ValueError", "message": "Invalid input", "traceback": ["line 1", "line 2"]}
            Output:
            ```error
            ValueError: Invalid input

            Traceback:
              line 1
              line 2
            ```
        """
        error_name = error_data.get('name', 'Error')
        error_message = error_data.get('message', '')
        traceback = error_data.get('traceback', [])

        lines = ['```error']
        lines.append(f"{error_name}: {error_message}")

        if traceback:
            lines.append('')
            lines.append('Traceback:')
            for trace_line in traceback:
                # Remove ANSI color codes from traceback if any
                clean_trace = re.sub(r'\x1b\[[0-9;]*m', '', str(trace_line))
                lines.append(f"  {clean_trace}")

        lines.append('```')
        return '\n'.join(lines)

    def render_image(self, image_url: str, alt_text: str = '') -> str:
        """
        Render image reference to standard markdown format.

        Args:
            image_url: Image URL or reference (e.g., "<image #cell-1-img request-to-see>")
            alt_text: Alternative text for the image

        Returns:
            Rendered image in markdown format

        Example:
            Input: "<image #cell-1-img request-to-see>", "Plot output"
            Output: ![Plot output](<image #cell-1-img request-to-see>)
        """
        # If alt_text is not provided, try to extract image id from url
        if not alt_text:
            image_id_match = re.search(r'#([^\s>]+)', image_url)
            if image_id_match:
                alt_text = f"Image {image_id_match.group(1)}"
            else:
                alt_text = "Image"

        return f"![{alt_text}]({image_url})"

    def parse_and_render_content(self, content: str, content_type: str = 'text') -> str:
        """
        Parse and render content based on its type.

        Args:
            content: Content to render
            content_type: Type of content ('text', 'error', 'image')

        Returns:
            Rendered content in markdown format
        """
        if content_type == 'error':
            # If content is a string, try to parse it as error format
            if isinstance(content, str):
                # Simple error string format
                return f"```error\n{content}\n```"
            elif isinstance(content, dict):
                return self.render_error(content)

        elif content_type == 'image':
            if isinstance(content, str):
                return self.render_image(content)
            elif isinstance(content, dict) and 'image_url' in content:
                return self.render_image(content['image_url'], content.get('alt_text', ''))

        # Default: render as regular markdown text
        return self.render(str(content))
