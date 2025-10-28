"""
Workflow Handlers - Manage workflow structure and metadata
Handles: update_title, complete_step, update_workflow, update_step_list
"""

from typing import Optional, Dict, Any
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


def handle_complete_step(script_store, step: ExecutionStep) -> bool:
    """
    Handle COMPLETE_STEP type.

    Args:
        script_store: Reference to ScriptStore instance
        step: Execution step

    Returns:
        True always (command acknowledgment)
    """
    if hasattr(script_store, 'info'):
        script_store.info("[WorkflowHandler] Received command to complete step")
    return True


def handle_update_workflow(script_store, step: ExecutionStep) -> Optional[Dict[str, Any]]:
    """
    Handle UPDATE_WORKFLOW type.

    Args:
        script_store: Reference to ScriptStore instance
        step: Execution step containing workflow update

    Returns:
        Update status dictionary or None
    """
    try:
        if hasattr(script_store, 'info'):
            script_store.info("[WorkflowHandler] Workflow update requested")

        if not step or not step.updated_workflow:
            if hasattr(script_store, 'warning'):
                script_store.warning("[WorkflowHandler] UPDATE_WORKFLOW requires updated_workflow")
            return None

        script_store.pending_workflow_update = step.updated_workflow
        workflow_name = step.updated_workflow.get('name', 'Unknown')
        if hasattr(script_store, 'info'):
            script_store.info(f"[WorkflowHandler] Stored pending workflow update: {workflow_name}")

        # Initialize workflow_progress in AI context
        if script_store.ai_context_store:
            script_store.ai_context_store.initialize_workflow_progress(step.updated_workflow)
            if hasattr(script_store, 'info'):
                script_store.info("[WorkflowHandler] Initialized workflow_progress in AI context")

        return {'workflow_update_pending': True, 'workflow_name': workflow_name}

    except Exception as e:
        if hasattr(script_store, 'error'):
            script_store.error(f"[WorkflowHandler] Error handling UPDATE_WORKFLOW: {e}", exc_info=True)
        return None


def handle_update_step_list(script_store, step: ExecutionStep) -> bool:
    """
    Handle UPDATE_STEP_LIST type.

    Args:
        script_store: Reference to ScriptStore instance
        step: Execution step containing stage update info

    Returns:
        True if successful, False otherwise
    """
    try:
        if not step or not step.stage_id:
            if hasattr(script_store, 'warning'):
                script_store.warning("[WorkflowHandler] UPDATE_STEP_LIST requires stage_id")
            return False

        if hasattr(script_store, 'info'):
            script_store.info(f"[WorkflowHandler] Updating steps for stage: {step.stage_id}")
        return True

    except Exception as e:
        if hasattr(script_store, 'error'):
            script_store.error(f"[WorkflowHandler] Error handling UPDATE_STEP_LIST: {e}", exc_info=True)
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
