"""
Notebook commands - handles notebook-related operations.
"""


class NotebookCommands:
    """
    Handles notebook-related commands: show, list, export, export-markdown.
    """

    def cmd_show(self, args):
        """Show notebook content."""
        if args.notebook:
            # Load from file
            notebook_data = self.notebook_manager.load_notebook(args.notebook)
            if not notebook_data:
                print(f"Error: Notebook not found: {args.notebook}")
                return

            cells = [cell for cell in self.notebook_store.cells]
            self.notebook_store.from_dict(notebook_data)
        else:
            notebook_data = self.notebook_store.to_dict()

        # Render
        print(self.cell_renderer.render_notebook_summary(notebook_data))

        cells = notebook_data.get('cells', [])
        if cells:
            from models.cell import Cell
            cell_objects = [Cell.from_dict(c) for c in cells]
            print(self.cell_renderer.render_cells(cell_objects))
        else:
            print("No cells to display.")

    def cmd_list(self, _args=None):
        """List all notebooks."""
        notebooks = self.notebook_manager.list_notebooks()

        print(f"\nNotebooks ({len(notebooks)})")
        print("=" * 60)

        if notebooks:
            for nb in notebooks:
                print(f"  - {nb}")
        else:
            print("  No notebooks found.")

        print()

    def cmd_export(self, args):
        """Export notebook to markdown."""
        notebook_data = self.notebook_manager.load_notebook(args.notebook)

        if not notebook_data:
            print(f"Error: Notebook not found: {args.notebook}")
            return

        output_path = self.notebook_manager.export_to_markdown(
            notebook_data,
            output_file=args.output
        )

        print(f"Exported to: {output_path}")

    def cmd_export_markdown(self, args):
        """Export notebook from state file to markdown."""
        from utils.notebook_exporter import NotebookExporter

        print(f"\nLoading state file: {args.state_file}")

        # Export to markdown
        markdown = NotebookExporter.export_from_state_file(
            args.state_file,
            args.output
        )

        if args.output:
            print(f"Markdown exported to: {args.output}")
        else:
            print("\n" + "="*60)
            print(markdown)
            print("="*60)
