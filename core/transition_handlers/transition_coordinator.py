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


class TransitionCoordinator(ModernLogger):
    """
    Coordinates FSM state transitions.

    Responsibilities:
    1. Maintains registry of all transition handlers
    2. Selects appropriate handler based on API response
    3. Applies transition using the selected handler
    4. Returns updated state
    """

    def __init__(self):
        """Initialize the coordinator."""
        super().__init__("TransitionCoordinator")
        self._handlers: List[BaseTransitionHandler] = []
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
        ]
        self.info(f"Registered {len(self._handlers)} transition handlers")

    def apply_transition(
        self,
        state: Dict[str, Any],
        api_response: Any,
        api_type: str = None
    ) -> Dict[str, Any]:
        """
        Apply state transition based on API response.

        Args:
            state: Current state JSON
            api_response: API response (parsed content)
            api_type: Optional API type hint ('planning', 'generating', 'reflecting')

        Returns:
            Updated state JSON with transition applied

        Raises:
            ValueError: If no handler can process the response
        """
        self.info(f"[Coordinator] Applying transition (api_type={api_type})")

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
