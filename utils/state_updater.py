"""
State Updater
Apply transition (API response) to state and generate updated state.

REFACTORED: Now delegates to core.transition_handlers for FSM-based transitions.
"""

from typing import Dict, Any
from silantui import ModernLogger
from .response_parser import ResponseParser
from core.transition_handlers import get_transition_coordinator


class StateUpdater(ModernLogger):
    """
    Apply transition responses to workflow states.

    This class now acts as a facade, delegating to the transition_handlers
    module for actual state transitions.

    Maintains backward compatibility with the old API while using the new
    FSM-based transition handler architecture.
    """

    def __init__(self):
        """Initialize the state updater."""
        super().__init__("StateUpdater")
        self.parser = ResponseParser()
        self.coordinator = get_transition_coordinator()

    def apply_transition(
        self,
        state: Dict[str, Any],
        transition_response: str,
        transition_type: str = 'auto'
    ) -> Dict[str, Any]:
        """
        Apply transition response to state.

        Args:
            state: Current state (loaded from state JSON)
            transition_response: Transition response (XML or JSON string)
            transition_type: Type of transition ('planning', 'generating', 'reflecting', 'auto')

        Returns:
            Updated state

        Raises:
            ValueError: If no handler can process the response
        """
        # Parse the transition response using response parser
        parsed = self.parser.parse_response(transition_response)

        self.info(f"[StateUpdater] Parsed transition type: {parsed['type']}")

        # Delegate to transition coordinator
        try:
            updated_state = self.coordinator.apply_transition(
                state=state,
                api_response=parsed['content'],
                api_type=transition_type
            )
            return updated_state

        except ValueError as e:
            self.error(f"[StateUpdater] Transition failed: {e}")

            # Fallback: try legacy methods for backward compatibility
            self.warning("[StateUpdater] Attempting legacy transition handling")
            return self._fallback_apply_transition(state, parsed)

    def _fallback_apply_transition(
        self,
        state: Dict[str, Any],
        parsed: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Fallback for unsupported transitions.

        This handles edge cases not yet covered by transition handlers.

        Args:
            state: Current state
            parsed: Parsed response with 'type' and 'content'

        Returns:
            Updated state (may be unchanged if no handler available)
        """
        response_type = parsed['type']
        content = parsed['content']

        self.warning(f"[StateUpdater] Fallback handling for type: {response_type}")

        # For now, just log and return original state
        # Future: implement fallback handlers as needed
        if response_type == 'json':
            self.warning("[StateUpdater] Generic JSON response - no specific handler")
            # Could implement generic context_update handling here
            return self._apply_generic_json_transition(state, content)

        self.warning(f"[StateUpdater] No fallback handler for type: {response_type}")
        return state

    def _apply_generic_json_transition(
        self,
        state: Dict[str, Any],
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply generic JSON transition (for backward compatibility).

        Handles context_update in JSON responses.

        Args:
            state: Current state
            content: Parsed JSON content

        Returns:
            Updated state
        """
        from copy import deepcopy
        new_state = deepcopy(state)

        # Check for context_update
        if 'context_update' in content:
            context_update = content['context_update']

            # Update variables if present
            if 'variables' in context_update:
                new_vars = context_update['variables']
                state_data = new_state.get('state', {})
                current_vars = state_data.setdefault('variables', {})
                current_vars.update(new_vars)
                self.info(f"[StateUpdater] Updated {len(new_vars)} variables")

        # Check for transition info
        if 'transition' in content:
            transition = content['transition']
            if transition.get('target_achieved'):
                # Move to completed state
                fsm = new_state.get('state', {}).get('FSM', {})
                current_state = fsm.get('state', 'UNKNOWN')

                if 'STEP' in current_state:
                    fsm['state'] = 'STEP_COMPLETED'
                elif 'BEHAVIOR' in current_state:
                    fsm['state'] = 'BEHAVIOR_COMPLETED'
                elif 'STAGE' in current_state:
                    fsm['state'] = 'STAGE_COMPLETED'

                self.info(f"[StateUpdater] Generic transition: {current_state} → {fsm.get('state')}")

        return new_state


# Global singleton
state_updater = StateUpdater()
