"""
START_WORKFLOW Handler
Handles: IDLE → STAGE_RUNNING transition

Responsibilities:
1. Call Planning API (/planning) to get workflow stages definition
2. Parse XML response to extract stages
3. Create/update WorkflowTemplate with stages
4. Set current_stage_id to first stage
5. Trigger START_STEP transition
"""

from typing import Any, Dict
from silantui import ModernLogger


class StartWorkflowHandler(ModernLogger):
    """Handler for START_WORKFLOW transition."""

    def __init__(self):
        super().__init__("StartWorkflowHandler")

    def handle(self, state_machine, payload: Any = None) -> None:
        """
        Handle START_WORKFLOW transition.

        Args:
            state_machine: WorkflowStateMachine instance
            payload: Optional payload data
        """
        self.info("[Handler] START_WORKFLOW: IDLE → STAGE_RUNNING")

        if not state_machine.pipeline_store:
            self.error("[Handler] Pipeline store not available")
            from core.events import WorkflowEvent
            state_machine.transition(WorkflowEvent.FAIL, {'error': 'Pipeline store not available'})
            return

        try:
            # Call Planning API to get stages definition
            from utils.api_client import workflow_api_client
            from utils.state_builder import build_api_state

            current_state = build_api_state(state_machine, require_progress_info=True)

            self.info("[Handler] Calling Planning API for stages definition...")

            planning_response = workflow_api_client.send_feedback_sync(
                stage_id="",  # Empty for initial request
                step_index="",
                state=current_state
            )

            # Parse response
            response_type = planning_response.get('type')
            self.info(f"[Handler] Planning API response type: {response_type}")

            if response_type != 'stages':
                self.error(f"[Handler] Expected 'stages' response, got '{response_type}'")
                from core.events import WorkflowEvent
                state_machine.transition(WorkflowEvent.FAIL, {'error': f'Unexpected response type: {response_type}'})
                return

            # Update workflow using workflow_updater
            from utils.workflow_updater import workflow_updater
            workflow_updater.update_from_response(state_machine, planning_response)

            ctx = state_machine.execution_context.workflow_context

            if not ctx.current_stage_id:
                self.error("[Handler] Failed to set current_stage_id")
                from core.events import WorkflowEvent
                state_machine.transition(WorkflowEvent.FAIL, {'error': 'Failed to set current stage'})
                return

            self.info(f"[Handler] Workflow initialized with {len(planning_response['content']['stages'])} stages")
            self.info(f"[Handler] Current stage: {ctx.current_stage_id}")

            # Transition to START_STEP
            from core.events import WorkflowEvent
            state_machine.transition(WorkflowEvent.START_STEP)

        except Exception as e:
            self.error(f"[Handler] Failed to start workflow: {e}", exc_info=True)
            from core.events import WorkflowEvent
            state_machine.transition(WorkflowEvent.FAIL, {'error': str(e)})


# Create singleton instance
handle_start_workflow = StartWorkflowHandler().handle
