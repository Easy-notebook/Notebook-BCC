"""
Behavior Effects - Behavior-level state effect handlers
Handles: behavior_running, behavior_completed

Note: This module now delegates to transition_handlers for actual implementation.
"""

from typing import Any


def effect_behavior_running(state_machine, payload: Any = None):
    """
    Effect for BEHAVIOR_RUNNING state.
    Delegates to BEHAVIOR_RUNNING handler.

    Args:
        state_machine: Reference to WorkflowStateMachine instance
        payload: Optional payload data
    """
    # Delegate to BEHAVIOR_RUNNING handler
    from core.transition_handlers import handle_behavior_running
    handle_behavior_running(state_machine, payload)


def effect_behavior_completed(state_machine, payload: Any = None):
    """
    Effect for BEHAVIOR_COMPLETED state.
    Delegates to COMPLETE_BEHAVIOR handler.

    Args:
        state_machine: Reference to WorkflowStateMachine instance
        payload: Optional payload data
    """
    # Delegate to COMPLETE_BEHAVIOR handler
    from core.transition_handlers import handle_complete_behavior
    handle_complete_behavior(state_machine, payload)
