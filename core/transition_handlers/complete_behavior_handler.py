"""
COMPLETE_BEHAVIOR Event Handler
Handles action completion from generating API.
Event: COMPLETE_BEHAVIOR (internally uses COMPLETE_ACTION)
Transition: BEHAVIOR_RUNNING → BEHAVIOR_COMPLETED
"""

from typing import Dict, Any
from .base_transition_handler import BaseTransitionHandler


class CompleteBehaviorHandler(BaseTransitionHandler):
    """
    Handles COMPLETE_BEHAVIOR event.
    Transition: BEHAVIOR_RUNNING → BEHAVIOR_COMPLETED

    Triggered by: Generating API returning actions list

    Updates:
    - state.FSM.state to 'BEHAVIOR_COMPLETED'

    Note: Actions should already be executed and state updated from stores
    before calling this handler. This handler only performs the FSM transition.
    """

    def __init__(self):
        super().__init__(
            'BEHAVIOR_RUNNING',
            'BEHAVIOR_COMPLETED',
            'COMPLETE_BEHAVIOR'
        )

    def can_handle(self, api_response: Any) -> bool:
        """Check if response contains actions list."""
        if isinstance(api_response, dict):
            # Check for actions field
            if 'actions' in api_response:
                return isinstance(api_response['actions'], list)
            # Also handle count field from iteration loop
            if 'count' in api_response and isinstance(api_response.get('count'), int):
                return True
        return False

    def apply(self, state: Dict[str, Any], api_response: Any) -> Dict[str, Any]:
        """
        Apply COMPLETE_BEHAVIOR transition.

        Args:
            state: Current state JSON (should already contain updated notebook/effects)
            api_response: Generating API response with actions

        Returns:
            Updated state JSON with FSM transitioned
        """
        new_state = self._deep_copy_state(state)

        actions = api_response.get('actions', [])
        action_count = api_response.get('count', len(actions))

        self.info(f"Applying actions transition: {action_count} actions received")

        # Update FSM state to BEHAVIOR_COMPLETED
        # This signals that all actions have been executed
        self._update_fsm_state(new_state, 'BEHAVIOR_COMPLETED', 'COMPLETE_ACTION')

        self.info("Transition complete: COMPLETE_BEHAVIOR")

        return new_state
