"""
NewSectionAction - Creates a new section (Level 2 heading)
"""

import uuid
from typing import Optional
from models.action import ExecutionStep, ScriptAction, ActionMetadata
from ..base import ActionBase, action


@action('new_section')
class NewSectionAction(ActionBase):
    """Handle NEW_SECTION type (Level 2 heading: ##)."""

    def execute(self, step: ExecutionStep) -> Optional[str]:
        """Execute new section action."""
        if not step or not step.content:
            self.script_store.warning("[NewSectionAction] Requires content")
            return None

        action_id = step.store_id or str(uuid.uuid4())
        self.script_store.add_action(ScriptAction(
            id=action_id,
            type='text',
            content=f"## {step.content}",
            metadata=step.metadata or ActionMetadata()
        ))
        self.script_store.section_counter += 1
        return action_id
