"""
Step Effects - Step-level state effect handlers
Handles: step_running, step_completed
"""

from typing import Any
from utils.state_builder import build_api_state


def effect_step_running(state_machine, payload: Any = None):
    """
    Effect for STEP_RUNNING state.

    Args:
        state_machine: Reference to WorkflowStateMachine instance
        payload: Optional payload data
    """
    state_machine.info(f"[FSM Effect] STEP_RUNNING - Always starting with planning API")

    # Always start with planning API first (new protocol requirement)
    _start_with_planning(state_machine)


def effect_step_completed(state_machine, payload: Any = None):
    """
    Effect for STEP_COMPLETED state - CLIENT-CONTROLLED navigation.

    Args:
        state_machine: Reference to WorkflowStateMachine instance
        payload: Optional payload data
    """
    state_machine.info(f"[FSM Effect] STEP_COMPLETED")

    if not state_machine.pipeline_store:
        state_machine.error("[FSM Effect] Pipeline store not available")
        return

    workflow = state_machine.pipeline_store.workflow_template
    ctx = state_machine.execution_context.workflow_context

    if not workflow or not ctx.current_stage_id or not ctx.current_step_id:
        state_machine.error("[FSM Effect] Invalid context in STEP_COMPLETED")
        return

    # Client-side navigation based on workflow template
    is_last = workflow.is_last_step_in_stage(ctx.current_stage_id, ctx.current_step_id)

    from core.events import WorkflowEvent
    if is_last:
        state_machine.transition(WorkflowEvent.COMPLETE_STAGE)
    else:
        # Move to next step
        next_step = workflow.get_next_step(ctx.current_stage_id, ctx.current_step_id)
        if next_step:
            ctx.current_step_id = next_step.id
            ctx.reset_for_new_step()
            state_machine.transition(WorkflowEvent.NEXT_STEP)
        else:
            state_machine.error("[FSM Effect] No next step found")
            state_machine.transition(WorkflowEvent.COMPLETE_STAGE)


# Helper function
def _start_with_planning(state_machine):
    """Start step with planning API (always called first in new protocol)."""
    state_machine.info("[FSM Effect] Starting with planning API")

    ctx = state_machine.execution_context.workflow_context

    if not ctx.current_stage_id or not ctx.current_step_id:
        state_machine.error("[FSM Effect] Missing stage/step ID for reflection")
        from core.events import WorkflowEvent
        state_machine.transition(WorkflowEvent.FAIL, {'error': 'Missing stage/step ID'})
        return

    if not state_machine.ai_context_store:
        state_machine.error("[FSM Effect] AI context store not available")
        from core.events import WorkflowEvent
        state_machine.transition(WorkflowEvent.FAIL, {'error': 'AI context store not available'})
        return

    try:
        # Build API state (progress_info is optional for planning)
        from utils.api_client import workflow_api_client
        current_state = build_api_state(state_machine, require_progress_info=False)

        state_machine.info(f"[FSM Effect] Calling reflection API for stage={ctx.current_stage_id}, step={ctx.current_step_id}")

        # Call feedback API
        feedback_response = workflow_api_client.send_feedback_sync(
            stage_id=ctx.current_stage_id,
            step_index=ctx.current_step_id,
            state=current_state
        )

        state_machine.info(f"[FSM Effect] Reflection response: {feedback_response}")

        # Check if target achieved
        target_achieved = feedback_response.get('targetAchieved', False)

        from core.events import WorkflowEvent
        if target_achieved:
            state_machine.info("[FSM Effect] Target achieved per reflection API, completing step")
            state_machine.transition(WorkflowEvent.COMPLETE_STEP)
        else:
            # Target not achieved, proceed with behavior generation
            state_machine.info("[FSM Effect] Target not achieved, proceeding with behavior generation")
            state_machine.transition(WorkflowEvent.START_BEHAVIOR)

    except Exception as e:
        state_machine.error(f"[FSM Effect] Failed to call reflection API: {e}", exc_info=True)
        # On error, fall back to behavior generation
        state_machine.warning("[FSM Effect] Falling back to behavior generation due to reflection error")
        from core.events import WorkflowEvent
        state_machine.transition(WorkflowEvent.START_BEHAVIOR)
