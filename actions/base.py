"""
Action Base Class - Foundation for all action handlers
Provides decorator-based registration and standard execution interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Type, Dict
from models.action import ExecutionStep


class ActionBase(ABC):
    """
    Base class for all action handlers.

    Each action class:
    - Defines its action_type as a class attribute
    - Implements the execute() method
    - Gets automatically registered via the @action decorator

    Usage:
        @action('add')
        class AddAction(ActionBase):
            def execute(self, step: ExecutionStep) -> Any:
                # Implementation here
                pass
    """

    # Class attribute - must be set by subclasses or decorator
    action_type: str = None

    def __init__(self, script_store):
        """
        Initialize action with reference to script_store.

        Args:
            script_store: The ScriptStore instance that manages actions
        """
        self.script_store = script_store
        self.notebook_store = script_store.notebook_store
        self.ai_context_store = script_store.ai_context_store
        self.code_executor = script_store.code_executor

    @abstractmethod
    def execute(self, step: ExecutionStep) -> Any:
        """
        Execute the action.

        Args:
            step: The execution step containing action parameters

        Returns:
            Result of the action execution (type depends on action)
        """
        raise NotImplementedError(f"Action {self.__class__.__name__} must implement execute()")

    def __call__(self, step: ExecutionStep) -> Any:
        """Allow action to be called directly."""
        return self.execute(step)


# Registry of all action classes
_action_registry: Dict[str, Type[ActionBase]] = {}


def action(action_type: str):
    """
    Decorator to register an action class.

    Args:
        action_type: The action type identifier (e.g., 'add', 'exec')

    Returns:
        Decorator function

    Usage:
        @action('add')
        class AddAction(ActionBase):
            def execute(self, step: ExecutionStep) -> Any:
                pass
    """
    def decorator(cls: Type[ActionBase]) -> Type[ActionBase]:
        if not issubclass(cls, ActionBase):
            raise TypeError(f"{cls.__name__} must inherit from ActionBase")

        # Set the action_type on the class
        cls.action_type = action_type

        # Register the class
        _action_registry[action_type] = cls

        return cls

    return decorator


def get_action_class(action_type: str) -> Optional[Type[ActionBase]]:
    """
    Get the action class for a given action type.

    Args:
        action_type: The action type identifier

    Returns:
        The action class, or None if not found
    """
    return _action_registry.get(action_type)


def get_all_action_types() -> list[str]:
    """
    Get all registered action types.

    Returns:
        List of action type identifiers
    """
    return list(_action_registry.keys())


def clear_registry():
    """Clear all registered actions (useful for testing)."""
    _action_registry.clear()
