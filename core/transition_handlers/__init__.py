"""
Transition Handlers
Handles FSM state transitions and associated state updates.

Each handler corresponds to a specific FSM transition and:
1. Parses the API response
2. Updates the state JSON
3. Performs the FSM state transition
"""

from .base_transition_handler import BaseTransitionHandler
from .transition_coordinator import TransitionCoordinator, get_transition_coordinator

__all__ = [
    'BaseTransitionHandler',
    'TransitionCoordinator',
    'get_transition_coordinator',
]
