"""
START_STEP Handler
Handles: STAGE_RUNNING → STEP_RUNNING transition

Responsibilities:
1. Call Planning API (/planning) to get steps definition for current stage
2. Parse XML response to extract steps
3. Update current stage with steps
4. Set current_step_id to first step
5. Trigger START_BEHAVIOR transition (or check if step already achieved)
"""

from typing import Any, Dict
from silantui import ModernLogger


class StartStepHandler(ModernLogger):
    """Handler for START_STEP transition."""

    def __init__(self):
        super().__init__("StartStepHandler")

    def handle(self, state_machine, payload: Any = None) -> None:
        """
        Handle START_STEP transition.

        Args:
            state_machine: WorkflowStateMachine instance
            payload: Optional payload data
        """
        self.info("[Handler] START_STEP: STAGE_RUNNING → STEP_RUNNING")

        if not state_machine.pipeline_store:
            self.error("[Handler] Pipeline store not available")
            from core.events import WorkflowEvent
            state_machine.transition(WorkflowEvent.FAIL, {'error': 'Pipeline store not available'})
            return

        ctx = state_machine.execution_context.workflow_context

        if not ctx.current_stage_id:
            self.error("[Handler] No current stage ID")
            from core.events import WorkflowEvent
            state_machine.transition(WorkflowEvent.FAIL, {'error': 'No current stage'})
            return

        try:
            # Call Planning API to get steps definition
            from utils.api_client import workflow_api_client
            from utils.state_builder import build_api_state

            current_state = build_api_state(state_machine, require_progress_info=True)

            self.info(f"[Handler] Calling Planning API for steps of stage: {ctx.current_stage_id}")

            planning_response = workflow_api_client.send_feedback_sync(
                stage_id=ctx.current_stage_id,
                step_index=ctx.current_step_id or "",
                state=current_state
            )

            # Parse response
            response_type = planning_response.get('type')
            self.info(f"[Handler] Planning API response type: {response_type}")

            if response_type == 'steps':
                # Update steps using workflow_updater
                from utils.workflow_updater import workflow_updater
                workflow_updater.update_from_response(state_machine, planning_response)

                if not ctx.current_step_id:
                    self.error("[Handler] Failed to set current_step_id")
                    from core.events import WorkflowEvent
                    state_machine.transition(WorkflowEvent.FAIL, {'error': 'Failed to set current step'})
                    return

                self.info(f"[Handler] Steps updated, current step: {ctx.current_step_id}")

                # Transition to START_BEHAVIOR
                from core.events import WorkflowEvent
                state_machine.transition(WorkflowEvent.START_BEHAVIOR)

            elif response_type == 'json':
                # Check if target already achieved
                content = planning_response.get('content', {})
                target_achieved = content.get('targetAchieved', False)

                if target_achieved:
                    self.info("[Handler] Stage target already achieved per Planning API")
                    from core.events import WorkflowEvent
                    state_machine.transition(WorkflowEvent.COMPLETE_STAGE)
                else:
                    self.info("[Handler] Proceeding to START_BEHAVIOR")
                    from core.events import WorkflowEvent
                    state_machine.transition(WorkflowEvent.START_BEHAVIOR)

            else:
                self.error(f"[Handler] Unexpected response type: {response_type}")
                from core.events import WorkflowEvent
                state_machine.transition(WorkflowEvent.FAIL, {'error': f'Unexpected response type: {response_type}'})

        except Exception as e:
            self.error(f"[Handler] Failed to start step: {e}", exc_info=True)
            from core.events import WorkflowEvent
            state_machine.transition(WorkflowEvent.FAIL, {'error': str(e)})


# Create singleton instance
handle_start_step = StartStepHandler().handle
