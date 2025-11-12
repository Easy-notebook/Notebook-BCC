"""
Code Handlers - Manage code execution and effects
Handles: exec_code, set_effect_as_thinking
"""

from typing import Any, Optional
from models.action import ExecutionStep
from models.cell import CellType


# =====================================================================
# Handler Functions
# =====================================================================

def handle_exec_code(script_store, step: ExecutionStep) -> Any:
    """
    Handle EXEC_CODE type.

    Args:
        script_store: Reference to ScriptStore instance
        step: Execution step containing code execution details

    Returns:
        Execution result or None
    """
    try:
        if not step or not step.codecell_id:
            if hasattr(script_store, 'warning'):
                script_store.warning("[CodeHandler] EXEC_CODE requires codecell_id")
            return None

        target_id = (script_store.last_added_action_id if step.codecell_id == "lastAddedCellId"
                     else step.codecell_id)

        if not target_id:
            if hasattr(script_store, 'warning'):
                script_store.warning("[CodeHandler] No valid cell ID for code execution")
            return None

        if hasattr(script_store, 'info'):
            script_store.info(f"[CodeHandler] Executing code: {target_id}")

        return script_store.exec_code_cell(
            target_id,
            step.need_output if step.need_output is not None else True,
            step.auto_debug if step.auto_debug is not None else False
        )

    except Exception as e:
        if hasattr(script_store, 'error'):
            script_store.error(f"[CodeHandler] Error handling EXEC_CODE: {e}", exc_info=True)
        return None


def handle_set_effect_thinking(script_store, step: ExecutionStep) -> bool:
    """
    Handle set_effect_as_thinking type.

    Args:
        script_store: Reference to ScriptStore instance
        step: Execution step

    Returns:
        True if successful, False otherwise
    """
    try:
        script_store.set_effect_as_thinking(step.thinking_text or "finished thinking")
        return True
    except Exception as e:
        if hasattr(script_store, 'error'):
            script_store.error(f"[CodeHandler] Error handling set_effect_thinking: {e}", exc_info=True)
        return False


# =====================================================================
# Helper Method (Called by ScriptStore)
# =====================================================================

def exec_code_cell(
    script_store,
    codecell_id: str,
    need_output: bool = True,
    auto_debug: bool = False
) -> Any:
    """
    Execute a code cell.

    Args:
        script_store: Reference to ScriptStore instance
        codecell_id: The cell ID to execute
        need_output: Whether to capture output
        auto_debug: Whether to auto-debug on error

    Returns:
        Execution result
    """
    if not codecell_id or not script_store.code_executor:
        if hasattr(script_store, 'error'):
            script_store.error("[CodeHandler] No code executor available")
        return None

    try:
        if hasattr(script_store, 'info'):
            script_store.info(f"[CodeHandler] Executing code cell: {codecell_id}")

        # Get cell
        cell = script_store.notebook_store.get_cell(codecell_id) if script_store.notebook_store else None
        if not cell:
            if hasattr(script_store, 'error'):
                script_store.error(f"[CodeHandler] Cell not found: {codecell_id}")
            return None

        # Execute code
        result = script_store.code_executor.execute(cell.content, codecell_id=codecell_id)

        if result.get('success'):
            # Add outputs to cell
            if script_store.notebook_store and result.get('outputs'):
                script_store.notebook_store.clear_cell_outputs(codecell_id)
                for output in result['outputs']:
                    script_store.notebook_store.add_cell_output(codecell_id, output)

                # Update execution count (critical!)
                script_store.notebook_store.execution_count += 1
                cell = script_store.notebook_store.get_cell(codecell_id)
                if cell:
                    cell.execution_count = script_store.notebook_store.execution_count

            # Add to effect context
            if script_store.ai_context_store and result.get('outputs'):
                for output in result['outputs']:
                    output_text = output.content or output.text or str(output)
                    script_store.ai_context_store.add_effect(output_text)

            return result.get('outputs')
        else:
            error = result.get('error', 'Unknown error')
            if hasattr(script_store, 'error'):
                script_store.error(f"[CodeHandler] Code execution failed: {error}")
            if auto_debug:
                if hasattr(script_store, 'info'):
                    script_store.info(f"[CodeHandler] Auto-debug triggered for cell: {codecell_id}")
            return error

    except Exception as e:
        if hasattr(script_store, 'error'):
            script_store.error(f"[CodeHandler] Error executing cell: {e}", exc_info=True)
        return None


def set_effect_as_thinking(script_store, thinking_text: str = "finished thinking") -> None:
    """
    Mark the last code cell as having finished thinking.

    Args:
        script_store: Reference to ScriptStore instance
        thinking_text: Text to mark the thinking process
    """
    if not script_store.notebook_store:
        return

    last_cell = script_store.notebook_store.get_last_cell()
    if last_cell and last_cell.type == CellType.CODE:
        metadata = {
            **last_cell.metadata,
            'finished_thinking': True,
            'thinkingText': thinking_text
        }
        script_store.notebook_store.update_cell_metadata(last_cell.id, metadata)

        # Update action metadata
        for action in script_store.actions:
            if action.id == last_cell.id:
                action.metadata.finished_thinking = True
                action.metadata.thinking_text = thinking_text
                break

        if hasattr(script_store, 'info'):
            script_store.info(f"[CodeHandler] Set effect as thinking for cell: {last_cell.id}")
