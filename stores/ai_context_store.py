"""
AI Planning Context Store
Manages workflow execution context including:
- Variables: key-value storage for workflow data
- To-Do List: task tracking
- Effect: execution results storage
- Custom Context: user-defined context data
- Section Progress: section completion tracking
- Workflow Progress: stage progress tracking
"""

from typing import Dict, List, Any, Optional
import copy
from silantui import ModernLogger
from core.context import SectionProgress


class AIContext(ModernLogger):
    """
    Core AI context data structure.
    Stores all runtime state for workflow execution.
    """

    def __init__(self):
        super().__init__("AIContext")
        self.variables: Dict[str, Any] = {}
        self.to_do_list: List[str] = []
        self.effect: Dict[str, List[str]] = {'current': [], 'history': []}
        self.custom_context: Dict[str, Any] = {}
        self.section_progress: Optional[SectionProgress] = None
        self.workflow_progress: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API transmission."""
        result = {
            'variables': self.variables,
            'toDoList': self.to_do_list,
            'effects': self.effect,
        }

        # Add optional progress tracking
        if self.section_progress:
            result['section_progress'] = self.section_progress.to_dict()

        if self.workflow_progress:
            result['workflow_progress'] = self.workflow_progress

        return result

    def copy(self) -> 'AIContext':
        """Create a deep copy."""
        new_context = AIContext()
        new_context.variables = copy.deepcopy(self.variables)
        new_context.to_do_list = self.to_do_list.copy()
        new_context.effect = copy.deepcopy(self.effect)
        new_context.custom_context = copy.deepcopy(self.custom_context)

        if self.section_progress:
            new_context.section_progress = SectionProgress(
                current_section_id=self.section_progress.current_section_id,
                current_section_number=self.section_progress.current_section_number,
                completed_sections=self.section_progress.completed_sections.copy(),
                all=self.section_progress.all.copy()
            )

        if self.workflow_progress:
            new_context.workflow_progress = copy.deepcopy(self.workflow_progress)

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
    # State Checks
    # ==============================================

    def is_cur_step_completed(self) -> bool:
        """Check if current step is completed (no pending TODOs)."""
        return len(self._context.to_do_list) == 0

    def can_auto_advance_to_next_step(self) -> bool:
        """Check if can auto-advance to next step."""
        return self.is_cur_step_completed()

    # ==============================================
    # To-Do List Management
    # ==============================================

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
            new_context.to_do_list = context.get('toDoList', context.get('to_do_list', []))
            new_context.effect = context.get('effects', context.get('effect', {'current': [], 'history': []}))
            new_context.workflow_progress = context.get('workflow_progress')

            # Handle custom context if present
            custom_context = context.copy()
            for key in ['variables', 'toDoList', 'to_do_list', 'effect', 'effects', 'workflow_progress']:
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

    # ==============================================
    # Section Progress Management
    # ==============================================

    def set_section_progress(self, section_progress: dict):
        """
        Set the section progress from a dictionary.

        Args:
            section_progress: Dictionary with section progress data or SectionProgress object
        """
        if isinstance(section_progress, dict):
            self._context.section_progress = SectionProgress(
                current_section_id=section_progress.get('current_section_id'),
                current_section_number=section_progress.get('current_section_number'),
                completed_sections=section_progress.get('completed_sections', []),
                all=section_progress.get('all', [])
            )
        else:
            self._context.section_progress = section_progress
        self.info(f"[AI Context] Set section progress: {section_progress}")

    def update_current_section(self, section_id: str, section_number: int):
        """
        Update the current section being worked on.

        Args:
            section_id: ID of the current section
            section_number: Number of the current section
        """
        if not self._context.section_progress:
            self._context.section_progress = SectionProgress()

        self._context.section_progress.current_section_id = section_id
        self._context.section_progress.current_section_number = section_number
        self.info(f"[AI Context] Updated current section: {section_id} (#{section_number})")

    def complete_section(self, section_id: str):
        """
        Mark a section as completed.

        Args:
            section_id: ID of the section to mark as completed
        """
        if not self._context.section_progress:
            self._context.section_progress = SectionProgress()

        if section_id not in self._context.section_progress.completed_sections:
            self._context.section_progress.completed_sections.append(section_id)
            self.info(f"[AI Context] Completed section: {section_id}")

    def get_section_progress(self) -> Optional[SectionProgress]:
        """
        Get the current section progress.

        Returns:
            SectionProgress object or None
        """
        return self._context.section_progress

    def reset_section_progress(self):
        """Reset section progress."""
        self._context.section_progress = None
        self.info("[AI Context] Reset section progress")

    # ==============================================
    # Workflow Progress Management
    # ==============================================

    def set_workflow_progress(self, workflow_progress: dict):
        """
        Set the workflow progress from a dictionary.

        Args:
            workflow_progress: Dictionary with workflow progress data
        """
        self._context.workflow_progress = workflow_progress
        self.info(f"[AI Context] Set workflow progress: {workflow_progress}")

    def update_workflow_progress(self, update: dict):
        """
        Update specific fields in workflow progress.

        Args:
            update: Dictionary with fields to update
        """
        if not self._context.workflow_progress:
            self._context.workflow_progress = {
                "all_stages": [],
                "current_stage_id": None,
                "completed_stages": []
            }

        self._context.workflow_progress.update(update)
        self.info(f"[AI Context] Updated workflow progress: {update}")

    def initialize_workflow_progress(self, workflow: Dict[str, Any]):
        """
        Initialize workflow progress from a workflow configuration.

        Args:
            workflow: Workflow configuration with stages
        """
        if not workflow:
            return

        stages = workflow.get("stages", [])
        if not stages:
            return

        all_stages = [stage.get("id") for stage in stages if stage.get("id")]

        self._context.workflow_progress = {
            "all_stages": all_stages,
            "current_stage_id": None,
            "completed_stages": []
        }
        self.info(f"[AI Context] Initialized workflow progress with {len(all_stages)} stages")

    def get_workflow_progress(self) -> Optional[Dict[str, Any]]:
        """
        Get the current workflow progress.

        Returns:
            Workflow progress dictionary or None
        """
        return self._context.workflow_progress

    def reset_workflow_progress(self):
        """Reset workflow progress."""
        self._context.workflow_progress = None
        self.info("[AI Context] Reset workflow progress")
