from typing import Dict, Any, Optional
from app.core.config import llm, ProblemDefinitionAndDataCollectionAgent
from app.models.BaseAction import BaseAction, event
from DCLSAgents.prompts.problem_definition_prompts import Define_SYSTEM_PROMPT
from app.knowledge.chapter_missions import CHAPTER_1_MISSION
from app.utils.xwl_parser import parse_xwl
from app.utils.xwl_actions import apply_xwl_to_step_template

class ObservationUnitIdentification(BaseAction):
    """
    Section 4: Observation Unit Identification

    Goal (from docs):
    Clarify the observation unit and analysis granularity of the data

    Steps (from docs):
    1. Observation Unit Definition - identify basic observation units
    2. Temporal Dimension Analysis - analyze time span and frequency
    3. Spatial Dimension Analysis - identify geographic/spatial distribution
    """

    def __init__(self, step: Dict[str, Any], state: Optional[Dict[str, Any]] = None, stream: bool = False):
        super().__init__(step, state, stream,
                         chapter_id="chapter_1_data_existence_establishment",
                         section_id="section_4_observation_unit_identification",
                         name="Observation Unit Identification",
                         ability="Identify observation units using Define Agent",
                         require_variables=["csv_file_path", "problem_description"])

    @event("start")
    def start(self):
        """Use Define Agent to identify observation units"""

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
            current_section="Observation Unit Identification",
            current_goal="Clarify observation units and analysis granularity",
            observations=self.get_variable("variable_semantic_analysis", ""),
            to_do_list=to_do_list_str
        )

        # Prepare task description following docs
        csv_file_path = self.get_full_csv_path()
        task_description = f"""
You are performing Section 4: Observation Unit Identification.

## Your Objectives (from VDS principles):

### 1. Observation Unit Definition
- Identify the basic observation units in the data (individuals, events, time points, etc.)
- Determine unique identifiers for observation units
- Analyze representativeness and completeness of observation units

### 2. Temporal Dimension Analysis
- Identify data time span and collection frequency
- Analyze continuity and consistency of time series
- Evaluate time-related biases and limitations

### 3. Spatial Dimension Analysis
- Identify geographic or spatial distribution of data
- Analyze uniformity and representativeness of spatial sampling
- Evaluate spatial-related biases and limitations

## Available Tools:
Use `vdstools` for analysis:
- `EDAToolkit().basic_data_audit(file_path)` - includes observation unit info
- `EDAToolkit().temporal_analysis(file_path)` - temporal dimension analysis (if applicable)
- `EDAToolkit().spatial_analysis(file_path)` - spatial dimension analysis (if applicable)
- `DataPreview(file_path).column_list()` - check for ID columns

## Data File:
{csv_file_path}

## Previous Analysis:
You have access to variable semantic analysis from Section 3.

## Instructions:
1. Use <add-text> to explain your observation unit identification approach
2. Use <add-code2run> to examine data structure and identify observation units
3. Use <add-code2run> for temporal analysis if time-related variables exist
4. Use <add-code2run> for spatial analysis if location-related variables exist
5. After analysis, use <add-text> to provide:
   - Clear definition of observation unit(s)
   - Temporal dimension findings (if applicable)
   - Spatial dimension findings (if applicable)
   - Assessment of representativeness and completeness
6. Be systematic and thorough

Start by examining the data structure to identify observation units.
"""

        # Agent generates XML response
        response = define_agent.answer(task_description)

        # Parse XML and apply to actions
        parsed = parse_xwl(response)
        apply_xwl_to_step_template(parsed, self, self.state)

        return self.end_event()


def generate_data_loading_and_hypothesis_proposal_step_3(
    step: Dict[str, Any],
    state: Optional[Dict[str, Any]] = None,
    stream: bool = False
) -> Dict[str, Any]:
    state = state or {}
    return ObservationUnitIdentification(step, state, stream).run()
