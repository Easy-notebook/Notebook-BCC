"""
State Updater
Apply transition (API response) to state and generate updated state.

REFACTORED: Now delegates to core.transition_handlers for FSM-based transitions.

Response Handling:
- Planning API: Returns XML (stages/steps/behaviors) - parsed by xml_parser
- Generating API: Returns action stream (NDJSON) - converted to JSON
- Reflecting API: Returns action stream (NDJSON) - converted to JSON
"""

import json
from typing import Dict, Any
from silantui import ModernLogger
from core.transition_handlers import get_transition_coordinator
from .xml_parser import planning_xml_parser


class StateUpdater(ModernLogger):
    """
    Apply transition responses to workflow states.

    This class now acts as a facade, delegating to the transition_handlers
    module for actual state transitions.

    Maintains backward compatibility with the old API while using the new
    FSM-based transition handler architecture.
    """

    def __init__(self, script_store=None):
        """Initialize the state updater.

        Args:
            script_store: Optional ScriptStore instance for executing actions during transitions
        """
        super().__init__("StateUpdater")
        self.coordinator = get_transition_coordinator()
        if script_store:
            self.coordinator.set_script_store(script_store)

    def set_script_store(self, script_store) -> None:
        """
        Set the script_store for the coordinator.

        Args:
            script_store: ScriptStore instance for executing actions during transitions
        """
        self.coordinator.set_script_store(script_store)

    def apply_transition(
        self,
        state: Dict[str, Any],
        transition_response: str,
        transition_type: str = 'auto'
    ) -> tuple[Dict[str, Any], str]:
        """
        Apply transition response to state.

        Args:
            state: Current state (loaded from state JSON)
            transition_response: Transition response
                - Planning API: XML string (stages/steps/behaviors)
                - Generating/Reflecting: JSON string or dict (from action stream)
            transition_type: Type of transition ('planning', 'generating', 'reflecting', 'auto')

        Returns:
            Tuple of (updated state, transition name)

        Raises:
            ValueError: If no handler can process the response
        """
        # Parse the transition response based on type
        if isinstance(transition_response, dict):
            # Already a dict, use directly
            api_response = transition_response
            self.info(f"[StateUpdater] Using dict response directly")

        elif isinstance(transition_response, str):
            # String response - could be XML (planning) or JSON (generating/reflecting)
            transition_response = transition_response.strip()

            # Planning API returns XML
            if transition_type == 'planning' or transition_response.startswith('<'):
                self.info(f"[StateUpdater] Parsing XML response (Planning API)")
                try:
                    api_response = planning_xml_parser.parse(transition_response)
                except Exception as e:
                    self.error(f"[StateUpdater] Failed to parse XML: {e}")
                    self.error(f"[StateUpdater] Response preview: {transition_response[:200]}")
                    raise ValueError(f"Invalid XML response: {e}")

            # Generating/Reflecting APIs return JSON (from action stream)
            else:
                self.info(f"[StateUpdater] Parsing JSON response (Generating/Reflecting API)")
                try:
                    api_response = json.loads(transition_response)
                except json.JSONDecodeError as e:
                    self.error(f"[StateUpdater] Failed to parse JSON: {e}")
                    self.error(f"[StateUpdater] Response preview: {transition_response[:200]}")
                    raise ValueError(f"Invalid JSON response: {e}")
        else:
            raise ValueError(f"Unsupported response type: {type(transition_response)}")

        # Delegate to transition coordinator
        try:
            updated_state, transition_name = self.coordinator.apply_transition(
                state=state,
                api_response=api_response,
                api_type=transition_type
            )

            # Debug: log the final FSM state
            final_fsm_state = updated_state.get('state', {}).get('FSM', {}).get('state', 'UNKNOWN')
            self.info(f"[StateUpdater] Final FSM state after transition: {final_fsm_state} (via {transition_name})")

            return updated_state, transition_name

        except ValueError as e:
            self.error(f"[StateUpdater] Transition failed: {e}")
            raise


# Global singleton
state_updater = StateUpdater()
