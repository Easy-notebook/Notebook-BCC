"""
NEXT_STAGE Handler
Handles: STAGE_COMPLETED → STAGE_RUNNING transition

Responsibilities:
1. Verify that current_stage_id has been updated to the next stage
2. Trigger START_STEP to begin the new stage
"""

from typing import Any, Dict
from silantui import ModernLogger


class NextStageHandler(ModernLogger):
    """Handler for NEXT_STAGE transition."""

    def __init__(self):
        super().__init__("NextStageHandler")

    def handle(self, state_machine, payload: Any = None) -> None:
        """
        Handle NEXT_STAGE transition.

        Args:
            state_machine: WorkflowStateMachine instance
            payload: Optional payload data
        """
        self.info("[Handler] NEXT_STAGE: STAGE_COMPLETED → STAGE_RUNNING")

        ctx = state_machine.execution_context.workflow_context

        if not ctx.current_stage_id:
            self.error("[Handler] No current stage ID")
            from core.events import WorkflowEvent
            state_machine.transition(WorkflowEvent.FAIL, {'error': 'No current stage'})
            return

        self.info(f"[Handler] Starting new stage: {ctx.current_stage_id}")

        # Transition to START_STEP
        from core.events import WorkflowEvent
        state_machine.transition(WorkflowEvent.START_STEP)


# Create singleton instance
handle_next_stage = NextStageHandler().handle
