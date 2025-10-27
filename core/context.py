"""
Execution context for the workflow.
Contains the state needed during workflow execution.
"""

from dataclasses import dataclass, field
from typing import List, Any, Optional


@dataclass
class WorkflowContext:
    """
    Context maintained by the state machine during execution.
    Maps to TypeScript's WorkflowContext interface.
    """
    current_stage_id: Optional[str] = None
    current_step_id: Optional[str] = None
    current_behavior_id: Optional[str] = None
    current_behavior_actions: List[Any] = field(default_factory=list)
    current_action_index: int = 0

    def reset_for_new_step(self):
        """Reset context for a new step."""
        self.current_behavior_id = None
        self.current_behavior_actions = []
        self.current_action_index = 0

    def reset_for_new_behavior(self):
        """Reset context for a new behavior."""
        self.current_behavior_actions = []
        self.current_action_index = 0


@dataclass
class ExecutionHistoryEntry:
    """
    Represents a single entry in the execution history.
    Maps to TypeScript's ExecutionHistoryEntry interface.
    """
    timestamp: float
    from_state: str
    to_state: str
    event: str
    payload: Any = None
    hierarchical_id: Optional[str] = None
    stage_id: Optional[str] = None
    step_id: Optional[str] = None
    step_index: Optional[int] = None
    behavior_counter: Optional[int] = None
    action_counter: Optional[int] = None

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp,
            'from_state': self.from_state,
            'to_state': self.to_state,
            'event': self.event,
            'payload': self.payload,
            'hierarchical_id': self.hierarchical_id,
            'stage_id': self.stage_id,
            'step_id': self.step_id,
            'step_index': self.step_index,
            'behavior_counter': self.behavior_counter,
            'action_counter': self.action_counter,
        }


@dataclass
class ExecutionContext:
    """
    Full execution context including workflow context and history.
    Used by the state machine to track execution state.
    """
    workflow_context: WorkflowContext = field(default_factory=WorkflowContext)
    execution_history: List[ExecutionHistoryEntry] = field(default_factory=list)
    pending_workflow_data: Optional[Any] = None

    def add_history_entry(
        self,
        timestamp: float,
        from_state: str,
        to_state: str,
        event: str,
        payload: Any = None
    ):
        """Add an entry to the execution history."""
        entry = ExecutionHistoryEntry(
            timestamp=timestamp,
            from_state=from_state,
            to_state=to_state,
            event=event,
            payload=payload,
            stage_id=self.workflow_context.current_stage_id,
            step_id=self.workflow_context.current_step_id,
        )
        self.execution_history.append(entry)

    def reset(self):
        """Reset the execution context."""
        self.workflow_context = WorkflowContext()
        self.execution_history = []
        self.pending_workflow_data = None
