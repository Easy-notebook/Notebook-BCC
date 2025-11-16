"""
Content Actions - Manage content addition and organization

This module contains actions for creating and organizing notebook content:
- AddAction: Adds text or code cells to the notebook
- NewChapterAction: Creates level 1 headings (#)
- NewSectionAction: Creates level 2 headings (##)
- NewStepAction: Creates level 3 headings (###)
- CommentResultAction: Adds content and moves effects to history
"""

from .add_action import AddAction, AddTextAction
from .new_chapter_action import NewChapterAction
from .new_section_action import NewSectionAction
from .new_step_action import NewStepAction
from .comment_result_action import CommentResultAction

__all__ = [
    'AddAction',
    'AddTextAction',
    'NewChapterAction',
    'NewSectionAction',
    'NewStepAction',
    'CommentResultAction',
]
