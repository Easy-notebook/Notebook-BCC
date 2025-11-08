"""
Step Effects - Step-level state effect handlers
Handles: step_running, step_completed

Note: This module now delegates to transition_handlers for actual implementation.
"""

from typing import Any


def effect_step_running(state_machine, payload: Any = None):
    """
    Effect for STEP_RUNNING state.
    Delegates to START_BEHAVIOR handler.

    Args:
        state_machine: Reference to WorkflowStateMachine instance
        payload: Optional payload data
    """
    # Delegate to START_BEHAVIOR handler
    from core.transition_handlers import handle_start_behavior
    handle_start_behavior(state_machine, payload)


def effect_step_completed(state_machine, payload: Any = None):
    """
    Effect for STEP_COMPLETED state.
    Delegates to COMPLETE_STEP handler.

    Args:
        state_machine: Reference to WorkflowStateMachine instance
        payload: Optional payload data
    """
    # Delegate to COMPLETE_STEP handler
    from core.transition_handlers import handle_complete_step
    handle_complete_step(state_machine, payload)
