"""
Workflow Actions - Manage workflow metadata and text updates

This module contains actions for updating workflow properties:
- UpdateTitleAction: Updates the notebook title
- UpdateLastTextAction: Updates the content of the last text cell
"""

from .update_title_action import UpdateTitleAction
from .update_last_text_action import UpdateLastTextAction

__all__ = [
    'UpdateTitleAction',
    'UpdateLastTextAction',
]
