"""
Thinking Handlers - Manage thinking process visualization
Handles: is_thinking, finish_thinking
"""

import uuid
from typing import Optional
from models.action import ExecutionStep, ScriptAction
from models.cell import CellType


# =====================================================================
# Handler Functions
# =====================================================================

def handle_is_thinking(script_store, step: ExecutionStep) -> Optional[str]:
    """
    Handle IS_THINKING type.

    Args:
        script_store: Reference to ScriptStore instance
        step: Execution step containing thinking information

    Returns:
        Action ID if successful, None otherwise
    """
    try:
        action_id = str(uuid.uuid4())
        script_store.add_action(ScriptAction(
            id=action_id,
            type='thinking',
            content='',
            text_array=step.text_array or [],
            agent_name=step.agent_name or 'AI',
            custom_text=step.custom_text
        ))
        return action_id

    except Exception as e:
        if hasattr(script_store, 'error'):
            script_store.error(f"[ThinkingHandler] Error handling IS_THINKING: {e}", exc_info=True)
        return None


def handle_finish_thinking(script_store, step: ExecutionStep) -> bool:
    """
    Handle FINISH_THINKING type.

    Args:
        script_store: Reference to ScriptStore instance
        step: Execution step

    Returns:
        True if successful, False otherwise
    """
    try:
        finish_thinking(script_store)
        return True
    except Exception as e:
        if hasattr(script_store, 'error'):
            script_store.error(f"[ThinkingHandler] Error handling FINISH_THINKING: {e}", exc_info=True)
        return False


# =====================================================================
# Helper Functions
# =====================================================================

def finish_thinking(script_store) -> None:
    """
    Remove the last thinking cell.

    Args:
        script_store: Reference to ScriptStore instance
    """
    if not script_store.notebook_store:
        return

    thinking_cells = script_store.notebook_store.get_cells_by_type(CellType.THINKING)
    if thinking_cells:
        last_thinking = thinking_cells[-1]
        script_store.notebook_store.delete_cell(last_thinking.id)
        script_store.actions = [a for a in script_store.actions if a.id != last_thinking.id]
        if hasattr(script_store, 'info'):
            script_store.info(f"[ThinkingHandler] Finished thinking, removed cell: {last_thinking.id}")
