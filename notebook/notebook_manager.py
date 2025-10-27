"""
Notebook Manager
Manages notebook files and persistence.
"""

import json
from silantui import ModernLogger
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime



class NotebookManager(ModernLogger):
    """
    Manages notebook file operations and persistence.
    """

    def __init__(self, notebooks_dir: str = "notebooks"):
        """
        Initialize the manager.

        Args:
            notebooks_dir: Directory to store notebooks
        """
        super().__init__("NotebookManager")
        self.notebooks_dir = Path(notebooks_dir)
        self.notebooks_dir.mkdir(parents=True, exist_ok=True)
        self.info(f"[NotebookManager] Initialized with dir: {self.notebooks_dir}")

    def save_notebook(
        self,
        notebook_data: Dict[str, Any],
        notebook_id: str = None,
        filename: str = None
    ) -> Path:
        """
        Save a notebook to a file.

        Args:
            notebook_data: The notebook data to save
            notebook_id: Optional notebook ID
            filename: Optional custom filename

        Returns:
            Path to the saved notebook
        """
        if not filename:
            if notebook_id:
                filename = f"{notebook_id}.json"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"notebook_{timestamp}.json"

        filepath = self.notebooks_dir / filename

        # Add metadata
        notebook_data['saved_at'] = datetime.now().isoformat()
        notebook_data['notebook_id'] = notebook_id or filename.replace('.json', '')

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(notebook_data, f, indent=2, ensure_ascii=False)

        self.info(f"[NotebookManager] Saved notebook: {filepath}")
        return filepath

    def load_notebook(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Load a notebook from a file.

        Args:
            filename: The notebook filename

        Returns:
            Notebook data or None if not found
        """
        filepath = self.notebooks_dir / filename

        if not filepath.exists():
            self.error(f"[NotebookManager] Notebook not found: {filepath}")
            return None

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                notebook_data = json.load(f)

            self.info(f"[NotebookManager] Loaded notebook: {filepath}")
            return notebook_data
        except Exception as e:
            self.error(f"[NotebookManager] Error loading notebook: {e}", exc_info=True)
            return None

    def list_notebooks(self) -> list:
        """
        List all notebooks in the directory.

        Returns:
            List of notebook filenames
        """
        notebooks = list(self.notebooks_dir.glob("*.json"))
        self.info(f"[NotebookManager] Found {len(notebooks)} notebooks")
        return [nb.name for nb in notebooks]

    def delete_notebook(self, filename: str) -> bool:
        """
        Delete a notebook file.

        Args:
            filename: The notebook filename

        Returns:
            True if deleted successfully
        """
        filepath = self.notebooks_dir / filename

        if not filepath.exists():
            self.error(f"[NotebookManager] Notebook not found: {filepath}")
            return False

        try:
            filepath.unlink()
            self.info(f"[NotebookManager] Deleted notebook: {filepath}")
            return True
        except Exception as e:
            self.error(f"[NotebookManager] Error deleting notebook: {e}", exc_info=True)
            return False

    def export_to_markdown(
        self,
        notebook_data: Dict[str, Any],
        output_file: Optional[str] = None
    ) -> Path:
        """
        Export notebook to markdown format.

        Args:
            notebook_data: The notebook data
            output_file: Optional output filename

        Returns:
            Path to the markdown file
        """
        if not output_file:
            notebook_id = notebook_data.get('notebook_id', 'notebook')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"{notebook_id}_{timestamp}.md"

        filepath = self.notebooks_dir / output_file

        # Build markdown content
        markdown_lines = []

        # Title
        title = notebook_data.get('title', 'Untitled Notebook')
        markdown_lines.append(f"# {title}\n")
        markdown_lines.append(f"*Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        markdown_lines.append("---\n\n")

        # Cells
        cells = notebook_data.get('cells', [])
        for cell in cells:
            cell_type = cell.get('type', 'markdown')
            content = cell.get('content', '')

            if cell_type == 'markdown':
                markdown_lines.append(content)
                markdown_lines.append("\n\n")
            elif cell_type == 'code':
                markdown_lines.append(f"```{cell.get('language', 'python')}\n")
                markdown_lines.append(content)
                markdown_lines.append("\n```\n\n")

                # Add outputs if present
                outputs = cell.get('outputs', [])
                if outputs:
                    markdown_lines.append("**Output:**\n")
                    markdown_lines.append("```\n")
                    for output in outputs:
                        output_text = output.get('content') or output.get('text', '')
                        markdown_lines.append(output_text)
                    markdown_lines.append("\n```\n\n")
            elif cell_type == 'thinking':
                markdown_lines.append(f"> **{cell.get('agent_name', 'AI')} is thinking...**\n\n")

        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(markdown_lines)

        self.info(f"[NotebookManager] Exported to markdown: {filepath}")
        return filepath
