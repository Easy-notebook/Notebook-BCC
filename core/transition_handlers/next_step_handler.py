"""
NEXT_STEP Handler
Handles: STEP_COMPLETED → STEP_RUNNING transition

Responsibilities:
1. Verify that current_step_id has been updated to the next step
2. Trigger START_BEHAVIOR to begin the new step
"""

from typing import Any, Dict
from silantui import ModernLogger


class NextStepHandler(ModernLogger):
    """Handler for NEXT_STEP transition."""

    def __init__(self):
        super().__init__("NextStepHandler")

    def handle(self, state_machine, payload: Any = None) -> None:
        """
        Handle NEXT_STEP transition.

        Args:
            state_machine: WorkflowStateMachine instance
            payload: Optional payload data
        """
        self.info("[Handler] NEXT_STEP: STEP_COMPLETED → STEP_RUNNING")

        ctx = state_machine.execution_context.workflow_context

        if not ctx.current_step_id:
            self.error("[Handler] No current step ID")
            from core.events import WorkflowEvent
            state_machine.transition(WorkflowEvent.FAIL, {'error': 'No current step'})
            return

        self.info(f"[Handler] Starting new step: {ctx.current_step_id}")

        # Transition to START_BEHAVIOR
        from core.events import WorkflowEvent
        state_machine.transition(WorkflowEvent.START_BEHAVIOR)


# Create singleton instance
handle_next_step = NextStepHandler().handle
