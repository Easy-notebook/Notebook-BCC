"""
Behavior Effects - Behavior-level state effect handlers
Handles: behavior_running, behavior_completed
"""

from typing import Any
from utils.state_builder import build_api_state, build_behavior_feedback


def effect_behavior_running(state_machine, payload: Any = None):
    """
    Effect for BEHAVIOR_RUNNING state.

    Args:
        state_machine: Reference to WorkflowStateMachine instance
        payload: Optional payload data
    """
    state_machine.info(f"[FSM Effect] BEHAVIOR_RUNNING")

    ctx = state_machine.execution_context.workflow_context

    if not ctx.current_stage_id or not ctx.current_step_id:
        state_machine.error("[FSM Effect] Missing stage/step ID")
        from core.events import WorkflowEvent
        state_machine.transition(WorkflowEvent.FAIL, {'error': 'Missing stage/step ID'})
        return

    # Get current context from AI store
    if not state_machine.ai_context_store:
        state_machine.error("[FSM Effect] AI context store not available")
        from core.events import WorkflowEvent
        state_machine.transition(WorkflowEvent.FAIL, {'error': 'AI context store not available'})
        return

    try:
        # Generate behavior_id and increment iteration
        if not ctx.current_behavior_id:
            ctx.behavior_iteration += 1
            ctx.current_behavior_id = f"behavior_{ctx.behavior_iteration:03d}"
            state_machine.info(f"[FSM Effect] Starting behavior: {ctx.current_behavior_id} (iteration {ctx.behavior_iteration})")

        # Fetch actions from API
        from utils.api_client import workflow_api_client

        state_machine.info(f"[FSM Effect] Fetching actions for stage={ctx.current_stage_id}, step={ctx.current_step_id}")

        # Build API state (progress_info is required for behavior generation)
        current_state = build_api_state(state_machine, require_progress_info=True)

        # Fetch actions (synchronous wrapper)
        actions = workflow_api_client.fetch_behavior_actions_sync(
            stage_id=ctx.current_stage_id,
            step_index=ctx.current_step_id,
            state=current_state,
            stream=True
        )

        state_machine.info(f"[FSM Effect] Fetched {len(actions)} actions")

        # Store actions in context
        state_machine.execution_context.workflow_context.current_behavior_actions = actions
        state_machine.execution_context.workflow_context.current_action_index = 0

        from core.events import WorkflowEvent
        if actions:
            state_machine.transition(WorkflowEvent.START_ACTION)
        else:
            # No actions, complete behavior immediately
            state_machine.transition(WorkflowEvent.COMPLETE_BEHAVIOR)

    except Exception as e:
        state_machine.error(f"[FSM Effect] Failed to fetch actions: {e}", exc_info=True)
        from core.events import WorkflowEvent
        state_machine.transition(WorkflowEvent.FAIL, {'error': f'Failed to fetch actions: {str(e)}'})


def effect_behavior_completed(state_machine, payload: Any = None):
    """
    Effect for BEHAVIOR_COMPLETED state.

    Args:
        state_machine: Reference to WorkflowStateMachine instance
        payload: Optional payload data
    """
    state_machine.info(f"[FSM Effect] BEHAVIOR_COMPLETED")

    ctx = state_machine.execution_context.workflow_context

    if not ctx.current_stage_id or not ctx.current_step_id:
        state_machine.error("[FSM Effect] Missing stage/step ID")
        from core.events import WorkflowEvent
        state_machine.transition(WorkflowEvent.FAIL, {'error': 'Missing stage/step ID'})
        return

    if not state_machine.ai_context_store:
        state_machine.error("[FSM Effect] AI context store not available")
        from core.events import WorkflowEvent
        state_machine.transition(WorkflowEvent.FAIL, {'error': 'AI context store not available'})
        return

    try:
        # Send feedback to get next instruction
        from utils.api_client import workflow_api_client

        state_machine.info(f"[FSM Effect] Sending feedback for stage={ctx.current_stage_id}, step={ctx.current_step_id}")

        # Build API state (progress_info is required for feedback)
        current_state = build_api_state(state_machine, require_progress_info=True)

        # Build behavior feedback
        behavior_feedback = build_behavior_feedback(state_machine)

        # Send feedback (synchronous wrapper) with behavior feedback
        feedback_response = workflow_api_client.send_feedback_sync(
            stage_id=ctx.current_stage_id,
            step_index=ctx.current_step_id,
            state=current_state,
            behavior_feedback=behavior_feedback
        )

        state_machine.info(f"[FSM Effect] Feedback response: {feedback_response}")

        # Apply context updates from server
        if 'context_update' in feedback_response:
            _apply_context_update(state_machine, feedback_response['context_update'])

        # Check server directives for behavior control
        transition = feedback_response.get('transition', {})
        continue_behaviors = transition.get('continue_behaviors', False)
        target_achieved = transition.get('target_achieved', feedback_response.get('targetAchieved', False))

        # Mark current behavior as completed before transitioning
        if ctx.current_behavior_id and ctx.current_behavior_id not in ctx.completed_behaviors:
            ctx.completed_behaviors.append(ctx.current_behavior_id)
            state_machine.info(f"[FSM Effect] Marked behavior as completed: {ctx.current_behavior_id}")

        from core.events import WorkflowEvent
        # Server controls behavior loop, client controls stage/step navigation
        if continue_behaviors:
            state_machine.info("[FSM Effect] Server requests more behaviors, clearing behavior state and starting next")
            # Clear behavior state for next iteration
            ctx.current_behavior_id = None
            ctx.current_behavior_actions = []
            ctx.current_action_index = 0
            state_machine.transition(WorkflowEvent.NEXT_BEHAVIOR)

        elif target_achieved:
            state_machine.info("[FSM Effect] Target achieved, completing step")
            state_machine.transition(WorkflowEvent.COMPLETE_STEP)

        else:
            # Fallback: if neither flag is set, default to continuing behaviors
            state_machine.info("[FSM Effect] No clear directive, defaulting to next behavior")
            ctx.current_behavior_id = None
            ctx.current_behavior_actions = []
            ctx.current_action_index = 0
            state_machine.transition(WorkflowEvent.NEXT_BEHAVIOR)

    except Exception as e:
        state_machine.error(f"[FSM Effect] Failed to send feedback: {e}", exc_info=True)
        # On error, default to completing step to avoid infinite loop
        state_machine.warning("[FSM Effect] Defaulting to COMPLETE_STEP due to error")
        from core.events import WorkflowEvent
        state_machine.transition(WorkflowEvent.COMPLETE_STEP)


# Helper function
def _apply_context_update(state_machine, context_update):
    """
    Apply context updates from the server response.

    Args:
        context_update: Dictionary containing context updates
    """
    if not state_machine.ai_context_store:
        state_machine.warning("[FSM] Cannot apply context update: AI context store not available")
        return

    state_machine.info(f"[FSM] Applying context update: {list(context_update.keys())}")

    # Update variables
    if 'variables' in context_update:
        for key, value in context_update['variables'].items():
            state_machine.ai_context_store.add_variable(key, value)
            state_machine.info(f"[FSM] Updated variable: {key} = {value}")

    # Handle todo_list updates
    if 'todo_list_update' in context_update and context_update['todo_list_update'] is not None:
        todo_update = context_update['todo_list_update']
        operation = todo_update.get('operation')
        items = todo_update.get('items', [])

        if operation == 'remove':
            for item in items:
                state_machine.ai_context_store.remove_from_to_do_list(item)
                state_machine.info(f"[FSM] Removed TODO: {item}")
        elif operation == 'add':
            for item in items:
                state_machine.ai_context_store.add_to_do_list(item)
                state_machine.info(f"[FSM] Added TODO: {item}")
        elif operation == 'replace':
            state_machine.ai_context_store.clear_to_do_list()
            for item in items:
                state_machine.ai_context_store.add_to_do_list(item)
            state_machine.info(f"[FSM] Replaced TODO list with {len(items)} items")

    # Update section progress
    if 'section_progress' in context_update and context_update['section_progress'] is not None:
        state_machine.ai_context_store.set_section_progress(context_update['section_progress'])
        state_machine.info(f"[FSM] Updated section progress: {context_update['section_progress']}")

    state_machine.info("[FSM] Context update applied successfully")
