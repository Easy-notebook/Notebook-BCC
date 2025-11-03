"""
Stage Effects - Stage-level state effect handlers
Handles: stage_running, stage_completed
"""

from typing import Any


def effect_stage_running(state_machine, payload: Any = None):
    """
    Effect for STAGE_RUNNING state.
    Per STATE_MACHINE_PROTOCOL.md: Should call Planning API to determine which step to start.

    Args:
        state_machine: Reference to WorkflowStateMachine instance
        payload: Optional payload data
    """
    state_machine.info(f"[FSM Effect] STAGE_RUNNING - Calling Planning API")

    if not state_machine.pipeline_store:
        state_machine.error("[FSM Effect] Pipeline store not available")
        from core.events import WorkflowEvent
        state_machine.transition(WorkflowEvent.FAIL, {'error': 'Pipeline store not available'})
        return

    workflow = state_machine.pipeline_store.workflow_template
    ctx = state_machine.execution_context.workflow_context

    if not workflow or not ctx.current_stage_id:
        from core.events import WorkflowEvent
        state_machine.transition(WorkflowEvent.FAIL, {'error': 'No workflow or stage ID'})
        return

    stage = workflow.find_stage(ctx.current_stage_id)
    if not stage or not stage.steps:
        from core.events import WorkflowEvent
        state_machine.transition(WorkflowEvent.FAIL, {'error': f'No steps in stage {ctx.current_stage_id}'})
        return

    # If no step specified, default to first step
    if not ctx.current_step_id:
        ctx.current_step_id = stage.steps[0].id

    try:
        # Call Planning API to check stage status
        from utils.api_client import workflow_api_client
        from utils.state_builder import build_api_state

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

        # Transition to step
        from core.events import WorkflowEvent
        state_machine.transition(WorkflowEvent.START_STEP)

    except Exception as e:
        state_machine.error(f"[FSM Effect] Failed to call Planning API: {e}", exc_info=True)
        # Fallback: proceed to step anyway
        from core.events import WorkflowEvent
        state_machine.transition(WorkflowEvent.START_STEP)


def effect_stage_completed(state_machine, payload: Any = None):
    """
    Effect for STAGE_COMPLETED state.
    Per STATE_MACHINE_PROTOCOL.md: Should call Planning API to determine if workflow is complete.

    Args:
        state_machine: Reference to WorkflowStateMachine instance
        payload: Optional payload data
    """
    state_machine.info(f"[FSM Effect] STAGE_COMPLETED - Calling Planning API")

    if not state_machine.pipeline_store:
        state_machine.error("[FSM Effect] Pipeline store not available")
        from core.events import WorkflowEvent
        state_machine.transition(WorkflowEvent.FAIL, {'error': 'Pipeline store not available'})
        return

    workflow = state_machine.pipeline_store.workflow_template
    ctx = state_machine.execution_context.workflow_context

    if not workflow or not ctx.current_stage_id:
        state_machine.error("[FSM Effect] Invalid context in STAGE_COMPLETED")
        from core.events import WorkflowEvent
        state_machine.transition(WorkflowEvent.FAIL, {'error': 'Invalid context'})
        return

    try:
        # Call Planning API to check if workflow is complete
        from utils.api_client import workflow_api_client
        from utils.state_builder import build_api_state

        current_state = build_api_state(state_machine, require_progress_info=True)

        state_machine.info(f"[FSM Effect] Calling Planning API for workflow completion check")

        feedback_response = workflow_api_client.send_feedback_sync(
            stage_id=ctx.current_stage_id,
            step_index=ctx.current_step_id or "completed",
            state=current_state
        )

        # Apply context updates
        if 'context_update' in feedback_response:
            from core.state_effects.behavior_effects import _apply_context_update
            _apply_context_update(state_machine, feedback_response['context_update'])

        # Check if workflow is complete (targetAchieved at workflow level)
        target_achieved = feedback_response.get('targetAchieved', False)

        from core.events import WorkflowEvent
        if target_achieved:
            state_machine.info("[FSM Effect] Workflow complete per Planning API")
            state_machine.transition(WorkflowEvent.COMPLETE_WORKFLOW)
        else:
            # Move to next stage
            next_stage = workflow.get_next_stage(ctx.current_stage_id)
            if next_stage:
                ctx.current_stage_id = next_stage.id
                ctx.current_step_id = next_stage.steps[0].id if next_stage.steps else None
                ctx.reset_for_new_step()
                state_machine.info(f"[FSM Effect] Moving to next stage: {next_stage.id}")
                state_machine.transition(WorkflowEvent.NEXT_STAGE)
            else:
                # No more stages, complete workflow
                state_machine.info("[FSM Effect] No more stages, completing workflow")
                state_machine.transition(WorkflowEvent.COMPLETE_WORKFLOW)

    except Exception as e:
        state_machine.error(f"[FSM Effect] Failed to call Planning API: {e}", exc_info=True)
        # Fallback: check if there are more stages
        from core.events import WorkflowEvent
        next_stage = workflow.get_next_stage(ctx.current_stage_id)
        if next_stage:
            ctx.current_stage_id = next_stage.id
            ctx.current_step_id = next_stage.steps[0].id if next_stage.steps else None
            ctx.reset_for_new_step()
            state_machine.transition(WorkflowEvent.NEXT_STAGE)
        else:
            state_machine.transition(WorkflowEvent.COMPLETE_WORKFLOW)
