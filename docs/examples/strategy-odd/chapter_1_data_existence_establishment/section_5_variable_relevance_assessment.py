from typing import Dict, Any, Optional
from app.core.config import llm, ProblemDefinitionAndDataCollectionAgent
from app.models.BaseAction import BaseAction, event
from DCLSAgents.prompts.problem_definition_prompts import Define_SYSTEM_PROMPT
from app.knowledge.chapter_missions import CHAPTER_1_MISSION
from app.utils.xwl_parser import parse_xwl
from app.utils.xwl_actions import apply_xwl_to_step_template

class VariableRelevanceAssessment(BaseAction):
    """
    Section 5: Variable Relevance Assessment

    Goal (from docs):
    Assess the relevance and importance of variables to project objectives

    Steps (from docs):
    1. Target Variable Correlation Analysis - analyze correlation with target variables
    2. Feature Importance Initial Assessment - evaluate variable importance statistically
    3. Business Logic Validation - verify statistical correlations align with business logic
    """

    def __init__(self, step: Dict[str, Any], state: Optional[Dict[str, Any]] = None, stream: bool = False):
        super().__init__(step, state, stream,
                         chapter_id="chapter_1_data_existence_establishment",
                         section_id="section_5_variable_relevance_assessment",
                         name="Variable Relevance Assessment",
                         ability="Assess variable relevance using Define Agent",
                         require_variables=["csv_file_path", "problem_description"])

    @event("start")
    def start(self):
        """Use Define Agent to assess variable relevance and importance"""

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
            current_section="Variable Relevance Assessment",
            current_goal="Assess relevance and importance of variables to project objectives",
            observations=self.get_variable("observation_unit_analysis", ""),
            to_do_list=to_do_list_str
        )

        # Prepare task description following docs
        csv_file_path = self.get_full_csv_path()
        task_description = f"""
You are performing Section 5: Variable Relevance Assessment.

## Your Objectives (from VDS principles):

### 1. Target Variable Correlation Analysis
- Analyze correlation between each variable and target variable(s)
- Identify potentially predictive variables
- Assess multicollinearity among variables
- Calculate correlation matrices and coefficients

### 2. Feature Importance Initial Assessment
- Use statistical methods to evaluate variable importance
- Identify redundant and irrelevant variables
- Establish variable priority ranking
- Consider both univariate and multivariate relationships

### 3. Business Logic Validation
- Verify alignment between statistical correlations and business logic
- Identify spurious correlations and causation confusion
- Obtain domain expert confirmation on variable importance
- Document any conflicts between statistics and domain knowledge

## Available Tools:
Use `vdstools` for analysis:
- `EDAToolkit().correlation_analysis(file_path)` - correlation matrix and analysis
- `EDAToolkit().target_correlation(file_path, target_col)` - correlation with target
- `EDAToolkit().feature_importance_initial(file_path, target_col)` - initial importance ranking
- `EDAToolkit().multicollinearity_check(file_path)` - check for multicollinearity

## Data File:
{csv_file_path}

## Previous Analysis:
You have access to observation unit analysis from Section 4.

## Instructions:
1. Use <add-text> to explain your variable relevance assessment approach
2. Use <add-code2run> to perform correlation analysis
3. Use <add-code2run> to assess feature importance (if target variable is identified)
4. Use <add-code2run> to check for multicollinearity
5. After analysis, use <add-text> to provide:
   - Key findings on variable-target correlations
   - Feature importance rankings
   - Multicollinearity issues (if any)
   - Business logic validation insights
   - Recommendations for variable selection
6. Be thorough and focus on project objectives

Start by analyzing correlations between variables and the target.
"""

        # Agent generates XML response
        response = define_agent.answer(task_description)

        # Parse XML and apply to actions
        parsed = parse_xwl(response)
        apply_xwl_to_step_template(parsed, self, self.state)

        return self.end_event()


def generate_data_loading_and_hypothesis_proposal_step_4(
    step: Dict[str, Any],
    state: Optional[Dict[str, Any]] = None,
    stream: bool = False
) -> Dict[str, Any]:
    state = state or {}
    return VariableRelevanceAssessment(step, state, stream).run()
