"""
COMPLETE_BEHAVIOR Handler
Handles: BEHAVIOR_RUNNING → BEHAVIOR_COMPLETED transition

Responsibilities:
1. Call Reflecting API (/reflecting) with behavior feedback
2. Parse JSON response
3. Apply context updates
4. Check transition directives (continue_behaviors, target_achieved)
5. Trigger appropriate next transition
"""

from typing import Any, Dict
from silantui import ModernLogger


class CompleteBehaviorHandler(ModernLogger):
    """Handler for COMPLETE_BEHAVIOR transition."""

    def __init__(self):
        super().__init__("CompleteBehaviorHandler")

    def handle(self, state_machine, payload: Any = None) -> None:
        """
        Handle COMPLETE_BEHAVIOR transition.

        Args:
            state_machine: WorkflowStateMachine instance
            payload: Optional payload data
        """
        self.info("[Handler] COMPLETE_BEHAVIOR: BEHAVIOR_RUNNING → BEHAVIOR_COMPLETED")

        ctx = state_machine.execution_context.workflow_context

        if not ctx.current_stage_id or not ctx.current_step_id:
            self.error("[Handler] Missing stage/step ID")
            from core.events import WorkflowEvent
            state_machine.transition(WorkflowEvent.FAIL, {'error': 'Missing stage/step'})
            return

        try:
            # Call Reflecting API
            from utils.api_client import workflow_api_client
            from utils.state_builder import build_api_state, build_behavior_feedback

            current_state = build_api_state(state_machine, require_progress_info=True)
            behavior_feedback = build_behavior_feedback(state_machine)

            self.info(f"[Handler] Calling Reflecting API for behavior completion")

            reflecting_response = workflow_api_client.send_reflecting_sync(
                stage_id=ctx.current_stage_id,
                step_index=ctx.current_step_id,
                state=current_state,
                behavior_feedback=behavior_feedback
            )

            response_type = reflecting_response.get('type')
            self.info(f"[Handler] Reflecting API response type: {response_type}")

            # Update context from response
            from utils.workflow_updater import workflow_updater
            workflow_updater.update_from_response(state_machine, reflecting_response)

            # Mark current behavior as completed
            if ctx.current_behavior_id and ctx.current_behavior_id not in ctx.completed_behaviors:
                ctx.completed_behaviors.append(ctx.current_behavior_id)

            # Check transition directives (for JSON responses)
            if response_type == 'json':
                content = reflecting_response.get('content', {})
                transition = content.get('transition', {})
                continue_behaviors = transition.get('continue_behaviors', False)
                target_achieved = transition.get('target_achieved', content.get('targetAchieved', False))

                from core.events import WorkflowEvent
                if target_achieved:
                    self.info("[Handler] Step target achieved per Reflecting API")
                    state_machine.transition(WorkflowEvent.COMPLETE_STEP)
                elif continue_behaviors:
                    self.info("[Handler] Continuing to next behavior")
                    ctx.current_behavior_id = None
                    ctx.current_behavior_actions = []
                    ctx.current_action_index = 0
                    state_machine.transition(WorkflowEvent.NEXT_BEHAVIOR)
                else:
                    self.info("[Handler] No clear directive, defaulting to COMPLETE_STEP")
                    state_machine.transition(WorkflowEvent.COMPLETE_STEP)
            else:
                # For XML responses, default to next behavior
                self.info("[Handler] XML response, continuing to next behavior")
                from core.events import WorkflowEvent
                ctx.current_behavior_id = None
                state_machine.transition(WorkflowEvent.NEXT_BEHAVIOR)

        except Exception as e:
            self.error(f"[Handler] Failed to complete behavior: {e}", exc_info=True)
            from core.events import WorkflowEvent
            state_machine.transition(WorkflowEvent.FAIL, {'error': str(e)})


# Create singleton instance
handle_complete_behavior = CompleteBehaviorHandler().handle
