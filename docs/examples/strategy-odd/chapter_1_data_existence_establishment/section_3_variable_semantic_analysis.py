from typing import Dict, Any, Optional
from app.core.config import llm, ProblemDefinitionAndDataCollectionAgent
from app.models.BaseAction import BaseAction, event
from DCLSAgents.prompts.problem_definition_prompts import Define_SYSTEM_PROMPT
from app.knowledge.chapter_missions import CHAPTER_1_MISSION
from app.utils.xwl_parser import parse_xwl
from app.utils.xwl_actions import apply_xwl_to_step_template

class VariableSemanticAnalysis(BaseAction):
    """
    Section 3: Variable Semantic Analysis

    Goal (from docs):
    Understand the business meaning and actual significance of each variable

    Steps (from docs):
    1. Variable Semantic Mapping - map variable n to business concepts
    2. Variable Quality Assessment - evaluate variable value rationality
    3. Domain Knowledge Verification - confirm variable interpretation with domain experts
    """

    def __init__(self, step: Dict[str, Any], state: Optional[Dict[str, Any]] = None, stream: bool = False):
        super().__init__(step, state, stream,
                         chapter_id="chapter_1_data_existence_establishment",
                         section_id="section_3_variable_semantic_analysis",
                         name="Variable Semantic Analysis",
                         ability="Analyze variable semantics using Define Agent",
                         require_variables=["csv_file_path", "problem_description"])

    @event("start")
    def start(self):
        """Use Define Agent to perform variable semantic analysis"""

        # Create Define Agent with Chapter 1 mission
        define_agent = ProblemDefinitionAndDataCollectionAgent(llm=llm)
        current_todo = self.get_toDoList() or []
        to_do_list_str = "\n".join([f"- {ev}" for ev in current_todo])
        define_agent.system_prompt = Define_SYSTEM_PROMPT(
            mission_description=CHAPTER_1_MISSION,
            problem_description=self.input.get("problem_description", ""),
            context_description=self.input.get("context_description", ""),
            current_workflow="",
            current_sections="",
            current_section="Variable Semantic Analysis",
            current_goal="Understand business meaning and significance of each variable",
            observations=self.get_variable("data_structure_analysis", ""),
            to_do_list=to_do_list_str
        )

        # Prepare task description following docs
        csv_file_path = self.get_full_csv_path()
        task_description = f"""
You are performing Section 3: Variable Semantic Analysis.

## Your Objectives (from VDS principles):

### 1. Variable Semantic Mapping
- Establish correspondence between variable n and business concepts
- Identify measurement units and scales for each variable
- Understand business context and usage scenarios for variables

### 2. Variable Quality Assessment
- Evaluate rationality and validity of variable values
- Identify possible encoding errors or data entry issues
- Verify reasonableness of variable value ranges

### 3. Domain Knowledge Verification
- Confirm accuracy of variable interpretations
- Get expert opinions on variable importance
- Understand business logic relationships between variables

## Available Tools:
Use `vdstools` for analysis:
- `EDAToolkit().data_type_analysis(file_path)` - analyze data types
- `EDAToolkit().data_quality_report(file_path)` - quality assessment
- `EDAToolkit().basic_data_audit(file_path)` - basic audit

## Data File:
{csv_file_path}

## Previous Analysis:
You have access to data structure analysis results from Section 2.

## Instructions:
1. Use <add-text> to explain the semantic analysis approach
2. Use <add-code2run> to collect variable information using VDS tools
3. After collecting data, use <add-text> to provide:
   - Semantic mapping for key variables
   - Quality assessment findings
   - Domain knowledge insights
4. Be thorough and business-focused

Start by collecting comprehensive variable information.
"""

        # Agent generates XML response
        response = define_agent.answer(task_description)

        # Parse XML and apply to actions
        parsed = parse_xwl(response)
        apply_xwl_to_step_template(parsed, self, self.state)

        return self.end_event()


def generate_data_loading_and_hypothesis_proposal_step_2(
    step: Dict[str, Any],
    state: Optional[Dict[str, Any]] = None,
    stream: bool = False
) -> Dict[str, Any]:
    state = state or {}
    return VariableSemanticAnalysis(step, state, stream).run()
