"""
ExecCodeAction - Executes code cells in the notebook
"""

from typing import Any
from models.action import ExecutionStep
from ..base import ActionBase, action


@action('exec')
class ExecCodeAction(ActionBase):
    """Handle EXEC_CODE type - executes code cells in the notebook."""

    def execute(self, step: ExecutionStep) -> Any:
        """Execute code execution action."""
        if not step or not step.codecell_id:
            self.script_store.warning("[ExecCodeAction] Requires codecell_id")
            return None

        target_id = (self.script_store.last_added_action_id if step.codecell_id == "lastAddedCellId"
                     else step.codecell_id)

        if not target_id:
            self.script_store.warning("[ExecCodeAction] No valid cell ID")
            return None

        self.script_store.info(f"[ExecCodeAction] Executing code: {target_id}")

        return self._exec_code_cell(
            target_id,
            step.need_output if step.need_output is not None else True,
            step.auto_debug if step.auto_debug is not None else False
        )

    def _exec_code_cell(
        self,
        codecell_id: str,
        need_output: bool = True,
        auto_debug: bool = False
    ) -> Any:
        """Execute a code cell."""
        if not codecell_id or not self.code_executor:
            self.script_store.error("[ExecCodeAction] No code executor available")
            return None

        self.script_store.info(f"[ExecCodeAction] Executing cell: {codecell_id}")

        # Get cell
        cell = self.notebook_store.get_cell(codecell_id) if self.notebook_store else None
        if not cell:
            self.script_store.error(f"[ExecCodeAction] Cell not found: {codecell_id}")
            return None

        # Execute code
        result = self.code_executor.execute(cell.content, codecell_id=codecell_id)

        if result.get('success'):
            # Add outputs to cell
            if self.notebook_store and result.get('outputs'):
                self.notebook_store.clear_cell_outputs(codecell_id)
                for output in result['outputs']:
                    self.notebook_store.add_cell_output(codecell_id, output)

                # Update execution count
                self.notebook_store.execution_count += 1
                cell = self.notebook_store.get_cell(codecell_id)
                if cell:
                    cell.execution_count = self.notebook_store.execution_count

            # Add to effect context
            if self.ai_context_store and result.get('outputs'):
                for output in result['outputs']:
                    output_text = output.content or output.text or str(output)
                    self.ai_context_store.add_effect(output_text)

            return result.get('outputs')
        else:
            error = result.get('error', 'Unknown error')
            self.script_store.error(f"[ExecCodeAction] Execution failed: {error}")
            if auto_debug:
                self.script_store.info(f"[ExecCodeAction] Auto-debug triggered")
            return error
