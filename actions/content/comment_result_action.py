"""
CommentResultAction - Adds markdown content and moves current effects to history
"""

import uuid
from typing import Optional
from models.action import ExecutionStep, ScriptAction, ActionMetadata
from ..base import ActionBase, action
from ..utils import clean_content


@action('comment_result')
class CommentResultAction(ActionBase):
    """
    Handle COMMENT_RESULT type.

    This action type works exactly like add_markdown (adding markdown content),
    but after execution it moves effect.current to effect.history.
    """

    def execute(self, step: ExecutionStep) -> Optional[str]:
        """Execute comment result action."""
        if not step:
            raise ValueError("Execution step cannot be None")

        cell_type = 'text'
        cleaned_content = clean_content(step.content or '', cell_type)

        # Create new markdown cell
        action_id = step.store_id or str(uuid.uuid4())
        self.script_store.add_action(ScriptAction(
            id=action_id,
            type=cell_type,
            content=cleaned_content,
            metadata=step.metadata or ActionMetadata()
        ))

        # After adding the content, move current effects to history
        if self.ai_context_store:
            self.ai_context_store.move_current_effects_to_history()
            self.script_store.info("[CommentResultAction] Moved effect.current to history")

        return action_id
