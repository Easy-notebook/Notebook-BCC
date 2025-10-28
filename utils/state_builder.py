"""
State Builder - Helper functions for building API state payloads
Eliminates code duplication in state effect handlers
"""

from typing import Dict, Any, Optional


def build_api_state(
    state_machine,
    require_progress_info: bool = True
) -> Dict[str, Any]:
    """
    Build the complete state dictionary for API calls.

    This function consolidates the repeated state construction logic
    that appears in multiple state effect handlers.

    Args:
        state_machine: Reference to WorkflowStateMachine instance
        require_progress_info: If True, raises RuntimeError when progress_info is None
                             If False, omits progress_info when None

    Returns:
        Dictionary containing:
        - All AI context data (variables, todo_list, etc.)
        - Notebook data (if available)
        - Progress info (hierarchical stage/step/behavior tracking)
        - FSM tracking (current state and transition history)

    Raises:
        RuntimeError: If require_progress_info=True and progress_info is None
    """
    if not state_machine.ai_context_store:
        raise RuntimeError("AI context store not available")

    # Get current state from AI context store
    current_state = state_machine.ai_context_store.get_context().to_dict()

    # Add notebook data if available
    if (state_machine.script_store and
        hasattr(state_machine.script_store, 'notebook_store') and
        state_machine.script_store.notebook_store):
        current_state['notebook'] = state_machine.script_store.notebook_store.to_dict()

    # Add hierarchical progress info (POMDP observation)
    progress_info = state_machine.get_progress_info()
    if progress_info:
        current_state['progress_info'] = progress_info
    elif require_progress_info:
        raise RuntimeError("Failed to generate progress_info for POMDP observation")

    # Add FSM tracking to context
    current_state['FSM'] = {
        'state': state_machine.current_state.value,
        'transition': [entry.to_dict() for entry in state_machine.execution_context.execution_history]
    }

    return current_state


def build_behavior_feedback(state_machine) -> Dict[str, Any]:
    """
    Build behavior feedback to send to the server.

    Args:
        state_machine: Reference to WorkflowStateMachine instance

    Returns:
        Dictionary with behavior execution statistics:
        - behavior_id: Current behavior ID
        - actions_executed: Number of actions executed
        - actions_succeeded: Number of successful actions
        - sections_added: Number of section-type actions
        - last_action_result: Result of last action (default: "success")
    """
    ctx = state_machine.execution_context.workflow_context

    # Count sections added
    sections_added = 0
    if ctx.current_behavior_actions:
        for action in ctx.current_behavior_actions:
            if isinstance(action, dict):
                metadata = action.get('metadata', {})
                if metadata.get('is_section'):
                    sections_added += 1

    # Get last action result
    last_action_result = "success"  # Default to success

    feedback = {
        'behavior_id': ctx.current_behavior_id,
        'actions_executed': len(ctx.current_behavior_actions),
        'actions_succeeded': len(ctx.current_behavior_actions),
        'sections_added': sections_added,
        'last_action_result': last_action_result
    }

    return feedback


__all__ = [
    'build_api_state',
    'build_behavior_feedback',
]
