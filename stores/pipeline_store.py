"""
Pipeline Store
Manages workflow template structure and execution state.
"""

from silantui import ModernLogger
from typing import Optional, List
from models.workflow import WorkflowTemplate, WorkflowStage, WorkflowStep


class PipelineStore(ModernLogger):
    """
    Pipeline Store for managing workflow template.
    Handles workflow structure and execution lifecycle.
    """

    def __init__(self):
        """Initialize the store."""
        super().__init__("PipelineStore")
        self.workflow_template: Optional[WorkflowTemplate] = None
        self.is_workflow_active: bool = False

    # ==============================================
    # Workflow Template Management
    # ==============================================

    def set_workflow_template(self, template: WorkflowTemplate):
        """Set the workflow template."""
        self.info(f"[PipelineStore] Setting workflow template: {template.name}")
        self.workflow_template = template

    def get_workflow_template(self) -> Optional[WorkflowTemplate]:
        """Get the workflow template."""
        return self.workflow_template

    def update_steps_for_stage(self, stage_id: str, new_steps: List[WorkflowStep]):
        """Update the steps for a specific stage."""
        if not self.workflow_template:
            self.warning(f"[PipelineStore] Cannot update steps: no workflow template")
            return

        for stage in self.workflow_template.stages:
            if stage.id == stage_id:
                stage.steps = new_steps
                self.info(f"[PipelineStore] Updated {len(new_steps)} steps for stage: {stage_id}")
                return

        self.warning(f"[PipelineStore] Stage not found: {stage_id}")

    # ==============================================
    # Workflow Activation
    # ==============================================

    def set_workflow_active(self, active: bool):
        """Set workflow active state."""
        self.is_workflow_active = active
        self.info(f"[PipelineStore] Workflow active: {active}")

    def is_active(self) -> bool:
        """Check if workflow is active."""
        return self.is_workflow_active

    # ==============================================
    # Initialization
    # ==============================================

    def initialize_workflow(self, planning_request: dict) -> WorkflowTemplate:
        """
        Initialize workflow with a predefined template.

        Args:
            planning_request: Dict containing problem info

        Returns:
            The initialized workflow template
        """
        self.info(f"[PipelineStore] Initializing workflow with request: {planning_request}")

        # Create predefined workflow template
        workflow_template = WorkflowTemplate(
            id="dcls_workflow",
            name="Data Science Lifecycle (DCLS) Analysis",
            description="Complete data science workflow based on existence first principles",
            stages=[
                WorkflowStage(
                    id="chapter_0_planning",
                    title="Planning & Analysis",
                    description="Initial problem analysis and workflow planning",
                    steps=[
                        WorkflowStep(
                            step_id="chapter_0_planning_section_1_design_workflow",
                            id="chapter_0_planning_section_1_design_workflow",
                            title="Design Workflow",
                            description="Design customized workflow based on requirements"
                        )
                    ]
                ),
            ]
        )

        self.workflow_template = workflow_template
        self.is_workflow_active = False

        self.info("[PipelineStore] Workflow template initialized successfully")
        return workflow_template

    def start_workflow_execution(self, state_machine):
        """
        Start the workflow execution.

        Args:
            state_machine: The workflow state machine instance
        """
        if not self.workflow_template:
            self.error("[PipelineStore] Cannot start workflow: no template")
            return

        if not self.workflow_template.stages:
            self.error("[PipelineStore] Cannot start workflow: no stages")
            return

        first_stage = self.workflow_template.stages[0]
        first_step = first_stage.steps[0] if first_stage.steps else None

        if not first_step:
            self.error("[PipelineStore] Cannot start workflow: no steps in first stage")
            return

        self.is_workflow_active = True

        # Start the state machine
        state_machine.start_workflow(
            stage_id=first_stage.id,
            step_id=first_step.id
        )

        self.info("[PipelineStore] Workflow execution started")

    # ==============================================
    # Reset
    # ==============================================

    def reset(self):
        """Reset the store to initial state."""
        self.info("[PipelineStore] Resetting store")
        self.workflow_template = None
        self.is_workflow_active = False
