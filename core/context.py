"""
Workflow Context (Minimal)
Provides minimal context classes for legacy state_machine compatibility.

Note: This module exists for backward compatibility with the old state_machine.
The new architecture uses stores directly instead of context objects.
"""

from typing import List, Dict, Any, Optional


class WorkflowContext:
    """Minimal workflow context for state machine."""

    def __init__(self):
        self.current_stage_id: Optional[str] = None
        self.current_step_id: Optional[str] = None
        self.current_behavior_id: Optional[str] = None


class ExecutionContext:
    """Minimal execution context for state machine."""

    def __init__(self):
        self.workflow_context = WorkflowContext()
        self.history: List[Dict[str, Any]] = []
        self.pending_workflow_data: Any = None

    def add_history_entry(
        self,
        timestamp: float,
        from_state: str,
        to_state: str,
        event: str,
        payload: Any = None
    ) -> None:
        """Add entry to history."""
        self.history.append({
            'timestamp': timestamp,
            'from_state': from_state,
            'to_state': to_state,
            'event': event,
            'payload': payload
        })
