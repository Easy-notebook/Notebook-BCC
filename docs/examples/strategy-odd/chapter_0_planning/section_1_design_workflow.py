from typing import Dict, Any, Optional
import os
from app.models.BaseAction import BaseAction, event
from app.core.config import llm, ProblemDefinitionAndDataCollectionAgent
from DCLSAgents.prompts.pcs_prompts import PCS_SYSTEM_PROMPT
from app.utils.xwl_parser import parse_xwl
from app.utils.xwl_actions import apply_xwl_to_step_template


class DesignWorkflow(BaseAction):
    """
    Chapter 0 · Section 1 — Design Workflow

    Correct architecture:
    - Create agent with system prompt including mission/context
    - Prepare task description (based on docs) for PCS workflow planning
    - Agent outputs XWL tags (<update-title>, <add-text>, <update-workflow>, <communication>)
    - Parse XWL and convert into StepTemplate actions
    """

    def __init__(self, step: Dict[str, Any], state: Optional[Dict[str, Any]] = None, stream: bool = False):
        super().__init__(
            step,
            state,
            stream,
            chapter_id="chapter_0_planning",
            section_id="section_1_design_workflow",
            name="DesignWorkflow",
            ability="Design a customized workflow based on PCS planning principles.",
            require_variables=["problem_name", "user_goal", "problem_description", "context_description"],
        )

    @event("start")
    def start(self):
        """Plan minimal workflow using PCS prompts, robust to non-streaming XML.

        Strategy: ask for JSON (per PCS_WORKFLOW_PROMPT) and convert to actions locally.
        """
        # 1) Create agent with PCS system prompt (Chapter 0 uses PCS)
        agent = ProblemDefinitionAndDataCollectionAgent(llm=llm)
        # Available internal events for this section (none by default)
        available_events = "- (none)"
        current_todo = self.get_toDoList() or []
        to_do_list_str = "\n".join([f"- {ev}" for ev in current_todo])

        agent.system_prompt = PCS_SYSTEM_PROMPT(
            mission_description="",  # Chapter 0 planning mission kept generic
            problem_description=self.input.get("problem_description", ""),
            context_description=self.input.get("context_description", ""),
            events=available_events,
            to_do_list=to_do_list_str,
        )

        # 2) Prepare detailed task description (XWL output required per backend protocol)
        task_description = f"""
You are planning Chapter 0: Workflow Planning.

Context:
- Problem: {self.input.get('problem_description','')}
- Context: {self.input.get('context_description','')}
- User Goal: {self.input.get('user_goal','')}

Output strictly using XWL action tags only, no other text:
- <update-title>Short title including the problem name</update-title>
- <add-text>One-paragraph rationale for stage selection</add-text>
- <update-workflow>["Data Existence Establishment", "Data Integrity Assurance", ...]</update-workflow>
- <next-event>event_tag</next-event> (Optional: only when you need to continue within this step)

Rules:
- Choose the minimal stages necessary to achieve the user's goal.
- Do not overthink; avoid unnecessary stages.
- No JSON, no markdown fences, only the XWL tags listed above.
- If you need more actions within this step, emit <next-event> with an available event; otherwise, do not emit <next-event> so the step can finish.
"""

        # 3) Agent answers with XWL
        if os.environ.get("PCS_MOCK", "false").lower() == "true" or (self.state or {}).get("mock"):
            raw = (
                f"<update-title>{self.input.get('problem_name','Project')}: Workflow Planning</update-title>\n"
                "<add-text>Plan derived from user goal using PCS principles.</add-text>\n"
                "<update-workflow>[\n"
                "  \"Data Existence Establishment\",\n"
                "  \"Data Integrity Assurance\",\n"
                "  \"Data Insight Acquisition\",\n"
                "  \"Methodology Strategy Formulation\",\n"
                "  \"Model Implementation Execution\",\n"
                "  \"Stability Validation\",\n"
                "  \"Results Evaluation Confirmation\"\n"
                "]</update-workflow>\n"
            )
        else:
            raw = agent.answer(task_description)

        # 4) Parse XWL and apply actions
        parsed = parse_xwl(raw if isinstance(raw, str) else str(raw))
        apply_xwl_to_step_template(parsed, self, self.state)

        return self.end_event()


def generate_workflow(step: Dict[str, Any], state: Optional[Dict[str, Any]] = None, stream: bool = False):
    return DesignWorkflow(step, state, stream).run()
