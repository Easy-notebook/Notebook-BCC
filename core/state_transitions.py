"""
State Transition Rules for Workflow State Machine
Defines the finite state machine transition table.
"""

from typing import Dict
from .events import WorkflowEvent
from .states import WorkflowState


# =====================================================================
# State Transition Table
# =====================================================================

STATE_TRANSITIONS: Dict[WorkflowState, Dict[WorkflowEvent, WorkflowState]] = {
    WorkflowState.IDLE: {
        WorkflowEvent.START_WORKFLOW: WorkflowState.STAGE_RUNNING,
    },

    WorkflowState.STAGE_RUNNING: {
        WorkflowEvent.START_STEP: WorkflowState.STEP_RUNNING,
        WorkflowEvent.COMPLETE_STAGE: WorkflowState.STAGE_COMPLETED,
        WorkflowEvent.FAIL: WorkflowState.ERROR,
        WorkflowEvent.CANCEL: WorkflowState.CANCELLED,
    },

    WorkflowState.STEP_RUNNING: {
        WorkflowEvent.START_BEHAVIOR: WorkflowState.BEHAVIOR_RUNNING,
        WorkflowEvent.COMPLETE_STEP: WorkflowState.STEP_COMPLETED,
        WorkflowEvent.FAIL: WorkflowState.ERROR,
        WorkflowEvent.CANCEL: WorkflowState.CANCELLED,
    },

    WorkflowState.BEHAVIOR_RUNNING: {
        WorkflowEvent.START_ACTION: WorkflowState.ACTION_RUNNING,
        WorkflowEvent.COMPLETE_BEHAVIOR: WorkflowState.BEHAVIOR_COMPLETED,
        WorkflowEvent.FAIL: WorkflowState.ERROR,
        WorkflowEvent.CANCEL: WorkflowState.CANCELLED,
    },

    WorkflowState.ACTION_RUNNING: {
        WorkflowEvent.COMPLETE_ACTION: WorkflowState.ACTION_COMPLETED,
        WorkflowEvent.FAIL: WorkflowState.ERROR,
        WorkflowEvent.CANCEL: WorkflowState.CANCELLED,
        WorkflowEvent.UPDATE_WORKFLOW: WorkflowState.WORKFLOW_UPDATE_PENDING,
        WorkflowEvent.UPDATE_STEP: WorkflowState.STEP_UPDATE_PENDING,
    },

    WorkflowState.ACTION_COMPLETED: {
        WorkflowEvent.NEXT_ACTION: WorkflowState.ACTION_RUNNING,
        WorkflowEvent.COMPLETE_BEHAVIOR: WorkflowState.BEHAVIOR_COMPLETED,
        WorkflowEvent.FAIL: WorkflowState.ERROR,
        WorkflowEvent.CANCEL: WorkflowState.CANCELLED,
    },

    WorkflowState.BEHAVIOR_COMPLETED: {
        WorkflowEvent.NEXT_BEHAVIOR: WorkflowState.BEHAVIOR_RUNNING,
        WorkflowEvent.COMPLETE_STEP: WorkflowState.STEP_COMPLETED,
        WorkflowEvent.FAIL: WorkflowState.ERROR,
        WorkflowEvent.CANCEL: WorkflowState.CANCELLED,
    },

    WorkflowState.STEP_COMPLETED: {
        WorkflowEvent.COMPLETE_STAGE: WorkflowState.STAGE_COMPLETED,
        WorkflowEvent.NEXT_STEP: WorkflowState.STEP_RUNNING,
        WorkflowEvent.FAIL: WorkflowState.ERROR,
        WorkflowEvent.CANCEL: WorkflowState.CANCELLED,
    },

    WorkflowState.STAGE_COMPLETED: {
        WorkflowEvent.NEXT_STAGE: WorkflowState.STAGE_RUNNING,
        WorkflowEvent.COMPLETE_WORKFLOW: WorkflowState.WORKFLOW_COMPLETED,
        WorkflowEvent.CANCEL: WorkflowState.CANCELLED,
    },

    WorkflowState.WORKFLOW_COMPLETED: {
        WorkflowEvent.RESET: WorkflowState.IDLE,
    },

    WorkflowState.WORKFLOW_UPDATE_PENDING: {
        WorkflowEvent.UPDATE_WORKFLOW_CONFIRMED: WorkflowState.ACTION_COMPLETED,
        WorkflowEvent.UPDATE_WORKFLOW_REJECTED: WorkflowState.ACTION_COMPLETED,
        WorkflowEvent.COMPLETE_ACTION: WorkflowState.WORKFLOW_UPDATE_PENDING,  # Ignore
        WorkflowEvent.CANCEL: WorkflowState.CANCELLED,
    },

    WorkflowState.STEP_UPDATE_PENDING: {
        WorkflowEvent.UPDATE_STEP_CONFIRMED: WorkflowState.ACTION_COMPLETED,
        WorkflowEvent.UPDATE_STEP_REJECTED: WorkflowState.ERROR,
        WorkflowEvent.CANCEL: WorkflowState.CANCELLED,
    },

    WorkflowState.ERROR: {
        WorkflowEvent.RESET: WorkflowState.IDLE,
        WorkflowEvent.START_WORKFLOW: WorkflowState.STAGE_RUNNING,
        WorkflowEvent.START_BEHAVIOR: WorkflowState.BEHAVIOR_RUNNING,
    },

    WorkflowState.CANCELLED: {
        WorkflowEvent.RESET: WorkflowState.IDLE,
    },
}


# =====================================================================
# Helper Functions
# =====================================================================

def get_next_state(current_state: WorkflowState, event: WorkflowEvent) -> WorkflowState | None:
    """
    Get the next state for a given current state and event.

    Args:
        current_state: The current state
        event: The event triggering the transition

    Returns:
        The next state, or None if transition is invalid
    """
    return STATE_TRANSITIONS.get(current_state, {}).get(event)


def is_valid_transition(current_state: WorkflowState, event: WorkflowEvent) -> bool:
    """
    Check if a transition is valid.

    Args:
        current_state: The current state
        event: The event triggering the transition

    Returns:
        True if transition is valid, False otherwise
    """
    return event in STATE_TRANSITIONS.get(current_state, {})


def get_valid_events(current_state: WorkflowState) -> list[WorkflowEvent]:
    """
    Get all valid events for a given state.

    Args:
        current_state: The current state

    Returns:
        List of valid events for this state
    """
    return list(STATE_TRANSITIONS.get(current_state, {}).keys())
