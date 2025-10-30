"""
Workflow Handlers - Manage workflow metadata
Handles: update_title

Note: Other workflow actions (update_workflow, update_stage_steps, end_phase)
are now handled by Planning API via context_update.
"""

from models.action import ExecutionStep
from .content_handlers import clean_content


# =====================================================================
# Handler Functions
# =====================================================================

def handle_update_title(script_store, step: ExecutionStep) -> bool:
    """
    Handle UPDATE_TITLE type.

    Args:
        script_store: Reference to ScriptStore instance
        step: Execution step containing new title

    Returns:
        True if successful, False otherwise
    """
    try:
        if not step or not step.title:
            if hasattr(script_store, 'warning'):
                script_store.warning("[WorkflowHandler] UPDATE_TITLE requires title")
            return False

        cleaned_title = clean_content(step.title, 'text')
        update_title(script_store, cleaned_title)
        return True

    except Exception as e:
        if hasattr(script_store, 'error'):
            script_store.error(f"[WorkflowHandler] Error handling UPDATE_TITLE: {e}", exc_info=True)
        return False


# =====================================================================
# Helper Functions
# =====================================================================

def update_title(script_store, title: str) -> None:
    """
    Update notebook title.

    Args:
        script_store: Reference to ScriptStore instance
        title: New title for the notebook
    """
    if script_store.notebook_store:
        script_store.notebook_store.update_title(title)
        if hasattr(script_store, 'info'):
            script_store.info(f"[WorkflowHandler] Updated title: {title}")
