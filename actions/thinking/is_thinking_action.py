"""
IsThinkingAction - Displays a thinking indicator in the notebook
"""

import uuid
from typing import Optional
from models.action import ExecutionStep, ScriptAction
from ..base import ActionBase, action


@action('is_thinking')
class IsThinkingAction(ActionBase):
    """Handle IS_THINKING type - displays a thinking indicator."""

    def execute(self, step: ExecutionStep) -> Optional[str]:
        """Execute is thinking action."""
        action_id = str(uuid.uuid4())
        self.script_store.add_action(ScriptAction(
            id=action_id,
            type='thinking',
            content='',
            text_array=step.text_array or [],
            agent_name=step.agent_name or 'AI',
            custom_text=step.custom_text
        ))
        return action_id
