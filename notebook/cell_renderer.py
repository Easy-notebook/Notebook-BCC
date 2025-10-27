"""
Cell Renderer
Renders notebook cells for display.
"""

from silantui import ModernLogger
from typing import List
from models.cell import Cell, CellType
from .markdown_renderer import MarkdownRenderer



class CellRenderer(ModernLogger):
    """
    Renders notebook cells for terminal display.
    """

    def __init__(self, use_colors: bool = True, show_cell_numbers: bool = True):
        """
        Initialize the renderer.

        Args:
            use_colors: Whether to use ANSI colors
            show_cell_numbers: Whether to show cell numbers
        """
        super().__init__("CellRenderer")
        self.use_colors = use_colors
        self.show_cell_numbers = show_cell_numbers
        self.markdown_renderer = MarkdownRenderer(use_colors=use_colors)

        # ANSI color codes
        self.colors = {
            'reset': '\033[0m',
            'bold': '\033[1m',
            'dim': '\033[2m',
            'gray': '\033[90m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'magenta': '\033[95m',
            'cyan': '\033[96m',
            'red': '\033[91m',
        } if use_colors else {k: '' for k in ['reset', 'bold', 'dim', 'gray', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'red']}

    def render_cell(self, cell: Cell, cell_number: int = None) -> str:
        """
        Render a single cell.

        Args:
            cell: The cell to render
            cell_number: Optional cell number

        Returns:
            Rendered cell content
        """
        lines = []

        # Cell header
        if self.show_cell_numbers and cell_number is not None:
            header = f"{self.colors['gray']}[{cell_number}] {cell.type.value}{self.colors['reset']}"
            lines.append(header)
            lines.append(self.colors['gray'] + "─" * 60 + self.colors['reset'])

        # Render based on type
        if cell.type == CellType.MARKDOWN:
            rendered_content = self.markdown_renderer.render(cell.content)
            lines.append(rendered_content)

        elif cell.type == CellType.CODE:
            # Code header
            lines.append(f"{self.colors['blue']}Code ({cell.language}):{self.colors['reset']}")

            # Code content
            code_lines = cell.content.split('\n')
            for code_line in code_lines:
                lines.append(f"  {self.colors['cyan']}{code_line}{self.colors['reset']}")

            # Outputs
            if cell.outputs:
                lines.append(f"\n{self.colors['green']}Output:{self.colors['reset']}")
                for output in cell.outputs:
                    if output.output_type == 'error':
                        lines.append(f"{self.colors['red']}{output.content}{self.colors['reset']}")
                    else:
                        output_text = output.content or output.text or ''
                        lines.append(f"{self.colors['gray']}{output_text}{self.colors['reset']}")

        elif cell.type == CellType.THINKING:
            # Thinking cell
            agent_name = cell.agent_name or 'AI'
            lines.append(f"{self.colors['magenta']}💭 {agent_name} is thinking...{self.colors['reset']}")
            if cell.text_array:
                for text in cell.text_array:
                    lines.append(f"{self.colors['dim']}  {text}{self.colors['reset']}")

        elif cell.type == CellType.OUTCOME:
            lines.append(f"{self.colors['green']}✓ Outcome:{self.colors['reset']}")
            lines.append(cell.content)

        elif cell.type == CellType.ERROR:
            lines.append(f"{self.colors['red']}✗ Error:{self.colors['reset']}")
            lines.append(f"{self.colors['red']}{cell.content}{self.colors['reset']}")

        # Cell footer
        if self.show_cell_numbers:
            lines.append("")

        return '\n'.join(lines)

    def render_cells(self, cells: List[Cell]) -> str:
        """
        Render multiple cells.

        Args:
            cells: List of cells to render

        Returns:
            Rendered content
        """
        rendered_cells = []

        for i, cell in enumerate(cells):
            rendered = self.render_cell(cell, cell_number=i+1)
            rendered_cells.append(rendered)

        return '\n'.join(rendered_cells)

    def render_notebook_summary(self, notebook_data: dict) -> str:
        """
        Render a notebook summary.

        Args:
            notebook_data: The notebook data

        Returns:
            Rendered summary
        """
        lines = []

        lines.append(f"{self.colors['bold']}{self.colors['cyan']}{'='*60}{self.colors['reset']}")
        title = notebook_data.get('title', 'Untitled Notebook')
        lines.append(f"{self.colors['bold']}{self.colors['cyan']}{title.center(60)}{self.colors['reset']}")
        lines.append(f"{self.colors['bold']}{self.colors['cyan']}{'='*60}{self.colors['reset']}")
        lines.append("")

        # Cell count
        cells = notebook_data.get('cells', [])
        cell_counts = {}
        for cell in cells:
            cell_type = cell.get('type', 'unknown')
            cell_counts[cell_type] = cell_counts.get(cell_type, 0) + 1

        lines.append(f"{self.colors['bold']}Cells:{self.colors['reset']}")
        for cell_type, count in cell_counts.items():
            lines.append(f"  {cell_type}: {count}")

        lines.append("")

        return '\n'.join(lines)
