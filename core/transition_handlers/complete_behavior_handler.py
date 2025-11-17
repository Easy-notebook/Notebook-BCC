"""
COMPLETE_BEHAVIOR Event Handler
Handles action completion from generating API.
Event: COMPLETE_BEHAVIOR (internally uses COMPLETE_ACTION)
Transition: BEHAVIOR_RUNNING → BEHAVIOR_COMPLETED
"""

from typing import Dict, Any
from .base_transition_handler import BaseTransitionHandler


class CompleteBehaviorHandler(BaseTransitionHandler):
    """
    Handles COMPLETE_BEHAVIOR event.
    Transition: BEHAVIOR_RUNNING → BEHAVIOR_COMPLETED

    Triggered by: Generating API returning actions list

    Updates:
    - state.FSM.state to 'BEHAVIOR_COMPLETED'

    Note: Actions should already be executed and state updated from stores
    before calling this handler. This handler only performs the FSM transition.
    """

    def __init__(self):
        super().__init__(
            'BEHAVIOR_RUNNING',
            'BEHAVIOR_COMPLETED',
            'COMPLETE_BEHAVIOR'
        )

    def can_handle(self, api_response: Any) -> bool:
        """
        Check if response contains actions list from GENERATING API.

        This handler should ONLY match generating API responses,
        NOT reflecting API responses (which also contain actions).

        Reflecting API responses have control signals like:
        - complete_reflection
        - mark_step_complete
        - mark_stage_complete
        """
        if not isinstance(api_response, dict):
            return False

        # Check if response has actions
        actions = api_response.get('actions', [])
        if not isinstance(actions, list):
            return False

        # Distinguish from reflecting API: check for control signals
        # If any action is a control signal, this is from reflecting API
        for action in actions:
            if isinstance(action, dict):
                action_type = action.get('type', '')
                if action_type in ('complete_reflection', 'mark_step_complete', 'mark_stage_complete'):
                    # This is a reflecting API response, not generating API
                    return False

        # If we have actions but no control signals, it's from generating API
        return len(actions) > 0

    def apply(self, state: Dict[str, Any], api_response: Any) -> Dict[str, Any]:
        """
        Apply COMPLETE_BEHAVIOR transition.

        Args:
            state: Current state JSON (should already contain updated notebook/effects)
            api_response: Generating API response with actions

        Returns:
            Updated state JSON with FSM transitioned
        """
        new_state = self._deep_copy_state(state)

        actions = api_response.get('actions', [])
        action_count = api_response.get('count', len(actions))

        self.info(f"Applying actions transition: {action_count} actions received")

        # Execute all actions from the generating API
        if self.script_store:
            self._execute_actions(actions)
        else:
            self.warning("No script_store available, skipping action execution")

        # Sync notebook state after executing actions
        self._sync_notebook_to_state(new_state)

        # Update FSM state to BEHAVIOR_COMPLETED
        # This signals that all actions have been executed
        self._update_fsm_state(new_state, 'BEHAVIOR_COMPLETED', 'COMPLETE_ACTION')

        self.info("Transition complete: COMPLETE_BEHAVIOR")

        return new_state

    def _execute_actions(self, actions: list) -> None:
        """
        Execute all actions from the generating API.

        Args:
            actions: List of action dictionaries to execute
        """
        from models.action import ExecutionStep, ActionMetadata
        import uuid

        for i, action_dict in enumerate(actions):
            if not isinstance(action_dict, dict):
                self.warning(f"Action {i} is not a dict, skipping: {type(action_dict)}")
                continue

            action_type = action_dict.get('type', 'unknown')
            content = action_dict.get('content', '')

            self.info(f"Executing action {i+1}/{len(actions)}: {action_type}")

            try:
                # Create ExecutionStep from action dict
                step = ExecutionStep(
                    action=action_type,
                    content=content,
                    store_id=action_dict.get('store_id') or str(uuid.uuid4()),
                    metadata=action_dict.get('metadata') or ActionMetadata(),
                    # Pass through any other fields from action_dict
                    **{k: v for k, v in action_dict.items()
                       if k not in ['type', 'content', 'store_id', 'metadata']}
                )

                # Execute the action
                self.script_store.exec_action(step)
                self.info(f"Action {i+1} executed successfully: {action_type}")

            except Exception as e:
                self.error(f"Failed to execute action {i+1} ({action_type}): {e}", exc_info=True)
                # Continue with remaining actions even if one fails
