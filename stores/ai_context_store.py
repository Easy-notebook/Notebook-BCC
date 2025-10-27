"""
AI Planning Context Store
Replicates the TypeScript aiPlanningContext.ts

Manages:
- Variables: key-value storage for workflow data
- To-Do List: task tracking
- Checklist: current and completed items
- Thinking: AI thinking logs
- Effect: execution results storage
- Stage Status: completion tracking
"""

from typing import Dict, List, Any
from dataclasses import dataclass
import copy
from silantui import ModernLogger

class AIContext(ModernLogger):
    """
    Core AI context data structure.
    Maps to TypeScript's AIContext interface.
    """

    def __init__(self):
        super().__init__("AIContext")
        self.checklist: Dict[str, List[str]] = {'current': [], 'completed': []}
        self.thinking: List[str] = []
        self.variables: Dict[str, Any] = {}
        self.to_do_list: List[str] = []
        self.stage_status: Dict[str, bool] = {}
        self.effect: Dict[str, List[str]] = {'current': [], 'history': []}
        self.custom_context: Dict[str, Any] = {}  # User-defined custom context

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, merging custom context."""
        base_dict = {
            'checklist': self.checklist,
            'thinking': self.thinking,
            'variables': self.variables,
            'toDoList': self.to_do_list,
            'stageStatus': self.stage_status,
            'effect': self.effect,
        }

        # Merge custom context (custom context can override base fields)
        if self.custom_context:
            base_dict.update(self.custom_context)

        return base_dict

    def copy(self) -> 'AIContext':
        """Create a deep copy."""
        new_context = AIContext()
        new_context.checklist = copy.deepcopy(self.checklist)
        new_context.thinking = self.thinking.copy()
        new_context.variables = copy.deepcopy(self.variables)
        new_context.to_do_list = self.to_do_list.copy()
        new_context.stage_status = self.stage_status.copy()
        new_context.effect = copy.deepcopy(self.effect)
        new_context.custom_context = copy.deepcopy(self.custom_context)
        return new_context


@dataclass
class RequestContext:
    """
    Tracks request context to prevent duplicate executions.
    Maps to TypeScript's RequestContext interface.
    """
    step_id: str
    stage_id: str
    to_do_list: List[str]
    variables: Dict[str, Any]
    thinking_length: int


class AIPlanningContextStore(ModernLogger):
    """
    AI Planning Context Store.
    Replicates TypeScript's useAIPlanningContextStore.

    This is the Python implementation of the Zustand store.
    """

    def __init__(self):
        """Initialize the store."""
        super().__init__("AIPlanningContextStore")
        self._context = AIContext()
        self._backup = {
            'last_stage': AIContext(),
            'last_step': AIContext(),
            'cache': AIContext(),
        }
        self._last_request_context: Dict[str, RequestContext] = {}

    # ==============================================
    # State Machine Integration & Checks
    # ==============================================

    def is_cur_step_completed(self) -> bool:
        """Check if current step is completed (no pending TODOs)."""
        return len(self._context.to_do_list) == 0

    def can_auto_advance_to_next_step(self) -> bool:
        """Check if can auto-advance to next step."""
        return self.is_cur_step_completed()

    def can_auto_advance_to_next_stage(self, stage_id: str) -> bool:
        """Check if can auto-advance to next stage."""
        return self._context.stage_status.get(stage_id, False)

    def is_workflow_update_confirmed(self) -> bool:
        """Check if workflow update is confirmed (placeholder)."""
        return True

    def notify_step_started(self, step_id: str):
        """Notify that a step has started."""
        self.info(f"[AI Context] Step started: {step_id}")

    def notify_step_completed(self, step_id: str, result: Any):
        """Notify that a step has completed."""
        self.info(f"[AI Context] Step completed: {step_id}, Result: {result}")
        if self.is_cur_step_completed():
            self._context.checklist['completed'].append(f"step_{step_id}_completed")

    def notify_stage_completed(self, stage_id: str):
        """Notify that a stage has completed."""
        self.info(f"[AI Context] Stage completed: {stage_id}")
        self.mark_stage_as_complete(stage_id)
        # Reset context for next stage
        self._context.to_do_list = []
        self._context.checklist = {'current': [], 'completed': []}
        self._context.thinking = []

    def is_step_ready_for_completion(self, step_id: str) -> bool:
        """Check if step is ready for completion."""
        return (len(self._context.to_do_list) == 0 and
                len(self._context.checklist['current']) == 0)

    def is_stage_ready_for_completion(self, stage_id: str) -> bool:
        """Check if stage is ready for completion."""
        return (len(self._context.to_do_list) == 0 and
                self._context.stage_status.get(stage_id, False))

    # ==============================================
    # Request Context Management
    # ==============================================

    def is_request_context_same(self, step_id: str, stage_id: str) -> bool:
        """Check if the request context is the same as the last one."""
        current_context = RequestContext(
            step_id=step_id,
            stage_id=stage_id,
            to_do_list=self._context.to_do_list.copy(),
            variables=copy.deepcopy(self._context.variables),
            thinking_length=len(self._context.thinking),
        )

        context_key = f"{stage_id}_{step_id}"
        last_context = self._last_request_context.get(context_key)

        if not last_context:
            return False

        is_same = (
            current_context.step_id == last_context.step_id and
            current_context.stage_id == last_context.stage_id and
            current_context.to_do_list == last_context.to_do_list and
            current_context.variables == last_context.variables and
            current_context.thinking_length == last_context.thinking_length
        )

        self.info(f"[AI Context] Request context comparison: {is_same} for {context_key}")
        return is_same

    def update_request_context(self, step_id: str, stage_id: str):
        """Update the last request context."""
        context_key = f"{stage_id}_{step_id}"
        current_context = RequestContext(
            step_id=step_id,
            stage_id=stage_id,
            to_do_list=self._context.to_do_list.copy(),
            variables=copy.deepcopy(self._context.variables),
            thinking_length=len(self._context.thinking),
        )
        self._last_request_context[context_key] = current_context
        self.info(f"[AI Context] Updated request context for: {context_key}")

    def clear_request_context(self, step_id: str, stage_id: str):
        """Clear the request context."""
        context_key = f"{stage_id}_{step_id}"
        if context_key in self._last_request_context:
            del self._last_request_context[context_key]
        self.info(f"[AI Context] Cleared request context for: {context_key}")

    # ==============================================
    # State Manipulators
    # ==============================================

    def set_checklist(self, current: List[str], completed: List[str]):
        """Set the checklist."""
        self._context.checklist = {'current': current, 'completed': completed}

    def add_to_do_list(self, item: str):
        """Add an item to the to-do list."""
        if item not in self._context.to_do_list:
            self._context.to_do_list.append(item)
            self.info(f"[AI Context] Added TODO: {item}")

    def remove_from_to_do_list(self, item: str):
        """Remove an item from the to-do list."""
        if item in self._context.to_do_list:
            self._context.to_do_list.remove(item)
            self.info(f"[AI Context] Removed TODO: {item}")

    def clear_to_do_list(self):
        """Clear the to-do list."""
        self._context.to_do_list = []
        self.info("[AI Context] Cleared TODO list")

    def add_checklist_current_item(self, item: str):
        """Add an item to current checklist."""
        if item not in self._context.checklist['current']:
            self._context.checklist['current'].append(item)

    def add_checklist_completed_item(self, item: str):
        """Move an item from current to completed."""
        if item in self._context.checklist['current']:
            self._context.checklist['current'].remove(item)
        if item not in self._context.checklist['completed']:
            self._context.checklist['completed'].append(item)

    def set_thinking(self, thinking: List[str]):
        """Set the thinking logs."""
        self._context.thinking = thinking if thinking else []

    def add_thinking_log(self, thought: str):
        """Add a thinking log entry."""
        self._context.thinking.append(thought)
        self.info(f"[AI Context] Added thinking: {thought[:50]}...")

    def mark_stage_as_complete(self, stage_id: str):
        """Mark a stage as complete."""
        self._context.stage_status[stage_id] = True
        self.info(f"[AI Context] Marked stage as complete: {stage_id}")

    def is_stage_complete(self, stage_id: str) -> bool:
        """Check if a stage is complete."""
        return self._context.stage_status.get(stage_id, False)

    # ==============================================
    # Custom Context Management
    # ==============================================

    def set_custom_context(self, context: Dict[str, Any]):
        """
        Set custom context data to be sent with API calls.
        This allows users to inject additional information into the context.

        Args:
            context: Custom context dictionary
        """
        self._context.custom_context = context
        self.info(f"[AI Context] Set custom context: {list(context.keys())}")

    def update_custom_context(self, key: str, value: Any):
        """
        Update a specific key in custom context.

        Args:
            key: Context key
            value: Context value
        """
        self._context.custom_context[key] = value
        self.info(f"[AI Context] Updated custom context: {key}")

    def get_custom_context(self) -> Dict[str, Any]:
        """Get the current custom context."""
        return self._context.custom_context.copy()

    def clear_custom_context(self):
        """Clear all custom context."""
        self._context.custom_context = {}
        self.info("[AI Context] Cleared custom context")

    def clear_stage_status(self, stage_id: str):
        """Clear a stage's completion status."""
        self._context.stage_status[stage_id] = False

    def clear_all_stage_status(self):
        """Clear all stage statuses."""
        self._context.stage_status = {}

    # ==============================================
    # Variables Management
    # ==============================================

    def add_variable(self, key: str, value: Any):
        """Add or update a variable."""
        self._context.variables[key] = value
        self.info(f"[AI Context] Set variable: {key} = {value}")

    def update_variable(self, key: str, value: Any):
        """Update a variable (alias for add_variable)."""
        self.add_variable(key, value)

    def get_variable(self, key: str, default: Any = None) -> Any:
        """Get a variable value."""
        return self._context.variables.get(key, default)

    def set_variables(self, new_variables: Dict[str, Any]):
        """Set all variables."""
        self._context.variables = new_variables

    def reset_variables(self):
        """Reset all variables."""
        self._context.variables = {}

    # ==============================================
    # Effect Management
    # ==============================================

    def reset_effect(self):
        """Reset the effect state."""
        self._context.effect = {'current': [], 'history': []}
        self.info("[AI Context] Reset effect state")

    def set_effect(self, new_effect: Dict[str, List[str]]):
        """Set the effect state."""
        self._context.effect = new_effect

    def add_effect(self, effect: str):
        """Add an effect to the current list."""
        self._context.effect['current'].append(effect)
        self.info(f"[AI Context] Added effect: {effect[:50]}...")

    def move_current_effects_to_history(self):
        """Move current effects to history."""
        self._context.effect['history'].extend(self._context.effect['current'])
        self._context.effect['current'] = []
        self.info("[AI Context] Moved current effects to history")

    # ==============================================
    # Context Management
    # ==============================================

    def get_context(self) -> AIContext:
        """Get the current context."""
        return self._context

    def set_context(self, context: AIContext):
        """Set the entire context."""
        self._context = context
        self.info("[AI Context] Context updated")

    def reset_ai_planning_context(self):
        """Reset the entire context."""
        self._context = AIContext()
        self.info("[AI Context] Context reset")

    # ==============================================
    # Backup & Restore
    # ==============================================

    def store_current_context_to_backup_cache(self):
        """Store current context to backup cache."""
        self._backup['cache'] = self._context.copy()
        self.info("[AI Context] Stored to backup cache")

    def store_current_context_to_backup_last_stage(self):
        """Store current context to last stage backup."""
        self._backup['last_stage'] = self._context.copy()
        self.info("[AI Context] Stored to last stage backup")

    def store_current_context_to_backup_last_step(self):
        """Store current context to last step backup."""
        self._backup['last_step'] = self._context.copy()
        self.info("[AI Context] Stored to last step backup")

    def load_backup_cache_to_context(self):
        """Restore context from backup cache."""
        self._context = self._backup['cache'].copy()
        self.info("[AI Context] Restored from backup cache")

    def load_backup_last_step_to_context(self):
        """Restore context from last step backup."""
        self._context = self._backup['last_step'].copy()
        self.info("[AI Context] Restored from last step backup")

    def load_backup_last_stage_to_context(self):
        """Restore context from last stage backup."""
        self._context = self._backup['last_stage'].copy()
        self.info("[AI Context] Restored from last stage backup")
