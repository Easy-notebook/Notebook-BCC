"""
Action Effects - Action-level state effect handlers
Handles: action_running, action_completed
"""

from typing import Any


def effect_action_running(state_machine, payload: Any = None):
    """
    Effect for ACTION_RUNNING state.

    Args:
        state_machine: Reference to WorkflowStateMachine instance
        payload: Optional payload data
    """
    state_machine.info(f"[FSM Effect] ACTION_RUNNING")

    ctx = state_machine.execution_context.workflow_context
    if not ctx.current_behavior_actions:
        state_machine.warning("[FSM Effect] No actions to execute")
        from core.events import WorkflowEvent
        state_machine.transition(WorkflowEvent.COMPLETE_ACTION)
        return

    if ctx.current_action_index >= len(ctx.current_behavior_actions):
        state_machine.warning("[FSM Effect] Action index out of bounds")
        from core.events import WorkflowEvent
        state_machine.transition(WorkflowEvent.COMPLETE_ACTION)
        return

    current_action = ctx.current_behavior_actions[ctx.current_action_index]
    state_machine.info(f"[FSM Effect] Executing action #{ctx.current_action_index + 1}: {current_action}")

    # Execute the action via script store
    if state_machine.script_store:
        try:
            result = state_machine.script_store.exec_action(current_action)

            # Check if there's a pending workflow update
            if isinstance(result, dict) and result.get('workflow_update_pending'):
                state_machine.info("[FSM Effect] Detected pending workflow update, transitioning to WORKFLOW_UPDATE_PENDING")
                workflow_update = state_machine.script_store.pending_workflow_update
                if workflow_update:
                    # Trigger workflow update transition with payload
                    from core.events import WorkflowEvent
                    state_machine.transition(WorkflowEvent.UPDATE_WORKFLOW, {'workflowTemplate': workflow_update})
                    return  # Don't complete action yet, will complete after update confirmed

        except Exception as e:
            state_machine.error(f"[FSM Effect] Action execution failed: {e}", exc_info=True)
            from core.events import WorkflowEvent
            state_machine.transition(WorkflowEvent.FAIL, {'error': str(e)})
            return

    # Complete action
    from core.events import WorkflowEvent
    state_machine.transition(WorkflowEvent.COMPLETE_ACTION)


def effect_action_completed(state_machine, payload: Any = None):
    """
    Effect for ACTION_COMPLETED state.

    Args:
        state_machine: Reference to WorkflowStateMachine instance
        payload: Optional payload data
    """
    state_machine.info(f"[FSM Effect] ACTION_COMPLETED")

    ctx = state_machine.execution_context.workflow_context
    next_index = ctx.current_action_index + 1

    from core.events import WorkflowEvent
    if next_index < len(ctx.current_behavior_actions):
        # More actions to execute
        ctx.current_action_index = next_index
        state_machine.transition(WorkflowEvent.NEXT_ACTION)
    else:
        # All actions done, complete behavior
        state_machine.transition(WorkflowEvent.COMPLETE_BEHAVIOR)
