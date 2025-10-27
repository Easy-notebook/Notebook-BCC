"""
Workflow data models.
Replicates the TypeScript WorkflowTemplate, WorkflowStage, WorkflowStep interfaces.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class WorkflowStep:
    """
    Represents a single step within a stage.
    Maps to TypeScript's WorkflowStep interface.
    """
    step_id: str
    id: Optional[str] = None
    status: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    index: Optional[int] = None

    def __post_init__(self):
        # Ensure id is set to step_id if not provided
        if self.id is None:
            self.id = self.step_id


@dataclass
class WorkflowStage:
    """
    Represents a stage containing multiple steps.
    Maps to TypeScript's WorkflowStage interface.
    """
    id: str
    steps: List[WorkflowStep] = field(default_factory=list)
    title: Optional[str] = None
    description: Optional[str] = None


@dataclass
class WorkflowTemplate:
    """
    Represents the complete workflow structure.
    Maps to TypeScript's WorkflowTemplate interface.
    """
    name: str
    stages: List[WorkflowStage] = field(default_factory=list)
    id: Optional[str] = None
    description: Optional[str] = None

    def find_stage(self, stage_id: str) -> Optional[WorkflowStage]:
        """Find a stage by its ID."""
        for stage in self.stages:
            if stage.id == stage_id:
                return stage
        return None

    def find_step(self, stage_id: str, step_id: str) -> Optional[WorkflowStep]:
        """Find a step by stage and step IDs."""
        stage = self.find_stage(stage_id)
        if not stage:
            return None
        for step in stage.steps:
            if step.id == step_id or step.step_id == step_id:
                return step
        return None

    def get_next_step(self, stage_id: str, current_step_id: str) -> Optional[WorkflowStep]:
        """Get the next step in the current stage."""
        stage = self.find_stage(stage_id)
        if not stage:
            return None

        current_index = -1
        for i, step in enumerate(stage.steps):
            if step.id == current_step_id or step.step_id == current_step_id:
                current_index = i
                break

        if current_index == -1 or current_index >= len(stage.steps) - 1:
            return None

        return stage.steps[current_index + 1]

    def get_next_stage(self, current_stage_id: str) -> Optional[WorkflowStage]:
        """Get the next stage in the workflow."""
        current_index = -1
        for i, stage in enumerate(self.stages):
            if stage.id == current_stage_id:
                current_index = i
                break

        if current_index == -1 or current_index >= len(self.stages) - 1:
            return None

        return self.stages[current_index + 1]

    def is_last_step_in_stage(self, stage_id: str, step_id: str) -> bool:
        """Check if this is the last step in the stage."""
        stage = self.find_stage(stage_id)
        if not stage or not stage.steps:
            return False
        last_step = stage.steps[-1]
        return last_step.id == step_id or last_step.step_id == step_id

    def is_last_stage(self, stage_id: str) -> bool:
        """Check if this is the last stage in the workflow."""
        if not self.stages:
            return False
        return self.stages[-1].id == stage_id
