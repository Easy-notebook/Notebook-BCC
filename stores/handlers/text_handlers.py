"""
Text Handlers - Manage text cell updates
Handles: update_last_text
"""

from models.action import ExecutionStep
from models.cell import CellType


# =====================================================================
# Handler Functions
# =====================================================================

def handle_update_last_text(script_store, step: ExecutionStep) -> bool:
    """
    Handle update_last_text type.

    Args:
        script_store: Reference to ScriptStore instance
        step: Execution step containing text update

    Returns:
        True if successful, False otherwise
    """
    try:
        if not step or step.text is None:
            if hasattr(script_store, 'warning'):
                script_store.warning("[TextHandler] update_last_text requires text")
            return False

        update_last_text(script_store, step.text)
        return True

    except Exception as e:
        if hasattr(script_store, 'error'):
            script_store.error(f"[TextHandler] Error handling update_last_text: {e}", exc_info=True)
        return False


# =====================================================================
# Helper Functions
# =====================================================================

def update_last_text(script_store, text: str) -> None:
    """
    Update the last text cell's content.

    Args:
        script_store: Reference to ScriptStore instance
        text: New text content
    """
    if not script_store.notebook_store:
        return

    last_cell = script_store.notebook_store.get_last_cell()
    if last_cell and last_cell.type == CellType.MARKDOWN:
        script_store.notebook_store.update_cell(last_cell.id, text)
        if hasattr(script_store, 'info'):
            script_store.info(f"[TextHandler] Updated last text cell")
