from typing import Dict, Any, Optional
from app.core.config import llm, EvaluateAgent
from app.models.BaseAction import BaseAction, event
from DCLSAgents.prompts.results_evaluation_prompts import Evaluate_SYSTEM_PROMPT
from app.knowledge.chapter_missions import CHAPTER_7_MISSION
from app.utils.xwl_parser import parse_xwl
from app.utils.xwl_actions import apply_xwl_to_step_template

class WorkflowInitialization(BaseAction):
    """
    Section 1: Workflow Initialization for Chapter 7

    Purpose:
    - Present chapter mission through Evaluate Agent
    - Initialize results evaluation confirmation workflow
    - Agent outputs XML tags that are parsed into action flow
    """

    def __init__(self, step: Dict[str, Any], state: Optional[Dict[str, Any]] = None, stream: bool = False):
        super().__init__(
            step,
            state,
            stream,
            chapter_id="chapter_7_results_evaluation_confirmation",
            section_id="section_1_workflow_initialization",
            name="Workflow Initialization",
            ability="Initialize Results Evaluation Confirmation workflow using Evaluate Agent",
            require_variables=["problem_description", "csv_file_path"]
        )

    @event("start")
    def start(self):
        """Use Evaluate Agent to present mission and initialize workflow"""

        # Get required parameters for EvaluateAgent
        problem_description = self.input.get("problem_description", "")
        context_description = self.input.get("context_description", "")
        best_five_result = self.get_variable("stability_validation_results", "") or self.get_variable("best_five_result", "")

        # Create Evaluate Agent with required parameters
        evaluate_agent = EvaluateAgent(
            problem_description=problem_description,
            context_description=context_description,
            best_five_result=best_five_result,
            llm=llm
        )

        # Override system prompt with Chapter 7 mission
        evaluate_agent.system_prompt = Evaluate_SYSTEM_PROMPT(
            mission_description=CHAPTER_7_MISSION,
            problem_description=problem_description,
            context_description=context_description,
            current_workflow="",
            current_sections="",
            current_section="Workflow Initialization",
            current_goal="Present chapter mission and initialize results evaluation workflow",
            observations=best_five_result
        )

        # Prepare task description
        csv_file_path = self.get_full_csv_path()
        task_description = f"""
You are starting Chapter 7: Results Evaluation Confirmation.

Your tasks:
1. Present the chapter mission and goals to the user
2. Initialize the results evaluation confirmation workflow
3. Prepare for comprehensive final assessment

Data file path: {csv_file_path}

Based on stability validation from Chapter 6, explain:
- The importance of final results evaluation
- Test set validation approach
- DCLS report framework
- Business value assessment methods
- The evaluation methodology for this chapter

Please:
- Use <add-text> to explain the chapter mission
- Use <add-text> to outline the results evaluation framework
- Prepare for comprehensive final confirmation

Begin with presenting the chapter and its importance for confirming analytical results.
"""

        # Agent generates XML response
        response = evaluate_agent.answer(task_description)

        # Parse XML and apply to actions
        parsed = parse_xwl(response)
        apply_xwl_to_step_template(parsed, self, self.state)

        return self.end_event()


async def results_evaluation_step0(
    step: Dict[str, Any],
    state: Optional[Dict[str, Any]] = None,
    stream: bool = False
) -> Dict[str, Any]:
    """Entry point for this section"""
    state = state or {}
    return WorkflowInitialization(step, state, stream).run()
