"""
COMPLETE_STEP Event Handler
Handles reflection result indicating step completion.
Event: COMPLETE_STEP
Transition: BEHAVIOR_COMPLETED → STEP_COMPLETED
"""

from typing import Dict, Any
from copy import deepcopy
from .base_transition_handler import BaseTransitionHandler


class CompleteStepHandler(BaseTransitionHandler):
    """
    Handles COMPLETE_STEP event.
    Transition: BEHAVIOR_COMPLETED → STEP_COMPLETED

    Triggered by: Reflecting API indicating behavior and step complete
    (current_step_is_complete=True, next_state=STEP_COMPLETED)

    Updates:
    - state.variables with new variables_produced
    - observation.location.progress.behaviors.completed list
    - observation.location.progress.steps.completed list
    - Outputs tracking for both behavior and step
    - state.FSM.state to 'STEP_COMPLETED'

    Note: After reaching STEP_COMPLETED, the TransitionCoordinator will automatically
    trigger NEXT_STEP if there are remaining steps, or COMPLETE_STAGE if this was the last step.
    """

    def __init__(self):
        super().__init__(
            'BEHAVIOR_COMPLETED',
            'STEP_COMPLETED',
            'COMPLETE_STEP'
        )

    def can_handle(self, api_response: Any) -> bool:
        """
        Check if response indicates step completion.

        Looks for 'mark_step_complete' action in the actions list.
        """
        if not isinstance(api_response, dict):
            return False

        # Don't handle auto-triggered transitions
        if api_response.get('_auto_trigger'):
            return False

        # Check for mark_step_complete action signal
        actions = api_response.get('actions', [])
        for action in actions:
            if isinstance(action, dict) and action.get('type') == 'mark_step_complete':
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

        current_step_is_complete = api_response.get('current_step_is_complete', False)
        variables_produced = api_response.get('variables_produced', {})
        artifacts_produced = api_response.get('artifacts_produced', [])
        outputs_tracking = api_response.get('outputs_tracking', {})
        context_for_next = api_response.get('context_for_next', {})

        self.info(
            f"Applying COMPLETE_STEP: step_complete={current_step_is_complete}"
        )

        # Get structures
        state_data = self._get_state_data(new_state)
        progress = self._get_progress(new_state)

        # Add new variables
        if variables_produced:
            current_vars = state_data.setdefault('variables', {})
            current_vars.update(variables_produced)
            self.info(f"Added {len(variables_produced)} new variables")

        # Update context information in current behavior before completing it
        if context_for_next:
            behaviors_progress = progress.get('behaviors', {})
            current_behavior = behaviors_progress.get('current')
            if current_behavior:
                # Update whathappened information
                whathappened = context_for_next.get('whathappened', {})
                if whathappened:
                    if 'whathappened' not in current_behavior:
                        current_behavior['whathappened'] = {}
                    current_behavior['whathappened'].update(whathappened)
                    self.info("Updated whathappened context in current behavior")

                # Store recommendations for next step
                recommendations = context_for_next.get('recommendations_for_next', {})
                if recommendations:
                    current_behavior['recommendations_for_next'] = recommendations
                    self.info("Stored recommendations for next step")

        # Complete current behavior
        self._complete_behavior(new_state, artifacts_produced, outputs_tracking)

        # Complete current step and update tracking
        self._complete_current_step(new_state, outputs_tracking, artifacts_produced)

        # Update FSM state to STEP_COMPLETED
        self._update_fsm_state(
            new_state,
            'STEP_COMPLETED',
            'COMPLETE_STEP'
        )

        self.info("Transition complete: COMPLETE_STEP → STEP_COMPLETED")

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

    def _complete_current_step(
        self,
        state: Dict[str, Any],
        outputs_tracking: Dict[str, Any],
        artifacts_produced: list
    ) -> None:
        """
        Mark current step as completed and update tracking.

        Note: Does NOT move current step to completed list or clear current.
        That will be done by NEXT_STEP_handler when transitioning to next step.
        """
        progress = self._get_progress(state)
        steps_progress = progress.get('steps', {})
        current_step = steps_progress.get('current')

        if not current_step:
            self.warning("No current step to complete")
            return

        # Just mark completion status in current step
        # Don't move to completed list yet - NEXT_STEP_handler will do that
        current_step['completion_status'] = 'all_acceptance_criteria_passed'
        current_step['artifacts_produced'] = outputs_tracking.get('produced', [])

        self.info(f"Step marked as complete: {current_step.get('step_id')}")

        # Update step outputs tracking
        step_outputs = steps_progress.get('current_outputs', {})
        if outputs_tracking.get('produced'):
            step_outputs['produced'] = outputs_tracking['produced']
        step_outputs['in_progress'] = outputs_tracking.get('in_progress', [])
        step_outputs['remaining'] = outputs_tracking.get('remaining', [])

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
