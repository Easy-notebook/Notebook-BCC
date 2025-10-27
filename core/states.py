"""
Workflow states definition.
Replicates the TypeScript WORKFLOW_STATES constants.
"""

from enum import Enum
from typing import Final


class WorkflowState(str, Enum):
    """
    All possible states in the workflow state machine.
    Maps to TypeScript's WORKFLOW_STATES constant.
    """

    # Start state
    IDLE = 'idle'
    """The machine is idle, waiting for the workflow to begin."""

    # Stage states
    STAGE_RUNNING = 'stage_running'
    """A stage is active, ready to execute its steps."""

    STAGE_COMPLETED = 'stage_completed'
    """A stage has successfully completed all its steps."""

    # Step states
    STEP_RUNNING = 'step_running'
    """A step is active, ready to execute its behaviors."""

    STEP_COMPLETED = 'step_completed'
    """A step has successfully completed all its behaviors."""

    # Behavior states
    BEHAVIOR_RUNNING = 'behavior_running'
    """A behavior is active, managing the execution of its actions."""

    BEHAVIOR_COMPLETED = 'behavior_completed'
    """A behavior has successfully completed after passing feedback."""

    # Action states
    ACTION_RUNNING = 'action_running'
    """A single, atomic action is being executed."""

    ACTION_COMPLETED = 'action_completed'
    """An action has just completed, waiting for next command."""

    # Workflow states
    WORKFLOW_COMPLETED = 'workflow_completed'
    """The entire workflow has finished successfully."""

    # Update pending states
    WORKFLOW_UPDATE_PENDING = 'workflow_update_pending'
    """Waiting for user confirmation on a major workflow update."""

    STEP_UPDATE_PENDING = 'step_update_pending'
    """Waiting for user confirmation on a minor step update."""

    # Terminal states
    ERROR = 'error'
    """A terminal error state."""

    CANCELLED = 'cancelled'
    """A terminal cancelled state."""


# For backward compatibility, create a dictionary similar to TypeScript's WORKFLOW_STATES
WORKFLOW_STATES: Final[dict] = {
    'IDLE': WorkflowState.IDLE,
    'STAGE_RUNNING': WorkflowState.STAGE_RUNNING,
    'STAGE_COMPLETED': WorkflowState.STAGE_COMPLETED,
    'STEP_RUNNING': WorkflowState.STEP_RUNNING,
    'STEP_COMPLETED': WorkflowState.STEP_COMPLETED,
    'BEHAVIOR_RUNNING': WorkflowState.BEHAVIOR_RUNNING,
    'BEHAVIOR_COMPLETED': WorkflowState.BEHAVIOR_COMPLETED,
    'ACTION_RUNNING': WorkflowState.ACTION_RUNNING,
    'ACTION_COMPLETED': WorkflowState.ACTION_COMPLETED,
    'WORKFLOW_COMPLETED': WorkflowState.WORKFLOW_COMPLETED,
    'WORKFLOW_UPDATE_PENDING': WorkflowState.WORKFLOW_UPDATE_PENDING,
    'STEP_UPDATE_PENDING': WorkflowState.STEP_UPDATE_PENDING,
    'ERROR': WorkflowState.ERROR,
    'CANCELLED': WorkflowState.CANCELLED,
}
