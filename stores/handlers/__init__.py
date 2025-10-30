"""
Action Handlers - Modular handler implementations
Each module contains related action handlers for better organization.
"""

from .content_handlers import (
    handle_add_action,
    handle_new_chapter,
    handle_new_section,
)
from .code_handlers import (
    handle_exec_code,
    handle_set_effect_thinking,
)
from .thinking_handlers import (
    handle_is_thinking,
    handle_finish_thinking,
)
from .workflow_handlers import (
    handle_update_title,
)
from .text_handlers import (
    handle_update_last_text,
)

__all__ = [
    # Content handlers
    'handle_add_action',
    'handle_new_chapter',
    'handle_new_section',
    # Code handlers
    'handle_exec_code',
    'handle_set_effect_thinking',
    # Thinking handlers
    'handle_is_thinking',
    'handle_finish_thinking',
    # Workflow handlers
    'handle_update_title',
    # Text handlers
    'handle_update_last_text',
]
