"""
Workflow events definition.
Replicates the TypeScript EVENTS constants.
"""

from enum import Enum
from typing import Final


class WorkflowEvent(str, Enum):
    """
    All possible events that can trigger state transitions in the workflow.
    Maps to TypeScript's EVENTS constant.
    """

    # ==============================================
    # 1. Lifecycle: START Events
    # ==============================================
    START_WORKFLOW = 'START_WORKFLOW'
    """Starts the entire workflow. Transition: IDLE -> STAGE_RUNNING"""

    START_STEP = 'START_STEP'
    """Starts the next step within the current stage. Transition: STAGE_RUNNING -> STEP_RUNNING"""

    START_BEHAVIOR = 'START_BEHAVIOR'
    """Starts the next behavior within the current step. Transition: STEP_RUNNING -> BEHAVIOR_RUNNING"""

    START_ACTION = 'START_ACTION'
    """Starts the next action within the current behavior. Transition: BEHAVIOR_RUNNING -> ACTION_RUNNING"""

    # ==============================================
    # 2. Lifecycle: COMPLETE Events
    # ==============================================
    COMPLETE_ACTION = 'COMPLETE_ACTION'
    """Declares the current action has finished. Transition: ACTION_RUNNING -> ACTION_COMPLETED"""

    COMPLETE_BEHAVIOR = 'COMPLETE_BEHAVIOR'
    """Declares the current behavior has completed. Transition: BEHAVIOR_RUNNING -> BEHAVIOR_COMPLETED"""

    COMPLETE_STEP = 'COMPLETE_STEP'
    """Declares the current step has finished. Transition: STEP_RUNNING -> STEP_COMPLETED"""

    COMPLETE_STAGE = 'COMPLETE_STAGE'
    """Declares the current stage has finished. Transition: STAGE_RUNNING -> STAGE_COMPLETED"""

    COMPLETE_WORKFLOW = 'COMPLETE_WORKFLOW'
    """Declares the final stage is complete. Transition: STAGE_COMPLETED -> WORKFLOW_COMPLETED"""

    # ==============================================
    # 3. Feedback & Looping Events
    # ==============================================
    NEXT_ACTION = 'NEXT_ACTION'
    """Start the next action in the behavior. Transition: ACTION_COMPLETED -> ACTION_RUNNING"""

    NEXT_BEHAVIOR = 'NEXT_BEHAVIOR'
    """Start the next behavior in the step. Transition: BEHAVIOR_COMPLETED -> BEHAVIOR_RUNNING"""

    NEXT_STEP = 'NEXT_STEP'
    """Start the next step in the stage. Transition: STEP_COMPLETED -> STEP_RUNNING"""

    NEXT_STAGE = 'NEXT_STAGE'
    """Start the next stage. Transition: STAGE_COMPLETED -> STAGE_RUNNING"""

    # ==============================================
    # 4. Update Events
    # ==============================================
    UPDATE_WORKFLOW = 'UPDATE_WORKFLOW'
    """Requests a full workflow update. Transition: any_running_state -> WORKFLOW_UPDATE_PENDING"""

    UPDATE_WORKFLOW_CONFIRMED = 'UPDATE_WORKFLOW_CONFIRMED'
    """Confirms the workflow update. Transition: WORKFLOW_UPDATE_PENDING -> ACTION_COMPLETED"""

    UPDATE_WORKFLOW_REJECTED = 'UPDATE_WORKFLOW_REJECTED'
    """Rejects the workflow update. Transition: WORKFLOW_UPDATE_PENDING -> ACTION_COMPLETED"""

    UPDATE_STEP = 'UPDATE_STEP'
    """Requests an update to the steps of a stage. Transition: any_running_state -> STEP_UPDATE_PENDING"""

    UPDATE_STEP_CONFIRMED = 'UPDATE_STEP_CONFIRMED'
    """Confirms the step update. Transition: STEP_UPDATE_PENDING -> previous_state"""

    UPDATE_STEP_REJECTED = 'UPDATE_STEP_REJECTED'
    """Rejects the step update. Transition: STEP_UPDATE_PENDING -> previous_state"""

    # ==============================================
    # 5. General Control Events
    # ==============================================
    FAIL = 'FAIL'
    """A non-recoverable error occurred. Transition: * -> ERROR"""

    CANCEL = 'CANCEL'
    """The user or system cancels the workflow. Transition: * -> CANCELLED"""

    RESET = 'RESET'
    """Resets the machine from a terminal state. Transition: WORKFLOW_COMPLETED | ERROR | CANCELLED -> IDLE"""


# For backward compatibility, create a dictionary similar to TypeScript's EVENTS
EVENTS: Final[dict] = {
    'START_WORKFLOW': WorkflowEvent.START_WORKFLOW,
    'START_STEP': WorkflowEvent.START_STEP,
    'START_BEHAVIOR': WorkflowEvent.START_BEHAVIOR,
    'START_ACTION': WorkflowEvent.START_ACTION,
    'COMPLETE_ACTION': WorkflowEvent.COMPLETE_ACTION,
    'COMPLETE_BEHAVIOR': WorkflowEvent.COMPLETE_BEHAVIOR,
    'COMPLETE_STEP': WorkflowEvent.COMPLETE_STEP,
    'COMPLETE_STAGE': WorkflowEvent.COMPLETE_STAGE,
    'COMPLETE_WORKFLOW': WorkflowEvent.COMPLETE_WORKFLOW,
    'NEXT_ACTION': WorkflowEvent.NEXT_ACTION,
    'NEXT_BEHAVIOR': WorkflowEvent.NEXT_BEHAVIOR,
    'NEXT_STEP': WorkflowEvent.NEXT_STEP,
    'NEXT_STAGE': WorkflowEvent.NEXT_STAGE,
    'UPDATE_WORKFLOW': WorkflowEvent.UPDATE_WORKFLOW,
    'UPDATE_WORKFLOW_CONFIRMED': WorkflowEvent.UPDATE_WORKFLOW_CONFIRMED,
    'UPDATE_WORKFLOW_REJECTED': WorkflowEvent.UPDATE_WORKFLOW_REJECTED,
    'UPDATE_STEP': WorkflowEvent.UPDATE_STEP,
    'UPDATE_STEP_CONFIRMED': WorkflowEvent.UPDATE_STEP_CONFIRMED,
    'UPDATE_STEP_REJECTED': WorkflowEvent.UPDATE_STEP_REJECTED,
    'FAIL': WorkflowEvent.FAIL,
    'CANCEL': WorkflowEvent.CANCEL,
    'RESET': WorkflowEvent.RESET,
}
