"""
NEXT_BEHAVIOR Event Handler
Handles reflection result indicating more behaviors needed.
Event: NEXT_BEHAVIOR
Transition: BEHAVIOR_COMPLETED → BEHAVIOR_RUNNING
"""

from typing import Dict, Any
from copy import deepcopy
from .base_transition_handler import BaseTransitionHandler


class NextBehaviorHandler(BaseTransitionHandler):
    """
    Handles NEXT_BEHAVIOR event.
    Transition: BEHAVIOR_COMPLETED → BEHAVIOR_RUNNING

    Triggered by: Reflecting API indicating behavior incomplete,
    need another behavior iteration (current_step_is_complete=False)

    Updates:
    - state.variables with new variables_produced
    - observation.location.progress.behaviors.completed list (if behavior complete)
    - Outputs tracking
    - state.FSM.state to 'BEHAVIOR_RUNNING'
    """

    def __init__(self):
        super().__init__(
            'BEHAVIOR_COMPLETED',
            'BEHAVIOR_RUNNING',
            'NEXT_BEHAVIOR'
        )

    def can_handle(self, api_response: Any) -> bool:
        """Check if response indicates need for another behavior iteration."""
        if isinstance(api_response, dict):
            next_state = api_response.get('next_state', '')
            step_complete = api_response.get('current_step_is_complete', False)
            transition = api_response.get('transition', '')

            # Check for explicit NEXT_BEHAVIOR transition
            if 'NEXT_BEHAVIOR' in transition.upper():
                return True

            # Check if explicitly transitioning to BEHAVIOR_RUNNING (need another iteration)
            if 'BEHAVIOR_RUNNING' in next_state.upper():
                return True

            # Or if step not complete and no explicit next_state specified
            # (but avoid conflicting with STEP_RUNNING which is handled by CompleteStepHandler)
            if not step_complete and not next_state:
                return True

        return False

    def apply(self, state: Dict[str, Any], api_response: Any) -> Dict[str, Any]:
        """
        Apply NEXT_BEHAVIOR transition.

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
            f"Applying NEXT_BEHAVIOR: step_complete={current_step_is_complete}"
        )

        # Get structures
        state_data = self._get_state_data(new_state)
        progress = self._get_progress(new_state)

        # Add new variables
        if variables_produced:
            current_vars = state_data.setdefault('variables', {})
            current_vars.update(variables_produced)
            self.info(f"Added {len(variables_produced)} new variables")

        # Update context information in current behavior
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

                # Store recommendations for next iteration
                recommendations = context_for_next.get('recommendations_for_next', {})
                if recommendations:
                    current_behavior['recommendations_for_next'] = recommendations
                    self.info("Stored recommendations for next iteration")

        # Update behaviors if complete (rarely happens in NEXT_BEHAVIOR, but possible)
        if current_step_is_complete:
            self._complete_behavior(new_state, artifacts_produced, outputs_tracking)

        # Update FSM state to BEHAVIOR_RUNNING (ready for next behavior iteration)
        self._update_fsm_state(
            new_state,
            'BEHAVIOR_RUNNING',
            'NEXT_BEHAVIOR'
        )

        self.info("Transition complete: NEXT_BEHAVIOR → BEHAVIOR_RUNNING")

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
