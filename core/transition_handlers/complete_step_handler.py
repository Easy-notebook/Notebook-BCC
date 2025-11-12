"""
COMPLETE_STEP Handler
Handles: STEP_RUNNING → STEP_COMPLETED transition

Responsibilities:
1. Call Reflecting API (/reflecting) with step completion feedback
2. Parse JSON response
3. Apply context updates
4. Check if stage is complete (targetAchieved)
5. Trigger COMPLETE_STAGE or NEXT_STEP
"""

from typing import Any, Dict
from silantui import ModernLogger


class CompleteStepHandler(ModernLogger):
    """Handler for COMPLETE_STEP transition."""

    def __init__(self):
        super().__init__("CompleteStepHandler")

    def handle(self, state_machine, payload: Any = None) -> None:
        """
        Handle COMPLETE_STEP transition.

        Args:
            state_machine: WorkflowStateMachine instance
            payload: Optional payload data
        """
        self.info("[Handler] COMPLETE_STEP: STEP_RUNNING → STEP_COMPLETED")

        ctx = state_machine.execution_context.workflow_context
        workflow = state_machine.pipeline_store.workflow_template

        if not ctx.current_stage_id or not ctx.current_step_id:
            self.error("[Handler] Missing stage/step ID")
            from core.events import WorkflowEvent
            state_machine.transition(WorkflowEvent.FAIL, {'error': 'Missing stage/step'})
            return

        try:
            # Call Reflecting API
            from utils.api_client import workflow_api_client
            from utils.state_builder import build_api_state

            current_state = build_api_state(state_machine, require_progress_info=True)

            # Extract notebook_id from state
            notebook_id = current_state.get('state', {}).get('notebook', {}).get('notebook_id')

            self.info(f"[Handler] Calling Reflecting API for step completion")

            reflecting_response = workflow_api_client.send_reflecting_sync(
                stage_id=ctx.current_stage_id,
                step_index=ctx.current_step_id,
                state=current_state,
                notebook_id=notebook_id
            )

            response_type = reflecting_response.get('type')
            self.info(f"[Handler] Reflecting API response type: {response_type}")

            # Update context from response
            from utils.workflow_updater import workflow_updater
            workflow_updater.update_from_response(state_machine, reflecting_response)

            # Check if stage is complete
            target_achieved = False
            if response_type == 'json':
                content = reflecting_response.get('content', {})
                target_achieved = content.get('targetAchieved', False)

            from core.events import WorkflowEvent
            if target_achieved:
                self.info("[Handler] Stage complete per Reflecting API")
                state_machine.transition(WorkflowEvent.COMPLETE_STAGE)
            else:
                # Check if there are more steps
                next_step = workflow.get_next_step(ctx.current_stage_id, ctx.current_step_id)
                if next_step:
                    ctx.current_step_id = next_step.id
                    ctx.reset_for_new_step()
                    self.info(f"[Handler] Moving to next step: {ctx.current_step_id}")
                    state_machine.transition(WorkflowEvent.NEXT_STEP)
                else:
                    self.info("[Handler] No more steps, completing stage")
                    state_machine.transition(WorkflowEvent.COMPLETE_STAGE)

        except Exception as e:
            self.error(f"[Handler] Failed to complete step: {e}", exc_info=True)
            from core.events import WorkflowEvent
            # Fallback: check if there are more steps
            next_step = workflow.get_next_step(ctx.current_stage_id, ctx.current_step_id) if workflow else None
            if next_step:
                ctx.current_step_id = next_step.id
                ctx.reset_for_new_step()
                state_machine.transition(WorkflowEvent.NEXT_STEP)
            else:
                state_machine.transition(WorkflowEvent.COMPLETE_STAGE)


# Create singleton instance
handle_complete_step = CompleteStepHandler().handle
