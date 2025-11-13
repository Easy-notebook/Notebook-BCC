"""
STAGE_COMPLETED State Class
Represents a stage that has just completed successfully.
"""

from typing import Dict, Any, Optional
from .base_state import BaseState
from core.api_types import APIResponseType


class StageCompletedState(BaseState):
    """
    STAGE_COMPLETED state - A stage has completed all its steps.

    Valid outgoing transitions:
    - COMPLETE_WORKFLOW -> WORKFLOW_COMPLETED (if no more stages)
    - NEXT_STAGE -> STAGE_RUNNING (if more stages in workflow)
    - FAIL -> ERROR
    - CANCEL -> CANCELLED
    """

    def __init__(self):
        super().__init__('STAGE_COMPLETED')

    def get_valid_transitions(self) -> Dict[str, str]:
        """Get valid outgoing transitions."""
        from ..events import WorkflowEvent
        return {
            'complete_workflow': WorkflowEvent.COMPLETE_WORKFLOW,
            'next_stage': WorkflowEvent.NEXT_STAGE,
            'fail': WorkflowEvent.FAIL,
            'cancel': WorkflowEvent.CANCEL,
        }

    def determine_next_transition(
        self,
        state_data: Dict[str, Any],
        api_response: Optional[Any] = None
    ) -> Optional[str]:
        """
        Determine next transition from STAGE_COMPLETED.

        Logic:
        1. If no remaining stages -> COMPLETE_WORKFLOW
        2. Otherwise -> NEXT_STAGE

        Args:
            state_data: Current state JSON
            api_response: Optional API response

        Returns:
            WorkflowEvent to trigger
        """
        from ..events import WorkflowEvent

        # Check if there are remaining stages
        progress = self._get_progress(state_data)
        stages_progress = progress.get('stages', {})
        remaining_stages = stages_progress.get('remaining', [])

        if not remaining_stages:
            self.info("No remaining stages, completing workflow")
            return WorkflowEvent.COMPLETE_WORKFLOW

        # Move to next stage
        self.info(f"Moving to next stage ({len(remaining_stages)} remaining)")
        return WorkflowEvent.NEXT_STAGE

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

        # COMPLETE_WORKFLOW requires no remaining stages
        if event == WorkflowEvent.COMPLETE_WORKFLOW:
            progress = self._get_progress(state_data)
            stages_progress = progress.get('stages', {})
            remaining_stages = stages_progress.get('remaining', [])
            return len(remaining_stages) == 0

        # NEXT_STAGE requires remaining stages
        if event == WorkflowEvent.NEXT_STAGE:
            progress = self._get_progress(state_data)
            stages_progress = progress.get('stages', {})
            remaining_stages = stages_progress.get('remaining', [])
            return len(remaining_stages) > 0

        # Other transitions are allowed
        return True

    def get_required_api_type(self) -> Optional[APIResponseType]:
        """
        STAGE_COMPLETED state requires Reflecting API for feedback.

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
