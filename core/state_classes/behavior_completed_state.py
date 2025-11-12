"""
BEHAVIOR_COMPLETED State Class
Represents a behavior that has just completed successfully.
"""

from typing import Dict, Any, Optional
from .base_state import BaseState
from core.api_types import APIResponseType


class BehaviorCompletedState(BaseState):
    """
    BEHAVIOR_COMPLETED state - A behavior has completed after passing feedback.

    Valid outgoing transitions:
    - NEXT_BEHAVIOR -> BEHAVIOR_RUNNING (if more behaviors needed)
    - COMPLETE_STEP -> STEP_COMPLETED (if step is done)
    - FAIL -> ERROR
    - CANCEL -> CANCELLED
    """

    def __init__(self):
        super().__init__('BEHAVIOR_COMPLETED')

    def get_valid_transitions(self) -> Dict[str, str]:
        """Get valid outgoing transitions."""
        from ..events import WorkflowEvent
        return {
            'next_behavior': WorkflowEvent.NEXT_BEHAVIOR,
            'complete_step': WorkflowEvent.COMPLETE_STEP,
            'fail': WorkflowEvent.FAIL,
            'cancel': WorkflowEvent.CANCEL,
        }

    def determine_next_transition(
        self,
        state_data: Dict[str, Any],
        api_response: Optional[Any] = None
    ) -> Optional[str]:
        """
        Determine next transition from BEHAVIOR_COMPLETED.

        Logic:
        1. Check if step outputs are satisfied -> COMPLETE_STEP
        2. Otherwise -> NEXT_BEHAVIOR (generate more behaviors)

        Args:
            state_data: Current state JSON
            api_response: Optional API response

        Returns:
            WorkflowEvent to trigger
        """
        from ..events import WorkflowEvent

        # Check if step is completed
        progress = self._get_progress(state_data)
        steps_progress = progress.get('steps', {})
        current_outputs = steps_progress.get('current_outputs', {})

        expected = current_outputs.get('expected', [])
        produced = current_outputs.get('produced', [])

        if expected and len(produced) >= len(expected):
            self.info("Step outputs satisfied, completing step")
            return WorkflowEvent.COMPLETE_STEP

        # Need more behaviors
        self.info("Step not complete, need next behavior")
        return WorkflowEvent.NEXT_BEHAVIOR

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

        # COMPLETE_STEP requires outputs to be satisfied
        if event == WorkflowEvent.COMPLETE_STEP:
            progress = self._get_progress(state_data)
            steps_progress = progress.get('steps', {})
            current_outputs = steps_progress.get('current_outputs', {})

            expected = current_outputs.get('expected', [])
            produced = current_outputs.get('produced', [])

            return len(produced) >= len(expected) if expected else True

        # Other transitions are allowed
        return True

    def get_required_api_type(self) -> Optional[APIResponseType]:
        """
        BEHAVIOR_COMPLETED state requires Reflecting API for feedback.

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
