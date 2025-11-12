"""
Workflow Updater - Updates state machine context based on API responses.
Handles workflow definitions (stages/steps/behaviors) from Planning API.
"""

from typing import Dict, Any
from silantui import ModernLogger


class WorkflowUpdater(ModernLogger):
    """
    Updates workflow state based on API responses.

    Handles:
    - Stages definition updates
    - Steps definition updates
    - Behavior definition updates
    - Progress tracking updates
    """

    def __init__(self):
        """Initialize the workflow updater."""
        super().__init__("WorkflowUpdater")

    def update_from_response(self, state_machine, response: Dict[str, Any]) -> None:
        """
        Update state machine context based on API response.

        Args:
            state_machine: WorkflowStateMachine instance
            response: Parsed API response
        """
        response_type = response.get('type')
        content = response.get('content', {})

        self.info(f"[Updater] Processing response type: {response_type}")

        if response_type == 'stages':
            self._update_stages(state_machine, content)
        elif response_type == 'steps':
            self._update_steps(state_machine, content)
        elif response_type == 'behavior':
            self._update_behavior(state_machine, content)
        elif response_type == 'reflection':
            self._update_reflection(state_machine, content)
        else:
            self.warning(f"[Updater] Unknown response type: {response_type}")

    def _update_stages(self, state_machine, content: Dict[str, Any]) -> None:
        """
        Update stages definition in workflow template.

        Args:
            state_machine: State machine instance
            content: Parsed stages content
        """
        stages = content.get('stages', [])
        focus = content.get('focus', '')

        self.info(f"[Updater] Updating stages: {len(stages)} stages")

        if not state_machine.execution_context:
            self.error("[Updater] No execution context available")
            return

        ctx = state_machine.execution_context.workflow_context

        # Update workflow template with stages
        if stages and state_machine.pipeline_store:
            # Convert stages to WorkflowTemplate format
            from models.workflow import WorkflowTemplate, WorkflowStage

            workflow_stages = []
            for stage_data in stages:
                stage = WorkflowStage(
                    id=stage_data.get('stage_id'),
                    title=stage_data.get('title', ''),
                    name=stage_data.get('title', ''),
                    description=stage_data.get('goal', ''),
                    steps=[]  # Steps will be loaded later
                )
                workflow_stages.append(stage)

            # Create or update workflow template
            if state_machine.pipeline_store.workflow_template:
                state_machine.pipeline_store.workflow_template.stages = workflow_stages
            else:
                template = WorkflowTemplate(
                    name="Generated Workflow",
                    stages=workflow_stages
                )
                state_machine.pipeline_store.set_workflow_template(template)

            # Set first stage as current if not set
            if not ctx.current_stage_id and len(stages) > 0:
                ctx.current_stage_id = stages[0]['stage_id']

            # Update stages focus
            state_machine.update_progress_focus('stages', focus)

            self.info(f"[Updater] Set current stage: {ctx.current_stage_id}")

    def _update_steps(self, state_machine, content: Dict[str, Any]) -> None:
        """
        Update steps definition in workflow template.

        Args:
            state_machine: State machine instance
            content: Parsed steps content
        """
        steps = content.get('steps', [])
        focus = content.get('focus', '')
        goals = content.get('goals', '')

        self.info(f"[Updater] Updating steps: {len(steps)} steps")

        if not state_machine.execution_context:
            self.error("[Updater] No execution context available")
            return

        ctx = state_machine.execution_context.workflow_context

        # Update workflow template with steps for current stage
        if steps and state_machine.pipeline_store and ctx.current_stage_id:
            from models.workflow import WorkflowStep

            workflow = state_machine.pipeline_store.workflow_template
            if workflow:
                stage = workflow.find_stage(ctx.current_stage_id)
                if stage:
                    # Convert steps to WorkflowStep format
                    workflow_steps = []
                    for step_data in steps:
                        step = WorkflowStep(
                            id=step_data.get('step_id'),
                            description=step_data.get('goal', ''),  # Use goal as description
                            title=step_data.get('title', '')
                        )
                        workflow_steps.append(step)

                    stage.steps = workflow_steps

                    # Set first step as current if not set
                    if not ctx.current_step_id and len(steps) > 0:
                        ctx.current_step_id = steps[0]['step_id']

                    # Update steps focus
                    state_machine.update_progress_focus('steps', focus)

                    self.info(f"[Updater] Set current step: {ctx.current_step_id}")
                else:
                    self.error(f"[Updater] Stage {ctx.current_stage_id} not found")
            else:
                self.error("[Updater] No workflow template available")

    def _update_behavior(self, state_machine, content: Dict[str, Any]) -> None:
        """
        Update behavior definition (for behavior focus).

        Args:
            state_machine: State machine instance
            content: Parsed behavior content
        """
        behavior_id = content.get('behavior_id')
        task = content.get('task', '')

        self.info(f"[Updater] Updating behavior: {behavior_id}")

        if not state_machine.execution_context:
            self.error("[Updater] No execution context available")
            return

        ctx = state_machine.execution_context.workflow_context

        # Set behavior as current
        if behavior_id:
            # Increment iteration if behavior_id changed
            if ctx.current_behavior_id != behavior_id:
                ctx.behavior_iteration += 1
                ctx.current_behavior_id = behavior_id

            # Update behavior focus
            state_machine.update_progress_focus('behaviors', task)

            self.info(f"[Updater] Set current behavior: {behavior_id}, iteration: {ctx.behavior_iteration}")

    def _update_reflection(self, state_machine, content: Dict[str, Any]) -> None:
        """
        Update state based on reflection response.

        Args:
            state_machine: State machine instance
            content: Parsed reflection content
        """
        behavior_is_complete = content.get('behavior_is_complete', False)
        next_state = content.get('next_state')
        variables_produced = content.get('variables_produced', {})

        self.info(f"[Updater] Processing reflection: behavior_complete={behavior_is_complete}, next_state={next_state}")

        if not state_machine.execution_context:
            self.error("[Updater] No execution context available")
            return

        # Add new variables to variables store
        if variables_produced and state_machine.script_store:
            for var_name, var_value in variables_produced.items():
                state_machine.script_store.add_variable(var_name, var_value)
                self.info(f"[Updater] Added variable: {var_name}")

        # Note: FSM state transition is handled by the state machine itself
        # via WorkflowEvent.COMPLETE_STEP or WorkflowEvent.NEXT_BEHAVIOR


# Create singleton instance
workflow_updater = WorkflowUpdater()
