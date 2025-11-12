"""
START_BEHAVIOR Event Handler
Handles behavior initialization from planning API.
Event: START_BEHAVIOR
Transition: STEP_RUNNING → BEHAVIOR_RUNNING
"""

from typing import Dict, Any
from .base_transition_handler import BaseTransitionHandler


class StartBehaviorHandler(BaseTransitionHandler):
    """
    Handles START_BEHAVIOR event.
    Transition: STEP_RUNNING → BEHAVIOR_RUNNING

    Triggered by: Planning API returning behavior definition

    Updates:
    - observation.location.progress.behaviors with new behavior
    - observation.location.current with behavior_id and iteration
    - observation.location.goals with behavior task
    - state.FSM.state to 'BEHAVIOR_RUNNING'
    """

    def __init__(self):
        super().__init__('STEP_RUNNING', 'BEHAVIOR_RUNNING', 'START_BEHAVIOR')

    def can_handle(self, api_response: Any) -> bool:
        """Check if response contains behavior definition."""
        if isinstance(api_response, dict):
            # Check for behavior fields
            has_behavior_id = 'behavior_id' in api_response
            has_agent = 'agent' in api_response
            has_task = 'task' in api_response
            return has_behavior_id and (has_agent or has_task)
        return False

    def apply(self, state: Dict[str, Any], api_response: Any) -> Dict[str, Any]:
        """
        Apply START_BEHAVIOR transition.

        Args:
            state: Current state JSON
            api_response: Planning API response with behavior

        Returns:
            Updated state JSON
        """
        new_state = self._deep_copy_state(state)

        # Extract behavior fields
        behavior_id = api_response.get('behavior_id')
        step_id = api_response.get('step_id')
        agent = api_response.get('agent')
        task = api_response.get('task', '').strip()
        inputs = api_response.get('inputs', {})
        outputs = api_response.get('outputs', {})
        acceptance = api_response.get('acceptance', [])
        whathappened = api_response.get('whathappened', {})

        self.info(f"Applying behavior: {behavior_id}")

        # Get structures
        progress = self._get_progress(new_state)
        behaviors_progress = progress.setdefault('behaviors', {})
        location = self._get_location(new_state)

        # Build current behavior
        current_behavior = {
            'behavior_id': behavior_id,
            'step_id': step_id,
            'agent': agent,
            'task': task,
            'inputs': inputs,
            'outputs': outputs,
            'acceptance': acceptance
        }

        if whathappened:
            current_behavior['whathappened'] = whathappened

        # Update behaviors progress
        behaviors_progress['current'] = current_behavior
        behaviors_progress['completed'] = []
        behaviors_progress['iteration'] = 1
        behaviors_progress['focus'] = task

        # Initialize outputs tracking
        expected_outputs = [
            {'name': name, 'description': desc}
            for name, desc in outputs.items()
        ]
        behaviors_progress['current_outputs'] = {
            'expected': expected_outputs,
            'produced': [],
            'in_progress': []
        }

        # Update location.current
        self._update_location_current(
            new_state,
            behavior_id=behavior_id,
            behavior_iteration=1
        )

        # Update location.goals
        if task:
            location['goals'] = task

        # Update FSM state
        self._update_fsm_state(new_state, 'BEHAVIOR_RUNNING', 'START_BEHAVIOR')

        self.info(f"Transition complete: START_BEHAVIOR (behavior: {behavior_id})")

        return new_state
