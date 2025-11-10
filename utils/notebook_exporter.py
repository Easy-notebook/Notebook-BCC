"""
Notebook Exporter - Convert notebook from state to markdown
"""

import json
from typing import Dict, Any, List


class NotebookExporter:
    """Export notebook from state to markdown format"""

    @staticmethod
    def state_to_markdown(state_data: Dict[str, Any]) -> str:
        """
        Convert notebook from state to markdown format

        Args:
            state_data: Complete state dictionary

        Returns:
            Markdown string
        """
        notebook = state_data.get('state', {}).get('notebook', {})
        title = notebook.get('title', 'Untitled Notebook')
        cells = notebook.get('cells', [])

        markdown_lines = []

        # Add title
        markdown_lines.append(f"# {title}\n")

        # Process each cell
        for cell in cells:
            cell_type = cell.get('type')
            content = cell.get('content', '')

            if cell_type == 'markdown':
                # Add markdown cell content directly
                markdown_lines.append(content)
                markdown_lines.append("")  # Empty line between cells

            elif cell_type == 'code':
                # Add code cell with fence
                markdown_lines.append("```python")
                markdown_lines.append(content)
                markdown_lines.append("```")

                # Add outputs if present
                outputs = cell.get('outputs', [])
                if outputs:
                    markdown_lines.append("")

                    for output in outputs:
                        output_type = output.get('output_type')

                        if output_type == 'stream':
                            # Standard output
                            text = output.get('text', '')
                            markdown_lines.append("<output>")
                            markdown_lines.append(text.rstrip())
                            markdown_lines.append("</output>")

                        elif output_type == 'error':
                            # Error output
                            ename = output.get('ename', 'Error')
                            evalue = output.get('evalue', '')
                            traceback = output.get('traceback', [])

                            markdown_lines.append("<output>")
                            markdown_lines.append(f"{ename}: {evalue}")
                            if traceback:
                                for line in traceback:
                                    # Remove ANSI color codes
                                    clean_line = NotebookExporter._remove_ansi_codes(line)
                                    markdown_lines.append(clean_line)
                            markdown_lines.append("</output>")

                        elif output_type == 'execute_result':
                            # Execution result
                            text = output.get('text', '')
                            markdown_lines.append("<output>")
                            markdown_lines.append(text.rstrip())
                            markdown_lines.append("</output>")

                markdown_lines.append("")  # Empty line between cells

        return "\n".join(markdown_lines)

    @staticmethod
    def _remove_ansi_codes(text: str) -> str:
        """Remove ANSI color codes from text"""
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    @staticmethod
    def export_from_state_file(state_file_path: str, output_md_path: str = None) -> str:
        """
        Export markdown from state file

        Args:
            state_file_path: Path to state JSON file
            output_md_path: Optional path to save markdown file

        Returns:
            Markdown content
        """
        with open(state_file_path, 'r', encoding='utf-8') as f:
            state_data = json.load(f)

        markdown = NotebookExporter.state_to_markdown(state_data)

        if output_md_path:
            with open(output_md_path, 'w', encoding='utf-8') as f:
                f.write(markdown)

        return markdown


if __name__ == '__main__':
    # Test
    import sys
    if len(sys.argv) > 1:
        state_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None

        md = NotebookExporter.export_from_state_file(state_file, output_file)

        if output_file:
            print(f"Exported to: {output_file}")
        else:
            print(md)
