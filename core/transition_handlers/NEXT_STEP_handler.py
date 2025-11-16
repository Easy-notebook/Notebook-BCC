"""
NEXT_STEP Event Handler
Handles transition to the next step after completing the current step.
Event: NEXT_STEP
Transition: STEP_COMPLETED → STEP_RUNNING
"""

from typing import Dict, Any
from copy import deepcopy
from .base_transition_handler import BaseTransitionHandler
from ..states import WorkflowState


class NextStepHandler(BaseTransitionHandler):
    """
    Handles NEXT_STEP event.
    Transition: STEP_COMPLETED → STEP_RUNNING

    Triggered by: Automatic transition after STEP_COMPLETED when remaining steps exist

    Updates:
    - observation.location.progress.steps.current to next step
    - observation.location.progress.steps.remaining (removes first item)
    - observation.location.current.step_id to next step ID
    - observation.location.current.behavior_id cleared
    - observation.location.goals to next step's goal
    - Initializes outputs tracking for the new step
    - state.FSM.state to 'STEP_RUNNING'
    """

    def __init__(self):
        super().__init__(
            'STEP_COMPLETED',
            'STEP_RUNNING',
            'NEXT_STEP'
        )

    def can_handle(self, api_response: Any) -> bool:
        """
        Check if response indicates advancing to next step.

        This handler is typically triggered automatically by the state machine
        rather than directly by an API response.
        """
        if isinstance(api_response, dict):
            # Check if this is an auto-trigger from state machine
            if api_response.get('_auto_trigger') == 'NEXT_STEP':
                return True

            next_state = api_response.get('next_state', '')
            transition = api_response.get('transition', '')

            # Check for explicit NEXT_STEP transition
            if 'NEXT_STEP' in transition.upper():
                return True

            # Check if transitioning to STEP_RUNNING from STEP_COMPLETED context
            if 'STEP_RUNNING' in next_state.upper():
                # Only handle if not coming from BEHAVIOR_COMPLETED
                # (that's handled by CompleteStepHandler)
                step_complete = api_response.get('current_step_is_complete')
                if step_complete is None:
                    return True

        return False

    def apply(self, state: Dict[str, Any], api_response: Any) -> Dict[str, Any]:
        """
        Apply NEXT_STEP transition.

        Args:
            state: Current state JSON
            api_response: Command or API response indicating next step

        Returns:
            Updated state JSON
        """
        new_state = self._deep_copy_state(state)

        self.info("Applying NEXT_STEP transition")

        # Get structures
        progress = self._get_progress(new_state)
        location = self._get_location(new_state)
        steps_progress = progress.get('steps', {})
        current_step = steps_progress.get('current')

        if not current_step:
            self.warning("No current step found to transition from")
            # Set FSM to STEP_COMPLETED since there's nothing to do
            self._update_fsm_state(
                new_state,
                WorkflowState.STEP_COMPLETED.value,
                'NO_CURRENT_STEP'
            )
            return new_state

        # Get context for next step if provided
        context_for_next = api_response.get('context_for_next', {})

        # Store context in current step before transitioning
        if context_for_next:
            recommendations = context_for_next.get('recommendations_for_next', {})
            if recommendations:
                current_step['recommendations_for_next'] = recommendations
                self.info("Stored recommendations for next step")

        # Move to next step
        remaining_steps = steps_progress.get('remaining', [])
        if not remaining_steps:
            self.warning("No remaining steps to transition to")
            # Transition to STAGE_COMPLETED instead
            self._update_fsm_state(
                new_state,
                WorkflowState.STAGE_COMPLETED.value,
                'NO_MORE_STEPS'
            )
            return new_state

        # Get next step
        next_step = remaining_steps[0]
        next_step_id = next_step.get('step_id')

        # Update steps progress
        steps_progress['current'] = next_step
        steps_progress['remaining'] = remaining_steps[1:]

        # Update location.current
        self._update_location_current(
            new_state,
            step_id=next_step_id,
            behavior_id='clear'
        )

        # Update location.goals
        location['goals'] = next_step.get('goal', '')

        # Initialize outputs tracking for new step
        verified_artifacts = next_step.get('verified_artifacts', {})
        steps_progress['current_outputs'] = self._init_outputs_tracking(
            verified_artifacts
        )

        self.info(f"Advanced to next step: {next_step_id}")

        # Update FSM state
        self._update_fsm_state(
            new_state,
            WorkflowState.STEP_RUNNING.value,
            'NEXT_STEP'
        )

        # Execute new_step action (will add "### {title}" markdown automatically)
        next_step_title = next_step.get('title', '')
        if next_step_title:
            self._execute_action('new_step', content=next_step_title)

        self.info("Transition complete: NEXT_STEP → STEP_RUNNING")

        # Sync notebook data to state before returning
        self._sync_notebook_to_state(new_state)

        return new_state
