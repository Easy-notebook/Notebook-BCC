"""
START_BEHAVIOR Handler
Handles: STEP_RUNNING → BEHAVIOR_RUNNING transition

Responsibilities:
1. Call Planning API (/planning) to check step status or get behavior definition
2. If behavior definition returned (XML), parse and store it
3. If JSON returned, check targetAchieved
4. Call Generating API (/generating) to get actions
5. Store actions in context
"""

from typing import Any, Dict
from silantui import ModernLogger


class StartBehaviorHandler(ModernLogger):
    """Handler for START_BEHAVIOR transition."""

    def __init__(self):
        super().__init__("StartBehaviorHandler")

    def handle(self, state_machine, payload: Any = None) -> None:
        """
        Handle START_BEHAVIOR transition.

        Args:
            state_machine: WorkflowStateMachine instance
            payload: Optional payload data
        """
        self.info("[Handler] START_BEHAVIOR: STEP_RUNNING → BEHAVIOR_RUNNING")

        ctx = state_machine.execution_context.workflow_context

        if not ctx.current_stage_id or not ctx.current_step_id:
            self.error("[Handler] Missing stage/step ID")
            from core.events import WorkflowEvent
            state_machine.transition(WorkflowEvent.FAIL, {'error': 'Missing stage/step'})
            return

        try:
            # First, call Planning API to check if we should proceed
            from utils.api_client import workflow_api_client
            from utils.state_builder import build_api_state

            current_state = build_api_state(state_machine, require_progress_info=True)

            # Extract notebook_id from state
            notebook_id = current_state.get('state', {}).get('notebook', {}).get('notebook_id')

            self.info(f"[Handler] Calling Planning API for behavior check")

            planning_response = workflow_api_client.send_feedback_sync(
                stage_id=ctx.current_stage_id,
                step_index=ctx.current_step_id,
                state=current_state,
                notebook_id=notebook_id
            )

            response_type = planning_response.get('type')
            self.info(f"[Handler] Planning API response type: {response_type}")

            if response_type == 'behavior':
                # Update behavior definition
                from utils.workflow_updater import workflow_updater
                workflow_updater.update_from_response(state_machine, planning_response)
                self.info(f"[Handler] Behavior definition updated: {ctx.current_behavior_id}")

            elif response_type == 'json':
                content = planning_response.get('content', {})
                target_achieved = content.get('targetAchieved', False)

                if target_achieved:
                    self.info("[Handler] Step target already achieved")
                    from core.events import WorkflowEvent
                    state_machine.transition(WorkflowEvent.COMPLETE_STEP)
                    return

                # Apply any context updates
                from utils.workflow_updater import workflow_updater
                workflow_updater.update_from_response(state_machine, planning_response)

            # Now call Generating API to get actions
            self.info(f"[Handler] Calling Generating API for actions")

            actions_response = workflow_api_client.fetch_behavior_actions_sync(
                stage_id=ctx.current_stage_id,
                step_index=ctx.current_step_id,
                state=current_state
            )

            # Store actions in context
            if 'actions' in actions_response:
                ctx.current_behavior_actions = actions_response['actions']
                ctx.current_action_index = 0
                self.info(f"[Handler] Received {len(ctx.current_behavior_actions)} actions")

                # Transition to ACTION_RUNNING (or start executing)
                from core.events import WorkflowEvent
                state_machine.transition(WorkflowEvent.START_ACTION)
            else:
                self.warning("[Handler] No actions returned from Generating API")
                from core.events import WorkflowEvent
                state_machine.transition(WorkflowEvent.COMPLETE_BEHAVIOR)

        except Exception as e:
            self.error(f"[Handler] Failed to start behavior: {e}", exc_info=True)
            from core.events import WorkflowEvent
            state_machine.transition(WorkflowEvent.FAIL, {'error': str(e)})


# Create singleton instance
handle_start_behavior = StartBehaviorHandler().handle
