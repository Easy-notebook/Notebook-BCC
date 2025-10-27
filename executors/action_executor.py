"""
Action Executor
High-level executor that coordinates action execution.
"""

from silantui import ModernLogger
from typing import Any
from models.action import ExecutionStep



class ActionExecutor(ModernLogger):
    """
    High-level action executor.
    Coordinates execution of actions through the script store.
    """

    def __init__(self, script_store=None):
        """
        Initialize the executor.

        Args:
            script_store: Reference to script store
        """
        super().__init__("ActionExecutor")
        self.script_store = script_store

    def execute(self, action: ExecutionStep) -> Any:
        """
        Execute an action.

        Args:
            action: The action to execute

        Returns:
            Execution result
        """
        if not self.script_store:
            self.error("[ActionExecutor] No script store available")
            return None

        self.info(f"[ActionExecutor] Executing action: {action.action}")

        try:
            result = self.script_store.exec_action(action)
            self.info(f"[ActionExecutor] Action executed successfully")
            return result
        except Exception as e:
            self.error(f"[ActionExecutor] Error executing action: {e}", exc_info=True)
            raise
