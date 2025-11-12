"""
AI Planning Context Store
Manages workflow execution context including:
- Variables: key-value storage for workflow data
- Effects: execution results storage
- Custom Context: user-defined context data

Note: Focus-based goal tracking is managed by WorkflowStateMachine via progress.*.focus
"""

from typing import Dict, List, Any, Optional
import copy
from silantui import ModernLogger


class AIContext(ModernLogger):
    """
    Core AI context data structure.
    Stores runtime variables and effects for workflow execution.
    """

    def __init__(self):
        super().__init__("AIContext")
        self.variables: Dict[str, Any] = {}
        self.effect: Dict[str, List[str]] = {'current': [], 'history': []}
        self.custom_context: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API transmission."""
        return {
            'variables': self.variables,
            'effects': self.effect,
        }

    def copy(self) -> 'AIContext':
        """Create a deep copy."""
        new_context = AIContext()
        new_context.variables = copy.deepcopy(self.variables)
        new_context.effect = copy.deepcopy(self.effect)
        new_context.custom_context = copy.deepcopy(self.custom_context)
        return new_context


class AIPlanningContextStore(ModernLogger):
    """
    AI Planning Context Store.
    Manages workflow execution state and context.
    """

    def __init__(self):
        """Initialize the store."""
        super().__init__("AIPlanningContextStore")
        self._context = AIContext()

    # ==============================================
    # Variables Management
    # ==============================================

    def add_variable(self, key: str, value: Any):
        """Add or update a variable."""
        self._context.variables[key] = value
        self.info(f"[AI Context] Set variable: {key} = {value}")

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
    # Custom Context Management
    # ==============================================

    def set_custom_context(self, context: Dict[str, Any]):
        """
        Set custom context data to be sent with API calls.

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

    # ==============================================
    # Context Management
    # ==============================================

    def get_context(self) -> AIContext:
        """Get the current context."""
        return self._context

    def set_context(self, context):
        """
        Set the entire context.

        Args:
            context: Can be either an AIContext object or a dict
        """
        if isinstance(context, dict):
            # Convert dict to AIContext
            new_context = AIContext()
            new_context.variables = context.get('variables', {})
            new_context.effect = context.get('effects', context.get('effect', {'current': [], 'history': []}))

            # Handle custom context if present
            custom_context = context.copy()
            for key in ['variables', 'effect', 'effects']:
                custom_context.pop(key, None)
            if custom_context:
                new_context.custom_context = custom_context

            self._context = new_context
        else:
            self._context = context
        self.info("[AI Context] Context updated")

    def reset_ai_planning_context(self):
        """Reset the entire context."""
        self._context = AIContext()
        self.info("[AI Context] Context reset")

    def update_current_section(self, section_id: str, section_number: Optional[int] = None):
        """
        Update the current section in variables.progress.
        """
        progress = self._context.variables.get('progress', {})
        progress['current_section'] = {'id': section_id, 'number': section_number}
        self._context.variables['progress'] = progress
        self.info(f"[AI Context] Updated current section: {section_id}#{section_number}")

    def complete_section(self, section_id: str):
        """
        Mark a section as completed in variables.progress.
        """
        progress = self._context.variables.get('progress', {})
        completed = progress.get('completed_sections', [])
        if section_id not in completed:
            completed.append(section_id)
        progress['completed_sections'] = completed
        self._context.variables['progress'] = progress
        self.info(f"[AI Context] Completed section: {section_id}")
