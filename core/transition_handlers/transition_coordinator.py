"""
Transition Coordinator
Coordinates FSM state transitions using appropriate handlers.

This is the main entry point for applying state transitions,
replacing the old state_updater.apply_transition() method.
"""

from typing import Dict, Any, List
from silantui import ModernLogger

from .base_transition_handler import BaseTransitionHandler
from .START_WORKFLOW_handler import StartWorkflowHandler
from .START_STEP_handler import StartStepHandler
from .START_BEHAVIOR_handler import StartBehaviorHandler
from .COMPLETE_BEHAVIOR_handler import CompleteBehaviorHandler
from .NEXT_BEHAVIOR_handler import NextBehaviorHandler
from .COMPLETE_STEP_handler import CompleteStepHandler
from .NEXT_STEP_handler import NextStepHandler
from .COMPLETE_STAGE_handler import CompleteStageHandler
from .NEXT_STAGE_handler import NextStageHandler


class TransitionCoordinator(ModernLogger):
    """
    Coordinates FSM state transitions.

    Responsibilities:
    1. Maintains registry of all transition handlers
    2. Selects appropriate handler based on API response
    3. Applies transition using the selected handler
    4. Returns updated state
    """

    def __init__(self, script_store=None):
        """Initialize the coordinator.

        Args:
            script_store: Optional ScriptStore instance for executing actions during transitions
        """
        super().__init__("TransitionCoordinator")
        self._handlers: List[BaseTransitionHandler] = []
        self._script_store = script_store
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register all transition handlers."""
        self._handlers = [
            StartWorkflowHandler(),
            StartStepHandler(),
            StartBehaviorHandler(),
            CompleteBehaviorHandler(),
            NextBehaviorHandler(),
            CompleteStepHandler(),
            NextStepHandler(),
            CompleteStageHandler(),
            NextStageHandler(),
        ]

        # Inject script_store into all handlers
        if self._script_store:
            for handler in self._handlers:
                handler.script_store = self._script_store
            self.info(f"Injected script_store into {len(self._handlers)} handlers")

        self.info(f"Registered {len(self._handlers)} transition handlers")

    def apply_transition(
        self,
        state: Dict[str, Any],
        api_response: Any,
        api_type: str = None,
        auto_trigger: bool = True
    ) -> Dict[str, Any]:
        """
        Apply state transition based on API response.

        Args:
            state: Current state JSON
            api_response: API response (parsed content)
            api_type: Optional API type hint ('planning', 'generating', 'reflecting')
            auto_trigger: If True, automatically trigger next transition if determined by state

        Returns:
            Updated state JSON with transition applied

        Raises:
            ValueError: If no handler can process the response
        """
        self.info(f"[Coordinator] Applying transition (api_type={api_type}, auto_trigger={auto_trigger})")

        # Find handler that can process this response
        handler = self._find_handler(api_response)

        if not handler:
            self.warning(f"No handler found for response: {type(api_response)}")
            self.warning(f"Response keys: {api_response.keys() if isinstance(api_response, dict) else 'N/A'}")
            raise ValueError(
                f"No transition handler found for API response. "
                f"Response type: {type(api_response)}, "
                f"Keys: {list(api_response.keys()) if isinstance(api_response, dict) else 'N/A'}"
            )

        self.info(f"[Coordinator] Selected handler: {handler.__class__.__name__}")

        # Apply transition
        updated_state = handler.apply(state, api_response)

        self.info("[Coordinator] Transition applied successfully")

        # Auto-trigger next transition if enabled
        if auto_trigger:
            updated_state = self._auto_trigger_next_transition(updated_state)

        return updated_state

    def _find_handler(self, api_response: Any) -> BaseTransitionHandler | None:
        """
        Find the appropriate handler for the API response.

        Args:
            api_response: API response to process

        Returns:
            Handler instance or None if no handler found
        """
        for handler in self._handlers:
            if handler.can_handle(api_response):
                return handler
        return None

    def set_script_store(self, script_store) -> None:
        """
        Set the script_store for all handlers.

        Args:
            script_store: ScriptStore instance for executing actions during transitions
        """
        self._script_store = script_store
        for handler in self._handlers:
            handler.script_store = script_store
        self.info("Updated script_store for all handlers")

    def get_registered_handlers(self) -> List[BaseTransitionHandler]:
        """
        Get list of all registered handlers.

        Returns:
            List of handler instances
        """
        return self._handlers.copy()

    def get_handler(self, from_state: str, to_state: str) -> BaseTransitionHandler | None:
        """
        Get a specific transition handler by state transition.

        Args:
            from_state: Source state name (e.g., 'IDLE')
            to_state: Target state name (e.g., 'STAGE_RUNNING')

        Returns:
            Handler instance or None if not found
        """
        # Normalize state names
        from_state = from_state.upper()
        to_state = to_state.upper()

        # Search for matching handler
        for handler in self._handlers:
            handler_from = handler.from_state.upper()
            handler_to = handler.to_state.upper()

            if handler_from == from_state and handler_to == to_state:
                return handler

        self.warning(f"No handler found for {from_state} -> {to_state}")
        return None

    def _auto_trigger_next_transition(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Automatically trigger the next transition if determined by current state.

        Only certain states support auto-triggering:
        - STEP_COMPLETED: Can auto-trigger NEXT_STEP or COMPLETE_STAGE
        - STAGE_COMPLETED: Can auto-trigger NEXT_STAGE or COMPLETE_WORKFLOW

        States that require API response (e.g., BEHAVIOR_COMPLETED) are excluded.

        Args:
            state: Current state JSON after a transition

        Returns:
            Updated state JSON (may be modified by auto-triggered transition)
        """
        from core.state_classes.state_factory import StateFactory

        # Get current FSM state
        fsm_data = state.get('state', {}).get('FSM', {})
        current_state_name = fsm_data.get('state')

        if not current_state_name:
            return state

        # Only auto-trigger for specific states
        # BEHAVIOR_COMPLETED requires Reflecting API response, not auto-trigger
        AUTO_TRIGGER_ALLOWED_STATES = [
            'STEP_COMPLETED',
            'STAGE_COMPLETED',
            'ACTION_COMPLETED',  # May need auto-trigger in future
        ]

        if current_state_name not in AUTO_TRIGGER_ALLOWED_STATES:
            self.info(f"[Auto-Trigger] Skipping auto-trigger for {current_state_name} (requires API response)")
            return state

        # Get state class instance
        state_instance = StateFactory.get_state(current_state_name)
        if not state_instance:
            return state

        # Determine if there's a next transition
        next_event = state_instance.determine_next_transition(state)
        if not next_event:
            return state

        self.info(f"[Auto-Trigger] Triggering {next_event.value} from {current_state_name}")

        # Create auto-trigger API response
        auto_response = {
            '_auto_trigger': next_event.value,
            'transition': next_event.value,
            'next_state': current_state_name  # Placeholder
        }

        # Apply the auto-triggered transition (without recursion)
        try:
            state = self.apply_transition(state, auto_response, auto_trigger=False)
            self.info(f"[Auto-Trigger] Successfully triggered {next_event.value}")
        except ValueError as e:
            self.warning(f"[Auto-Trigger] Failed to trigger {next_event.value}: {e}")

        return state


# Global singleton instance
_coordinator_instance = None


def get_transition_coordinator() -> TransitionCoordinator:
    """
    Get the global transition coordinator instance.

    Returns:
        Singleton TransitionCoordinator instance
    """
    global _coordinator_instance
    if _coordinator_instance is None:
        _coordinator_instance = TransitionCoordinator()
    return _coordinator_instance
