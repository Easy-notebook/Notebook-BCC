"""
FinishThinkingAction - Removes the thinking indicator
"""

from models.action import ExecutionStep
from models.cell import CellType
from ..base import ActionBase, action


@action('finish_thinking')
class FinishThinkingAction(ActionBase):
    """Handle FINISH_THINKING type - removes the thinking indicator."""

    def execute(self, step: ExecutionStep) -> bool:
        """Execute finish thinking action."""
        self._finish_thinking()
        return True

    def _finish_thinking(self) -> None:
        """Remove the last thinking cell."""
        if not self.notebook_store:
            return

        thinking_cells = self.notebook_store.get_cells_by_type(CellType.THINKING)
        if thinking_cells:
            last_thinking = thinking_cells[-1]
            self.notebook_store.delete_cell(last_thinking.id)
            self.script_store.actions = [a for a in self.script_store.actions if a.id != last_thinking.id]
            self.script_store.info(f"[FinishThinkingAction] Removed cell: {last_thinking.id}")
