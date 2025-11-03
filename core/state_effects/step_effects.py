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
    Effect for STEP_COMPLETED state.
    Per STATE_MACHINE_PROTOCOL.md: Should call Planning API to determine if stage is complete.

    Args:
        state_machine: Reference to WorkflowStateMachine instance
        payload: Optional payload data
    """
    state_machine.info(f"[FSM Effect] STEP_COMPLETED - Calling Planning API")

    if not state_machine.pipeline_store:
        state_machine.error("[FSM Effect] Pipeline store not available")
        from core.events import WorkflowEvent
        state_machine.transition(WorkflowEvent.FAIL, {'error': 'Pipeline store not available'})
        return

    workflow = state_machine.pipeline_store.workflow_template
    ctx = state_machine.execution_context.workflow_context

    if not workflow or not ctx.current_stage_id or not ctx.current_step_id:
        state_machine.error("[FSM Effect] Invalid context in STEP_COMPLETED")
        from core.events import WorkflowEvent
        state_machine.transition(WorkflowEvent.FAIL, {'error': 'Invalid context'})
        return

    try:
        # Call Planning API to check if stage is complete
        from utils.api_client import workflow_api_client

        current_state = build_api_state(state_machine, require_progress_info=True)

        state_machine.info(f"[FSM Effect] Calling Planning API for stage={ctx.current_stage_id}")

        feedback_response = workflow_api_client.send_feedback_sync(
            stage_id=ctx.current_stage_id,
            step_index=ctx.current_step_id,
            state=current_state
        )

        # Apply context updates
        if 'context_update' in feedback_response:
            from core.state_effects.behavior_effects import _apply_context_update
            _apply_context_update(state_machine, feedback_response['context_update'])

        # Check if stage is complete (targetAchieved at stage level)
        target_achieved = feedback_response.get('targetAchieved', False)

        from core.events import WorkflowEvent
        if target_achieved:
            state_machine.info("[FSM Effect] Stage complete per Planning API")
            state_machine.transition(WorkflowEvent.COMPLETE_STAGE)
        else:
            # Move to next step
            next_step = workflow.get_next_step(ctx.current_stage_id, ctx.current_step_id)
            if next_step:
                ctx.current_step_id = next_step.id
                ctx.reset_for_new_step()
                state_machine.info(f"[FSM Effect] Moving to next step: {next_step.id}")
                state_machine.transition(WorkflowEvent.NEXT_STEP)
            else:
                # No more steps, complete stage
                state_machine.info("[FSM Effect] No more steps, completing stage")
                state_machine.transition(WorkflowEvent.COMPLETE_STAGE)

    except Exception as e:
        state_machine.error(f"[FSM Effect] Failed to call Planning API: {e}", exc_info=True)
        # Fallback: check if there are more steps
        from core.events import WorkflowEvent
        next_step = workflow.get_next_step(ctx.current_stage_id, ctx.current_step_id)
        if next_step:
            ctx.current_step_id = next_step.id
            ctx.reset_for_new_step()
            state_machine.transition(WorkflowEvent.NEXT_STEP)
        else:
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
        # Build API state (progress_info is REQUIRED per OBSERVATION_PROTOCOL.md)
        from utils.api_client import workflow_api_client
        current_state = build_api_state(state_machine, require_progress_info=True)

        state_machine.info(f"[FSM Effect] Calling reflection API for stage={ctx.current_stage_id}, step={ctx.current_step_id}")

        # Call feedback API
        feedback_response = workflow_api_client.send_feedback_sync(
            stage_id=ctx.current_stage_id,
            step_index=ctx.current_step_id,
            state=current_state
        )

        state_machine.info(f"[FSM Effect] Planning API response: {feedback_response}")

        # Apply context updates from Planning API
        if 'context_update' in feedback_response:
            from core.state_effects.behavior_effects import _apply_context_update
            _apply_context_update(state_machine, feedback_response['context_update'])

        # Check if target achieved
        target_achieved = feedback_response.get('targetAchieved', False)

        from core.events import WorkflowEvent
        if target_achieved:
            state_machine.info("[FSM Effect] Target achieved per Planning API, completing step")
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
