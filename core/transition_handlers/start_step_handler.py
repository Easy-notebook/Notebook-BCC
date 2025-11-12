"""
START_STEP Event Handler
Handles step initialization with steps from planning API.
Event: START_STEP
Transition: STAGE_RUNNING → STEP_RUNNING
"""

from typing import Dict, Any
from .base_transition_handler import BaseTransitionHandler


class StartStepHandler(BaseTransitionHandler):
    """
    Handles START_STEP event.
    Transition: STAGE_RUNNING → STEP_RUNNING

    Triggered by: Planning API returning steps list

    Updates:
    - observation.location.progress.steps with new steps
    - observation.location.current with first step
    - state.FSM.state to 'STEP_RUNNING'
    """

    def __init__(self):
        super().__init__('STAGE_RUNNING', 'STEP_RUNNING', 'START_STEP')

    def can_handle(self, api_response: Any) -> bool:
        """Check if response contains steps list."""
        if isinstance(api_response, dict):
            return 'steps' in api_response and isinstance(api_response['steps'], list)
        return False

    def apply(self, state: Dict[str, Any], api_response: Any) -> Dict[str, Any]:
        """
        Apply START_STEP transition.

        Args:
            state: Current state JSON
            api_response: Planning API response with steps

        Returns:
            Updated state JSON
        """
        new_state = self._deep_copy_state(state)

        steps_data = api_response.get('steps', [])
        focus = api_response.get('focus', '')
        goals = api_response.get('goals', '')

        self.info(f"Applying {len(steps_data)} steps")

        if not steps_data:
            self.warning("No steps in planning response")
            return new_state

        # Get structures
        progress = self._get_progress(new_state)
        steps_progress = progress.setdefault('steps', {})

        # Build first step (current)
        first_step = steps_data[0]
        current_step = {
            'step_id': first_step.get('step_id'),
            'title': first_step.get('title', ''),
            'goal': first_step.get('goal', ''),
            'verified_artifacts': first_step.get('verified_artifacts', {}),
            'required_variables': first_step.get('required_variables', {}),
            'pcs_considerations': first_step.get('pcs_considerations', {})
        }

        # Update steps progress
        steps_progress['current'] = current_step
        steps_progress['completed'] = []
        steps_progress['focus'] = focus

        # Build remaining steps
        remaining_steps = []
        for step_data in steps_data[1:]:
            remaining_step = {
                'step_id': step_data.get('step_id'),
                'title': step_data.get('title', ''),
                'goal': step_data.get('goal', ''),
                'verified_artifacts': step_data.get('verified_artifacts', {}),
                'required_variables': step_data.get('required_variables', {}),
                'pcs_considerations': step_data.get('pcs_considerations', {})
            }
            remaining_steps.append(remaining_step)

        steps_progress['remaining'] = remaining_steps

        # Initialize outputs tracking
        steps_progress['current_outputs'] = self._init_outputs_tracking(
            first_step.get('verified_artifacts', {})
        )

        # Update location
        location = self._get_location(new_state)
        self._update_location_current(
            new_state,
            step_id=first_step.get('step_id'),
            behavior_id='clear'
        )

        if goals:
            location['goals'] = goals

        # Update FSM state
        self._update_fsm_state(new_state, 'STEP_RUNNING', 'START_STEP')

        self.info(f"Transition complete: START_STEP (step: {first_step.get('step_id')})")

        return new_state
