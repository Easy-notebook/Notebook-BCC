"""
NewChapterAction - Creates a new chapter (Level 1 heading)
"""

import uuid
from typing import Optional
from models.action import ExecutionStep, ScriptAction, ActionMetadata
from ..base import ActionBase, action


@action('new_chapter')
class NewChapterAction(ActionBase):
    """Handle NEW_CHAPTER type (Level 1 heading: #)."""

    def execute(self, step: ExecutionStep) -> Optional[str]:
        """Execute new chapter action."""
        if not step or not step.content:
            self.script_store.warning("[NewChapterAction] Requires content")
            return None

        action_id = step.store_id or str(uuid.uuid4())
        self.script_store.add_action(ScriptAction(
            id=action_id,
            type='text',
            content=f"# {step.content}",
            metadata=step.metadata or ActionMetadata()
        ))
        self.script_store.chapter_counter += 1
        return action_id
