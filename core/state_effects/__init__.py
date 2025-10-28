"""
State Effects - Modular state effect handlers for WorkflowStateMachine
Each module contains related state effects for better organization.
"""

from .stage_effects import effect_stage_running, effect_stage_completed
from .step_effects import effect_step_running, effect_step_completed
from .behavior_effects import effect_behavior_running, effect_behavior_completed
from .action_effects import effect_action_running, effect_action_completed
from .workflow_effects import effect_workflow_completed, effect_workflow_update_pending


def register_effects(state_machine):
    """
    Register all state effect handlers with the state machine.

    Args:
        state_machine: WorkflowStateMachine instance
    """
    from core.states import WorkflowState

    state_machine._state_effects = {
        WorkflowState.STAGE_RUNNING: lambda p: effect_stage_running(state_machine, p),
        WorkflowState.STEP_RUNNING: lambda p: effect_step_running(state_machine, p),
        WorkflowState.BEHAVIOR_RUNNING: lambda p: effect_behavior_running(state_machine, p),
        WorkflowState.ACTION_RUNNING: lambda p: effect_action_running(state_machine, p),
        WorkflowState.ACTION_COMPLETED: lambda p: effect_action_completed(state_machine, p),
        WorkflowState.BEHAVIOR_COMPLETED: lambda p: effect_behavior_completed(state_machine, p),
        WorkflowState.STEP_COMPLETED: lambda p: effect_step_completed(state_machine, p),
        WorkflowState.STAGE_COMPLETED: lambda p: effect_stage_completed(state_machine, p),
        WorkflowState.WORKFLOW_COMPLETED: lambda p: effect_workflow_completed(state_machine, p),
        WorkflowState.WORKFLOW_UPDATE_PENDING: lambda p: effect_workflow_update_pending(state_machine, p),
    }


__all__ = [
    # Stage effects
    'effect_stage_running',
    'effect_stage_completed',
    # Step effects
    'effect_step_running',
    'effect_step_completed',
    # Behavior effects
    'effect_behavior_running',
    'effect_behavior_completed',
    # Action effects
    'effect_action_running',
    'effect_action_completed',
    # Workflow effects
    'effect_workflow_completed',
    'effect_workflow_update_pending',
    # Registration
    'register_effects',
]
