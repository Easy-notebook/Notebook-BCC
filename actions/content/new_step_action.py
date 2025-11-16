"""
NewStepAction - Creates a new step (Level 3 heading)
"""

import uuid
from typing import Optional
from models.action import ExecutionStep, ScriptAction, ActionMetadata
from ..base import ActionBase, action


@action('new_step')
class NewStepAction(ActionBase):
    """Handle NEW_STEP type (Level 3 heading: ###)."""

    def execute(self, step: ExecutionStep) -> Optional[str]:
        """Execute new step action."""
        if not step or not step.content:
            self.script_store.warning("[NewStepAction] Requires content")
            return None

        action_id = step.store_id or str(uuid.uuid4())
        self.script_store.add_action(ScriptAction(
            id=action_id,
            type='text',
            content=f"### {step.content}",
            metadata=step.metadata or ActionMetadata()
        ))
        return action_id
