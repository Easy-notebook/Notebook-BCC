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

    Handles:
    - variables: Update context variables
    - progress_update: Update hierarchical focus (stages/steps/behaviors)
    - effects_update: Update execution effects
    - workflow_update: Update workflow template
    - stage_steps_update: Update stage steps

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

    # Update hierarchical focus (detailed analysis text from Planner)
    if 'progress_update' in context_update and context_update['progress_update'] is not None:
        progress_update = context_update['progress_update']
        level = progress_update.get('level')  # "stages" | "steps" | "behaviors"
        focus = progress_update.get('focus', "")  # Detailed text string

        if level and isinstance(focus, str):
            state_machine.update_progress_focus(level, focus)
            state_machine.info(f"[FSM] Updated {level} focus ({len(focus)} chars)")
        else:
            state_machine.warning(f"[FSM] Invalid progress_update format: level={level}, focus type={type(focus)}")

    # Update outputs tracking (expected/produced/in_progress)
    if 'outputs_update' in context_update and context_update['outputs_update'] is not None:
        outputs_update = context_update['outputs_update']
        level = outputs_update.get('level')  # "stages" | "steps" | "behaviors"
        outputs = outputs_update.get('outputs', {})

        if level and isinstance(outputs, dict):
            state_machine.update_progress_outputs(level, outputs)
            state_machine.info(f"[FSM] Updated {level} outputs")

    # Update effects
    if 'effects_update' in context_update and context_update['effects_update'] is not None:
        effects = context_update['effects_update']
        if isinstance(effects, dict):
            state_machine.ai_context_store.set_effect(effects)
            state_machine.info(f"[FSM] Updated effects")

    # Update workflow template
    if 'workflow_update' in context_update and context_update['workflow_update'] is not None:
        workflow_data = context_update['workflow_update']
        if state_machine.pipeline_store and 'workflowTemplate' in workflow_data:
            from models.workflow import WorkflowTemplate
            updated_template = WorkflowTemplate.from_dict(workflow_data['workflowTemplate'])
            state_machine.pipeline_store.set_workflow_template(updated_template)
            state_machine.info(f"[FSM] Updated workflow template: {updated_template.name}")

    # Update stage steps
    if 'stage_steps_update' in context_update and context_update['stage_steps_update'] is not None:
        stage_steps = context_update['stage_steps_update']
        stage_id = stage_steps.get('stage_id')
        new_steps = stage_steps.get('steps', [])

        if state_machine.pipeline_store and state_machine.pipeline_store.workflow_template and stage_id:
            stage = state_machine.pipeline_store.workflow_template.find_stage(stage_id)
            if stage:
                # Update steps in the workflow template
                from models.workflow import WorkflowStep
                stage.steps = [WorkflowStep.from_dict(step) for step in new_steps]
                state_machine.info(f"[FSM] Updated steps for stage {stage_id}: {len(new_steps)} steps")

    state_machine.info("[FSM] Context update applied successfully")
