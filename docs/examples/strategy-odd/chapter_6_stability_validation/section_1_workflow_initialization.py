from typing import Dict, Any, Optional
from app.core.config import llm, EvaluateAgent
from app.models.BaseAction import BaseAction, event
from DCLSAgents.prompts.results_evaluation_prompts import Evaluate_SYSTEM_PROMPT
from app.knowledge.chapter_missions import CHAPTER_6_MISSION
from app.utils.xwl_parser import parse_xwl
from app.utils.xwl_actions import apply_xwl_to_step_template

class WorkflowInitialization(BaseAction):
    """
    Section 1: Workflow Initialization for Chapter 6

    Purpose:
    - Present chapter mission through Evaluate Agent
    - Initialize stability validation workflow
    - Agent outputs XML tags that are parsed into action flow
    """

    def __init__(self, step: Dict[str, Any], state: Optional[Dict[str, Any]] = None, stream: bool = False):
        super().__init__(
            step,
            state,
            stream,
            chapter_id="chapter_6_stability_validation",
            section_id="section_1_workflow_initialization",
            name="Workflow Initialization",
            ability="Initialize Stability Validation workflow using Evaluate Agent",
            require_variables=["problem_description", "csv_file_path"]
        )

    @event("start")
    def start(self):
        """Use Evaluate Agent to present mission and initialize workflow"""

        # Get required parameters for EvaluateAgent
        problem_description = self.input.get("problem_description", "")
        context_description = self.input.get("context_description", "")
        best_five_result = self.get_variable("model_results", "") or self.get_variable("best_five_result", "")

        # Create Evaluate Agent with required parameters
        evaluate_agent = EvaluateAgent(
            problem_description=problem_description,
            context_description=context_description,
            best_five_result=best_five_result,
            llm=llm
        )

        # Override system prompt with Chapter 6 mission
        evaluate_agent.system_prompt = Evaluate_SYSTEM_PROMPT(
            mission_description=CHAPTER_6_MISSION,
            problem_description=problem_description,
            context_description=context_description,
            current_workflow="",
            current_sections="",
            current_section="Workflow Initialization",
            current_goal="Present chapter mission and initialize stability validation workflow",
            observations=best_five_result
        )

        # Prepare task description
        csv_file_path = self.get_full_csv_path()
        task_description = f"""
You are starting Chapter 6: Stability Validation.

Your tasks:
1. Present the chapter mission and goals to the user
2. Initialize the stability validation workflow
3. Prepare for systematic robustness testing

Data file path: {csv_file_path}

Based on model results from Chapter 5, explain:
- The importance of stability validation
- Robustness testing approach
- Sensitivity analysis methods
- The validation framework for this chapter

Please:
- Use <add-text> to explain the chapter mission
- Use <add-text> to outline the stability validation framework
- Prepare for comprehensive robustness assessment

Begin with presenting the chapter and its importance for validating model stability.
"""

        # Agent generates XML response
        response = evaluate_agent.answer(task_description)

        # Parse XML and apply to actions
        parsed = parse_xwl(response)
        apply_xwl_to_step_template(parsed, self, self.state)

        return self.end_event()


async def stability_analysis_step0(
    step: Dict[str, Any],
    state: Optional[Dict[str, Any]] = None,
    stream: bool = False
) -> Dict[str, Any]:
    """Entry point for this section"""
    state = state or {}
    return WorkflowInitialization(step, state, stream).run()
