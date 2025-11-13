"""
START_WORKFLOW Event Handler
Handles workflow initialization with stages from planning API.
Event: START_WORKFLOW
Transition: IDLE → STAGE_RUNNING
"""

from typing import Dict, Any
from .base_transition_handler import BaseTransitionHandler


class StartWorkflowHandler(BaseTransitionHandler):
    """
    Handles START_WORKFLOW event.
    Transition: IDLE → STAGE_RUNNING

    Triggered by: Planning API returning stages list

    Updates:
    - observation.location.progress.stages with new stages
    - observation.location.current with first stage
    - state.FSM.state to 'STAGE_RUNNING'
    """

    def __init__(self):
        super().__init__('IDLE', 'STAGE_RUNNING', 'START_WORKFLOW')

    def can_handle(self, api_response: Any) -> bool:
        """Check if response contains stages list."""
        if isinstance(api_response, dict):
            return 'stages' in api_response and isinstance(api_response['stages'], list)
        return False

    def apply(self, state: Dict[str, Any], api_response: Any) -> Dict[str, Any]:
        """
        Apply START_WORKFLOW transition.

        Args:
            state: Current state JSON
            api_response: Planning API response with stages

        Returns:
            Updated state JSON
        """
        new_state = self._deep_copy_state(state)

        stages_data = api_response.get('stages', [])
        focus = api_response.get('focus', '')

        self.info(f"Applying {len(stages_data)} stages")

        if not stages_data:
            self.warning("No stages in planning response")
            return new_state

        # Get structures
        progress = self._get_progress(new_state)
        stages_progress = progress.setdefault('stages', {})

        # Build first stage (current)
        first_stage = stages_data[0]
        current_stage = {
            'stage_id': first_stage.get('stage_id'),
            'title': first_stage.get('title', ''),
            'goal': first_stage.get('goal', ''),
            'verified_artifacts': first_stage.get('verified_artifacts', {})
        }

        # Update stages progress
        stages_progress['current'] = current_stage
        stages_progress['completed'] = []
        stages_progress['focus'] = focus

        # Build remaining stages
        remaining_stages = []
        for stage_data in stages_data[1:]:
            remaining_stage = {
                'stage_id': stage_data.get('stage_id'),
                'title': stage_data.get('title', ''),
                'goal': stage_data.get('goal', ''),
                'verified_artifacts': stage_data.get('verified_artifacts', {})
            }
            if 'required_variables' in stage_data:
                remaining_stage['required_variables'] = stage_data['required_variables']
            remaining_stages.append(remaining_stage)

        stages_progress['remaining'] = remaining_stages

        # Initialize outputs tracking
        stages_progress['current_outputs'] = self._init_outputs_tracking(
            first_stage.get('verified_artifacts', {})
        )

        # Update location.current
        self._update_location_current(
            new_state,
            stage_id=first_stage.get('stage_id'),
            step_id='clear',
            behavior_id='clear'
        )

        # Update FSM state
        self._update_fsm_state(new_state, 'STAGE_RUNNING', 'START_WORKFLOW')

        # Execute update_title action with workflow focus
        if focus:
            self._execute_action('update_title', content=focus)

        # Execute new_section action with first stage title
        first_stage_title = first_stage.get('title', '')
        if first_stage_title:
            self._execute_action('new_section', content=first_stage_title)

        self.info(f"Transition complete: START_WORKFLOW (stage: {first_stage.get('stage_id')})")

        return new_state
