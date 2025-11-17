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
                            # Standard output - use code block to prevent markdown interpretation
                            text = output.get('text', '')
                            markdown_lines.append("")
                            markdown_lines.append("```")
                            markdown_lines.append(text.rstrip())
                            markdown_lines.append("```")
                            markdown_lines.append("")

                        elif output_type == 'error':
                            # Error output - render as error code block
                            ename = output.get('ename')
                            evalue = output.get('evalue')
                            traceback = output.get('traceback', [])

                            # Check if we have structured error data or just text
                            if ename and evalue is not None:
                                # Structured error with ename and evalue
                                markdown_lines.append("")
                                markdown_lines.append("```error")
                                markdown_lines.append(f"{ename}: {evalue}")

                                if traceback:
                                    markdown_lines.append("")
                                    markdown_lines.append("Traceback:")
                                    for line in traceback:
                                        # Remove ANSI color codes
                                        clean_line = NotebookExporter._remove_ansi_codes(line)
                                        markdown_lines.append(f"  {clean_line}")

                                markdown_lines.append("```")
                                markdown_lines.append("")
                            else:
                                # Fallback: error as text (might have full traceback in 'text' field)
                                error_text = output.get('text', '')
                                if error_text:
                                    # Remove ANSI codes and render as error block
                                    clean_text = NotebookExporter._remove_ansi_codes(error_text)
                                    markdown_lines.append("")
                                    markdown_lines.append("```error")
                                    markdown_lines.append(clean_text.rstrip())
                                    markdown_lines.append("```")
                                    markdown_lines.append("")

                        elif output_type == 'execute_result':
                            # Execution result - use code block
                            text = output.get('text', '')
                            if text:
                                markdown_lines.append("")
                                markdown_lines.append("```")
                                markdown_lines.append(text.rstrip())
                                markdown_lines.append("```")
                                markdown_lines.append("")

                        elif output_type == 'image':
                            # Image output (base64 encoded)
                            image_data = output.get('text', '')
                            if image_data.startswith('data:image/'):
                                # Extract format and render as markdown image
                                markdown_lines.append("")
                                markdown_lines.append(f"![Output Image]({image_data})")
                                markdown_lines.append("")
                            else:
                                # Fallback: treat as text
                                markdown_lines.append("<output>")
                                markdown_lines.append(image_data)
                                markdown_lines.append("</output>")

                        elif output_type == 'html':
                            # HTML output (like pandas DataFrame) - render directly for markdown viewers
                            html_text = output.get('text', '')
                            if html_text:
                                markdown_lines.append("")
                                markdown_lines.append(html_text.rstrip())
                                markdown_lines.append("")

                        elif output_type == 'display_data':
                            # Display data (can contain images or other data)
                            data = output.get('data', {})
                            if isinstance(data, dict):
                                # Check for image data
                                if 'image/png' in data:
                                    png_data = data['image/png']
                                    if not png_data.startswith('data:image/'):
                                        png_data = f"data:image/png;base64,{png_data}"
                                    markdown_lines.append("")
                                    markdown_lines.append(f"![Output Image]({png_data})")
                                    markdown_lines.append("")
                                elif 'image/jpeg' in data:
                                    jpeg_data = data['image/jpeg']
                                    if not jpeg_data.startswith('data:image/'):
                                        jpeg_data = f"data:image/jpeg;base64,{jpeg_data}"
                                    markdown_lines.append("")
                                    markdown_lines.append(f"![Output Image]({jpeg_data})")
                                    markdown_lines.append("")
                                elif 'text/html' in data:
                                    html_text = data['text/html']
                                    markdown_lines.append("")
                                    markdown_lines.append(html_text.rstrip())
                                    markdown_lines.append("")
                                elif 'text/plain' in data:
                                    plain_text = data['text/plain']
                                    markdown_lines.append("")
                                    markdown_lines.append("```")
                                    markdown_lines.append(plain_text.rstrip())
                                    markdown_lines.append("```")
                                    markdown_lines.append("")
                            else:
                                # Fallback for non-dict data
                                markdown_lines.append("")
                                markdown_lines.append("```")
                                markdown_lines.append(str(data).rstrip())
                                markdown_lines.append("```")
                                markdown_lines.append("")

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
