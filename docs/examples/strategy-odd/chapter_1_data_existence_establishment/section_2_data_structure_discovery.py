from typing import Dict, Any, Optional
from app.models.BaseAction import BaseAction, event
from app.core.config import llm, ProblemDefinitionAndDataCollectionAgent
from DCLSAgents.prompts.problem_definition_prompts import Define_SYSTEM_PROMPT
from app.knowledge.chapter_missions import CHAPTER_1_MISSION
from app.utils.xwl_parser import parse_xwl
from app.utils.xwl_actions import apply_xwl_to_step_template

class DataStructureDiscovery(BaseAction):
    """
    Section 2: Data Structure Discovery

    Goal (from docs):
    Deeply understand the internal structure and organization of the data

    Steps (from docs):
    1. Data Pattern Recognition - analyze hierarchical structure and relationships
    2. Data Type Analysis - determine data types for each variable
    3. Data Distribution Exploration - calculate basic statistics and identify distributions

    Implementation:
    - Define Agent receives mission and task
    - Outputs XML tags: <add-text>, <add-code2run>, etc.
    - XML is parsed into action flow
    """

    def __init__(self, step: Dict[str, Any], state: Optional[Dict[str, Any]] = None, stream: bool = False):
        super().__init__(step, state, stream,
                         chapter_id="chapter_1_data_existence_establishment",
                         section_id="section_2_data_structure_discovery",
                         name="Data Structure Discovery",
                         ability="Discover and analyze data structure using Define Agent",
                         require_variables=["csv_file_path", "problem_description"])

    @event("start")
    def start(self):
        """Use Define Agent to perform systematic data structure discovery"""

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
            current_section="Data Structure Discovery",
            current_goal="Analyze data patterns, types, and distributions",
            observations=self.get_variable("data_collection_report", ""),
            to_do_list=to_do_list_str
        )

        # Prepare comprehensive task description following docs
        csv_file_path = self.get_full_csv_path()
        task_description = f"""
You are performing Section 2: Data Structure Discovery.

## Your Objectives (from VDS principles):

### 1. Data Pattern Recognition
- Analyze the hierarchical structure and relationships in the data
- Identify potential primary keys, foreign keys, and index fields
- Discover relationships between different data columns

### 2. Data Type Analysis
- Categorize each variable's data type (numeric, categorical, text, datetime, etc.)
- Identify mixed data types and abnormal formats
- Evaluate necessity of data type conversions

### 3. Data Distribution Exploration
- Calculate and interpret basic statistical indicators (mean, std, quantiles)
- Identify distribution characteristics (normal, skewed, multimodal)
- Discover outliers and extreme value patterns

## Available Tools:
Use `vdstools` for data analysis:
- `DataPreview(file_path).column_list()` - get columns
- `DataPreview(file_path).top5line()` - preview data
- `EDAToolkit().data_type_analysis(file_path)` - analyze types
- `EDAToolkit().statistical_summary(file_path)` - get statistics
- `EDAToolkit().correlation_analysis(file_path)` - analyze correlations

## Data File:
{csv_file_path}

## Instructions:
1. Use <add-text> to explain what you're doing
2. Use <add-code2run> to generate VDS tool code for data collection
3. After collecting data, use <add-text> to provide structured analysis covering all 3 objectives above
4. Be systematic and thorough following VDS principles

Start by collecting comprehensive data structure information.
"""

        # Agent generates XML response
        response = define_agent.answer(task_description)

        # Parse XML and apply to actions
        parsed = parse_xwl(response)
        apply_xwl_to_step_template(parsed, self, self.state)

        return self.end_event()


def generate_data_loading_and_hypothesis_proposal_step_1(
    step: Dict[str, Any],
    state: Optional[Dict[str, Any]] = None,
    stream: bool = False
) -> Dict[str, Any]:
    state = state or {}
    return DataStructureDiscovery(step, state, stream).run()
