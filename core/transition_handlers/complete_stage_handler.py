"""
COMPLETE_STAGE Handler
Handles: STAGE_RUNNING → STAGE_COMPLETED transition

Responsibilities:
1. Call Reflecting API (/reflecting) with stage completion feedback
2. Parse JSON response
3. Apply context updates
4. Check if workflow is complete (targetAchieved at workflow level)
5. Trigger COMPLETE_WORKFLOW or NEXT_STAGE
"""

from typing import Any, Dict
from silantui import ModernLogger


class CompleteStageHandler(ModernLogger):
    """Handler for COMPLETE_STAGE transition."""

    def __init__(self):
        super().__init__("CompleteStageHandler")

    def handle(self, state_machine, payload: Any = None) -> None:
        """
        Handle COMPLETE_STAGE transition.

        Args:
            state_machine: WorkflowStateMachine instance
            payload: Optional payload data
        """
        self.info("[Handler] COMPLETE_STAGE: STAGE_RUNNING → STAGE_COMPLETED")

        ctx = state_machine.execution_context.workflow_context
        workflow = state_machine.pipeline_store.workflow_template

        if not ctx.current_stage_id:
            self.error("[Handler] Missing stage ID")
            from core.events import WorkflowEvent
            state_machine.transition(WorkflowEvent.FAIL, {'error': 'Missing stage'})
            return

        try:
            # Call Reflecting API
            from utils.api_client import workflow_api_client
            from utils.state_builder import build_api_state

            current_state = build_api_state(state_machine, require_progress_info=True)

            self.info(f"[Handler] Calling Reflecting API for stage completion")

            reflecting_response = workflow_api_client.send_reflecting_sync(
                stage_id=ctx.current_stage_id,
                step_index=ctx.current_step_id or "completed",
                state=current_state
            )

            response_type = reflecting_response.get('type')
            self.info(f"[Handler] Reflecting API response type: {response_type}")

            # Update context from response
            from utils.workflow_updater import workflow_updater
            workflow_updater.update_from_response(state_machine, reflecting_response)

            # Check if workflow is complete
            target_achieved = False
            if response_type == 'json':
                content = reflecting_response.get('content', {})
                target_achieved = content.get('targetAchieved', False)

            from core.events import WorkflowEvent
            if target_achieved:
                self.info("[Handler] Workflow complete per Reflecting API")
                state_machine.transition(WorkflowEvent.COMPLETE_WORKFLOW)
            else:
                # Check if there are more stages
                next_stage = workflow.get_next_stage(ctx.current_stage_id) if workflow else None
                if next_stage:
                    ctx.current_stage_id = next_stage.id
                    ctx.current_step_id = next_stage.steps[0].id if next_stage.steps else None
                    ctx.reset_for_new_step()
                    self.info(f"[Handler] Moving to next stage: {ctx.current_stage_id}")
                    state_machine.transition(WorkflowEvent.NEXT_STAGE)
                else:
                    self.info("[Handler] No more stages, completing workflow")
                    state_machine.transition(WorkflowEvent.COMPLETE_WORKFLOW)

        except Exception as e:
            self.error(f"[Handler] Failed to complete stage: {e}", exc_info=True)
            from core.events import WorkflowEvent
            # Fallback: check if there are more stages
            next_stage = workflow.get_next_stage(ctx.current_stage_id) if workflow else None
            if next_stage:
                ctx.current_stage_id = next_stage.id
                ctx.current_step_id = next_stage.steps[0].id if next_stage.steps else None
                ctx.reset_for_new_step()
                state_machine.transition(WorkflowEvent.NEXT_STAGE)
            else:
                state_machine.transition(WorkflowEvent.COMPLETE_WORKFLOW)


# Create singleton instance
handle_complete_stage = CompleteStageHandler().handle
