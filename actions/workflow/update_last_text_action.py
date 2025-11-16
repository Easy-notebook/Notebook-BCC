"""
UpdateLastTextAction - Updates the content of the last text cell
"""

from models.action import ExecutionStep
from models.cell import CellType
from ..base import ActionBase, action


@action('update_last_text')
class UpdateLastTextAction(ActionBase):
    """Handle update_last_text type - updates the last text cell's content."""

    def execute(self, step: ExecutionStep) -> bool:
        """Execute update last text action."""
        if not step or step.text is None:
            self.script_store.warning("[UpdateLastTextAction] Requires text")
            return False

        self._update_last_text(step.text)
        return True

    def _update_last_text(self, text: str) -> None:
        """Update the last text cell's content."""
        if not self.notebook_store:
            return

        last_cell = self.notebook_store.get_last_cell()
        if last_cell and last_cell.type == CellType.MARKDOWN:
            self.notebook_store.update_cell(last_cell.id, text)
            self.script_store.info(f"[UpdateLastTextAction] Updated last text cell")
