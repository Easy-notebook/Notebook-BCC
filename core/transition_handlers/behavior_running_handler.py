"""
BEHAVIOR_RUNNING Handler
Handles: BEHAVIOR_RUNNING state effect

Responsibilities:
1. Generate behavior_id if not present
2. Call Generating API (/generating) to get actions
3. Store actions in context
4. Trigger START_ACTION or COMPLETE_BEHAVIOR
"""

from typing import Any
from silantui import ModernLogger


class BehaviorRunningHandler(ModernLogger):
    """Handler for BEHAVIOR_RUNNING state."""

    def __init__(self):
        super().__init__("BehaviorRunningHandler")

    def handle(self, state_machine, payload: Any = None) -> None:
        """
        Handle BEHAVIOR_RUNNING state.

        Args:
            state_machine: WorkflowStateMachine instance
            payload: Optional payload data
        """
        self.info("[Handler] BEHAVIOR_RUNNING - Calling Generating API for actions")

        ctx = state_machine.execution_context.workflow_context

        if not ctx.current_stage_id or not ctx.current_step_id:
            self.error("[Handler] Missing stage/step ID")
            from core.events import WorkflowEvent
            state_machine.transition(WorkflowEvent.FAIL, {'error': 'Missing stage/step ID'})
            return

        if not state_machine.ai_context_store:
            self.error("[Handler] AI context store not available")
            from core.events import WorkflowEvent
            state_machine.transition(WorkflowEvent.FAIL, {'error': 'AI context store not available'})
            return

        try:
            # Generate behavior_id and increment iteration
            if not ctx.current_behavior_id:
                ctx.behavior_iteration += 1
                ctx.current_behavior_id = f"behavior_{ctx.behavior_iteration:03d}"
                self.info(f"[Handler] Starting behavior: {ctx.current_behavior_id} (iteration {ctx.behavior_iteration})")

            # Fetch actions from Generating API
            from utils.api_client import workflow_api_client
            from utils.state_builder import build_api_state

            self.info(f"[Handler] Fetching actions for stage={ctx.current_stage_id}, step={ctx.current_step_id}")

            current_state = build_api_state(state_machine, require_progress_info=True)

            actions = workflow_api_client.fetch_behavior_actions_sync(
                stage_id=ctx.current_stage_id,
                step_index=ctx.current_step_id,
                state=current_state,
                stream=True
            )

            self.info(f"[Handler] Fetched {len(actions)} actions")

            # Store actions in context
            ctx.current_behavior_actions = actions
            ctx.current_action_index = 0

            from core.events import WorkflowEvent
            if actions:
                state_machine.transition(WorkflowEvent.START_ACTION)
            else:
                # No actions, complete behavior immediately
                state_machine.transition(WorkflowEvent.COMPLETE_BEHAVIOR)

        except Exception as e:
            self.error(f"[Handler] Failed to fetch actions: {e}", exc_info=True)
            from core.events import WorkflowEvent
            state_machine.transition(WorkflowEvent.FAIL, {'error': f'Failed to fetch actions: {str(e)}'})


# Create singleton instance
handle_behavior_running = BehaviorRunningHandler().handle
