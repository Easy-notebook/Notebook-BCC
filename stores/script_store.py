"""
Script Store
Replicates the TypeScript useScriptStore.ts

Manages actions and their execution.
"""

from silantui import ModernLogger
import uuid
from typing import Dict, List, Optional, Any
from models.action import ScriptAction, ActionMetadata, ExecutionStep
from models.cell import CellType



# Cell type mapping
CELL_TYPE_MAPPING = {
    'text': 'markdown',
    'code': 'code',
    'Hybrid': 'Hybrid',
    'outcome': 'outcome',
    'error': 'error',
    'thinking': 'thinking',
}

# Action types
ACTION_TYPES = {
    'ADD_ACTION': 'add',
    'IS_THINKING': 'is_thinking',
    'FINISH_THINKING': 'finish_thinking',
    'EXEC_CODE': 'exec',
    'UPDATE_TITLE': 'update_title',
    'UPDATE_WORKFLOW': 'update_workflow',
    'UPDATE_STEP_LIST': 'update_stage_steps',
    'COMPLETE_STEP': 'end_phase',
    'NEXT_EVENT': 'next_event',
    'NEW_CHAPTER': 'new_chapter',
    'NEW_SECTION': 'new_section',
}


class ScriptStore(ModernLogger):
    """
    Script Store for managing actions and their execution.
    Replicates TypeScript's useScriptStore.
    """

    def __init__(self, notebook_store=None, ai_context_store=None, code_executor=None):
        super().__init__("ScriptStore")
        """
        Initialize the store.

        Args:
            notebook_store: Reference to notebook store
            ai_context_store: Reference to AI context store
            code_executor: Reference to code executor
        """
        self.actions: List[ScriptAction] = []
        self.steps: Dict[str, List[str]] = {}  # step_id -> list of action_ids
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

    # ==============================================
    # Helper Functions
    # ==============================================

    @staticmethod
    def clean_content(content: str, cell_type: str = 'text') -> str:
        """
        Clean content by removing meta-instruction prefixes.

        Args:
            content: Raw content from API
            cell_type: Type of cell ('text' or 'code')

        Returns:
            Cleaned content without meta-instruction prefixes
        """
        if not content:
            return content

        # Remove common meta-instruction prefixes
        prefixes_to_remove = [
            'Add text to the notebook:',
            'Add text to the notebook: ',
            'Add code to the notebook:',
            'Add code to the notebook: ',
            'Add code to the notebook and run it:',
            'Add code to the notebook and run it: ',
            'Update the title of the notebook:',
            'Update the title of the notebook: ',
        ]

        for prefix in prefixes_to_remove:
            if content.startswith(prefix):
                content = content[len(prefix):]
                break

        # For code cells, remove markdown code block markers if present
        if cell_type == 'code':
            content = content.strip()
            if content.startswith('```python\n'):
                content = content[10:]  # Remove ```python\n
            elif content.startswith('```\n'):
                content = content[4:]   # Remove ```\n
            if content.endswith('\n```'):
                content = content[:-4]  # Remove \n```
            elif content.endswith('```'):
                content = content[:-3]  # Remove ```

        return content.strip()

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
        # This would come from the state machine context
        # For now, return None - will be injected
        return None

    def get_current_step_actions(self) -> List[ScriptAction]:
        """Get actions for the current step."""
        current_step_id = self.get_current_step_id()
        if not current_step_id:
            return []

        action_ids = self.steps.get(current_step_id, [])
        return [action for action in self.actions if action.id in action_ids]

    # ==============================================
    # Action Management
    # ==============================================

    def create_new_action(
        self,
        action_type: str = 'text',
        content: str = '',
        metadata: Optional[ActionMetadata] = None
    ) -> Optional[str]:
        """Create a new action."""
        action_id = str(uuid.uuid4())
        content = content or self.get_default_content(action_type)
        metadata = metadata or ActionMetadata()

        new_action = ScriptAction(
            id=action_id,
            type=action_type,
            content=content,
            metadata=metadata
        )

        return self.add_action(new_action)

    def add_action(
        self,
        action: ScriptAction,
        could_visible_in_writing_mode: bool = True
    ) -> Optional[str]:
        """Add an action to the store and create corresponding notebook cell."""
        current_step_id = self.get_current_step_id()

        try:
            # Format content if text
            if action.type == 'text':
                content = action.content
                if action.metadata.is_step and not content.startswith('#'):
                    content = f"### {content}"
                action.content = content

            # Determine cell type
            cell_type = CELL_TYPE_MAPPING.get(action.type, 'markdown')

            # Create cell data
            cell_data = {
                'id': action.id,
                'type': cell_type,
                'content': action.content,
                'outputs': [],
                'enableEdit': cell_type != 'thinking',
                'phaseId': current_step_id,
                'description': action.description or '',
                'metadata': action.metadata.to_dict(),
                'couldVisibleInWritingMode': could_visible_in_writing_mode,
            }

            # Add type-specific data
            if cell_type in ['code', 'Hybrid']:
                cell_data['language'] = action.language

            if cell_type == 'thinking':
                cell_data['agentName'] = action.agent_name or 'AI'
                cell_data['customText'] = action.custom_text
                cell_data['textArray'] = action.text_array or [f"{action.agent_name or 'AI'} is thinking..."]
                cell_data['useWorkflowThinking'] = action.use_workflow_thinking

            # Add cell to notebook
            if self.notebook_store:
                self.notebook_store.add_cell(cell_data)

            # Add to actions list
            self.actions.append(action)

            # Add to step mapping
            if current_step_id:
                if current_step_id not in self.steps:
                    self.steps[current_step_id] = []
                self.steps[current_step_id].append(action.id)

            self.last_added_action_id = action.id

            self.info(f"[ScriptStore] Added action: {action.id} (type: {action.type})")
            return action.id

        except Exception as e:
            self.error(f"[ScriptStore] Error adding action: {e}", exc_info=True)
            return None

    def update_action(self, action_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing action."""
        try:
            # Find action
            action = None
            for a in self.actions:
                if a.id == action_id:
                    action = a
                    break

            if not action:
                return False

            # Update action
            for key, value in updates.items():
                if hasattr(action, key):
                    setattr(action, key, value)

            action.is_modified = True

            # Update notebook cell
            if self.notebook_store:
                if 'content' in updates:
                    self.notebook_store.update_cell(action_id, updates['content'])
                if 'metadata' in updates:
                    self.notebook_store.update_cell_metadata(action_id, updates['metadata'])

            self.info(f"[ScriptStore] Updated action: {action_id}")
            return True

        except Exception as e:
            self.error(f"[ScriptStore] Error updating action: {e}", exc_info=True)
            return False

    def remove_action(self, action_id: str) -> bool:
        """Remove an action."""
        try:
            # Remove from notebook
            if self.notebook_store:
                self.notebook_store.delete_cell(action_id)

            # Remove from actions list
            self.actions = [a for a in self.actions if a.id != action_id]

            # Remove from step mappings
            for step_id in self.steps:
                if action_id in self.steps[step_id]:
                    self.steps[step_id].remove(action_id)

            self.info(f"[ScriptStore] Removed action: {action_id}")
            return True

        except Exception as e:
            self.error(f"[ScriptStore] Error removing action: {e}", exc_info=True)
            return False

    # ==============================================
    # Specialized Operations
    # ==============================================

    def update_last_text(self, text: str):
        """Update the last text cell's content."""
        if not self.notebook_store:
            return

        last_cell = self.notebook_store.get_last_cell()
        if last_cell and last_cell.type == CellType.MARKDOWN:
            self.notebook_store.update_cell(last_cell.id, text)
            self.info(f"[ScriptStore] Updated last text cell")

    def finish_thinking(self):
        """Remove the last thinking cell."""
        if not self.notebook_store:
            return

        thinking_cells = self.notebook_store.get_cells_by_type(CellType.THINKING)
        if thinking_cells:
            last_thinking = thinking_cells[-1]
            self.notebook_store.delete_cell(last_thinking.id)
            self.actions = [a for a in self.actions if a.id != last_thinking.id]
            self.info(f"[ScriptStore] Finished thinking, removed cell: {last_thinking.id}")

    def set_effect_as_thinking(self, thinking_text: str = "finished thinking"):
        """Mark the last code cell as having finished thinking."""
        if not self.notebook_store:
            return

        last_cell = self.notebook_store.get_last_cell()
        if last_cell and last_cell.type == CellType.CODE:
            metadata = {
                **last_cell.metadata,
                'finished_thinking': True,
                'thinkingText': thinking_text
            }
            self.notebook_store.update_cell_metadata(last_cell.id, metadata)

            # Update action metadata
            for action in self.actions:
                if action.id == last_cell.id:
                    action.metadata.finished_thinking = True
                    action.metadata.thinking_text = thinking_text
                    break

            self.info(f"[ScriptStore] Set effect as thinking for cell: {last_cell.id}")

    # ==============================================
    # Code Execution
    # ==============================================

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
        if not codecell_id:
            return None

        if not self.code_executor:
            self.error("[ScriptStore] No code executor available")
            return None

        try:
            self.info(f"[ScriptStore] Executing code cell: {codecell_id}")

            # Get cell
            cell = self.notebook_store.get_cell(codecell_id) if self.notebook_store else None
            if not cell:
                self.error(f"[ScriptStore] Cell not found: {codecell_id}")
                return None

            # Execute code
            result = self.code_executor.execute(cell.content, cell_id=codecell_id)

            if result.get('success'):
                # Add outputs to cell
                if self.notebook_store and result.get('outputs'):
                    self.notebook_store.clear_cell_outputs(codecell_id)
                    for output in result['outputs']:
                        self.notebook_store.add_cell_output(codecell_id, output)

                # Add to effect context
                if self.ai_context_store and result.get('outputs'):
                    for output in result['outputs']:
                        output_text = output.content or output.text or str(output)
                        self.ai_context_store.add_effect(output_text)
                        self.info(f"[ScriptStore] Added effect: {output_text[:50]}...")

                return result.get('outputs')
            else:
                error = result.get('error', 'Unknown error')
                self.error(f"[ScriptStore] Code execution failed: {error}")

                if auto_debug:
                    self.info(f"[ScriptStore] Auto-debug triggered for cell: {codecell_id}")
                    # Implement auto-debug logic here

                return error

        except Exception as e:
            self.error(f"[ScriptStore] Error executing cell: {e}", exc_info=True)
            return None

    def update_title(self, title: str):
        """Update notebook title."""
        if self.notebook_store:
            self.notebook_store.update_title(title)
            self.info(f"[ScriptStore] Updated title: {title}")

    # ==============================================
    # Main Execution Engine
    # ==============================================

    @staticmethod
    def _dict_to_execution_step(data: Dict[str, Any]) -> ExecutionStep:
        """
        Convert a dictionary (from API) to an ExecutionStep object.
        Handles camelCase to snake_case conversion.

        Args:
            data: Dictionary from API response

        Returns:
            ExecutionStep object
        """
        # Map camelCase keys to snake_case
        key_mapping = {
            'shotType': 'shot_type',
            'storeId': 'store_id',
            'contentType': 'content_type',
            'agentName': 'agent_name',
            'customText': 'custom_text',
            'textArray': 'text_array',
            'thinkingText': 'thinking_text',
            'actionIdRef': 'action_id_ref',
            'stepId': 'step_id',
            'phaseId': 'phase_id',
            'keepDebugButtonVisible': 'keep_debug_button_visible',
            'codecellId': 'codecell_id',
            'needOutput': 'need_output',
            'autoDebug': 'auto_debug',
            'updatedWorkflow': 'updated_workflow',
            'updatedSteps': 'updated_steps',
            'stageId': 'stage_id',
        }

        # Convert keys
        converted = {}
        for key, value in data.items():
            new_key = key_mapping.get(key, key)
            converted[new_key] = value

        # Create ExecutionStep with converted data
        return ExecutionStep(**{k: v for k, v in converted.items() if k in ExecutionStep.__dataclass_fields__})

    def exec_action(self, step) -> Any:
        """
        Execute an action step.

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
            # Sync state if present
            if step.state and self.ai_context_store:
                self.info(f"[ScriptStore] Syncing state from action")
                context = self.ai_context_store.get_context()
                # Preserve effect state (use 'effects' to match server field name)
                merged_state = {**step.state, 'effects': context.effect}
                self.ai_context_store.set_context(merged_state)

            # Handle different action types
            if action_type == ACTION_TYPES['ADD_ACTION']:
                action_id = step.store_id or str(uuid.uuid4())
                cell_type = 'code' if step.shot_type == 'action' else 'text'
                # Clean content to remove meta-instruction prefixes
                cleaned_content = self.clean_content(step.content or '', cell_type)
                self.add_action(ScriptAction(
                    id=action_id,
                    type=cell_type,
                    content=cleaned_content,
                    metadata=step.metadata or ActionMetadata()
                ))

            elif action_type == ACTION_TYPES['NEW_CHAPTER']:
                action_id = step.store_id or str(uuid.uuid4())
                self.add_action(ScriptAction(
                    id=action_id,
                    type='text',
                    content=f"## {step.content}",
                    metadata=step.metadata or ActionMetadata()
                ))

            elif action_type == ACTION_TYPES['NEW_SECTION']:
                action_id = step.store_id or str(uuid.uuid4())
                self.add_action(ScriptAction(
                    id=action_id,
                    type='text',
                    content=f"### {step.content}",
                    metadata=step.metadata or ActionMetadata()
                ))

            elif action_type == ACTION_TYPES['IS_THINKING']:
                self.add_action(ScriptAction(
                    id=str(uuid.uuid4()),
                    type='thinking',
                    content='',
                    text_array=step.text_array or [],
                    agent_name=step.agent_name or 'AI',
                    custom_text=step.custom_text
                ))

            elif action_type == ACTION_TYPES['FINISH_THINKING']:
                self.finish_thinking()

            elif action_type == ACTION_TYPES['EXEC_CODE']:
                target_id = (self.last_added_action_id if step.codecell_id == "lastAddedCellId"
                             else step.codecell_id)
                if target_id:
                    self.info(f"[ScriptStore] Executing code: {target_id}")
                    result = self.exec_code_cell(target_id, step.need_output, step.auto_debug)
                    return result

            elif action_type == 'set_effect_as_thinking':
                self.set_effect_as_thinking(step.thinking_text or "finished thinking")

            elif action_type == 'update_last_text':
                self.update_last_text(step.text or '')

            elif action_type == ACTION_TYPES['UPDATE_TITLE']:
                if step.title:
                    # Clean title to remove meta-instruction prefixes
                    cleaned_title = self.clean_content(step.title, 'text')
                    self.update_title(cleaned_title)

            elif action_type == ACTION_TYPES['COMPLETE_STEP']:
                self.info("[ScriptStore] Received command to complete step")
                # This would trigger state machine transition
                # Handled externally

            elif action_type == ACTION_TYPES['UPDATE_WORKFLOW']:
                self.info("[ScriptStore] Workflow update requested")
                # Store the updated workflow for state machine to process
                if step.updated_workflow:
                    self.pending_workflow_update = step.updated_workflow
                    self.info(f"[ScriptStore] Stored pending workflow update: {step.updated_workflow.get('name', 'Unknown')}")

                    # Initialize workflow_progress in AI context
                    if self.ai_context_store:
                        self.ai_context_store.initialize_workflow_progress(step.updated_workflow)
                        self.info("[ScriptStore] Initialized workflow_progress in AI context")

                    # Return a special marker to indicate workflow update is pending
                    return {'workflow_update_pending': True}

            elif action_type == ACTION_TYPES['UPDATE_STEP_LIST']:
                self.info(f"[ScriptStore] Updating steps for stage: {step.stage_id}")
                # Update pipeline store
                # Handled externally

            else:
                self.warning(f"[ScriptStore] Unknown action type: {action_type}")

            # Check if this action marks a section (NEW)
            if step.metadata and step.metadata.is_section:
                self._handle_section(step)

        except Exception as e:
            self.error(f"[ScriptStore] Error executing action {action_type}: {e}", exc_info=True)
            raise

        return None

    def _handle_section(self, step):
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
