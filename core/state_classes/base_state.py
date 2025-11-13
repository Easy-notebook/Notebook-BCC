"""
Base State Class
Defines the interface for all state classes in the workflow state machine.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TYPE_CHECKING, AsyncIterator
from silantui import ModernLogger
from core.api_types import APIResponseType, PlanningResponseType

if TYPE_CHECKING:
    from ..events import WorkflowEvent


class BaseState(ABC, ModernLogger):
    """
    Base class for all workflow states.

    Each state encapsulates:
    1. Valid outgoing transitions
    2. Logic to determine next transition based on store/context
    3. Initialization from API response
    4. Reference to appropriate transition handler
    """

    def __init__(self, state_name: str):
        """
        Initialize the state.

        Args:
            state_name: The name of this state (e.g., 'IDLE', 'STAGE_RUNNING')
        """
        ModernLogger.__init__(self, f"State.{state_name}")
        self.state_name = state_name
        self._api_client = None  # Will be injected by state machine

    @abstractmethod
    def get_valid_transitions(self) -> Dict[str, 'WorkflowEvent']:
        """
        Get all valid outgoing transitions from this state.

        Returns:
            Dict mapping transition name to WorkflowEvent
            Example: {'start_workflow': WorkflowEvent.START_WORKFLOW}
        """
        pass

    @abstractmethod
    def determine_next_transition(
        self,
        state_data: Dict[str, Any],
        api_response: Optional[Any] = None
    ) -> Optional['WorkflowEvent']:
        """
        Determine the next transition based on current state data.

        This is the key method that encapsulates state-specific logic.
        It examines the store/context and decides which transition to take.

        Args:
            state_data: Current state JSON (the full state dict)
            api_response: Optional API response data

        Returns:
            WorkflowEvent to trigger, or None if no transition needed
        """
        pass

    @abstractmethod
    def can_transition_to(
        self,
        event: 'WorkflowEvent',
        state_data: Dict[str, Any]
    ) -> bool:
        """
        Check if transition is allowed based on current state data.

        This provides conditional logic for multi-branch transitions.

        Args:
            event: The event to check
            state_data: Current state JSON

        Returns:
            True if transition is allowed
        """
        pass

    @abstractmethod
    def get_required_api_type(self) -> Optional[APIResponseType]:
        """
        Get the API type required for this state.

        Each state knows which API it should call:
        - IDLE, STAGE_RUNNING, STEP_RUNNING → Planning API
        - BEHAVIOR_RUNNING → Generating API
        - *_COMPLETED → Reflecting API
        - Terminal states → None

        Returns:
            APIResponseType to call, or None if no API call needed
        """
        pass

    def initialize_from_response(
        self,
        state_data: Dict[str, Any],
        api_response: Any
    ) -> Dict[str, Any]:
        """
        Initialize or update state data from API response.

        This is called after a transition handler completes.
        Override this in subclasses if state-specific initialization is needed.

        Args:
            state_data: Current state JSON
            api_response: API response data

        Returns:
            Updated state JSON
        """
        # Default: no-op, just return state as-is
        return state_data

    def get_transition_handler(self, target_state: str):
        """
        Get the appropriate transition handler for moving to target state.

        Args:
            target_state: Target state name

        Returns:
            Transition handler instance, or None if not found
        """
        # Import here to avoid circular dependency
        from core.transition_handlers.transition_coordinator import get_transition_coordinator

        coordinator = get_transition_coordinator()
        return coordinator.get_handler(self.state_name, target_state)

    def execute_transition(
        self,
        event: 'WorkflowEvent',
        state_data: Dict[str, Any],
        api_response: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a transition from this state.

        This method:
        1. Validates the transition is allowed
        2. Gets the appropriate handler
        3. Applies the transition
        4. Initializes the new state

        Args:
            event: The transition event
            state_data: Current state JSON
            api_response: Optional API response

        Returns:
            Updated state JSON, or None if transition failed
        """
        # Check if transition is valid
        if not self.can_transition_to(event, state_data):
            self.warning(f"Transition {event} not allowed from {self.state_name}")
            return None

        # Get target state from transition table
        from ..state_transitions import STATE_TRANSITIONS
        from ..states import WorkflowState

        current_state_enum = WorkflowState(self.state_name.lower())
        target_state_enum = STATE_TRANSITIONS.get(current_state_enum, {}).get(event)

        if not target_state_enum:
            self.error(f"No target state for {event} from {self.state_name}")
            return None

        target_state = target_state_enum.value.upper()

        # Get and apply transition handler
        handler = self.get_transition_handler(target_state)
        if not handler:
            self.error(f"No handler found for {self.state_name} -> {target_state}")
            return None

        if api_response and not handler.can_handle(api_response):
            self.warning(f"Handler cannot process API response")
            return None

        # Apply transition
        self.info(f"Executing transition: {self.state_name} -> {target_state}")
        updated_state = handler.apply(state_data, api_response)

        # Initialize new state if needed
        # (This would be called on the NEW state instance, not this one)
        return updated_state

    def set_api_client(self, api_client):
        """
        Set the API client for this state.

        Args:
            api_client: WorkflowAPIClient instance
        """
        self._api_client = api_client
        self.info(f"API client injected for {self.state_name}")

    async def call_api(
        self,
        state_data: Dict[str, Any],
        transition_name: Optional[str] = None
    ) -> Any:
        """
        Call the appropriate API based on state requirements.

        This is the main entry point for API calls. Each state subclass
        should implement this method to call the appropriate API endpoint
        with the correct parameters.

        Args:
            state_data: Current state JSON
            transition_name: Optional transition name to pass to API

        Returns:
            API response (parsed JSON or async iterator for streaming)

        Raises:
            ValueError: If API client is not configured
            NotImplementedError: If state doesn't implement API calling
        """
        if not self._api_client:
            raise ValueError(f"API client not configured for {self.state_name}")

        api_type = self.get_required_api_type()
        if not api_type:
            self.info(f"State {self.state_name} does not require API call")
            return None

        # Extract stage_id and step_id from state
        observation = state_data.get('observation', {})
        location = observation.get('location', {})
        current = location.get('current', {})

        stage_id = current.get('stage_id', 'unknown')
        step_id = current.get('step_id', 'none')

        self.info(f"[{self.state_name}] Calling {api_type.value} API (stage={stage_id}, step={step_id})")

        # Route to appropriate API based on type
        if api_type == APIResponseType.PLANNING:
            return await self._call_planning_api(state_data, stage_id, step_id, transition_name)
        elif api_type == APIResponseType.GENERATING:
            return await self._call_generating_api(state_data, stage_id, step_id, transition_name)
        elif api_type == APIResponseType.COMPLETE:
            return await self._call_reflecting_api(state_data, stage_id, step_id, transition_name)
        else:
            raise ValueError(f"Unknown API type: {api_type}")

    async def _call_planning_api(
        self,
        state_data: Dict[str, Any],
        stage_id: str,
        step_id: str,
        transition_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call the Planning API.

        Args:
            state_data: Current state JSON
            stage_id: Current stage ID
            step_id: Current step ID
            transition_name: Transition name (e.g., 'START_WORKFLOW', 'START_STEP', 'START_BEHAVIOR')

        Returns:
            Planning API response
        """
        self.info(f"[{self.state_name}] Calling planning API with transition={transition_name}")

        response = await self._api_client.send_feedback(
            stage_id=stage_id,
            step_index=step_id,
            state=state_data,
            transition_name=transition_name
        )

        return response

    async def _call_generating_api(
        self,
        state_data: Dict[str, Any],
        stage_id: str,
        step_id: str,
        transition_name: Optional[str] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Call the Generating API.

        Args:
            state_data: Current state JSON
            stage_id: Current stage ID
            step_id: Current step ID
            transition_name: Transition name (typically 'COMPLETE_BEHAVIOR')

        Returns:
            Async iterator of actions
        """
        self.info(f"[{self.state_name}] Calling generating API with transition={transition_name}")

        # Return async iterator for streaming actions
        return self._api_client.fetch_behavior_actions(
            stage_id=stage_id,
            step_index=step_id,
            state=state_data,
            stream=False,
            transition_name=transition_name or 'COMPLETE_BEHAVIOR'
        )

    async def _call_reflecting_api(
        self,
        state_data: Dict[str, Any],
        stage_id: str,
        step_id: str,
        transition_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call the Reflecting API.

        Args:
            state_data: Current state JSON
            stage_id: Current stage ID
            step_id: Current step ID
            transition_name: Optional transition name (will be determined by API if None)

        Returns:
            Reflecting API response
        """
        self.info(f"[{self.state_name}] Calling reflecting API with transition={transition_name}")

        response = await self._api_client.send_reflecting(
            stage_id=stage_id,
            step_index=step_id,
            state=state_data,
            transition_name=transition_name
        )

        return response

    def __str__(self) -> str:
        return f"State({self.state_name})"

    def __repr__(self) -> str:
        return self.__str__()
