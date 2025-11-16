"""
AddAction - Adds text or code content to the notebook
"""

import uuid
from typing import Optional
from models.action import ExecutionStep, ScriptAction, ActionMetadata
from models.cell import CellType
from ..base import ActionBase, action
from ..utils import clean_content


@action('add')
class AddAction(ActionBase):
    """
    Handle ADD_ACTION type - adds text or code content to the notebook.

    For text cells with shot_type='markdown' or None (default to markdown):
    - If the last cell is a markdown cell and is NOT a heading (doesn't start with #),
      append content to the last cell instead of creating a new one
    - Otherwise, create a new cell as usual
    """

    def execute(self, step: ExecutionStep) -> Optional[str]:
        """Execute add action."""
        cell_type = 'code' if step.shot_type == 'action' else 'text'
        cleaned_content = clean_content(step.content or '', cell_type)

        # Special logic for text cells
        if cell_type == 'text' and (step.shot_type == 'markdown' or step.shot_type is None):
            if self.notebook_store:
                last_cell = self.notebook_store.get_last_cell()

                # Append to last cell if it's a non-heading markdown cell
                if last_cell and hasattr(last_cell, 'type'):
                    if (last_cell.type == CellType.MARKDOWN and
                        last_cell.content and
                        not last_cell.content.strip().startswith('#')):
                        new_content = last_cell.content + '\n\n' + cleaned_content
                        self.notebook_store.update_cell(last_cell.id, new_content)
                        self.script_store.info(f"[AddAction] Appended to cell: {last_cell.id}")
                        return last_cell.id

        # Default behavior: create new cell
        action_id = step.store_id or str(uuid.uuid4())
        self.script_store.add_action(ScriptAction(
            id=action_id,
            type=cell_type,
            content=cleaned_content,
            metadata=step.metadata or ActionMetadata()
        ))
        return action_id


# Alias for 'add-text' action type
@action('add-text')
class AddTextAction(AddAction):
    """Alias for AddAction - maintains backward compatibility."""
    def execute(self, step: ExecutionStep) -> Optional[str]:
        """Execute add action."""
        cell_type = 'text'
        cleaned_content = clean_content(step.content or '', cell_type)

        # Special logic for text cells
        if cell_type == 'text' and (step.shot_type == 'markdown' or step.shot_type is None):
            if self.notebook_store:
                last_cell = self.notebook_store.get_last_cell()

                # Append to last cell if it's a non-heading markdown cell
                if last_cell and hasattr(last_cell, 'type'):
                    if (last_cell.type == CellType.MARKDOWN and
                        last_cell.content and
                        not last_cell.content.strip().startswith('#')):
                        new_content = last_cell.content + '\n\n' + cleaned_content
                        self.notebook_store.update_cell(last_cell.id, new_content)
                        self.script_store.info(f"[AddAction] Appended to cell: {last_cell.id}")
                        return last_cell.id

        # Default behavior: create new cell
        action_id = step.store_id or str(uuid.uuid4())
        self.script_store.add_action(ScriptAction(
            id=action_id,
            type=cell_type,
            content=cleaned_content,
            metadata=step.metadata or ActionMetadata()
        ))
        return action_id
