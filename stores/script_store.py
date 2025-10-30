"""
Script Store - Highly Extensible Action Execution Engine
Manages actions with decorator-based handler registration for maximum extensibility.

Refactored: Action handlers are now in separate modules under stores/handlers/
"""

from silantui import ModernLogger
import uuid
from typing import Dict, List, Optional, Any, Callable
from models.action import ScriptAction, ActionMetadata, ExecutionStep
from models.cell import CellType

# Import modularized registry and handlers
from .action_registry import ActionRegistry, ActionHandler
from .handlers import (
    handle_add_action,
    handle_new_chapter,
    handle_new_section,
    handle_exec_code,
    handle_set_effect_thinking,
    handle_is_thinking,
    handle_finish_thinking,
    handle_update_title,
    handle_update_last_text,
)
from .handlers.code_handlers import exec_code_cell, set_effect_as_thinking
from .handlers.thinking_handlers import finish_thinking
from .handlers.text_handlers import update_last_text
from .handlers.workflow_handlers import update_title


# =====================================================================
# Constants and Configuration
# =====================================================================

# Cell type mapping
CELL_TYPE_MAPPING = {
    'text': 'markdown',
    'code': 'code',
    'Hybrid': 'Hybrid',
    'outcome': 'outcome',
    'error': 'error',
    'thinking': 'thinking',
}

# Action types (Generating Actions only - 7 types)
ACTION_TYPES = {
    'ADD_ACTION': 'add',
    'EXEC_CODE': 'exec',
    'IS_THINKING': 'is_thinking',
    'FINISH_THINKING': 'finish_thinking',
    'NEW_CHAPTER': 'new_chapter',
    'NEW_SECTION': 'new_section',
    'UPDATE_TITLE': 'update_title',
}

# Removed actions (now handled by Planning API context_update):
# - 'UPDATE_WORKFLOW': 'update_workflow' → context_update.workflow_update
# - 'UPDATE_STEP_LIST': 'update_stage_steps' → context_update.stage_steps_update
# - 'COMPLETE_STEP': 'end_phase' → Planning API targetAchieved
# - 'NEXT_EVENT': 'next_event' → Removed (unclear purpose)

# =====================================================================
# Main ScriptStore Class
# =====================================================================

class ScriptStore(ModernLogger):
    """
    Script Store for managing actions and their execution.

    Features:
    - Decorator-based action handler registration
    - Pre/post execution hooks
    - Extensible without code modification
    - Clean separation of concerns
    """

    # Class-level registry for shared handlers
    _registry = ActionRegistry()

    def __init__(self, notebook_store=None, ai_context_store=None, code_executor=None):
        super().__init__("ScriptStore")
        self.actions: List[ScriptAction] = []
        self.steps: Dict[str, List[str]] = {}
        self.last_added_action_id: Optional[str] = None

        # Store references
        self.notebook_store = notebook_store
        self.ai_context_store = ai_context_store
        self.code_executor = code_executor

        # Workflow update tracking
        self.pending_workflow_update: Optional[Dict[str, Any]] = None

        # Counters
        self.chapter_counter = 0
        self.section_counter = 0

        # Register default handlers
        self._register_default_handlers()

    # =================================================================
    # Handler Registration Methods
    # =================================================================

    def _register_default_handlers(self):
        """Register all default action handlers using modularized handlers."""
        registry = self.__class__._registry

        # Register handlers from modularized handler modules
        # Each handler is a lambda that passes self (script_store) to the handler function
        registry.register_handler(ACTION_TYPES['ADD_ACTION'], lambda step: handle_add_action(self, step))
        registry.register_handler(ACTION_TYPES['NEW_CHAPTER'], lambda step: handle_new_chapter(self, step))
        registry.register_handler(ACTION_TYPES['NEW_SECTION'], lambda step: handle_new_section(self, step))
        registry.register_handler(ACTION_TYPES['IS_THINKING'], lambda step: handle_is_thinking(self, step))
        registry.register_handler(ACTION_TYPES['FINISH_THINKING'], lambda step: handle_finish_thinking(self, step))
        registry.register_handler(ACTION_TYPES['EXEC_CODE'], lambda step: handle_exec_code(self, step))
        registry.register_handler('set_effect_as_thinking', lambda step: handle_set_effect_thinking(self, step))
        registry.register_handler('update_last_text', lambda step: handle_update_last_text(self, step))
        registry.register_handler(ACTION_TYPES['UPDATE_TITLE'], lambda step: handle_update_title(self, step))
        registry.register_handler(ACTION_TYPES['COMPLETE_STEP'], lambda step: handle_complete_step(self, step))
        registry.register_handler(ACTION_TYPES['UPDATE_WORKFLOW'], lambda step: handle_update_workflow(self, step))
        registry.register_handler(ACTION_TYPES['UPDATE_STEP_LIST'], lambda step: handle_update_step_list(self, step))

    @classmethod
    def register_custom_action(cls, action_type: str, handler: ActionHandler) -> None:
        """
        Register a custom action handler.

        This allows external modules to extend functionality without modifying core code.

        Args:
            action_type: Type identifier for the custom action
            handler: Handler function implementing ActionHandler protocol

        Raises:
            ValueError: If action_type is empty or handler is not callable

        Example:
            def custom_handler(step: ExecutionStep) -> Any:
                print(f"Custom action: {step.content}")
                return None

            ScriptStore.register_custom_action('my_custom_action', custom_handler)
        """
        cls._registry.register_handler(action_type, handler)

    @classmethod
    def add_execution_hook(cls, hook_type: str, hook: Callable) -> None:
        """
        Add execution hook.

        Args:
            hook_type: 'pre' or 'post'
            hook: Callable to execute before/after action execution

        Raises:
            ValueError: If hook_type is not 'pre' or 'post', or if hook is not callable

        Example:
            def my_pre_hook(step: ExecutionStep):
                print(f"About to execute: {step.action}")

            ScriptStore.add_execution_hook('pre', my_pre_hook)
        """
        if hook_type not in ('pre', 'post'):
            raise ValueError(f"Invalid hook_type: {hook_type}. Must be 'pre' or 'post'")

        if not callable(hook):
            raise ValueError("Hook must be callable")

        if hook_type == 'pre':
            cls._registry.add_pre_hook(hook)
        elif hook_type == 'post':
            cls._registry.add_post_hook(hook)

    # =================================================================
    # Helper Functions (delegated to handler modules)
    # =================================================================

    def get_default_content(self, content_type: str = 'text') -> str:
        """Get default content for a content type."""
        defaults = {
            'text': '',
            'code': '# Write your code here',
            'outcome': 'Results will be displayed here',
            'error': 'Error occurred',
            'thinking': 'AI is thinking...'
        }
        return defaults.get(content_type, '')

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
    # Specialized Operations (delegated to handler modules)
    # =================================================================

    def update_last_text(self, text: str):
        """Update the last text cell's content (delegated to text_handlers)."""
        update_last_text(self, text)

    def finish_thinking(self):
        """Remove the last thinking cell (delegated to thinking_handlers)."""
        finish_thinking(self)

    def set_effect_as_thinking(self, thinking_text: str = "finished thinking"):
        """Mark the last code cell as having finished thinking (delegated to code_handlers)."""
        set_effect_as_thinking(self, thinking_text)

    # =================================================================
    # Code Execution (delegated to code_handlers)
    # =================================================================

    def exec_code_cell(
        self,
        codecell_id: str,
        need_output: bool = True,
        auto_debug: bool = False
    ) -> Any:
        """
        Execute a code cell (delegated to code_handlers).

        Args:
            codecell_id: The cell ID to execute
            need_output: Whether to capture output
            auto_debug: Whether to auto-debug on error

        Returns:
            Execution result
        """
        return exec_code_cell(self, codecell_id, need_output, auto_debug)

    def update_title(self, title: str):
        """Update notebook title (delegated to workflow_handlers)."""
        update_title(self, title)

    # =================================================================
    # Action Handlers (Now in separate modules under stores/handlers/)
    # All handlers have been extracted to modular files for better organization
    # =================================================================

    # All handler implementations moved to stores/handlers/
    # See: content_handlers.py, code_handlers.py, thinking_handlers.py,
    #      workflow_handlers.py, text_handlers.py

    # =================================================================
    # Main Execution Engine with Hook Support
    # =================================================================

    @staticmethod
    def _dict_to_execution_step(data: Dict[str, Any]) -> ExecutionStep:
        """Convert dictionary to ExecutionStep object."""
        metadata_dict = data.get('metadata', {})
        metadata = ActionMetadata(
            enable_edit=metadata_dict.get('enableEdit', True),
            description=metadata_dict.get('description', ''),
            use_workflow_thinking=metadata_dict.get('useWorkflowThinking', False),
            finished_thinking=metadata_dict.get('finishedThinking', False),
            thinking_text=metadata_dict.get('thinkingText'),
            is_section=metadata_dict.get('isSection', False),
            section_id=metadata_dict.get('sectionId'),
            section_number=metadata_dict.get('sectionNumber')
        )

        return ExecutionStep(
            action=data.get('action', ''),
            shot_type=data.get('shotType'),
            content=data.get('content', ''),
            store_id=data.get('storeId'),
            codecell_id=data.get('codecellId'),
            need_output=data.get('needOutput', True),
            auto_debug=data.get('autoDebug', False),
            text_array=data.get('textArray', []),
            agent_name=data.get('agentName'),
            custom_text=data.get('customText'),
            text=data.get('text'),
            title=data.get('title'),
            thinking_text=data.get('thinkingText'),
            metadata=metadata,
            updated_workflow=data.get('updatedWorkflow'),
            new_steps=data.get('newSteps', []),
            stage_id=data.get('stageId'),
            state=data.get('state')
        )

    def exec_action(self, step) -> Any:
        """
        Execute an action step with full hook support.

        Args:
            step: The execution step to process (can be dict or ExecutionStep)

        Returns:
            Execution result
        """
        # Convert dict to ExecutionStep if needed
        if isinstance(step, dict):
            step = self._dict_to_execution_step(step)

        if not step or not step.action:
            self.error("[ScriptStore] Invalid execution step")
            return None

        action_type = step.action
        self.info(f"[ScriptStore] Executing action: {action_type}")

        try:
            # Execute pre-hooks
            self.__class__._registry.execute_pre_hooks(step)

            # Sync state if present
            if step.state and self.ai_context_store:
                self.info(f"[ScriptStore] Syncing state from action")
                context = self.ai_context_store.get_context()
                merged_state = {**step.state, 'effects': context.effect}
                self.ai_context_store.set_context(merged_state)

            # Execute action using registry
            handler = self.__class__._registry.get_handler(action_type)
            if handler:
                result = handler(step)
            else:
                self.warning(f"[ScriptStore] Unknown action type: {action_type}")
                result = None

            # Check if this action marks a section
            if step.metadata and step.metadata.is_section:
                self._handle_section(step)

            # Execute post-hooks
            self.__class__._registry.execute_post_hooks(step, result)

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

    @classmethod
    def list_registered_actions(cls) -> List[str]:
        """List all registered action types."""
        return cls._registry.registered_actions

    @classmethod
    def has_handler(cls, action_type: str) -> bool:
        """Check if a handler is registered for an action type."""
        return cls._registry.get_handler(action_type) is not None
