from typing import Dict, Any, Optional
from app.core.config import llm, ExploreAgent
from app.models.BaseAction import BaseAction, event
from DCLSAgents.prompts.data_cleaning_prompts import Explore_SYSTEM_PROMPT
from app.knowledge.chapter_missions import CHAPTER_3_MISSION
from app.utils.xwl_parser import parse_xwl
from app.utils.xwl_actions import apply_xwl_to_step_template

class WorkflowInitialization(BaseAction):
    """
    Section 1: Workflow Initialization for Chapter 3

    Purpose:
    - Present chapter mission through Explore Agent
    - Initialize exploratory data analysis foundation
    - Agent outputs XML tags that are parsed into action flow
    """

    def __init__(self, step: Dict[str, Any], state: Optional[Dict[str, Any]] = None, stream: bool = False):
        super().__init__(
            step,
            state,
            stream,
            chapter_id="chapter_3_data_insight_acquisition",
            section_id="section_1_workflow_initialization",
            name="Workflow Initialization",
            ability="Initialize Data Insight Acquisition workflow using Explore Agent",
            require_variables=["problem_description", "csv_file_path"]
        )

    @event("start")
    def start(self):
        """Use Explore Agent to present mission and initialize workflow"""

        # Create Explore Agent with Chapter 3 mission
        explore_agent = ExploreAgent(llm=llm)
        current_todo = self.get_toDoList() or []
        to_do_list_str = "\n".join([f"- {ev}" for ev in current_todo])
        explore_agent.system_prompt = Explore_SYSTEM_PROMPT(
            mission_description=CHAPTER_3_MISSION,
            problem_description=self.input.get("problem_description", ""),
            context_description=self.input.get("context_description", ""),
            current_workflow="",
            current_sections="",
            current_section="Workflow Initialization",
            current_goal="Present chapter mission and initialize exploratory data analysis strategy",
            observations=self.get_variable("data_integrity_report", ""),
            to_do_list=to_do_list_str
        )

        # Prepare task description
        csv_file_path = self.get_full_csv_path()
        task_description = f"""
You are starting Chapter 3: Data Insight Acquisition.

Your tasks:
1. Present the chapter mission and goals to the user
2. Initialize the exploratory data analysis (EDA) strategy
3. Create initial descriptive statistics using VDS tools

Data file path: {csv_file_path}

Based on clean data from Chapter 2, explain:
- The importance of exploratory data analysis
- Key patterns and relationships to discover
- The systematic EDA approach for this chapter

Please:
- Use <add-text> to explain the chapter mission
- Use <add-code2run> to create initial descriptive statistics using vdstools.EDAToolkit.statistical_summary()
- Store results appropriately

Begin with presenting the chapter and its importance for discovering data insights.
"""

        # Agent generates XML response
        response = explore_agent.answer(task_description)

        # Parse XML and apply to actions
        parsed = parse_xwl(response)
        apply_xwl_to_step_template(parsed, self, self.state)

        return self.end_event()


def generate_exploratory_data_sequence_step0(
    step: Dict[str, Any],
    state: Optional[Dict[str, Any]] = None,
    stream: bool = False
) -> Dict[str, Any]:
    """Entry point for this section"""
    state = state or {}
    return WorkflowInitialization(step, state, stream).run()
