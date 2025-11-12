"""
STEP_COMPLETED State Class
Represents a step that has just completed successfully.
"""

from typing import Dict, Any, Optional
from .base_state import BaseState
from core.api_types import APIResponseType


class StepCompletedState(BaseState):
    """
    STEP_COMPLETED state - A step has completed all its behaviors.

    Valid outgoing transitions:
    - COMPLETE_STAGE -> STAGE_COMPLETED (if no more steps)
    - NEXT_STEP -> STEP_RUNNING (if more steps in stage)
    - FAIL -> ERROR
    - CANCEL -> CANCELLED
    """

    def __init__(self):
        super().__init__('STEP_COMPLETED')

    def get_valid_transitions(self) -> Dict[str, str]:
        """Get valid outgoing transitions."""
        from ..events import WorkflowEvent
        return {
            'complete_stage': WorkflowEvent.COMPLETE_STAGE,
            'next_step': WorkflowEvent.NEXT_STEP,
            'fail': WorkflowEvent.FAIL,
            'cancel': WorkflowEvent.CANCEL,
        }

    def determine_next_transition(
        self,
        state_data: Dict[str, Any],
        api_response: Optional[Any] = None
    ) -> Optional[str]:
        """
        Determine next transition from STEP_COMPLETED.

        Logic:
        1. If no remaining steps -> COMPLETE_STAGE
        2. Otherwise -> NEXT_STEP

        Args:
            state_data: Current state JSON
            api_response: Optional API response

        Returns:
            WorkflowEvent to trigger
        """
        from ..events import WorkflowEvent

        # Check if there are remaining steps
        progress = self._get_progress(state_data)
        steps_progress = progress.get('steps', {})
        remaining_steps = steps_progress.get('remaining', [])

        if not remaining_steps:
            self.info("No remaining steps, completing stage")
            return WorkflowEvent.COMPLETE_STAGE

        # Move to next step
        self.info(f"Moving to next step ({len(remaining_steps)} remaining)")
        return WorkflowEvent.NEXT_STEP

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

        # COMPLETE_STAGE requires no remaining steps
        if event == WorkflowEvent.COMPLETE_STAGE:
            progress = self._get_progress(state_data)
            steps_progress = progress.get('steps', {})
            remaining_steps = steps_progress.get('remaining', [])
            return len(remaining_steps) == 0

        # NEXT_STEP requires remaining steps
        if event == WorkflowEvent.NEXT_STEP:
            progress = self._get_progress(state_data)
            steps_progress = progress.get('steps', {})
            remaining_steps = steps_progress.get('remaining', [])
            return len(remaining_steps) > 0

        # Other transitions are allowed
        return True

    def get_required_api_type(self) -> Optional[APIResponseType]:
        """
        STEP_COMPLETED state requires Reflecting API for feedback.

        Returns:
            APIResponseType.COMPLETE
        """
        return APIResponseType.COMPLETE

    def _get_progress(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """Helper to get progress from state data."""
        return (
            state_data.get('observation', {})
            .get('location', {})
            .get('progress', {})
        )
