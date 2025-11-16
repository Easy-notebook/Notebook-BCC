"""
Base Transition Handler
Provides common functionality for all FSM transition handlers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from copy import deepcopy
from silantui import ModernLogger
from utils.transition_logger import get_transition_logger


class BaseTransitionHandler(ABC, ModernLogger):
    """
    Base class for all FSM transition handlers.

    Each handler is responsible for:
    1. Parsing API response
    2. Updating state JSON based on the response
    3. Performing the FSM state transition
    4. Returning the updated state
    """

    def __init__(self, from_state: str, to_state: str, handler_name: str = None):
        """
        Initialize the transition handler.

        Args:
            from_state: Source FSM state
            to_state: Target FSM state
            handler_name: Name for logging (defaults to class name)
        """
        name = handler_name or self.__class__.__name__
        ModernLogger.__init__(self, name)
        self.from_state = from_state
        self.to_state = to_state
        self.transition_name = handler_name  # Store transition name for external access
        self.script_store = None  # Will be injected by coordinator
        self.api_client = None  # Will be injected by coordinator (for logging)

    @abstractmethod
    def can_handle(self, api_response: Any) -> bool:
        """
        Check if this handler can handle the given API response.

        Args:
            api_response: Parsed API response

        Returns:
            True if this handler can process this response
        """
        pass

    @abstractmethod
    def apply(self, state: Dict[str, Any], api_response: Any) -> Dict[str, Any]:
        """
        Apply the transition to the state.

        Args:
            state: Current state JSON (will be deep copied)
            api_response: Parsed API response

        Returns:
            Updated state JSON with transition applied
        """
        pass

    def apply_and_log(
        self,
        state: Dict[str, Any],
        api_response: Any,
        api_type: str = None,
        api_request: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Apply the transition and log it.

        Args:
            state: Current state JSON
            api_response: Parsed API response
            api_type: API type (planning, generating, reflecting)
            api_request: API request payload

        Returns:
            Updated state JSON with transition applied
        """
        # Get state before transition
        from_state = state.get('state', {}).get('FSM', {}).get('state', 'UNKNOWN')

        # Apply the transition
        updated_state = self.apply(state, api_response)

        # Get state after transition
        to_state = updated_state.get('state', {}).get('FSM', {}).get('state', 'UNKNOWN')

        # Log the transition
        try:
            logger = get_transition_logger()
            log_file = logger.log_transition(
                transition_name=self.transition_name,
                from_state=from_state,
                to_state=to_state,
                api_type=api_type,
                api_request=api_request,
                api_response=api_response,
                state_before=state.get('state', {}),
                state_after=updated_state.get('state', {})
            )
            if log_file:
                self.debug(f"[{self.transition_name}] Transition logged: {log_file}")
        except Exception as e:
            self.warning(f"[{self.transition_name}] Failed to log transition: {e}")

        return updated_state

    def _deep_copy_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create a deep copy of the state."""
        return deepcopy(state)

    def _normalize_state_name(self, state_name: str) -> str:
        """
        Normalize state name from server format to local FSM format.

        Examples:
            STATE_Behavior_Running → BEHAVIOR_RUNNING
            behavior_running → BEHAVIOR_RUNNING
        """
        if not state_name:
            return state_name

        # Remove STATE_ prefix if present
        if state_name.startswith('STATE_'):
            state_name = state_name[6:]

        # Convert to uppercase
        state_name = state_name.upper().replace(' ', '_')

        return state_name

    def _get_observation(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Get observation structure from state."""
        return state.get('observation', {})

    def _get_location(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Get location structure from state."""
        return self._get_observation(state).get('location', {})

    def _get_progress(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Get progress structure from state."""
        return self._get_location(state).get('progress', {})

    def _get_state_data(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Get state data structure."""
        return state.get('state', {})

    def _get_fsm(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Get FSM structure from state."""
        return self._get_state_data(state).get('FSM', {})

    def _update_fsm_state(
        self,
        state: Dict[str, Any],
        new_state: str,
        transition_name: str
    ) -> None:
        """
        Update FSM state and transition.

        Args:
            state: State dict (modified in place)
            new_state: New FSM state
            transition_name: Name of the transition
        """
        fsm = self._get_fsm(state)
        old_state = fsm.get('state', 'UNKNOWN')
        fsm['previous_state'] = old_state
        fsm['state'] = new_state
        fsm['last_transition'] = transition_name
        self.info(f"FSM transition: {old_state} → {new_state}")

    def _update_location_current(
        self,
        state: Dict[str, Any],
        stage_id: str = None,
        step_id: str = None,
        behavior_id: str = None,
        behavior_iteration: int = None
    ) -> None:
        """
        Update location.current fields.

        Args:
            state: State dict (modified in place)
            stage_id: Stage ID (None = no change)
            step_id: Step ID (None = no change, use 'clear' to set to None)
            behavior_id: Behavior ID (None = no change, use 'clear' to set to None)
            behavior_iteration: Behavior iteration number
        """
        location = self._get_location(state)
        current = location.setdefault('current', {})

        if stage_id is not None:
            current['stage_id'] = stage_id

        if step_id is not None:
            current['step_id'] = None if step_id == 'clear' else step_id

        if behavior_id is not None:
            current['behavior_id'] = None if behavior_id == 'clear' else behavior_id

        if behavior_iteration is not None:
            current['behavior_iteration'] = behavior_iteration

    def _init_outputs_tracking(
        self,
        expected_artifacts: Dict[str, str]
    ) -> Dict[str, list]:
        """
        Initialize outputs tracking structure.

        Args:
            expected_artifacts: Dict of {name: description}

        Returns:
            Outputs tracking dict with expected/produced/in_progress
        """
        expected_list = [
            {'name': name, 'description': desc}
            for name, desc in expected_artifacts.items()
        ]

        return {
            'expected': expected_list,
            'produced': [],
            'in_progress': []
        }

    def _execute_action(self, action_type: str, content: str = '', **kwargs) -> None:
        """
        Execute a notebook action if script_store is available.

        Args:
            action_type: Type of action to execute (e.g., 'update_title', 'new_section', 'new_step')
            content: Content for the action
            **kwargs: Additional action parameters
        """
        if not self.script_store:
            self.debug(f"[Action] Skipping {action_type}: no script_store available")
            return

        try:
            # Import here to avoid circular dependency
            from models.action import ExecutionStep, ActionMetadata
            import uuid

            # Create execution step
            step = ExecutionStep(
                action=action_type,
                content=content,
                store_id=kwargs.get('store_id') or str(uuid.uuid4()),
                metadata=kwargs.get('metadata') or ActionMetadata(),
                **{k: v for k, v in kwargs.items() if k not in ['store_id', 'metadata']}
            )

            # Execute action
            self.script_store.exec_action(step)
            self.info(f"[Action] Executed {action_type}: {content[:50] if content else '(no content)'}")

        except Exception as e:
            self.error(f"[Action] Failed to execute {action_type}: {e}", exc_info=True)

    def _sync_notebook_to_state(self, state: Dict[str, Any]) -> None:
        """
        Sync notebook data from script_store to state.

        Call this after executing notebook actions to ensure the returned
        state contains the latest notebook data.

        Args:
            state: State dictionary to update (modified in-place)
        """
        if not self.script_store:
            return

        if not hasattr(self.script_store, 'notebook_store'):
            return

        # Get latest notebook data from store
        notebook_data = self.script_store.notebook_store.to_dict()

        # Update state
        if 'state' not in state:
            state['state'] = {}

        state['state']['notebook'] = notebook_data

        self.debug(f"[Sync] Updated notebook in state (cells: {len(notebook_data.get('cells', []))})")
