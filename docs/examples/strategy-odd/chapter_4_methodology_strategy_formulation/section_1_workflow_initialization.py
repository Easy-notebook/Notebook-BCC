from typing import Dict, Any, Optional
from app.core.config import llm, ModelAgent
from app.models.BaseAction import BaseAction, event
from DCLSAgents.prompts.prediction_inference_prompts import Model_SYSTEM_PROMPT
from app.knowledge.chapter_missions import CHAPTER_4_MISSION
from app.utils.xwl_parser import parse_xwl
from app.utils.xwl_actions import apply_xwl_to_step_template

class WorkflowInitialization(BaseAction):
    """
    Section 1: Workflow Initialization for Chapter 4

    Purpose:
    - Present chapter mission through Model Agent
    - Initialize methodology strategy formulation
    - Agent outputs XML tags that are parsed into action flow
    """

    def __init__(self, step: Dict[str, Any], state: Optional[Dict[str, Any]] = None, stream: bool = False):
        super().__init__(
            step,
            state,
            stream,
            chapter_id="chapter_4_methodology_strategy_formulation",
            section_id="section_1_workflow_initialization",
            name="Workflow Initialization",
            ability="Initialize Methodology Strategy Formulation workflow using Model Agent",
            require_variables=["problem_description", "csv_file_path"]
        )

    @event("start")
    def start(self):
        """Use Model Agent to present mission and initialize workflow"""

        # Get required parameters for ModelAgent
        problem_description = self.input.get("problem_description", "")
        context_description = self.input.get("context_description", "")
        eda_summary = self.get_variable("eda_insights", "") or self.get_variable("eda_summary", "")

        # Create Model Agent with required parameters
        model_agent = ModelAgent(
            problem_description=problem_description,
            context_description=context_description,
            eda_summary=eda_summary,
            llm=llm
        )

        # Override system prompt with Chapter 4 mission
        model_agent.system_prompt = Model_SYSTEM_PROMPT(
            mission_description=CHAPTER_4_MISSION,
            problem_description=problem_description,
            context_description=context_description,
            current_workflow="",
            current_sections="",
            current_section="Workflow Initialization",
            current_goal="Present chapter mission and initialize modeling strategy",
            observations=eda_summary
        )

        # Prepare task description
        csv_file_path = self.get_full_csv_path()
        task_description = f"""
You are starting Chapter 4: Methodology Strategy Formulation.

Your tasks:
1. Present the chapter mission and goals to the user
2. Initialize the modeling strategy formulation
3. Assess data readiness for modeling

Data file path: {csv_file_path}

Based on insights from Chapter 3, explain:
- The importance of systematic modeling strategy
- Feature engineering considerations
- Model selection criteria
- The approach for this chapter

Please:
- Use <add-text> to explain the chapter mission
- Use <add-text> to outline the modeling strategy framework
- Prepare for systematic methodology formulation

Begin with presenting the chapter and its importance for building effective models.
"""

        # Agent generates XML response
        response = model_agent.answer(task_description)

        # Parse XML and apply to actions
        parsed = parse_xwl(response)
        apply_xwl_to_step_template(parsed, self, self.state)

        return self.end_event()


def generate_method_proposal_sequence_step0(
    step: Dict[str, Any],
    state: Optional[Dict[str, Any]] = None,
    stream: bool = False
) -> Dict[str, Any]:
    """Entry point for this section"""
    state = state or {}
    return WorkflowInitialization(step, state, stream).run()
