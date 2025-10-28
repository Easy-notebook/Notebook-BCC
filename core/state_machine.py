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
from .state_transitions import STATE_TRANSITIONS
from .state_effects import register_effects


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
        notebook_manager=None,
        max_steps: int = 0,
        interactive: bool = False
    ):
        """
        Initialize the state machine.

        Args:
            pipeline_store: Reference to the pipeline store
            script_store: Reference to the script store
            ai_context_store: Reference to the AI context store
            notebook_manager: Reference to the notebook manager
            max_steps: Maximum steps to execute (0 = unlimited)
            interactive: Enable interactive mode (pause at breakpoints)
        """
        super().__init__("WorkflowStateMachine")
        self.current_state = WorkflowState.IDLE
        self.execution_context = ExecutionContext()

        # Store references (will be injected)
        self.pipeline_store = pipeline_store
        self.script_store = script_store
        self.ai_context_store = ai_context_store
        self.notebook_manager = notebook_manager

        # Execution control
        self.step_counter = 0
        self.max_steps = max_steps
        self.interactive = interactive
        self.paused = False

        # State effect handlers (will be populated)
        self._state_effects: Dict[WorkflowState, Callable] = {}
        register_effects(self)

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
    # Special Handlers
    # ==============================================

    def _handle_workflow_update_confirmed(self):
        """Handle workflow update confirmation."""
        self.info("[FSM] Workflow update confirmed")

        pending_data = self.execution_context.pending_workflow_data
        if pending_data and self.pipeline_store:
            workflow_template_dict = pending_data.get('workflowTemplate')
            if workflow_template_dict:
                from models.workflow import WorkflowTemplate
                # Convert dict to WorkflowTemplate
                updated_template = WorkflowTemplate.from_dict(workflow_template_dict)
                self.pipeline_store.set_workflow_template(updated_template)
                self.info(f"[FSM] Workflow template updated to: {updated_template.name}")

            next_stage_id = pending_data.get('nextStageId')
            if next_stage_id:
                self.execution_context.workflow_context.current_stage_id = next_stage_id
                self.execution_context.workflow_context.current_step_id = None
                self.info(f"[FSM] Stage changed to: {next_stage_id}")

        # Clear pending data and script store's pending update
        self.execution_context.pending_workflow_data = None
        if self.script_store:
            self.script_store.pending_workflow_update = None

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
    # Progress Tracking (NEW)
    # ==============================================

    def get_progress_info(self) -> Optional[Dict[str, Any]]:
        """
        Get hierarchical progress information for POMDP observation.

        Returns:
            Dictionary containing current location, progress, and goals
        """
        if not self.pipeline_store or not self.pipeline_store.workflow_template:
            return None

        workflow = self.pipeline_store.workflow_template
        ctx = self.execution_context.workflow_context

        # Get stages progress
        all_stages = [stage.id for stage in workflow.stages]
        current_stage_idx = next((i for i, s in enumerate(all_stages) if s == ctx.current_stage_id), -1)

        stages_progress = {
            "completed": all_stages[:current_stage_idx] if current_stage_idx > 0 else [],
            "current": ctx.current_stage_id,
            "remaining": all_stages[current_stage_idx + 1:] if current_stage_idx >= 0 else []
        }

        # Get steps progress
        current_stage = workflow.find_stage(ctx.current_stage_id)
        if current_stage:
            all_steps = [step.id for step in current_stage.steps]
            current_step_idx = next((i for i, s in enumerate(all_steps) if s == ctx.current_step_id), -1)

            steps_progress = {
                "completed": all_steps[:current_step_idx] if current_step_idx > 0 else [],
                "current": ctx.current_step_id,
                "remaining": all_steps[current_step_idx + 1:] if current_step_idx >= 0 else []
            }
        else:
            steps_progress = {"completed": [], "current": None, "remaining": []}

        # Get behaviors progress (dynamically generated, track completed ones)
        behaviors_progress = {
            "completed": ctx.completed_behaviors.copy(),
            "current": ctx.current_behavior_id,
            "iteration": ctx.behavior_iteration
        }

        # Get goals
        stage_goal = current_stage.description if current_stage and hasattr(current_stage, 'description') else ""

        # Find step in current stage
        step_obj = None
        if current_stage and ctx.current_step_id:
            for step in current_stage.steps:
                if step.id == ctx.current_step_id or step.step_id == ctx.current_step_id:
                    step_obj = step
                    break

        step_goal = step_obj.description if step_obj and hasattr(step_obj, 'description') else ""

        return {
            "current": {
                "stage_id": ctx.current_stage_id,
                "step_id": ctx.current_step_id,
                "behavior_id": ctx.current_behavior_id,
                "behavior_iteration": ctx.behavior_iteration
            },
            "progress": {
                "stages": stages_progress,
                "steps": steps_progress,
                "behaviors": behaviors_progress
            },
            "goals": {
                "stage": stage_goal,
                "step": step_goal,
                "behavior": None  # Behavior goal is dynamic
            }
        }

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
