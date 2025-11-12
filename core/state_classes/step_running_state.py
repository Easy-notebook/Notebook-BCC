"""
STEP_RUNNING State Class
Represents a step that is currently running and ready to execute behaviors.
"""

from typing import Dict, Any, Optional
from .base_state import BaseState
from core.api_types import APIResponseType


class StepRunningState(BaseState):
    """
    STEP_RUNNING state - A step is active and ready to execute behaviors.

    Valid outgoing transitions:
    - START_BEHAVIOR -> BEHAVIOR_RUNNING (when planning API returns behaviors)
    - COMPLETE_STEP -> STEP_COMPLETED (when all behaviors are done)
    - FAIL -> ERROR
    - CANCEL -> CANCELLED
    """

    def __init__(self):
        super().__init__('STEP_RUNNING')

    def get_valid_transitions(self) -> Dict[str, str]:
        """Get valid outgoing transitions."""
        from ..events import WorkflowEvent
        return {
            'start_behavior': WorkflowEvent.START_BEHAVIOR,
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
        Determine next transition from STEP_RUNNING.

        Logic:
        1. If API response contains behaviors -> START_BEHAVIOR
        2. If step completion conditions met -> COMPLETE_STEP
        3. Otherwise -> None

        Args:
            state_data: Current state JSON
            api_response: API response from planning

        Returns:
            WorkflowEvent to trigger
        """
        from ..events import WorkflowEvent

        # Check if we have a planning response with behaviors
        if api_response and isinstance(api_response, dict):
            if 'behaviors' in api_response and isinstance(api_response['behaviors'], list):
                if len(api_response['behaviors']) > 0:
                    self.info("Planning response received with behaviors, transitioning to BEHAVIOR_RUNNING")
                    return WorkflowEvent.START_BEHAVIOR

        # Check if step is completed
        # This would check if all expected outputs are produced
        progress = self._get_progress(state_data)
        steps_progress = progress.get('steps', {})
        current_outputs = steps_progress.get('current_outputs', {})

        expected = current_outputs.get('expected', [])
        produced = current_outputs.get('produced', [])

        if expected and len(produced) >= len(expected):
            self.info("All expected outputs produced, step completed")
            return WorkflowEvent.COMPLETE_STEP

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
        if event == WorkflowEvent.COMPLETE_STEP:
            # Check if outputs are satisfied
            progress = self._get_progress(state_data)
            steps_progress = progress.get('steps', {})
            current_outputs = steps_progress.get('current_outputs', {})

            expected = current_outputs.get('expected', [])
            produced = current_outputs.get('produced', [])

            # Can complete if all expected outputs are produced
            return len(produced) >= len(expected) if expected else True

        # START_BEHAVIOR, FAIL, CANCEL are always allowed
        return True

    def get_required_api_type(self) -> Optional[APIResponseType]:
        """
        STEP_RUNNING state requires Planning API to get behaviors.

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
