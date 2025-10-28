"""
Action Registry - Handler Registration and Hook Management
Provides decorator-based action handler registration for maximum extensibility.
"""

from typing import Dict, List, Any, Callable, Protocol, Optional
from models.action import ExecutionStep


# =====================================================================
# Action Handler Protocol
# =====================================================================

class ActionHandler(Protocol):
    """Protocol for action handlers."""

    def __call__(self, step: ExecutionStep) -> Any:
        """Execute an action step."""
        ...


# =====================================================================
# Action Registry with Decorator Support
# =====================================================================

class ActionRegistry:
    """
    Registry for action handlers with decorator-based registration.
    Provides extensibility without modifying core code.
    """

    def __init__(self):
        self._handlers: Dict[str, ActionHandler] = {}
        self._pre_hooks: List[Callable] = []
        self._post_hooks: List[Callable] = []

    def register(self, action_type: str) -> Callable[[Callable], Callable]:
        """
        Decorator to register an action handler.

        Args:
            action_type: Type identifier for the action

        Returns:
            Decorator function

        Usage:
            @registry.register('custom_action')
            def handle_custom(self, step: ExecutionStep) -> Any:
                # Implementation
                pass
        """
        if not action_type:
            raise ValueError("Action type cannot be empty")

        def decorator(func: Callable) -> Callable:
            if not callable(func):
                raise ValueError(f"Handler for {action_type} must be callable")
            self._handlers[action_type] = func
            return func
        return decorator

    def register_handler(self, action_type: str, handler: ActionHandler) -> None:
        """
        Programmatically register a handler.

        Args:
            action_type: Type identifier for the action
            handler: Handler function implementing ActionHandler protocol

        Raises:
            ValueError: If action_type is empty or handler is not callable
        """
        if not action_type:
            raise ValueError("Action type cannot be empty")
        if not callable(handler):
            raise ValueError(f"Handler for {action_type} must be callable")
        self._handlers[action_type] = handler

    def get_handler(self, action_type: str) -> Optional[ActionHandler]:
        """
        Get handler for an action type.

        Args:
            action_type: Type identifier for the action

        Returns:
            Handler function or None if not found
        """
        return self._handlers.get(action_type)

    def add_pre_hook(self, hook: Callable) -> None:
        """
        Add a pre-execution hook.

        Args:
            hook: Callable that takes ExecutionStep as argument

        Raises:
            ValueError: If hook is not callable
        """
        if not callable(hook):
            raise ValueError("Hook must be callable")
        self._pre_hooks.append(hook)

    def add_post_hook(self, hook: Callable) -> None:
        """
        Add a post-execution hook.

        Args:
            hook: Callable that takes ExecutionStep and result as arguments

        Raises:
            ValueError: If hook is not callable
        """
        if not callable(hook):
            raise ValueError("Hook must be callable")
        self._post_hooks.append(hook)

    def execute_pre_hooks(self, step: ExecutionStep) -> None:
        """
        Execute all pre-execution hooks.

        Args:
            step: The execution step being processed
        """
        for i, hook in enumerate(self._pre_hooks):
            try:
                hook(step)
            except Exception as e:
                # Log but don't fail - hooks should not break execution
                print(f"[ActionRegistry] Warning: Pre-hook {i} failed: {e}")

    def execute_post_hooks(self, step: ExecutionStep, result: Any) -> None:
        """
        Execute all post-execution hooks.

        Args:
            step: The execution step that was processed
            result: The result from the handler execution
        """
        for i, hook in enumerate(self._post_hooks):
            try:
                hook(step, result)
            except Exception as e:
                # Log but don't fail - hooks should not break execution
                print(f"[ActionRegistry] Warning: Post-hook {i} failed: {e}")

    @property
    def registered_actions(self) -> List[str]:
        """Get list of registered action types."""
        return list(self._handlers.keys())

    def clear(self) -> None:
        """Clear all registered handlers and hooks."""
        self._handlers.clear()
        self._pre_hooks.clear()
        self._post_hooks.clear()

    def has_handler(self, action_type: str) -> bool:
        """Check if a handler is registered for an action type."""
        return action_type in self._handlers

    def unregister(self, action_type: str) -> bool:
        """
        Unregister a handler.

        Args:
            action_type: Type identifier for the action

        Returns:
            True if handler was removed, False if not found
        """
        if action_type in self._handlers:
            del self._handlers[action_type]
            return True
        return False

    def __len__(self) -> int:
        """Get number of registered handlers."""
        return len(self._handlers)

    def __contains__(self, action_type: str) -> bool:
        """Check if action type is registered."""
        return action_type in self._handlers

    def __repr__(self) -> str:
        """String representation."""
        return f"ActionRegistry(handlers={len(self._handlers)}, pre_hooks={len(self._pre_hooks)}, post_hooks={len(self._post_hooks)})"
