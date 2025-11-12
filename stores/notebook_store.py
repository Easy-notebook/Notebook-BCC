"""
Notebook Store
Manages notebook cells and their lifecycle.
"""

from silantui import ModernLogger
from typing import List, Optional, Dict, Any
from models.cell import Cell, CellType, CellOutput


class NotebookStore(ModernLogger):
    """
    Notebook Store for managing cells.
    Handles cell creation, updates, and lifecycle management.
    """

    def __init__(self):
        super().__init__("NotebookStore")
        self.cells: List[Cell] = []
        self.title: str = "Untitled Notebook"
        self.execution_count: int = 0
        self.notebook_id: Optional[str] = None  # Explicitly initialize notebook_id

        # Track cell updates for context
        self._cell_snapshots: Dict[str, Dict[str, Any]] = {}  # cell_id -> snapshot
        self._updated_cells: set = set()  # Track which cells were updated

    # ==============================================
    # Cell Management
    # ==============================================

    def add_cell(self, cell_data: Dict[str, Any]) -> Cell:
        """
        Add a new cell to the notebook.

        Args:
            cell_data: Dictionary containing cell configuration

        Returns:
            The created Cell instance
        """
        cell_id = cell_data.get('id')
        cell_type = CellType(cell_data.get('type', 'markdown'))

        # Convert dictionary outputs to CellOutput objects
        raw_outputs = cell_data.get('outputs', [])
        outputs = [CellOutput(**out) if isinstance(out, dict) else out
                   for out in raw_outputs]

        cell = Cell(
            id=cell_id,
            type=cell_type,
            content=cell_data.get('content', ''),
            outputs=outputs,
            enable_edit=cell_data.get('enableEdit', cell_type != CellType.THINKING),
            phase_id=cell_data.get('phaseId'),
            description=cell_data.get('description', ''),
            metadata=cell_data.get('metadata', {}),
            language=cell_data.get('language', 'python'),
            agent_name=cell_data.get('agentName', 'AI'),
            custom_text=cell_data.get('customText'),
            text_array=cell_data.get('textArray', []),
            use_workflow_thinking=cell_data.get('useWorkflowThinking', False),
            could_visible_in_writing_mode=cell_data.get('couldVisibleInWritingMode', True),
        )

        self.cells.append(cell)

        # Create snapshot for the newly added cell
        self._create_snapshot(cell)

        # Mark as updated (new cell is considered updated)
        self._updated_cells.add(cell_id)

        self.info(f"[NotebookStore] Added cell: {cell_id} (type: {cell_type.value})")

        return cell

    def get_cell(self, cell_id: str) -> Optional[Cell]:
        """Get a cell by ID."""
        for cell in self.cells:
            if cell.id == cell_id:
                return cell
        return None

    def update_cell(self, cell_id: str, content: str) -> bool:
        """Update a cell's content."""
        cell = self.get_cell(cell_id)
        if cell:
            # Check if content actually changed
            if cell.content != content:
                cell.content = content
                self._mark_as_updated(cell_id)
                self.info(f"[NotebookStore] Updated cell content: {cell_id}")
            return True
        return False

    def update_cell_metadata(self, cell_id: str, metadata: Dict[str, Any]) -> bool:
        """Update a cell's metadata."""
        cell = self.get_cell(cell_id)
        if cell:
            cell.metadata.update(metadata)
            self._mark_as_updated(cell_id)
            self.info(f"[NotebookStore] Updated cell metadata: {cell_id}")
            return True
        return False

    def delete_cell(self, cell_id: str) -> bool:
        """Delete a cell."""
        for i, cell in enumerate(self.cells):
            if cell.id == cell_id:
                self.cells.pop(i)
                self.info(f"[NotebookStore] Deleted cell: {cell_id}")
                return True
        return False

    def clear_cells(self):
        """Clear all cells."""
        self.cells = []
        self.info("[NotebookStore] Cleared all cells")

    # ==============================================
    # Cell Output Management
    # ==============================================

    def add_cell_output(self, cell_id: str, output: CellOutput) -> bool:
        """Add an output to a cell."""
        cell = self.get_cell(cell_id)
        if cell:
            cell.add_output(output)
            self._mark_as_updated(cell_id)
            self.info(f"[NotebookStore] Added output to cell: {cell_id}")
            return True
        return False

    def clear_cell_outputs(self, cell_id: str) -> bool:
        """Clear all outputs from a cell."""
        cell = self.get_cell(cell_id)
        if cell:
            # Only mark as updated if there were outputs to clear
            had_outputs = len(cell.outputs) > 0
            cell.clear_outputs()
            if had_outputs:
                self._mark_as_updated(cell_id)
            self.info(f"[NotebookStore] Cleared outputs for cell: {cell_id}")
            return True
        return False

    # ==============================================
    # Title Management
    # ==============================================

    def update_title(self, title: str):
        """Update the notebook title."""
        self.title = title
        self.info(f"[NotebookStore] Updated title: {title}")

    def get_title(self) -> str:
        """Get the notebook title."""
        return self.title

    # ==============================================
    # Execution Count
    # ==============================================

    def increment_execution_count(self) -> int:
        """Increment and return the execution count."""
        self.execution_count += 1
        return self.execution_count

    # ==============================================
    # Query Methods
    # ==============================================

    def get_cells_by_type(self, cell_type: CellType) -> List[Cell]:
        """Get all cells of a specific type."""
        return [cell for cell in self.cells if cell.type == cell_type]

    def get_cells_by_phase(self, phase_id: str) -> List[Cell]:
        """Get all cells associated with a phase/step."""
        return [cell for cell in self.cells if cell.phase_id == phase_id]

    def get_last_cell(self) -> Optional[Cell]:
        """Get the last cell in the notebook."""
        return self.cells[-1] if self.cells else None

    def get_cell_count(self) -> int:
        """Get the total number of cells."""
        return len(self.cells)

    # ==============================================
    # Update Tracking (for Context)
    # ==============================================

    def _create_snapshot(self, cell: Cell):
        """Create a snapshot of the cell's current state."""
        self._cell_snapshots[cell.id] = {
            'content': cell.content,
            'outputs_count': len(cell.outputs),
            'metadata': dict(cell.metadata)
        }

    def _mark_as_updated(self, cell_id: str):
        """Mark a cell as updated."""
        self._updated_cells.add(cell_id)
        self.info(f"[NotebookStore] Marked cell as updated: {cell_id}")

    def clear_update_tracking(self):
        """
        Clear update tracking and create new snapshots.
        Call this after sending state to API to reset tracking.
        """
        # Update all snapshots to current state
        for cell in self.cells:
            self._create_snapshot(cell)

        # Clear updated cells set
        self._updated_cells.clear()
        self.info("[NotebookStore] Cleared update tracking")

    def get_updated_cell_ids(self) -> List[str]:
        """Get list of cell IDs that have been updated."""
        return list(self._updated_cells)

    # ==============================================
    # Serialization
    # ==============================================

    def to_dict(self, include_update_status: bool = True) -> Dict[str, Any]:
        """
        Convert notebook to dictionary for serialization.

        Args:
            include_update_status: Whether to include isUpdate flag in cells

        Returns:
            Dictionary representation of the notebook
        """
        cells_data = []
        for cell in self.cells:
            cell_dict = cell.to_dict()

            # Add isUpdate flag if requested
            if include_update_status:
                cell_dict['isUpdate'] = cell.id in self._updated_cells

            cells_data.append(cell_dict)

        # Build base dict with required fields
        result = {
            'title': self.title,
            'cells': cells_data,
            'execution_count': self.execution_count,
            'cell_count': len(self.cells),
        }

        # Add optional/dynamic fields if they exist
        if self.notebook_id:
            result['notebook_id'] = self.notebook_id

        # Add last cell info if cells exist
        if self.cells:
            last_cell = self.cells[-1]
            result['last_cell_type'] = last_cell.type.value
            # Get last output if it's a code cell with outputs
            if last_cell.type == CellType.CODE and last_cell.outputs:
                last_output = last_cell.outputs[-1]
                if hasattr(last_output, 'to_dict'):
                    result['last_output'] = last_output.to_dict()
                elif isinstance(last_output, dict):
                    result['last_output'] = last_output

        return result

    def from_dict(self, data: Dict[str, Any]):
        """Load notebook from dictionary."""
        self.title = data.get('title', 'Untitled Notebook')
        self.execution_count = data.get('execution_count', 0)
        self.notebook_id = data.get('notebook_id')  # Load notebook_id if present
        self.cells = [Cell.from_dict(cell_data) for cell_data in data.get('cells', [])]
        self.info(f"[NotebookStore] Loaded {len(self.cells)} cells from dict, notebook_id={self.notebook_id}")
