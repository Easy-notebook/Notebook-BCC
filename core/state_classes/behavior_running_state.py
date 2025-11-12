"""
BEHAVIOR_RUNNING State Class
Represents a behavior that is currently being generated/executed.
"""

from typing import Dict, Any, Optional
from .base_state import BaseState
from core.api_types import APIResponseType


class BehaviorRunningState(BaseState):
    """
    BEHAVIOR_RUNNING state - A behavior is being generated and executed.

    Valid outgoing transitions:
    - START_ACTION -> ACTION_RUNNING (internal, not typically used)
    - COMPLETE_BEHAVIOR -> BEHAVIOR_COMPLETED (when behavior passes feedback)
    - FAIL -> ERROR
    - CANCEL -> CANCELLED
    """

    def __init__(self):
        super().__init__('BEHAVIOR_RUNNING')

    def get_valid_transitions(self) -> Dict[str, str]:
        """Get valid outgoing transitions."""
        from ..events import WorkflowEvent
        return {
            'start_action': WorkflowEvent.START_ACTION,
            'complete_behavior': WorkflowEvent.COMPLETE_BEHAVIOR,
            'fail': WorkflowEvent.FAIL,
            'cancel': WorkflowEvent.CANCEL,
        }

    def determine_next_transition(
        self,
        state_data: Dict[str, Any],
        api_response: Optional[Any] = None
    ) -> Optional[str]:
        """
        Determine next transition from BEHAVIOR_RUNNING.

        Logic:
        1. If API response indicates behavior completion -> COMPLETE_BEHAVIOR
        2. Otherwise -> None (continue running)

        Args:
            state_data: Current state JSON
            api_response: API response from generating/reflecting

        Returns:
            WorkflowEvent to trigger
        """
        from ..events import WorkflowEvent

        # Check if we have a reflecting response indicating completion
        if api_response and isinstance(api_response, dict):
            # Check for completion signal
            if api_response.get('status') == 'completed':
                self.info("Behavior completed successfully")
                return WorkflowEvent.COMPLETE_BEHAVIOR

            # Check if feedback passed
            feedback = api_response.get('feedback', {})
            if feedback.get('passed', False):
                self.info("Behavior feedback passed, completing behavior")
                return WorkflowEvent.COMPLETE_BEHAVIOR

        # Check behavior outputs
        progress = self._get_progress(state_data)
        behaviors_progress = progress.get('behaviors', {})
        current_outputs = behaviors_progress.get('current_outputs', {})

        expected = current_outputs.get('expected', [])
        produced = current_outputs.get('produced', [])

        if expected and len(produced) >= len(expected):
            self.info("All expected behavior outputs produced")
            return WorkflowEvent.COMPLETE_BEHAVIOR

        # No transition needed yet
        self.debug("Behavior still running")
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

        # All transitions are generally allowed from BEHAVIOR_RUNNING
        return True

    def get_required_api_type(self) -> Optional[APIResponseType]:
        """
        BEHAVIOR_RUNNING state requires Generating API to execute actions.

        Returns:
            APIResponseType.GENERATING
        """
        return APIResponseType.GENERATING

    def _get_progress(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """Helper to get progress from state data."""
        return (
            state_data.get('observation', {})
            .get('location', {})
            .get('progress', {})
        )
