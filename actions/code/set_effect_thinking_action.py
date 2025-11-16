"""
SetEffectThinkingAction - Marks the last code cell as having finished thinking
"""

from models.action import ExecutionStep
from models.cell import CellType
from ..base import ActionBase, action


@action('set_effect_as_thinking')
class SetEffectThinkingAction(ActionBase):
    """Handle set_effect_as_thinking type."""

    def execute(self, step: ExecutionStep) -> bool:
        """Execute set effect thinking action."""
        thinking_text = step.thinking_text or "finished thinking"
        self._set_effect_as_thinking(thinking_text)
        return True

    def _set_effect_as_thinking(self, thinking_text: str = "finished thinking") -> None:
        """Mark the last code cell as having finished thinking."""
        if not self.notebook_store:
            return

        last_cell = self.notebook_store.get_last_cell()
        if last_cell and last_cell.type == CellType.CODE:
            metadata = {
                **last_cell.metadata,
                'finished_thinking': True,
                'thinkingText': thinking_text
            }
            self.notebook_store.update_cell_metadata(last_cell.id, metadata)

            # Update action metadata
            for action in self.script_store.actions:
                if action.id == last_cell.id:
                    action.metadata.finished_thinking = True
                    action.metadata.thinking_text = thinking_text
                    break

            self.script_store.info(f"[SetEffectThinkingAction] Set effect for cell: {last_cell.id}")
