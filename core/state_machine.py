"""
Workflow State Machine - Core Implementation
Replicates the TypeScript workflowStateMachine.ts
"""

import time
from typing import Dict, Optional, Any, Callable
from silantui import ModernLogger
from .events import WorkflowEvent, EVENTS
from .states import WorkflowState, WORKFLOW_STATES
from .context import WorkflowContext, ExecutionContext


# State transition rules - maps (current_state, event) -> next_state
STATE_TRANSITIONS: Dict[WorkflowState, Dict[WorkflowEvent, WorkflowState]] = {
    WorkflowState.IDLE: {
        WorkflowEvent.START_WORKFLOW: WorkflowState.STAGE_RUNNING,
    },

    WorkflowState.STAGE_RUNNING: {
        WorkflowEvent.START_STEP: WorkflowState.STEP_RUNNING,
        WorkflowEvent.COMPLETE_STAGE: WorkflowState.STAGE_COMPLETED,
        WorkflowEvent.FAIL: WorkflowState.ERROR,
        WorkflowEvent.CANCEL: WorkflowState.CANCELLED,
    },

    WorkflowState.STEP_RUNNING: {
        WorkflowEvent.START_BEHAVIOR: WorkflowState.BEHAVIOR_RUNNING,
        WorkflowEvent.COMPLETE_STEP: WorkflowState.STEP_COMPLETED,
        WorkflowEvent.FAIL: WorkflowState.ERROR,
        WorkflowEvent.CANCEL: WorkflowState.CANCELLED,
    },

    WorkflowState.BEHAVIOR_RUNNING: {
        WorkflowEvent.START_ACTION: WorkflowState.ACTION_RUNNING,
        WorkflowEvent.COMPLETE_BEHAVIOR: WorkflowState.BEHAVIOR_COMPLETED,
        WorkflowEvent.FAIL: WorkflowState.ERROR,
        WorkflowEvent.CANCEL: WorkflowState.CANCELLED,
    },

    WorkflowState.ACTION_RUNNING: {
        WorkflowEvent.COMPLETE_ACTION: WorkflowState.ACTION_COMPLETED,
        WorkflowEvent.FAIL: WorkflowState.ERROR,
        WorkflowEvent.CANCEL: WorkflowState.CANCELLED,
        WorkflowEvent.UPDATE_WORKFLOW: WorkflowState.WORKFLOW_UPDATE_PENDING,
        WorkflowEvent.UPDATE_STEP: WorkflowState.STEP_UPDATE_PENDING,
    },

    WorkflowState.ACTION_COMPLETED: {
        WorkflowEvent.NEXT_ACTION: WorkflowState.ACTION_RUNNING,
        WorkflowEvent.COMPLETE_BEHAVIOR: WorkflowState.BEHAVIOR_COMPLETED,
        WorkflowEvent.FAIL: WorkflowState.ERROR,
        WorkflowEvent.CANCEL: WorkflowState.CANCELLED,
    },

    WorkflowState.BEHAVIOR_COMPLETED: {
        WorkflowEvent.NEXT_BEHAVIOR: WorkflowState.BEHAVIOR_RUNNING,
        WorkflowEvent.COMPLETE_STEP: WorkflowState.STEP_COMPLETED,
        WorkflowEvent.FAIL: WorkflowState.ERROR,
        WorkflowEvent.CANCEL: WorkflowState.CANCELLED,
    },

    WorkflowState.STEP_COMPLETED: {
        WorkflowEvent.COMPLETE_STAGE: WorkflowState.STAGE_COMPLETED,
        WorkflowEvent.NEXT_STEP: WorkflowState.STEP_RUNNING,
        WorkflowEvent.FAIL: WorkflowState.ERROR,
        WorkflowEvent.CANCEL: WorkflowState.CANCELLED,
    },

    WorkflowState.STAGE_COMPLETED: {
        WorkflowEvent.NEXT_STAGE: WorkflowState.STAGE_RUNNING,
        WorkflowEvent.COMPLETE_WORKFLOW: WorkflowState.WORKFLOW_COMPLETED,
        WorkflowEvent.CANCEL: WorkflowState.CANCELLED,
    },

    WorkflowState.WORKFLOW_COMPLETED: {
        WorkflowEvent.RESET: WorkflowState.IDLE,
    },

    WorkflowState.WORKFLOW_UPDATE_PENDING: {
        WorkflowEvent.UPDATE_WORKFLOW_CONFIRMED: WorkflowState.ACTION_COMPLETED,
        WorkflowEvent.UPDATE_WORKFLOW_REJECTED: WorkflowState.ACTION_COMPLETED,
        WorkflowEvent.COMPLETE_ACTION: WorkflowState.WORKFLOW_UPDATE_PENDING,  # Ignore
        WorkflowEvent.CANCEL: WorkflowState.CANCELLED,
    },

    WorkflowState.STEP_UPDATE_PENDING: {
        WorkflowEvent.UPDATE_STEP_CONFIRMED: WorkflowState.ACTION_COMPLETED,
        WorkflowEvent.UPDATE_STEP_REJECTED: WorkflowState.ERROR,
        WorkflowEvent.CANCEL: WorkflowState.CANCELLED,
    },

    WorkflowState.ERROR: {
        WorkflowEvent.RESET: WorkflowState.IDLE,
        WorkflowEvent.START_WORKFLOW: WorkflowState.STAGE_RUNNING,
        WorkflowEvent.START_BEHAVIOR: WorkflowState.BEHAVIOR_RUNNING,
    },

    WorkflowState.CANCELLED: {
        WorkflowEvent.RESET: WorkflowState.IDLE,
    },
}


class WorkflowStateMachine(ModernLogger):
    """
    The Workflow State Machine.
    Manages workflow state transitions and execution flow.

    This is the Python implementation of the TypeScript WorkflowStateMachine.
    """

    def __init__(
        self,
        pipeline_store=None,
        script_store=None,
        ai_context_store=None,
        max_steps: int = 0,
        start_mode: str = 'generation',
        interactive: bool = False
    ):
        """
        Initialize the state machine.

        Args:
            pipeline_store: Reference to the pipeline store
            script_store: Reference to the script store
            ai_context_store: Reference to the AI context store
            max_steps: Maximum steps to execute (0 = unlimited)
            start_mode: Start mode ('reflection' or 'generation')
            interactive: Enable interactive mode (pause at breakpoints)
        """
        super().__init__("WorkflowStateMachine")
        self.current_state = WorkflowState.IDLE
        self.execution_context = ExecutionContext()

        # Store references (will be injected)
        self.pipeline_store = pipeline_store
        self.script_store = script_store
        self.ai_context_store = ai_context_store

        # Execution control
        self.step_counter = 0
        self.max_steps = max_steps
        self.start_mode = start_mode  # 'reflection' or 'generation'
        self.interactive = interactive
        self.paused = False

        # State effect handlers (will be populated)
        self._state_effects: Dict[WorkflowState, Callable] = {}
        self._register_state_effects()

    def _register_state_effects(self):
        """Register side effect handlers for each state."""
        self._state_effects = {
            WorkflowState.STAGE_RUNNING: self._effect_stage_running,
            WorkflowState.STEP_RUNNING: self._effect_step_running,
            WorkflowState.BEHAVIOR_RUNNING: self._effect_behavior_running,
            WorkflowState.ACTION_RUNNING: self._effect_action_running,
            WorkflowState.ACTION_COMPLETED: self._effect_action_completed,
            WorkflowState.BEHAVIOR_COMPLETED: self._effect_behavior_completed,
            WorkflowState.STEP_COMPLETED: self._effect_step_completed,
            WorkflowState.STAGE_COMPLETED: self._effect_stage_completed,
        }

    # ==============================================
    # Execution Control Methods
    # ==============================================

    def check_step_limit(self) -> bool:
        """
        Check if step limit has been reached.

        Returns:
            True if should continue, False if limit reached
        """
        if self.max_steps <= 0:
            return True  # Unlimited

        if self.step_counter >= self.max_steps:
            self.warning(f"[FSM] Step limit reached: {self.step_counter}/{self.max_steps}")
            if self.interactive:
                self.paused = True
                self.info("[FSM] Paused at breakpoint. Call resume() to continue.")
            return False

        return True

    def increment_step(self):
        """Increment the step counter."""
        self.step_counter += 1
        self.info(f"[FSM] Step {self.step_counter}" + (f"/{self.max_steps}" if self.max_steps > 0 else ""))

    def reset_step_counter(self):
        """Reset the step counter."""
        self.step_counter = 0
        self.info("[FSM] Step counter reset")

    def pause(self):
        """Pause execution."""
        self.paused = True
        self.info("[FSM] Execution paused")

    def resume(self):
        """Resume execution."""
        self.paused = False
        self.info("[FSM] Execution resumed")
        # Re-trigger current state effects
        if self.current_state in self._state_effects:
            self._execute_state_effects(self.current_state, None)

    def set_max_steps(self, max_steps: int):
        """Update maximum steps."""
        self.max_steps = max_steps
        self.info(f"[FSM] Max steps set to: {max_steps}")

    def get_execution_status(self) -> Dict[str, Any]:
        """Get current execution status."""
        return {
            'current_step': self.step_counter,
            'max_steps': self.max_steps,
            'paused': self.paused,
            'start_mode': self.start_mode,
            'interactive': self.interactive,
            'state': self.current_state.value,
        }

    def transition(self, event: WorkflowEvent, payload: Any = None) -> bool:
        """
        Attempt to transition to a new state based on the event.

        Args:
            event: The event to process
            payload: Optional payload data

        Returns:
            True if transition was successful, False otherwise
        """
        from_state = self.current_state
        to_state = STATE_TRANSITIONS.get(from_state, {}).get(event)

        if not to_state:
            self.warning(f"[FSM] Invalid transition: From {from_state} via {event}")
            return False

        self.info(f"[FSM] Transition: {from_state} -> {to_state} (Event: {event})")

        # Record history
        self.execution_context.add_history_entry(
            timestamp=time.time(),
            from_state=from_state.value,
            to_state=to_state.value,
            event=event.value,
            payload=payload
        )

        # Update state
        self.current_state = to_state

        # Handle special transitions
        if event == WorkflowEvent.UPDATE_WORKFLOW and payload:
            self.execution_context.pending_workflow_data = payload

        if event == WorkflowEvent.UPDATE_WORKFLOW_CONFIRMED:
            self._handle_workflow_update_confirmed()

        if event == WorkflowEvent.UPDATE_WORKFLOW_REJECTED:
            self._handle_workflow_update_rejected()

        # Execute state effects asynchronously
        self._execute_state_effects(to_state, payload)

        return True

    def _execute_state_effects(self, state: WorkflowState, payload: Any = None):
        """Execute side effects for entering a new state."""
        # Check if execution is paused
        if self.paused:
            self.info(f"[FSM Effect] Execution paused, skipping effect for {state}")
            return

        # Check step limit (increment for action-level states)
        if state in [WorkflowState.ACTION_RUNNING, WorkflowState.ACTION_COMPLETED]:
            self.increment_step()
            if not self.check_step_limit():
                self.warning(f"[FSM Effect] Step limit reached, pausing execution")
                return

        effect_handler = self._state_effects.get(state)
        if effect_handler:
            try:
                effect_handler(payload)
            except Exception as e:
                self.error(f"[FSM Effect] Error in state {state}: {e}", exc_info=True)
                self.transition(WorkflowEvent.FAIL, {'error': str(e)})

    # ==============================================
    # State Effect Handlers
    # ==============================================

    def _effect_stage_running(self, payload: Any = None):
        """Effect for STAGE_RUNNING state."""
        self.info(f"[FSM Effect] STAGE_RUNNING")

        if not self.pipeline_store:
            self.error("[FSM Effect] Pipeline store not available")
            self.transition(WorkflowEvent.FAIL, {'error': 'Pipeline store not available'})
            return

        workflow = self.pipeline_store.workflow_template
        stage_id = self.execution_context.workflow_context.current_stage_id

        if not workflow or not stage_id:
            self.transition(WorkflowEvent.FAIL, {'error': 'No workflow or stage ID'})
            return

        stage = workflow.find_stage(stage_id)
        if not stage or not stage.steps:
            self.transition(WorkflowEvent.FAIL, {'error': f'No steps in stage {stage_id}'})
            return

        # Set first step
        first_step = stage.steps[0]
        self.execution_context.workflow_context.current_step_id = first_step.id

        # Transition to step
        self.transition(WorkflowEvent.START_STEP)

    def _effect_step_running(self, payload: Any = None):
        """Effect for STEP_RUNNING state."""
        self.info(f"[FSM Effect] STEP_RUNNING (start_mode={self.start_mode})")

        # Check start mode
        if self.start_mode == 'reflection':
            # Start with reflection/feedback API
            self._start_with_reflection()
        else:
            # Default: Start with generation/behavior API
            self.transition(WorkflowEvent.START_BEHAVIOR)

    def _start_with_reflection(self):
        """Start step with reflection API (feedback-driven mode)."""
        self.info("[FSM Effect] Starting with reflection API")

        ctx = self.execution_context.workflow_context

        if not ctx.current_stage_id or not ctx.current_step_id:
            self.error("[FSM Effect] Missing stage/step ID for reflection")
            self.transition(WorkflowEvent.FAIL, {'error': 'Missing stage/step ID'})
            return

        if not self.ai_context_store:
            self.error("[FSM Effect] AI context store not available")
            self.transition(WorkflowEvent.FAIL, {'error': 'AI context store not available'})
            return

        try:
            # Get current state
            from utils.api_client import workflow_api_client
            current_state = self.ai_context_store.get_context().to_dict()

            self.info(f"[FSM Effect] Calling reflection API for stage={ctx.current_stage_id}, step={ctx.current_step_id}")

            # Call feedback API
            feedback_response = workflow_api_client.send_feedback_sync(
                stage_id=ctx.current_stage_id,
                step_index=ctx.current_step_id,
                state=current_state
            )

            self.info(f"[FSM Effect] Reflection response: {feedback_response}")

            # Check if target achieved
            target_achieved = feedback_response.get('targetAchieved', False)

            if target_achieved:
                self.info("[FSM Effect] Target achieved per reflection API, completing step")
                self.transition(WorkflowEvent.COMPLETE_STEP)
            else:
                # Target not achieved, proceed with behavior generation
                self.info("[FSM Effect] Target not achieved, proceeding with behavior generation")
                self.transition(WorkflowEvent.START_BEHAVIOR)

        except Exception as e:
            self.error(f"[FSM Effect] Failed to call reflection API: {e}", exc_info=True)
            # On error, fall back to behavior generation
            self.warning("[FSM Effect] Falling back to behavior generation due to reflection error")
            self.transition(WorkflowEvent.START_BEHAVIOR)

    def _effect_behavior_running(self, payload: Any = None):
        """Effect for BEHAVIOR_RUNNING state."""
        self.info(f"[FSM Effect] BEHAVIOR_RUNNING")

        ctx = self.execution_context.workflow_context

        if not ctx.current_stage_id or not ctx.current_step_id:
            self.error("[FSM Effect] Missing stage/step ID")
            self.transition(WorkflowEvent.FAIL, {'error': 'Missing stage/step ID'})
            return

        # Get current context from AI store
        if not self.ai_context_store:
            self.error("[FSM Effect] AI context store not available")
            self.transition(WorkflowEvent.FAIL, {'error': 'AI context store not available'})
            return

        try:
            # Fetch actions from API
            from utils.api_client import workflow_api_client

            self.info(f"[FSM Effect] Fetching actions for stage={ctx.current_stage_id}, step={ctx.current_step_id}")

            # Get current state
            current_state = self.ai_context_store.get_context().to_dict()

            # Fetch actions (synchronous wrapper)
            actions = workflow_api_client.fetch_behavior_actions_sync(
                stage_id=ctx.current_stage_id,
                step_index=ctx.current_step_id,
                state=current_state,
                stream=True
            )

            self.info(f"[FSM Effect] Fetched {len(actions)} actions")

            # Store actions in context
            self.execution_context.workflow_context.current_behavior_actions = actions
            self.execution_context.workflow_context.current_action_index = 0

            if actions:
                self.transition(WorkflowEvent.START_ACTION)
            else:
                # No actions, complete behavior immediately
                self.transition(WorkflowEvent.COMPLETE_BEHAVIOR)

        except Exception as e:
            self.error(f"[FSM Effect] Failed to fetch actions: {e}", exc_info=True)
            self.transition(WorkflowEvent.FAIL, {'error': f'Failed to fetch actions: {str(e)}'})

    def _effect_action_running(self, payload: Any = None):
        """Effect for ACTION_RUNNING state."""
        self.info(f"[FSM Effect] ACTION_RUNNING")

        ctx = self.execution_context.workflow_context
        if not ctx.current_behavior_actions:
            self.warning("[FSM Effect] No actions to execute")
            self.transition(WorkflowEvent.COMPLETE_ACTION)
            return

        if ctx.current_action_index >= len(ctx.current_behavior_actions):
            self.warning("[FSM Effect] Action index out of bounds")
            self.transition(WorkflowEvent.COMPLETE_ACTION)
            return

        current_action = ctx.current_behavior_actions[ctx.current_action_index]
        self.info(f"[FSM Effect] Executing action #{ctx.current_action_index + 1}: {current_action}")

        # Execute the action via script store
        if self.script_store:
            try:
                self.script_store.exec_action(current_action)
            except Exception as e:
                self.error(f"[FSM Effect] Action execution failed: {e}", exc_info=True)
                self.transition(WorkflowEvent.FAIL, {'error': str(e)})
                return

        # Complete action
        self.transition(WorkflowEvent.COMPLETE_ACTION)

    def _effect_action_completed(self, payload: Any = None):
        """Effect for ACTION_COMPLETED state."""
        self.info(f"[FSM Effect] ACTION_COMPLETED")

        ctx = self.execution_context.workflow_context
        next_index = ctx.current_action_index + 1

        if next_index < len(ctx.current_behavior_actions):
            # More actions to execute
            ctx.current_action_index = next_index
            self.transition(WorkflowEvent.NEXT_ACTION)
        else:
            # All actions done, complete behavior
            self.transition(WorkflowEvent.COMPLETE_BEHAVIOR)

    def _effect_behavior_completed(self, payload: Any = None):
        """Effect for BEHAVIOR_COMPLETED state."""
        self.info(f"[FSM Effect] BEHAVIOR_COMPLETED")

        ctx = self.execution_context.workflow_context

        if not ctx.current_stage_id or not ctx.current_step_id:
            self.error("[FSM Effect] Missing stage/step ID")
            self.transition(WorkflowEvent.FAIL, {'error': 'Missing stage/step ID'})
            return

        if not self.ai_context_store:
            self.error("[FSM Effect] AI context store not available")
            self.transition(WorkflowEvent.FAIL, {'error': 'AI context store not available'})
            return

        try:
            # Send feedback to get next instruction
            from utils.api_client import workflow_api_client

            self.info(f"[FSM Effect] Sending feedback for stage={ctx.current_stage_id}, step={ctx.current_step_id}")

            # Get current state
            current_state = self.ai_context_store.get_context().to_dict()

            # Send feedback (synchronous wrapper)
            feedback_response = workflow_api_client.send_feedback_sync(
                stage_id=ctx.current_stage_id,
                step_index=ctx.current_step_id,
                state=current_state
            )

            self.info(f"[FSM Effect] Feedback response: {feedback_response}")

            # Check if target is achieved
            target_achieved = feedback_response.get('targetAchieved', False)

            if target_achieved:
                self.info("[FSM Effect] Target achieved, completing step")
                self.transition(WorkflowEvent.COMPLETE_STEP)
            else:
                self.info("[FSM Effect] Target not achieved, starting next behavior")
                self.transition(WorkflowEvent.NEXT_BEHAVIOR)

        except Exception as e:
            self.error(f"[FSM Effect] Failed to send feedback: {e}", exc_info=True)
            # On error, default to completing step to avoid infinite loop
            self.warning("[FSM Effect] Defaulting to COMPLETE_STEP due to error")
            self.transition(WorkflowEvent.COMPLETE_STEP)

    def _effect_step_completed(self, payload: Any = None):
        """Effect for STEP_COMPLETED state."""
        self.info(f"[FSM Effect] STEP_COMPLETED")

        if not self.pipeline_store:
            self.error("[FSM Effect] Pipeline store not available")
            return

        workflow = self.pipeline_store.workflow_template
        ctx = self.execution_context.workflow_context

        if not workflow or not ctx.current_stage_id or not ctx.current_step_id:
            self.error("[FSM Effect] Invalid context in STEP_COMPLETED")
            return

        # Check if last step in stage
        is_last = workflow.is_last_step_in_stage(ctx.current_stage_id, ctx.current_step_id)

        if is_last:
            self.transition(WorkflowEvent.COMPLETE_STAGE)
        else:
            # Move to next step
            next_step = workflow.get_next_step(ctx.current_stage_id, ctx.current_step_id)
            if next_step:
                ctx.current_step_id = next_step.id
                ctx.reset_for_new_step()
                self.transition(WorkflowEvent.NEXT_STEP)
            else:
                self.error("[FSM Effect] No next step found")
                self.transition(WorkflowEvent.COMPLETE_STAGE)

    def _effect_stage_completed(self, payload: Any = None):
        """Effect for STAGE_COMPLETED state."""
        self.info(f"[FSM Effect] STAGE_COMPLETED")

        if not self.pipeline_store:
            self.error("[FSM Effect] Pipeline store not available")
            return

        workflow = self.pipeline_store.workflow_template
        ctx = self.execution_context.workflow_context

        if not workflow or not ctx.current_stage_id:
            self.error("[FSM Effect] Invalid context in STAGE_COMPLETED")
            return

        # Check if last stage
        is_last = workflow.is_last_stage(ctx.current_stage_id)

        if is_last:
            self.transition(WorkflowEvent.COMPLETE_WORKFLOW)
        else:
            # Move to next stage
            next_stage = workflow.get_next_stage(ctx.current_stage_id)
            if next_stage:
                ctx.current_stage_id = next_stage.id
                ctx.current_step_id = next_stage.steps[0].id if next_stage.steps else None
                ctx.reset_for_new_behavior()
                self.transition(WorkflowEvent.NEXT_STAGE)
            else:
                self.error("[FSM Effect] No next stage found")
                self.transition(WorkflowEvent.COMPLETE_WORKFLOW)

    # ==============================================
    # Special Handlers
    # ==============================================

    def _handle_workflow_update_confirmed(self):
        """Handle workflow update confirmation."""
        self.info("[FSM] Workflow update confirmed")

        pending_data = self.execution_context.pending_workflow_data
        if pending_data and self.pipeline_store:
            workflow_template = pending_data.get('workflowTemplate')
            if workflow_template:
                self.pipeline_store.set_workflow_template(workflow_template)
                self.info("[FSM] Workflow template updated")

            next_stage_id = pending_data.get('nextStageId')
            if next_stage_id:
                self.execution_context.workflow_context.current_stage_id = next_stage_id
                self.execution_context.workflow_context.current_step_id = None

        self.execution_context.pending_workflow_data = None

    def _handle_workflow_update_rejected(self):
        """Handle workflow update rejection."""
        self.info("[FSM] Workflow update rejected")
        self.execution_context.pending_workflow_data = None

    # ==============================================
    # Public API
    # ==============================================

    def start_workflow(self, stage_id: str, step_id: Optional[str] = None):
        """
        Start the workflow execution.

        Args:
            stage_id: The ID of the starting stage
            step_id: Optional step ID (will be determined from stage if not provided)
        """
        self.info(f"[FSM] Starting workflow at stage: {stage_id}")

        self.execution_context.workflow_context.current_stage_id = stage_id
        self.execution_context.workflow_context.current_step_id = step_id

        self.transition(WorkflowEvent.START_WORKFLOW)

    def fail(self, error: Exception, message: Optional[str] = None):
        """Transition to ERROR state."""
        self.error(f"[FSM] Fail: {message or str(error)}")
        self.transition(WorkflowEvent.FAIL, {'error': str(error), 'message': message})

    def cancel(self):
        """Cancel the workflow."""
        self.info("[FSM] Cancelling workflow")
        self.transition(WorkflowEvent.CANCEL)

    def reset(self):
        """Reset the state machine."""
        self.info("[FSM] Resetting state machine")
        self.current_state = WorkflowState.IDLE
        self.execution_context.reset()

    def request_workflow_update(self, payload: Dict[str, Any]):
        """Request a workflow update."""
        self.info("[FSM] Requesting workflow update")
        self.transition(WorkflowEvent.UPDATE_WORKFLOW, payload)

    def confirm_workflow_update(self):
        """Confirm a pending workflow update."""
        self.info("[FSM] Confirming workflow update")
        self.transition(WorkflowEvent.UPDATE_WORKFLOW_CONFIRMED)

    def reject_workflow_update(self):
        """Reject a pending workflow update."""
        self.info("[FSM] Rejecting workflow update")
        self.transition(WorkflowEvent.UPDATE_WORKFLOW_REJECTED)

    # ==============================================
    # Getters
    # ==============================================

    @property
    def context(self) -> WorkflowContext:
        """Get the current workflow context."""
        return self.execution_context.workflow_context

    @property
    def state(self) -> WorkflowState:
        """Get the current state."""
        return self.current_state

    @property
    def history(self):
        """Get the execution history."""
        return self.execution_context.execution_history

    def get_state_info(self) -> Dict[str, Any]:
        """Get current state information."""
        return {
            'current_state': self.current_state.value,
            'stage_id': self.context.current_stage_id,
            'step_id': self.context.current_step_id,
            'behavior_id': self.context.current_behavior_id,
            'action_index': self.context.current_action_index,
            'total_actions': len(self.context.current_behavior_actions),
        }
