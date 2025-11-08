from typing import Dict, Any, Optional
from app.core.config import llm, PCSAgent
from app.models.BaseAction import BaseAction, event
from DCLSAgents.prompts.pcs_prompts import PCS_SYSTEM_PROMPT
from app.knowledge.chapter_missions import CHAPTER_1_MISSION
from app.utils.xwl_parser import parse_xwl
from app.utils.xwl_actions import apply_xwl_to_step_template

class PCSHypothesisGeneration(BaseAction):
    """
    Section 6: PCS Hypothesis Generation

    Goal (from docs):
    Generate testable hypotheses based on the PCS framework

    Steps (from docs):
    1. Predictability Hypothesis - generate predictive hypotheses based on variable correlations
    2. Stability Hypothesis - identify factors affecting result stability
    """

    def __init__(self, step: Dict[str, Any], state: Optional[Dict[str, Any]] = None, stream: bool = False):
        super().__init__(step, state, stream,
                         chapter_id="chapter_1_data_existence_establishment",
                         section_id="section_6_pcs_hypothesis_generation",
                         name="PCS Hypothesis Generation",
                         ability="Generate PCS hypotheses using PCS Agent",
                         require_variables=["csv_file_path", "problem_description"])

    @event("start")
    def start(self):
        """Use PCS Agent to generate PCS framework hypotheses"""

        # Create PCS Agent with Chapter 1 mission
        problem_description = self.input.get("problem_description", "")
        context_description = self.input.get("context_description", "")

        pcs_agent = PCSAgent(
            problem_description=problem_description,
            context_description=context_description,
            llm=llm
        )

        # Set system prompt with CHAPTER_1_MISSION
        current_todo = self.get_toDoList() or []
        to_do_list_str = "\n".join([f"- {ev}" for ev in current_todo])
        pcs_agent.system_prompt = PCS_SYSTEM_PROMPT(
            mission_description=CHAPTER_1_MISSION,
            problem_description=problem_description,
            context_description=context_description,
            sections="",
            observations=self.get_variable("variable_relevance_analysis", ""),
            to_do_list=to_do_list_str
        )

        # Prepare task description following docs
        csv_file_path = self.get_full_csv_path()
        task_description = f"""
You are performing Section 6: PCS Hypothesis Generation.

## Your Objectives (from VDS principles):

### 1. Predictability Hypothesis Generation
- Based on variable correlation analysis, generate predictive hypotheses
- Design experimental plans for hypothesis validation
- Identify key factors affecting predictability
- Formulate specific, testable predictions

### 2. Stability Hypothesis Generation
- Identify factors that may affect result stability
- Design sensitivity analysis test plans
- Plan data perturbation experiments
- Formulate robustness expectations

## Context from Previous Analysis:
You have access to all previous analysis results:
- Variable semantic analysis
- Observation unit identification
- Variable relevance assessment

## Data File:
{csv_file_path}

## PCS Framework Focus:
Based on the analysis so far, generate concrete hypotheses for:
- **Predictability**: Which variables/patterns can reliably predict outcomes?
- **Computability**: What computational requirements exist for validation?
- **Stability**: How robust will results be to data variations?

## Instructions:
1. Use <add-text> to explain the PCS hypothesis generation approach
2. Use <add-text> to present **Predictability Hypotheses**:
   - List specific predictive hypotheses
   - Identify key predictive variables
   - Describe validation experiments
3. Use <add-text> to present **Stability Hypotheses**:
   - Identify stability risk factors
   - Propose sensitivity tests
   - Define robustness criteria
4. Use <add-text> to present **Computability Assessment**:
   - Computational feasibility
   - Resource requirements
   - Implementation constraints
5. Summarize the complete PCS hypothesis framework

Begin by synthesizing insights from all previous sections.
"""

        # Agent generates XML response
        response = pcs_agent.answer(task_description)

        # Parse XML and apply to actions
        parsed = parse_xwl(response)
        apply_xwl_to_step_template(parsed, self, self.state)

        return self.end_event()


def generate_data_loading_and_hypothesis_proposal_step_5(
    step: Dict[str, Any],
    state: Optional[Dict[str, Any]] = None,
    stream: bool = False
) -> Dict[str, Any]:
    state = state or {}
    return PCSHypothesisGeneration(step, state, stream).run()
