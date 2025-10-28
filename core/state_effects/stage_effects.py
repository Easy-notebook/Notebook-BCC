"""
Stage Effects - Stage-level state effect handlers
Handles: stage_running, stage_completed
"""

from typing import Any


def effect_stage_running(state_machine, payload: Any = None):
    """
    Effect for STAGE_RUNNING state.

    Args:
        state_machine: Reference to WorkflowStateMachine instance
        payload: Optional payload data
    """
    state_machine.info(f"[FSM Effect] STAGE_RUNNING")

    if not state_machine.pipeline_store:
        state_machine.error("[FSM Effect] Pipeline store not available")
        from core.events import WorkflowEvent
        state_machine.transition(WorkflowEvent.FAIL, {'error': 'Pipeline store not available'})
        return

    workflow = state_machine.pipeline_store.workflow_template
    stage_id = state_machine.execution_context.workflow_context.current_stage_id

    if not workflow or not stage_id:
        from core.events import WorkflowEvent
        state_machine.transition(WorkflowEvent.FAIL, {'error': 'No workflow or stage ID'})
        return

    stage = workflow.find_stage(stage_id)
    if not stage or not stage.steps:
        from core.events import WorkflowEvent
        state_machine.transition(WorkflowEvent.FAIL, {'error': f'No steps in stage {stage_id}'})
        return

    # Set first step
    first_step = stage.steps[0]
    state_machine.execution_context.workflow_context.current_step_id = first_step.id

    # Transition to step
    from core.events import WorkflowEvent
    state_machine.transition(WorkflowEvent.START_STEP)


def effect_stage_completed(state_machine, payload: Any = None):
    """
    Effect for STAGE_COMPLETED state - CLIENT-CONTROLLED navigation.

    Args:
        state_machine: Reference to WorkflowStateMachine instance
        payload: Optional payload data
    """
    state_machine.info(f"[FSM Effect] STAGE_COMPLETED")

    if not state_machine.pipeline_store:
        state_machine.error("[FSM Effect] Pipeline store not available")
        return

    workflow = state_machine.pipeline_store.workflow_template
    ctx = state_machine.execution_context.workflow_context

    if not workflow or not ctx.current_stage_id:
        state_machine.error("[FSM Effect] Invalid context in STAGE_COMPLETED")
        return

    # Client-side navigation based on workflow template
    is_last = workflow.is_last_stage(ctx.current_stage_id)

    from core.events import WorkflowEvent
    if is_last:
        state_machine.transition(WorkflowEvent.COMPLETE_WORKFLOW)
    else:
        # Move to next stage
        next_stage = workflow.get_next_stage(ctx.current_stage_id)
        if next_stage:
            ctx.current_stage_id = next_stage.id
            ctx.current_step_id = next_stage.steps[0].id if next_stage.steps else None
            ctx.reset_for_new_step()
            state_machine.transition(WorkflowEvent.NEXT_STAGE)
        else:
            state_machine.error("[FSM Effect] No next stage found")
            state_machine.transition(WorkflowEvent.COMPLETE_WORKFLOW)
