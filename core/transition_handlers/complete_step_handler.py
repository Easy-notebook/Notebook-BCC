"""
COMPLETE_STEP Event Handler
Handles reflection result indicating step completion.
Event: COMPLETE_STEP
Transition: BEHAVIOR_COMPLETED → STEP_COMPLETED (or STEP_RUNNING if advancing to next step)
"""

from typing import Dict, Any
from copy import deepcopy
from .base_transition_handler import BaseTransitionHandler


class CompleteStepHandler(BaseTransitionHandler):
    """
    Handles COMPLETE_STEP event.
    Transition: BEHAVIOR_COMPLETED → STEP_COMPLETED

    Triggered by: Reflecting API indicating behavior and step complete
    (behavior_is_complete=True, next_state=STEP_COMPLETED)

    Updates:
    - state.variables with new variables_produced
    - observation.location.progress.behaviors.completed list
    - observation.location.progress.steps.completed list
    - Outputs tracking for both behavior and step
    - Advances to next step if available
    - state.FSM.state to 'STEP_RUNNING' (for next step) or 'STEP_COMPLETED'
    """

    def __init__(self):
        super().__init__(
            'BEHAVIOR_COMPLETED',
            'STEP_COMPLETED',
            'COMPLETE_STEP'
        )

    def can_handle(self, api_response: Any) -> bool:
        """Check if response indicates step completion."""
        if isinstance(api_response, dict):
            next_state = api_response.get('next_state', '')
            behavior_complete = api_response.get('behavior_is_complete', False)

            # Check for explicit STEP_COMPLETED(D) state
            next_state_upper = next_state.upper()
            if 'STEP_COMPLETED' in next_state_upper:
                return True

            # Or if behavior is complete but not explicitly STEP_RUNNING
            if behavior_complete and 'STEP_RUNNING' not in next_state_upper:
                return True

        return False

    def apply(self, state: Dict[str, Any], api_response: Any) -> Dict[str, Any]:
        """
        Apply COMPLETE_STEP transition.

        Args:
            state: Current state JSON
            api_response: Reflecting API response

        Returns:
            Updated state JSON
        """
        new_state = self._deep_copy_state(state)

        behavior_is_complete = api_response.get('behavior_is_complete', False)
        next_state = api_response.get('next_state', 'STATE_Step_Running')
        variables_produced = api_response.get('variables_produced', {})
        artifacts_produced = api_response.get('artifacts_produced', [])
        outputs_tracking = api_response.get('outputs_tracking', {})

        self.info(
            f"Applying reflection: behavior_complete={behavior_is_complete}, "
            f"next_state={next_state}"
        )

        # Get structures
        state_data = self._get_state_data(new_state)
        progress = self._get_progress(new_state)
        location = self._get_location(new_state)

        # Add new variables
        if variables_produced:
            current_vars = state_data.setdefault('variables', {})
            current_vars.update(variables_produced)
            self.info(f"Added {len(variables_produced)} new variables")

        # Complete current behavior
        self._complete_behavior(new_state, artifacts_produced, outputs_tracking)

        # If next_state is STEP_RUNNING, advance to next step
        if 'STEP_RUNNING' in next_state.upper():
            self._transition_to_next_step(new_state, outputs_tracking, artifacts_produced)
            final_state = next_state
            transition_name = 'TRANSITION_TO_Step_Running'
        else:
            # Otherwise just mark as complete
            final_state = next_state
            transition_name = 'COMPLETE_STEP'

        # Update FSM state
        self._update_fsm_state(new_state, final_state, transition_name)

        self.info(f"Transition complete: COMPLETE_STEP → {final_state}")

        return new_state

    def _complete_behavior(
        self,
        state: Dict[str, Any],
        artifacts_produced: list,
        outputs_tracking: Dict[str, Any]
    ) -> None:
        """Mark current behavior as completed."""
        progress = self._get_progress(state)
        behaviors_progress = progress.get('behaviors', {})
        current_behavior = behaviors_progress.get('current')

        if current_behavior:
            if 'completed' not in behaviors_progress:
                behaviors_progress['completed'] = []

            completed_behavior = deepcopy(current_behavior)
            completed_behavior['completion_status'] = 'success'
            completed_behavior['artifacts_produced'] = [
                a['name'] if isinstance(a, dict) else a
                for a in artifacts_produced
            ]

            behaviors_progress['completed'].append(completed_behavior)
            behaviors_progress['current'] = None
            self.info(f"Behavior completed: {current_behavior.get('behavior_id')}")

        # Update behavior outputs tracking
        behavior_outputs = behaviors_progress.get('current_outputs', {})
        if outputs_tracking.get('produced'):
            behavior_outputs['produced'] = outputs_tracking['produced']
        behavior_outputs['in_progress'] = outputs_tracking.get('in_progress', [])
        behavior_outputs['remaining'] = outputs_tracking.get('remaining', [])

    def _transition_to_next_step(
        self,
        state: Dict[str, Any],
        outputs_tracking: Dict[str, Any],
        artifacts_produced: list
    ) -> None:
        """Transition to the next step."""
        progress = self._get_progress(state)
        location = self._get_location(state)
        steps_progress = progress.get('steps', {})
        current_step = steps_progress.get('current')

        if current_step:
            # Mark current step as complete
            if 'completed' not in steps_progress:
                steps_progress['completed'] = []

            completed_step = deepcopy(current_step)
            completed_step['artifacts_produced'] = outputs_tracking.get('produced', [])
            completed_step['completion_status'] = 'all_acceptance_criteria_passed'

            steps_progress['completed'].append(completed_step)
            self.info(f"Step completed: {current_step.get('step_id')}")

            # Move to next step if available
            remaining_steps = steps_progress.get('remaining', [])
            if remaining_steps:
                next_step = remaining_steps[0]
                steps_progress['current'] = next_step
                steps_progress['remaining'] = remaining_steps[1:]

                # Update location
                self._update_location_current(
                    state,
                    step_id=next_step.get('step_id'),
                    behavior_id='clear'
                )
                location['goals'] = next_step.get('goal', '')

                # Update step outputs
                steps_progress['current_outputs'] = self._init_outputs_tracking(
                    next_step.get('verified_artifacts', {})
                )

                self.info(f"Advanced to next step: {next_step.get('step_id')}")

        # Update stage outputs tracking
        stages_progress = progress.get('stages', {})
        stage_outputs = stages_progress.get('current_outputs', {})

        if outputs_tracking.get('produced'):
            if 'produced' not in stage_outputs:
                stage_outputs['produced'] = []

            for artifact_name in outputs_tracking['produced']:
                if not any(item.get('name') == artifact_name for item in stage_outputs['produced']):
                    description = next(
                        (a.get('name') if isinstance(a, dict) else a
                         for a in artifacts_produced if
                         (a.get('name') if isinstance(a, dict) else a) == artifact_name),
                        artifact_name
                    )
                    stage_outputs['produced'].append({
                        'name': artifact_name,
                        'description': description
                    })
