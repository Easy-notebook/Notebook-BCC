"""
UpdateTitleAction - Updates the notebook title
"""

from models.action import ExecutionStep
from ..base import ActionBase, action
from ..utils import clean_content


@action('update_title')
class UpdateTitleAction(ActionBase):
    """Handle UPDATE_TITLE type - updates the notebook title."""

    def execute(self, step: ExecutionStep) -> bool:
        """Execute update title action."""
        # Title can be in either step.title or step.content
        title_text = step.title or step.content
        if not step or not title_text:
            self.script_store.warning("[UpdateTitleAction] Requires title or content")
            return False

        cleaned_title = clean_content(title_text, 'text')
        self._update_title(cleaned_title)
        return True

    def _update_title(self, title: str) -> None:
        """Update notebook title."""
        if self.notebook_store:
            self.notebook_store.update_title(title)
            self.script_store.info(f"[UpdateTitleAction] Updated title: {title}")
