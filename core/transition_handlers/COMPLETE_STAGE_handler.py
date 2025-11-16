"""
COMPLETE_STAGE Event Handler
Handles reflection result indicating stage completion.
Event: COMPLETE_STAGE
Transition: STEP_COMPLETED → STAGE_COMPLETED
"""

from typing import Dict, Any
from copy import deepcopy
from .base_transition_handler import BaseTransitionHandler


class CompleteStageHandler(BaseTransitionHandler):
    """
    Handles COMPLETE_STAGE event.
    Transition: STEP_COMPLETED → STAGE_COMPLETED

    Triggered by: Automatic transition after last step completes
    or by Reflecting API indicating stage complete

    Updates:
    - observation.location.progress.stages.current (completion_status)
    - Outputs tracking for stage
    - state.FSM.state to 'STAGE_COMPLETED'

    Note: After reaching STAGE_COMPLETED, the TransitionCoordinator will automatically
    trigger NEXT_STAGE if there are remaining stages, or COMPLETE_WORKFLOW if this was the last stage.
    """

    def __init__(self):
        super().__init__(
            'STEP_COMPLETED',
            'STAGE_COMPLETED',
            'COMPLETE_STAGE'
        )

    def can_handle(self, api_response: Any) -> bool:
        """
        Check if response indicates stage completion.

        Looks for either:
        - Auto-trigger from state machine
        - 'mark_stage_complete' action in the actions list
        """
        if not isinstance(api_response, dict):
            return False

        # Check if this is an auto-trigger from state machine
        if api_response.get('_auto_trigger') == 'COMPLETE_STAGE':
            return True

        # Check for mark_stage_complete action signal
        actions = api_response.get('actions', [])
        for action in actions:
            if isinstance(action, dict) and action.get('type') == 'mark_stage_complete':
                return True

        return False

    def apply(self, state: Dict[str, Any], api_response: Any) -> Dict[str, Any]:
        """
        Apply COMPLETE_STAGE transition.

        Args:
            state: Current state JSON
            api_response: Reflecting API response or auto-trigger command

        Returns:
            Updated state JSON
        """
        new_state = self._deep_copy_state(state)

        self.info("Applying COMPLETE_STAGE transition")

        # Get structures
        progress = self._get_progress(new_state)
        stages_progress = progress.get('stages', {})
        current_stage = stages_progress.get('current')

        if not current_stage:
            self.warning("No current stage to complete")
            # Set FSM to STAGE_COMPLETED anyway
            self._update_fsm_state(
                new_state,
                'STAGE_COMPLETED',
                'NO_CURRENT_STAGE'
            )
            return new_state

        # Extract API response data if provided
        context_for_next = api_response.get('context_for_next', {}) if isinstance(api_response, dict) else {}
        outputs_tracking = api_response.get('outputs_tracking', {}) if isinstance(api_response, dict) else {}

        # Update context information in current stage before completing it
        if context_for_next:
            # Update whathappened information
            whathappened = context_for_next.get('whathappened', {})
            if whathappened:
                if 'whathappened' not in current_stage:
                    current_stage['whathappened'] = {}
                current_stage['whathappened'].update(whathappened)
                self.info("Updated whathappened context in current stage")

            # Store recommendations for next stage
            recommendations = context_for_next.get('recommendations_for_next', {})
            if recommendations:
                current_stage['recommendations_for_next'] = recommendations
                self.info("Stored recommendations for next stage")

        # Mark current stage as completed
        current_stage['completion_status'] = 'all_steps_completed'

        # Update stage outputs tracking
        stage_outputs = stages_progress.get('current_outputs', {})
        if outputs_tracking.get('produced'):
            if 'produced' not in stage_outputs:
                stage_outputs['produced'] = []

            # Merge new produced items
            for artifact in outputs_tracking['produced']:
                if isinstance(artifact, dict):
                    artifact_name = artifact.get('name')
                else:
                    artifact_name = artifact

                # Check if not already in produced list
                if not any(
                    (item.get('name') if isinstance(item, dict) else item) == artifact_name
                    for item in stage_outputs['produced']
                ):
                    stage_outputs['produced'].append(artifact)

        # Update remaining and in_progress
        stage_outputs['in_progress'] = outputs_tracking.get('in_progress', [])
        stage_outputs['remaining'] = outputs_tracking.get('remaining', [])

        self.info(f"Stage marked as complete: {current_stage.get('stage_id')}")

        # Update FSM state to STAGE_COMPLETED
        self._update_fsm_state(
            new_state,
            'STAGE_COMPLETED',
            'COMPLETE_STAGE'
        )

        self.info("Transition complete: COMPLETE_STAGE → STAGE_COMPLETED")

        return new_state
