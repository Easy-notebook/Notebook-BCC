"""
Stage Effects - Stage-level state effect handlers
Handles: stage_running, stage_completed

Note: This module now delegates to transition_handlers for actual implementation.
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
    # Delegate to START_STEP handler
    from core.transition_handlers import handle_start_step
    handle_start_step(state_machine, payload)


def effect_stage_completed(state_machine, payload: Any = None):
    """
    Effect for STAGE_COMPLETED state.
    Delegates to COMPLETE_STAGE handler.

    Args:
        state_machine: Reference to WorkflowStateMachine instance
        payload: Optional payload data
    """
    # Delegate to COMPLETE_STAGE handler
    from core.transition_handlers import handle_complete_stage
    handle_complete_stage(state_machine, payload)
