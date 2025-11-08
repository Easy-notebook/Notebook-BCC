from typing import Dict, Any, Optional
from app.core.config import llm, ProblemDefinitionAndDataCollectionAgent
from app.models.BaseAction import BaseAction, event
from DCLSAgents.prompts.problem_definition_prompts import Define_SYSTEM_PROMPT
from app.knowledge.chapter_missions import CHAPTER_1_MISSION
from app.utils.xwl_parser import parse_xwl
from app.utils.xwl_actions import apply_xwl_to_step_template

class WorkflowInitialization(BaseAction):
    """
    Section 1: Workflow Initialization for Chapter 1

    Purpose:
    - Present chapter mission through Define Agent
    - Initialize data collection foundation
    - Agent outputs XML tags that are parsed into action flow
    """

    def __init__(self, step: Dict[str, Any], state: Optional[Dict[str, Any]] = None, stream: bool = False):
        super().__init__(
            step,
            state,
            stream,
            chapter_id="chapter_1_data_existence_establishment",
            section_id="section_1_workflow_initialization",
            name="Workflow Initialization",
            ability="Initialize Data Existence Establishment workflow using Define Agent",
            require_variables=["problem_description", "csv_file_path"]
        )

    @event("start")
    def start(self):
        """Use Define Agent to present mission and initialize workflow"""

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
            current_section="Workflow Initialization",
            current_goal="Present chapter mission and initialize data collection strategy",
            observations="",
            to_do_list=to_do_list_str
        )

        # Prepare task description
        csv_file_path = self.get_full_csv_path()
        task_description = f"""
You are starting Chapter 1: Data Existence Establishment.

Your tasks:
1. Present the chapter mission and goals to the user
2. Initialize the data collection strategy
3. Create initial data audit using VDS tools

Data file path: {csv_file_path}

Please:
- Use <add-text> to explain the chapter mission
- Use <add-code2run> to create initial data audit code using vdstools.EDAToolkit.basic_data_audit()
- Store results appropriately

Begin with presenting the chapter and its importance.
"""

        # Agent generates XML response
        response = define_agent.answer(task_description)

        # Parse XML and apply to actions
        parsed = parse_xwl(response)
        apply_xwl_to_step_template(parsed, self, self.state)

        return self.end_event()


def generate_data_loading_and_hypothesis_proposal_step_0(
    step: Dict[str, Any],
    state: Optional[Dict[str, Any]] = None,
    stream: bool = False
) -> Dict[str, Any]:
    """Entry point for this section"""
    state = state or {}
    return WorkflowInitialization(step, state, stream).run()
