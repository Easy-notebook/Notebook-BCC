"""
Transition Handlers - Handle state transitions and API interactions.

Each handler is responsible for:
1. Calling the appropriate API (planning/generating/reflecting)
2. Parsing the response
3. Updating the state machine context
4. Triggering the next transition if needed
"""

from .start_workflow_handler import handle_start_workflow
from .start_step_handler import handle_start_step
from .start_behavior_handler import handle_start_behavior
from .behavior_running_handler import handle_behavior_running
from .complete_behavior_handler import handle_complete_behavior
from .complete_step_handler import handle_complete_step
from .complete_stage_handler import handle_complete_stage
from .next_stage_handler import handle_next_stage
from .next_step_handler import handle_next_step
from .next_behavior_handler import handle_next_behavior

__all__ = [
    'handle_start_workflow',
    'handle_start_step',
    'handle_start_behavior',
    'handle_behavior_running',
    'handle_complete_behavior',
    'handle_complete_step',
    'handle_complete_stage',
    'handle_next_stage',
    'handle_next_step',
    'handle_next_behavior',
]
