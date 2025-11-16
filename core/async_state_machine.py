"""
Async State Machine Adapter

Provides event-driven async execution capabilities for the workflow state machine.

Responsibilities:
- Wraps WorkflowStateMachine to provide async interface
- Delegates API calls to state_classes
- Delegates transition execution to transition_handlers
- Contains no business logic, only coordination
"""

from typing import Dict, Any, Optional
from silantui import ModernLogger
from .state_machine import WorkflowStateMachine
from .events import WorkflowEvent
from .states import WorkflowState


class AsyncStateMachineAdapter(ModernLogger):
    """
    Async State Machine Adapter

    New architecture responsibility separation:
    - StateFactory & BaseState: Handle API calls (planning/generating/reflecting)
    - TransitionCoordinator & Handlers: Handle transition execution and state updates
    - AsyncStateMachineAdapter: Coordinate above components, provide async interface

    No longer contains:
    - API call logic (moved to BaseState)
    - Transition logic (moved to TransitionHandlers)
    - Action execution logic (moved to TransitionHandlers)
    """

    def __init__(
        self,
        state_machine: WorkflowStateMachine,
        api_client=None,
        script_store=None
    ):
        """
        Initialize async adapter

        Args:
            state_machine: Wrapped state machine instance
            api_client: WorkflowAPIClient instance for API operations
            script_store: ScriptStore instance for action execution
        """
        super().__init__("AsyncStateMachine")
        self.state_machine = state_machine
        self.api_client = api_client
        self.script_store = script_store

        # Track last executed transition name
        self._last_transition_name: Optional[str] = None

        # Inject API client into StateFactory for all states
        if api_client:
            from .state_classes.state_factory import StateFactory
            StateFactory.set_api_client(api_client)
            self.info("API client injected into StateFactory")

        # Inject script_store and api_client into TransitionCoordinator
        if script_store or api_client:
            from core.transition_handlers import get_transition_coordinator
            coordinator = get_transition_coordinator()
            if script_store:
                coordinator.set_script_store(script_store)
                self.info("Script store injected into TransitionCoordinator")
            if api_client:
                coordinator.set_api_client(api_client)
                self.info("API client injected into TransitionCoordinator")

    def set_api_client(self, api_client):
        """
        Set or update the API client

        This method can be called after initialization to inject or update
        the API client. It will propagate the client to StateFactory and
        TransitionCoordinator.

        Args:
            api_client: WorkflowAPIClient instance
        """
        self.api_client = api_client

        # Inject into StateFactory for all states
        from .state_classes.state_factory import StateFactory
        StateFactory.set_api_client(api_client)
        self.info("API client injected into StateFactory")

        # Inject into TransitionCoordinator
        from core.transition_handlers import get_transition_coordinator
        coordinator = get_transition_coordinator()
        coordinator.set_api_client(api_client)
        self.info("API client injected into TransitionCoordinator")

    async def step(self, state_json: Dict[str, Any]) -> tuple[Dict[str, Any], Optional[str]]:
        """
        Execute one state transition step

        New architecture flow:
        1. Get current FSM state from state_json
        2. Obtain corresponding State instance via StateFactory
        3. State instance calls required API (planning/generating/reflecting)
        4. API response is passed to TransitionCoordinator for processing
        5. TransitionCoordinator selects appropriate Handler and applies transition
        6. Return updated state

        Args:
            state_json: Current state JSON containing workflow state

        Returns:
            Tuple of (updated state JSON, transition name)
            Returns (original state, None) if no transition occurred or error
        """
        # Reset transition name tracking
        self._last_transition_name = None

        # Extract current FSM state from state JSON
        fsm_state_str = state_json.get('state', {}).get('FSM', {}).get('state', 'UNKNOWN')

        # Normalize state name (handle COMPLETE vs COMPLETED variants)
        normalized_state = fsm_state_str.upper()
        if normalized_state.endswith('_COMPLETE') and not normalized_state.endswith('_COMPLETED'):
            normalized_state = normalized_state + 'D'

        try:
            # First attempt direct match (lowercase)
            current_state = WorkflowState(normalized_state.lower())
        except ValueError:
            # If failed, try using WORKFLOW_STATES dict (uppercase)
            from .states import WORKFLOW_STATES
            if normalized_state in WORKFLOW_STATES:
                current_state = WORKFLOW_STATES[normalized_state]
            else:
                self.error(f"Unknown FSM state: {fsm_state_str} (normalized: {normalized_state})")
                return state_json, None

        # Obtain State instance from factory
        from .state_classes.state_factory import StateFactory
        state_instance = StateFactory.get_state(normalized_state)

        if not state_instance:
            self.warning(f"[AsyncFSM] Failed to get state instance for: {current_state}")
            return state_json, None

        # Check if state requires API call
        api_type_enum = state_instance.get_required_api_type()

        if not api_type_enum or api_type_enum.value == 'finish':
            # State does not require API call (e.g., terminal states)
            self.info(f"[AsyncFSM] State {current_state.value} does not require API call")
            return state_json, None

        try:
            self.info(f"[AsyncFSM] Calling {api_type_enum.value} API for state: {current_state.value}")

            # Predict transition name for correct log file naming
            predicted_transition_name = self._predict_transition_name(normalized_state, api_type_enum.value)

            # Call State's API method, passing predicted transition name
            api_response = await state_instance.call_api(state_json, transition_name=predicted_transition_name)

            # Pass API response to TransitionCoordinator for processing
            from core.transition_handlers import get_transition_coordinator
            coordinator = get_transition_coordinator()

            # For generating/reflecting APIs, collect async iterator first
            if api_type_enum.value in ['generating', 'reflecting']:
                # Collect all actions from async iterator
                actions = []
                async for action in api_response:
                    actions.append(action)

                # Wrap actions in response format expected by handlers
                api_response = {'actions': actions, 'count': len(actions)}

            # Apply transition (TransitionCoordinator selects appropriate handler)
            # Parse API response (handle both dict, JSON string, and XML string)
            if isinstance(api_response, dict):
                parsed_response = api_response
            else:
                # Try to parse as XML first, fallback to JSON
                from utils.xml_parser import planning_xml_parser
                try:
                    parsed_response = planning_xml_parser.parse(api_response)
                except Exception:
                    # If XML parsing fails, try JSON
                    import json
                    parsed_response = json.loads(api_response)

            updated_state, transition_name = coordinator.apply_transition(
                state=state_json,
                api_response=parsed_response,
                api_type=api_type_enum.value
            )

            self._last_transition_name = transition_name
            self.info(f"[AsyncFSM] Transition applied: {transition_name}")

            return updated_state, transition_name

        except Exception as e:
            self.error(f"[AsyncFSM] API call error for {current_state}: {e}", exc_info=True)
            # Trigger FAIL event to transition state machine to error state
            # self.state_machine.transition(WorkflowEvent.FAIL, {'error': str(e)})
            return state_json, None

    def _predict_transition_name(self, state_name: str, api_type: str) -> str:
        """
        Predict transition handler name based on current state and API type

        This prediction is used for log file naming, allowing log files to use
        the correct transition name from creation time, rather than using API type
        (e.g., "generating") and then renaming to transition name (e.g., "COMPLETE_BEHAVIOR").

        The prediction is based on the deterministic relationship between FSM states
        and the transitions they trigger when calling specific API types.

        Args:
            state_name: Current FSM state name (e.g., "BEHAVIOR_RUNNING")
            api_type: API type being called ("planning", "generating", "reflecting")

        Returns:
            Predicted transition handler name (e.g., "COMPLETE_BEHAVIOR")
            Falls back to api_type if prediction not available

        Note:
            For reflecting API, we predict the most common case. The actual transition
            may differ (e.g., NEXT_BEHAVIOR vs COMPLETE_STEP), but the prediction is
            good enough for log file naming purposes.
        """
        # Mapping table: (current_state, api_type) -> transition_handler_name
        # This table encodes the deterministic state machine behavior
        state_api_to_transition = {
            # IDLE state calls planning API -> START_WORKFLOW transition
            ('IDLE', 'planning'): 'START_WORKFLOW',

            # STAGE_RUNNING state calls planning API -> START_STEP transition
            ('STAGE_RUNNING', 'planning'): 'START_STEP',

            # STEP_RUNNING state calls planning API -> START_BEHAVIOR transition
            ('STEP_RUNNING', 'planning'): 'START_BEHAVIOR',

            # BEHAVIOR_RUNNING state calls generating API -> COMPLETE_BEHAVIOR transition
            ('BEHAVIOR_RUNNING', 'generating'): 'COMPLETE_BEHAVIOR',

            # BEHAVIOR_COMPLETED state calls reflecting API -> NEXT_BEHAVIOR or COMPLETE_STEP
            # Predict most common case (COMPLETE_STEP)
            ('BEHAVIOR_COMPLETED', 'reflecting'): 'COMPLETE_STEP',

            # STEP_COMPLETED state calls reflecting API -> NEXT_STEP or COMPLETE_STAGE
            # Predict most common case (COMPLETE_STAGE)
            ('STEP_COMPLETED', 'reflecting'): 'COMPLETE_STAGE',

            # STAGE_COMPLETED state calls reflecting API -> NEXT_STAGE or COMPLETE_WORKFLOW
            # Predict most common case (COMPLETE_WORKFLOW)
            ('STAGE_COMPLETED', 'reflecting'): 'COMPLETE_WORKFLOW',
        }

        predicted_name = state_api_to_transition.get((state_name, api_type))

        if predicted_name:
            self.debug(f"[AsyncFSM] Predicted transition: {state_name} + {api_type} API -> {predicted_name}")
            return predicted_name
        else:
            # [INCORRECT NAMING]: Fallback to API type when prediction unavailable
            # This leads to inaccurate log file names like "planning.log", "generating.log"
            # instead of proper transition names like "START_WORKFLOW.log", "COMPLETE_BEHAVIOR.log"
            self.warning(f"[AsyncFSM] Cannot predict transition for ({state_name}, {api_type}), using API type as fallback")
            return api_type

    def register_effect(self, state: WorkflowState, effect):
        """
        [DEPRECATED] Register custom state effect

        The new architecture no longer uses the effect pattern. All logic is now
        implemented in State classes and TransitionHandlers for better modularity
        and testability.

        This method is retained for backward compatibility but has no effect.

        Args:
            state: State enum value
            effect: Effect function (ignored)

        Note:
            To add custom logic, implement it in the appropriate State class
            or TransitionHandler instead.
        """
        self.warning(f"[AsyncFSM] register_effect() is deprecated in new architecture. "
                    f"Please implement logic in State class or TransitionHandler instead.")
