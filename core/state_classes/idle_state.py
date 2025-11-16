"""
IDLE State Class
Represents the idle state where the workflow is waiting to begin.
"""

from typing import Dict, Any, Optional
from .base_state import BaseState
from core.api_types import APIResponseType


class IdleState(BaseState):
    """
    IDLE state - The workflow is idle and waiting to start.

    Valid outgoing transitions:
    - START_WORKFLOW -> STAGE_RUNNING (when planning API returns stages)
    """

    def __init__(self):
        super().__init__('IDLE')

    def get_valid_transitions(self) -> Dict[str, str]:
        """
        Get valid outgoing transitions.

        Returns:
            Dict of transition names to event names
        """
        from ..events import WorkflowEvent
        return {
            'start_workflow': WorkflowEvent.START_WORKFLOW,
            'fail': WorkflowEvent.FAIL,
        }

    def determine_next_transition(
        self,
        state_data: Dict[str, Any],
        api_response: Optional[Any] = None
    ) -> Optional[str]:
        """
        Determine next transition from IDLE state.

        Logic:
        - If API response contains stages -> START_WORKFLOW
        - Otherwise -> None (stay in IDLE)

        Args:
            state_data: Current state JSON
            api_response: API response (should contain stages from planning API)

        Returns:
            WorkflowEvent to trigger
        """
        from ..events import WorkflowEvent

        # Check if we have a planning response with stages
        if api_response and isinstance(api_response, dict):
            if 'stages' in api_response and isinstance(api_response['stages'], list):
                if len(api_response['stages']) > 0:
                    self.info("Planning response received with stages, transitioning to STAGE_RUNNING")
                    return WorkflowEvent.START_WORKFLOW

        # No valid transition condition met
        self.debug("No transition conditions met, staying in IDLE")
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

        # Check if event is in valid transitions
        if event not in valid_events.values():
            return False

        # IDLE can always start workflow or fail (no additional conditions)
        if event in (WorkflowEvent.START_WORKFLOW, WorkflowEvent.FAIL):
            return True

        return False

    def get_required_api_type(self) -> Optional[APIResponseType]:
        """
        IDLE state requires Planning API to get stages.

        Returns:
            APIResponseType.PLANNING
        """
        return APIResponseType.PLANNING

    def initialize_from_response(
        self,
        state_data: Dict[str, Any],
        api_response: Any
    ) -> Dict[str, Any]:
        """
        Initialize state from API response.

        For IDLE state, this is typically called after START_WORKFLOW transition.
        The actual initialization is done by the transition handler.

        Args:
            state_data: Current state JSON
            api_response: API response

        Returns:
            Updated state JSON
        """
        # For IDLE, initialization is handled by StartWorkflowHandler
        # This method is here for completeness
        return state_data
