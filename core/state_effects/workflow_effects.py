"""
Workflow Effects - Workflow-level state effect handlers
Handles: workflow_completed, workflow_update_pending
"""

from typing import Any


def effect_workflow_update_pending(state_machine, payload: Any = None):
    """
    Effect for WORKFLOW_UPDATE_PENDING state.

    Args:
        state_machine: Reference to WorkflowStateMachine instance
        payload: Optional payload data
    """
    state_machine.info(f"[FSM Effect] WORKFLOW_UPDATE_PENDING - auto-confirming workflow update")

    # Auto-confirm the workflow update (can be made interactive later)
    # For now, we automatically accept all workflow updates from the API
    from core.events import WorkflowEvent
    state_machine.transition(WorkflowEvent.UPDATE_WORKFLOW_CONFIRMED)


def effect_workflow_completed(state_machine, payload: Any = None):
    """
    Effect for WORKFLOW_COMPLETED state - cleanup resources.

    Args:
        state_machine: Reference to WorkflowStateMachine instance
        payload: Optional payload data
    """
    state_machine.info(f"[FSM Effect] WORKFLOW_COMPLETED - cleaning up resources")

    # Save notebook to file
    if state_machine.notebook_manager and state_machine.script_store and hasattr(state_machine.script_store, 'notebook_store'):
        try:
            notebook_data = state_machine.script_store.notebook_store.to_dict()
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"workflow_{timestamp}.json"
            saved_path = state_machine.notebook_manager.save_notebook(notebook_data, filename=filename)
            state_machine.info(f"[FSM Effect] Notebook saved to: {saved_path}")
        except Exception as e:
            state_machine.error(f"[FSM Effect] Failed to save notebook: {e}", exc_info=True)

    # Close aiohttp session
    try:
        from utils.api_client import workflow_api_client
        workflow_api_client.close_sync()
        state_machine.info("[FSM Effect] API client session closed successfully")
    except Exception as e:
        state_machine.warning(f"[FSM Effect] Error during session cleanup: {e}")
