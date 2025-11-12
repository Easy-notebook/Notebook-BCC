"""
STAGE_RUNNING State Class
Represents a stage that is currently running and ready to execute steps.
"""

from typing import Dict, Any, Optional
from .base_state import BaseState
from core.api_types import APIResponseType


class StageRunningState(BaseState):
    """
    STAGE_RUNNING state - A stage is active and ready to execute steps.

    Valid outgoing transitions:
    - START_STEP -> STEP_RUNNING (when planning API returns steps)
    - COMPLETE_STAGE -> STAGE_COMPLETED (when all steps are done)
    - FAIL -> ERROR
    - CANCEL -> CANCELLED
    """

    def __init__(self):
        super().__init__('STAGE_RUNNING')

    def get_valid_transitions(self) -> Dict[str, str]:
        """Get valid outgoing transitions."""
        from ..events import WorkflowEvent
        return {
            'start_step': WorkflowEvent.START_STEP,
            'complete_stage': WorkflowEvent.COMPLETE_STAGE,
            'fail': WorkflowEvent.FAIL,
            'cancel': WorkflowEvent.CANCEL,
        }

    def determine_next_transition(
        self,
        state_data: Dict[str, Any],
        api_response: Optional[Any] = None
    ) -> Optional[str]:
        """
        Determine next transition from STAGE_RUNNING.

        Logic:
        1. If API response contains steps -> START_STEP
        2. If no remaining steps in progress -> COMPLETE_STAGE
        3. Otherwise -> None

        Args:
            state_data: Current state JSON
            api_response: API response from planning

        Returns:
            WorkflowEvent to trigger
        """
        from ..events import WorkflowEvent

        # Check if we have a planning response with steps
        if api_response and isinstance(api_response, dict):
            if 'steps' in api_response and isinstance(api_response['steps'], list):
                if len(api_response['steps']) > 0:
                    self.info("Planning response received with steps, transitioning to STEP_RUNNING")
                    return WorkflowEvent.START_STEP

        # Check if stage is completed (no remaining steps)
        progress = self._get_progress(state_data)
        steps_progress = progress.get('steps', {})
        remaining_steps = steps_progress.get('remaining', [])

        if not remaining_steps and not steps_progress.get('current'):
            self.info("No remaining steps, stage completed")
            return WorkflowEvent.COMPLETE_STAGE

        # No transition needed yet
        self.debug("No transition conditions met")
        return None

    def can_transition_to(
        self,
        event: str,
        state_data: Dict[str, Any]
    ) -> bool:
        """
        Check if transition is allowed.

        Args:
            event: The event to check
            state_data: Current state data

        Returns:
            True if transition is allowed
        """
        from ..events import WorkflowEvent

        valid_events = self.get_valid_transitions()

        if event not in valid_events.values():
            return False

        # Additional conditions for specific transitions
        if event == WorkflowEvent.COMPLETE_STAGE:
            # Can only complete if no steps remaining
            progress = self._get_progress(state_data)
            steps_progress = progress.get('steps', {})
            remaining_steps = steps_progress.get('remaining', [])
            return len(remaining_steps) == 0

        # START_STEP, FAIL, CANCEL are always allowed
        return True

    def get_required_api_type(self) -> Optional[APIResponseType]:
        """
        STAGE_RUNNING state requires Planning API to get steps.

        Returns:
            APIResponseType.PLANNING
        """
        return APIResponseType.PLANNING

    def _get_progress(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """Helper to get progress from state data."""
        return (
            state_data.get('observation', {})
            .get('location', {})
            .get('progress', {})
        )
