from typing import Dict, Any, Optional
from app.core.config import llm, ModelAgent
from app.models.BaseAction import BaseAction, event
from DCLSAgents.prompts.prediction_inference_prompts import Model_SYSTEM_PROMPT
from app.knowledge.chapter_missions import CHAPTER_5_MISSION
from app.utils.xwl_parser import parse_xwl
from app.utils.xwl_actions import apply_xwl_to_step_template

class WorkflowInitialization(BaseAction):
    """
    Section 1: Workflow Initialization for Chapter 5

    Purpose:
    - Present chapter mission through Model Agent
    - Initialize model implementation execution
    - Agent outputs XML tags that are parsed into action flow
    """

    def __init__(self, step: Dict[str, Any], state: Optional[Dict[str, Any]] = None, stream: bool = False):
        super().__init__(
            step,
            state,
            stream,
            chapter_id="chapter_5_model_implementation_execution",
            section_id="section_1_workflow_initialization",
            name="Workflow Initialization",
            ability="Initialize Model Implementation Execution workflow using Model Agent",
            require_variables=["problem_description", "csv_file_path"]
        )

    @event("start")
    def start(self):
        """Use Model Agent to present mission and initialize workflow"""

        # Get required parameters for ModelAgent
        problem_description = self.input.get("problem_description", "")
        context_description = self.input.get("context_description", "")
        eda_summary = self.get_variable("eda_insights", "") or self.get_variable("eda_summary", "")
        modeling_strategy = self.get_variable("modeling_strategy", "")

        # Create Model Agent with required parameters
        model_agent = ModelAgent(
            problem_description=problem_description,
            context_description=context_description,
            eda_summary=eda_summary,
            llm=llm
        )

        # Override system prompt with Chapter 5 mission
        model_agent.system_prompt = Model_SYSTEM_PROMPT(
            mission_description=CHAPTER_5_MISSION,
            problem_description=problem_description,
            context_description=context_description,
            current_workflow="",
            current_sections="",
            current_section="Workflow Initialization",
            current_goal="Present chapter mission and initialize model implementation execution",
            observations=modeling_strategy
        )

        # Prepare task description
        csv_file_path = self.get_full_csv_path()
        task_description = f"""
You are starting Chapter 5: Model Implementation Execution.

Your tasks:
1. Present the chapter mission and goals to the user
2. Initialize the model implementation execution workflow
3. Prepare for systematic model training

Data file path: {csv_file_path}

Based on modeling strategy from Chapter 4, explain:
- The importance of systematic model implementation
- Training workflow and execution plan
- Model optimization approach
- The methodology for this chapter

Please:
- Use <add-text> to explain the chapter mission
- Use <add-text> to outline the implementation execution framework
- Prepare for model training and optimization

Begin with presenting the chapter and its importance for executing the modeling strategy.
"""

        # Agent generates XML response
        response = model_agent.answer(task_description)

        # Parse XML and apply to actions
        parsed = parse_xwl(response)
        apply_xwl_to_step_template(parsed, self, self.state)

        return self.end_event()


async def model_training_and_evaluation_step0(
    step: Dict[str, Any],
    state: Optional[Dict[str, Any]] = None,
    stream: bool = False
) -> Dict[str, Any]:
    """Entry point for this section"""
    state = state or {}
    return WorkflowInitialization(step, state, stream).run()
