"""
Script Store - Highly Extensible Action Execution Engine
Manages actions with decorator-based class registration for maximum extensibility.

Refactored: Action handlers are now OOP classes under actions/
"""

from silantui import ModernLogger
import uuid
from typing import Dict, List, Optional, Any
from models.action import ScriptAction, ActionMetadata, ExecutionStep

# Import constants
from .constants import (
    CELL_TYPE_MAPPING,
    EXECUTION_STEP_FIELD_MAPPING,
    METADATA_STANDARD_FIELDS,
    DEFAULT_CONTENT,
)

# Import new action system
from actions import get_action_class, get_all_action_types

# =====================================================================
# Main ScriptStore Class
# =====================================================================

class ScriptStore(ModernLogger):
    """
    Script Store for managing actions and their execution.

    Features:
    - Decorator-based action class registration
    - Action classes automatically discovered and instantiated
    - Extensible without code modification
    - Clean OOP design with ActionBase classes
    """

    def __init__(self, notebook_store=None, ai_context_store=None, code_executor=None):
        super().__init__("ScriptStore")
        self.actions: List[ScriptAction] = []
        self.steps: Dict[str, List[str]] = {}
        self.last_added_action_id: Optional[str] = None

        # Store references
        self.notebook_store = notebook_store
        self.ai_context_store = ai_context_store
        self.code_executor = code_executor

        # Action instances registry (action_type -> action_instance)
        self._action_instances: Dict[str, Any] = {}

        # Workflow update tracking
        self.pending_workflow_update: Optional[Dict[str, Any]] = None

        # Counters
        self.chapter_counter = 0
        self.section_counter = 0

        # Initialize action instances
        self._initialize_actions()

    # =================================================================
    # Action Initialization
    # =================================================================

    def _initialize_actions(self):
        """
        Initialize all registered action classes.

        Automatically discovers and instantiates all action classes
        that were registered via the @action decorator.
        """
        registered_types = get_all_action_types()
        self.info(f"[ScriptStore] Initializing {len(registered_types)} action types")

        for action_type in registered_types:
            action_class = get_action_class(action_type)
            if action_class:
                try:
                    # Instantiate action class with reference to this ScriptStore
                    action_instance = action_class(self)
                    self._action_instances[action_type] = action_instance
                    self.debug(f"[ScriptStore] Registered action: {action_type} -> {action_class.__name__}")
                except Exception as e:
                    self.error(f"[ScriptStore] Failed to initialize action '{action_type}': {e}")

        self.info(f"[ScriptStore] Successfully initialized {len(self._action_instances)} actions")

    def get_action(self, action_type: str) -> Optional[Any]:
        """
        Get an action instance by type.

        Args:
            action_type: The action type identifier

        Returns:
            Action instance or None if not found
        """
        return self._action_instances.get(action_type)

    # =================================================================
    # Helper Functions
    # =================================================================

    def get_default_content(self, content_type: str = 'text') -> str:
        """Get default content for a content type."""
        return DEFAULT_CONTENT.get(content_type, '')

    def get_current_step_id(self) -> Optional[str]:
        """Get current step ID from state machine."""
        return None  # Injected from state machine

    def get_current_step_actions(self) -> List[ScriptAction]:
        """Get actions for the current step."""
        current_step_id = self.get_current_step_id()
        if not current_step_id:
            return []

        action_ids = self.steps.get(current_step_id, [])
        return [action for action in self.actions if action.id in action_ids]

    # =================================================================
    # Action Management
    # =================================================================

    def create_new_action(
        self,
        action_type: str = 'text',
        content: str = '',
        action_id: Optional[str] = None,
        metadata: Optional[ActionMetadata] = None
    ) -> ScriptAction:
        """Create a new action."""
        return ScriptAction(
            id=action_id or str(uuid.uuid4()),
            type=action_type,
            content=content,
            metadata=metadata or ActionMetadata()
        )

    def add_action(
        self,
        action: ScriptAction,
        step_id: Optional[str] = None,
        add_to_notebook: bool = True
    ) -> str:
        """
        Add an action to the store and optionally to the notebook.

        Args:
            action: The action to add
            step_id: Step ID to associate with
            add_to_notebook: Whether to add to notebook

        Returns:
            The action ID
        """
        self.actions.append(action)
        self.last_added_action_id = action.id

        # Associate with step
        if step_id:
            if step_id not in self.steps:
                self.steps[step_id] = []
            self.steps[step_id].append(action.id)

        # Add to notebook if requested
        if add_to_notebook and self.notebook_store:
            cell_type_str = CELL_TYPE_MAPPING.get(action.type, action.type)

            cell_data = {
                'id': action.id,
                'type': cell_type_str,
                'content': action.content,
                'enableEdit': True,  # Default to editable
                'phaseId': step_id,
                'description': action.description or '',
                'metadata': action.metadata.to_dict() if action.metadata else {},
                'language': action.language,
                'agentName': action.agent_name or 'AI',
                'customText': action.custom_text,
                'textArray': action.text_array,
                'useWorkflowThinking': action.use_workflow_thinking,
            }

            self.notebook_store.add_cell(cell_data)

        self.info(f"[ScriptStore] Added action: {action.id} (type: {action.type})")
        return action.id

    def update_action(self, action_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing action."""
        for action in self.actions:
            if action.id == action_id:
                for key, value in updates.items():
                    if hasattr(action, key):
                        setattr(action, key, value)

                # Update notebook cell if exists
                if self.notebook_store:
                    self.notebook_store.update_cell(action_id, action.content)

                self.info(f"[ScriptStore] Updated action: {action_id}")
                return True

        self.warning(f"[ScriptStore] Action not found: {action_id}")
        return False

    def remove_action(self, action_id: str) -> bool:
        """Remove an action."""
        for i, action in enumerate(self.actions):
            if action.id == action_id:
                self.actions.pop(i)

                # Remove from steps
                for step_id, action_ids in self.steps.items():
                    if action_id in action_ids:
                        action_ids.remove(action_id)

                # Remove from notebook
                if self.notebook_store:
                    self.notebook_store.delete_cell(action_id)

                self.info(f"[ScriptStore] Removed action: {action_id}")
                return True

        return False

    # =================================================================
    # Specialized Operations (delegates to action instances)
    # =================================================================

    def update_last_text(self, text: str):
        """Update the last text cell's content."""
        action = self.get_action('update_last_text')
        if action:
            action._update_last_text(text)

    def finish_thinking(self):
        """Remove the last thinking cell."""
        action = self.get_action('finish_thinking')
        if action:
            action._finish_thinking()

    def set_effect_as_thinking(self, thinking_text: str = "finished thinking"):
        """Mark the last code cell as having finished thinking."""
        action = self.get_action('set_effect_as_thinking')
        if action:
            action._set_effect_as_thinking(thinking_text)

    def exec_code_cell(
        self,
        codecell_id: str,
        need_output: bool = True,
        auto_debug: bool = False
    ) -> Any:
        """
        Execute a code cell.

        Args:
            codecell_id: The cell ID to execute
            need_output: Whether to capture output
            auto_debug: Whether to auto-debug on error

        Returns:
            Execution result
        """
        action = self.get_action('exec')
        if action:
            return action._exec_code_cell(codecell_id, need_output, auto_debug)
        return None

    def update_title(self, title: str):
        """Update notebook title."""
        action = self.get_action('update_title')
        if action:
            action._update_title(title)

    # =================================================================
    # Main Execution Engine
    # =================================================================

    @staticmethod
    def _dict_to_execution_step(data: Dict[str, Any]) -> ExecutionStep:
        """Convert dictionary to ExecutionStep object."""
        # Log incoming data structure for debugging
        import logging
        logger = logging.getLogger('ScriptStore')
        logger.info(f"[ScriptStore] _dict_to_execution_step received data with keys: {list(data.keys())[:20]}")
        logger.info(f"[ScriptStore] action field: '{data.get('action')}', type field: '{data.get('type')}', shot_type: '{data.get('shotType')}'")

        metadata_dict = data.get('metadata', {})

        # Build extra dict for any additional metadata fields not in the standard set
        extra = {}
        for key, value in metadata_dict.items():
            # Convert camelCase to snake_case for standard fields
            snake_key = ''.join(['_' + c.lower() if c.isupper() else c for c in key]).lstrip('_')
            if snake_key not in METADATA_STANDARD_FIELDS:
                extra[key] = value

        metadata = ActionMetadata(
            is_step=metadata_dict.get('is_step', metadata_dict.get('isStep', False)),
            is_chapter=metadata_dict.get('is_chapter', metadata_dict.get('isChapter', False)),
            is_section=metadata_dict.get('is_section', metadata_dict.get('isSection', False)),
            chapter_id=metadata_dict.get('chapter_id', metadata_dict.get('chapterId')),
            section_id=metadata_dict.get('section_id', metadata_dict.get('sectionId')),
            chapter_number=metadata_dict.get('chapter_number', metadata_dict.get('chapterNumber')),
            section_number=metadata_dict.get('section_number', metadata_dict.get('sectionNumber')),
            finished_thinking=metadata_dict.get('finished_thinking', metadata_dict.get('finishedThinking', False)),
            thinking_text=metadata_dict.get('thinking_text', metadata_dict.get('thinkingText')),
            extra=extra
        )

        # Only pass parameters that exist in ExecutionStep class definition
        # Build kwargs dict to handle optional fields gracefully
        # Support both 'action' and 'type' fields for action type
        action_type = data.get('action') or data.get('type', '')
        step_kwargs = {
            'action': action_type,
            'metadata': metadata,
        }

        # Add optional fields only if present in data
        for json_key, python_key in EXECUTION_STEP_FIELD_MAPPING.items():
            if json_key in data:
                step_kwargs[python_key] = data[json_key]
            else:
                # Also check for snake_case version (e.g., codecell_id instead of codecellId)
                snake_key = ''.join(['_' + c.lower() if c.isupper() else c for c in json_key]).lstrip('_')
                if snake_key in data:
                    step_kwargs[python_key] = data[snake_key]

        return ExecutionStep(**step_kwargs)

    def exec_action(self, step) -> Any:
        """
        Execute an action step using the new action class system.

        Args:
            step: The execution step to process (can be dict or ExecutionStep)

        Returns:
            Execution result
        """
        # Convert dict to ExecutionStep if needed
        if isinstance(step, dict):
            self.debug(f"[ScriptStore] Converting dict to ExecutionStep, keys: {list(step.keys())[:15]}")
            step = self._dict_to_execution_step(step)

        if not step:
            self.error(f"[ScriptStore] Invalid execution step: step is None or False")
            return None

        if not step.action:
            self.error(f"[ScriptStore] Invalid execution step: action is empty. Step attributes: action={step.action}, shot_type={getattr(step, 'shot_type', None)}, content={getattr(step, 'content', 'N/A')[:50] if hasattr(step, 'content') else 'N/A'}")
            return None

        action_type = step.action
        self.info(f"[ScriptStore] Executing action: {action_type}")

        try:
            # Sync state if present
            if step.state and self.ai_context_store:
                self.info(f"[ScriptStore] Syncing state from action")
                context = self.ai_context_store.get_context()
                merged_state = {**step.state, 'effects': context.effect}
                self.ai_context_store.set_context(merged_state)

            # Get action instance and execute
            action = self.get_action(action_type)
            if action:
                result = action.execute(step)
            else:
                self.warning(f"[ScriptStore] Unknown action type: {action_type}")
                result = None

            # Check if this action marks a section
            if step.metadata and step.metadata.is_section:
                self._handle_section(step)

            return result

        except Exception as e:
            self.error(f"[ScriptStore] Error executing action {action_type}: {e}", exc_info=True)
            raise

    def _handle_section(self, step: ExecutionStep):
        """
        Handle section markers by updating section progress in AI context.

        Args:
            step: ExecutionStep with section metadata
        """
        if not self.ai_context_store:
            return

        section_id = step.metadata.section_id
        section_number = step.metadata.section_number

        if not section_id:
            return

        self.info(f"[ScriptStore] Handling section: {section_id} (#{section_number})")

        # Update current section
        self.ai_context_store.update_current_section(section_id, section_number)

        # Mark section as completed
        self.ai_context_store.complete_section(section_id)

    # =================================================================
    # Utility Methods for Extensibility
    # =================================================================

    def list_registered_actions(self) -> List[str]:
        """List all registered action types."""
        return list(self._action_instances.keys())

    def has_action(self, action_type: str) -> bool:
        """Check if an action is registered for an action type."""
        return action_type in self._action_instances
