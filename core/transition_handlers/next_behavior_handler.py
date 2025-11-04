"""
NEXT_BEHAVIOR Handler
Handles: BEHAVIOR_COMPLETED → BEHAVIOR_RUNNING transition

Responsibilities:
1. Reset behavior context
2. Trigger START_BEHAVIOR to get the next behavior
"""

from typing import Any, Dict
from silantui import ModernLogger


class NextBehaviorHandler(ModernLogger):
    """Handler for NEXT_BEHAVIOR transition."""

    def __init__(self):
        super().__init__("NextBehaviorHandler")

    def handle(self, state_machine, payload: Any = None) -> None:
        """
        Handle NEXT_BEHAVIOR transition.

        Args:
            state_machine: WorkflowStateMachine instance
            payload: Optional payload data
        """
        self.info("[Handler] NEXT_BEHAVIOR: BEHAVIOR_COMPLETED → BEHAVIOR_RUNNING")

        ctx = state_machine.execution_context.workflow_context

        # Reset behavior context
        ctx.current_behavior_id = None
        ctx.current_behavior_actions = []
        ctx.current_action_index = 0

        self.info(f"[Handler] Starting next behavior for step: {ctx.current_step_id}")

        # Transition to START_BEHAVIOR
        from core.events import WorkflowEvent
        state_machine.transition(WorkflowEvent.START_BEHAVIOR)


# Create singleton instance
handle_next_behavior = NextBehaviorHandler().handle
