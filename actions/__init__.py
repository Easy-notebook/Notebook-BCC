"""
Actions Module - Decorator-Based Action Registration System

This module provides a clean, extensible action system using the decorator pattern.
All actions are automatically discovered and registered when this module is imported.

Architecture:
-----------
    actions/
    ├── base.py              # ActionBase class and @action decorator
    ├── utils.py             # Shared utilities (content cleaning, etc.)
    ├── content/             # Content creation and organization actions
    │   ├── add_action.py
    │   ├── new_chapter_action.py
    │   ├── new_section_action.py
    │   ├── new_step_action.py
    │   └── comment_result_action.py
    ├── code/                # Code execution actions
    │   ├── exec_code_action.py
    │   └── set_effect_thinking_action.py
    ├── thinking/            # Thinking process visualization actions
    │   ├── is_thinking_action.py
    │   └── finish_thinking_action.py
    └── workflow/            # Workflow metadata actions
        ├── update_title_action.py
        └── update_last_text_action.py

Usage:
-----
    # Get all registered action types
    from actions import get_all_action_types
    print(get_all_action_types())

    # Get a specific action class
    from actions import get_action_class
    AddAction = get_action_class('add')

    # Create custom action
    from actions import ActionBase, action

    @action('custom_action')
    class CustomAction(ActionBase):
        def execute(self, step):
            # Your implementation
            pass

Registered Actions:
------------------
Content Actions:
    - add: Adds text or code cells
    - add-text: Alias for add action
    - new_chapter: Creates level 1 heading (#)
    - new_section: Creates level 2 heading (##)
    - new_step: Creates level 3 heading (###)
    - comment_result: Adds content and moves effects to history

Code Actions:
    - exec: Executes code cells
    - set_effect_as_thinking: Marks code as finished thinking

Thinking Actions:
    - is_thinking: Shows thinking indicator
    - finish_thinking: Removes thinking indicator

Workflow Actions:
    - update_title: Updates notebook title
    - update_last_text: Updates last text cell content
"""

from .base import ActionBase, action, get_action_class, get_all_action_types, clear_registry

# Import all action category modules to trigger decorator registration
# Each import automatically registers all actions in that category
from . import content
from . import code
from . import thinking
from . import workflow

__all__ = [
    'ActionBase',
    'action',
    'get_action_class',
    'get_all_action_types',
    'clear_registry',
]
