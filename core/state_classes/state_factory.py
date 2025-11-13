"""
State Factory
Creates and manages state instances for the workflow state machine.
"""

from typing import Dict, Optional
from .base_state import BaseState
from .idle_state import IdleState
from .stage_running_state import StageRunningState
from .stage_completed_state import StageCompletedState
from .step_running_state import StepRunningState
from .behavior_running_state import BehaviorRunningState
from .behavior_completed_state import BehaviorCompletedState
from .step_completed_state import StepCompletedState


class StateFactory:
    """
    Factory for creating and managing state instances.

    Implements singleton pattern for state instances to avoid recreation.
    """

    # State class registry
    _STATE_CLASSES = {
        'IDLE': IdleState,
        'STAGE_RUNNING': StageRunningState,
        'STAGE_COMPLETED': StageCompletedState,
        'STEP_RUNNING': StepRunningState,
        'STEP_COMPLETED': StepCompletedState,
        'BEHAVIOR_RUNNING': BehaviorRunningState,
        'BEHAVIOR_COMPLETED': BehaviorCompletedState,
        # Add more states as needed
        # 'ACTION_RUNNING': ActionRunningState,
        # 'ACTION_COMPLETED': ActionCompletedState,
        # etc.
    }

    # Singleton instances cache
    _instances: Dict[str, BaseState] = {}

    # Global API client (injected once, shared by all states)
    _api_client = None

    @classmethod
    def get_state(cls, state_name: str) -> Optional[BaseState]:
        """
        Get or create a state instance.

        Args:
            state_name: The state name (e.g., 'IDLE', 'STAGE_RUNNING')

        Returns:
            State instance, or None if state not found
        """
        # Normalize state name
        state_name = cls._normalize_state_name(state_name)

        # Return cached instance if exists
        if state_name in cls._instances:
            return cls._instances[state_name]

        # Create new instance
        state_class = cls._STATE_CLASSES.get(state_name)
        if not state_class:
            return None

        instance = state_class()

        # Inject API client if available
        if cls._api_client:
            instance.set_api_client(cls._api_client)

        cls._instances[state_name] = instance
        return instance

    @classmethod
    def get_state_from_enum(cls, state_enum) -> Optional[BaseState]:
        """
        Get state instance from WorkflowState enum.

        Args:
            state_enum: WorkflowState enum value

        Returns:
            State instance
        """
        state_name = state_enum.value.upper()
        return cls.get_state(state_name)

    @classmethod
    def clear_cache(cls):
        """Clear the instances cache."""
        cls._instances.clear()

    @classmethod
    def _normalize_state_name(cls, state_name: str) -> str:
        """
        Normalize state name to uppercase format.

        Examples:
            'idle' -> 'IDLE'
            'stage_running' -> 'STAGE_RUNNING'
            'STATE_Behavior_Running' -> 'BEHAVIOR_RUNNING'
        """
        if not state_name:
            return state_name

        # Remove STATE_ prefix if present
        if state_name.startswith('STATE_'):
            state_name = state_name[6:]

        # Convert to uppercase and normalize separators
        state_name = state_name.upper().replace(' ', '_')

        return state_name

    @classmethod
    def get_all_states(cls) -> Dict[str, BaseState]:
        """
        Get all available state instances.

        Returns:
            Dict of state_name -> state_instance
        """
        return {
            name: cls.get_state(name)
            for name in cls._STATE_CLASSES.keys()
        }

    @classmethod
    def is_state_supported(cls, state_name: str) -> bool:
        """
        Check if a state is supported.

        Args:
            state_name: The state name to check

        Returns:
            True if state is supported
        """
        state_name = cls._normalize_state_name(state_name)
        return state_name in cls._STATE_CLASSES

    @classmethod
    def set_api_client(cls, api_client):
        """
        Set the global API client for all states.

        This should be called once during initialization to inject
        the API client into all state instances.

        Args:
            api_client: WorkflowAPIClient instance
        """
        cls._api_client = api_client

        # Inject into existing instances
        for instance in cls._instances.values():
            instance.set_api_client(api_client)
