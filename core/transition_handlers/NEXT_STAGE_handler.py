"""
NEXT_STAGE Event Handler
Handles transition to the next stage after completing the current stage.
Event: NEXT_STAGE
Transition: STAGE_COMPLETED → STAGE_RUNNING
"""

from typing import Dict, Any
from copy import deepcopy
from .base_transition_handler import BaseTransitionHandler
from ..states import WorkflowState


class NextStageHandler(BaseTransitionHandler):
    """
    Handles NEXT_STAGE event.
    Transition: STAGE_COMPLETED → STAGE_RUNNING

    Triggered by: Automatic transition after STAGE_COMPLETED when remaining stages exist

    Updates:
    - observation.location.progress.stages.current to next stage
    - observation.location.progress.stages.remaining (removes first item)
    - observation.location.current.stage_id to next stage ID
    - observation.location.current.step_id cleared
    - observation.location.current.behavior_id cleared
    - Initializes outputs tracking for the new stage
    - state.FSM.state to 'STAGE_RUNNING'
    - Executes new_section action with next stage title
    """

    def __init__(self):
        super().__init__(
            'STAGE_COMPLETED',
            'STAGE_RUNNING',
            'NEXT_STAGE'
        )

    def can_handle(self, api_response: Any) -> bool:
        """
        Check if response indicates advancing to next stage.

        This handler is typically triggered automatically by the state machine
        or by reflecting API response.
        """
        if isinstance(api_response, dict):
            # Check if this is an auto-trigger from state machine
            if api_response.get('_auto_trigger') == 'NEXT_STAGE':
                return True

            next_state = api_response.get('next_state', '')
            transition = api_response.get('transition', '')

            # Check for explicit NEXT_STAGE transition
            if 'NEXT_STAGE' in transition.upper():
                return True

            # Check if transitioning to STAGE_RUNNING from STAGE_COMPLETED context
            if 'STAGE_RUNNING' in next_state.upper():
                # Only handle if not coming from IDLE (that's handled by StartWorkflowHandler)
                return True

        return False

    def apply(self, state: Dict[str, Any], api_response: Any) -> Dict[str, Any]:
        """
        Apply NEXT_STAGE transition.

        Args:
            state: Current state JSON
            api_response: Command or API response indicating next stage

        Returns:
            Updated state JSON
        """
        new_state = self._deep_copy_state(state)

        self.info("Applying NEXT_STAGE transition")

        # Get structures
        progress = self._get_progress(new_state)
        location = self._get_location(new_state)
        stages_progress = progress.get('stages', {})
        current_stage = stages_progress.get('current')

        if not current_stage:
            self.warning("No current stage found to transition from")
            # Set FSM to STAGE_COMPLETED since there's nothing to do
            self._update_fsm_state(
                new_state,
                WorkflowState.STAGE_COMPLETED.value,
                'NO_CURRENT_STAGE'
            )
            return new_state

        # Get context for next stage if provided
        context_for_next = api_response.get('context_for_next', {})

        # Store context in current stage before transitioning
        if context_for_next:
            recommendations = context_for_next.get('recommendations_for_next', {})
            if recommendations:
                current_stage['recommendations_for_next'] = recommendations
                self.info("Stored recommendations for next stage")

        # Move current stage to completed
        if 'completed' not in stages_progress:
            stages_progress['completed'] = []

        completed_stage = deepcopy(current_stage)
        completed_stage['completion_status'] = 'success'
        stages_progress['completed'].append(completed_stage)

        # Move to next stage
        remaining_stages = stages_progress.get('remaining', [])
        if not remaining_stages:
            self.warning("No remaining stages to transition to")
            # Transition to WORKFLOW_COMPLETED instead
            self._update_fsm_state(
                new_state,
                WorkflowState.WORKFLOW_COMPLETED.value,
                'NO_MORE_STAGES'
            )
            return new_state

        # Get next stage
        next_stage = remaining_stages[0]
        next_stage_id = next_stage.get('stage_id')

        # Update stages progress
        stages_progress['current'] = next_stage
        stages_progress['remaining'] = remaining_stages[1:]

        # Update location.current
        self._update_location_current(
            new_state,
            stage_id=next_stage_id,
            step_id='clear',
            behavior_id='clear'
        )

        # Clear steps progress (will be initialized when START_STEP is called)
        if 'steps' in progress:
            progress['steps'] = {}

        # Initialize outputs tracking for new stage
        verified_artifacts = next_stage.get('verified_artifacts', {})
        stages_progress['current_outputs'] = self._init_outputs_tracking(
            verified_artifacts
        )

        self.info(f"Advanced to next stage: {next_stage_id}")

        # Update FSM state
        self._update_fsm_state(
            new_state,
            WorkflowState.STAGE_RUNNING.value,
            'NEXT_STAGE'
        )

        # Execute add-text action with stage title markdown, then new_section action
        next_stage_title = next_stage.get('title', '')
        if next_stage_title:
            # Add markdown title for stage
            self._execute_action('add-text', content=f'## {next_stage_title}', shot_type='markdown')
            # Execute new_section action
            self._execute_action('new_section', content=next_stage_title)

        self.info("Transition complete: NEXT_STAGE → STAGE_RUNNING")

        return new_state
