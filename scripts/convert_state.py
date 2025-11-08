"""
State Conversion Script
Converts IDLE state + Planning API XML response → STAGE_RUNNING state
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.response_parser import response_parser
from utils.workflow_updater import workflow_updater
from core.state_machine import WorkflowStateMachine
from stores.pipeline_store import PipelineStore
from stores.ai_context_store import AIPlanningContextStore


def convert_state(idle_state_path: str, xml_response_path: str, output_path: str = None):
    """
    Convert IDLE state to STAGE_RUNNING using Planning API XML response.

    Args:
        idle_state_path: Path to IDLE state JSON
        xml_response_path: Path to Planning API XML response
        output_path: Optional output path for converted state
    """
    print("=" * 80)
    print("State Conversion: IDLE → STAGE_RUNNING")
    print("=" * 80)

    # Load initial state
    print(f"\n📖 Loading IDLE state: {idle_state_path}")
    with open(idle_state_path, 'r', encoding='utf-8') as f:
        idle_state = json.load(f)
    print(f"   ✓ FSM state: {idle_state['state']['FSM']['state']}")

    # Load XML response
    print(f"\n📖 Loading Planning API XML response: {xml_response_path}")
    with open(xml_response_path, 'r', encoding='utf-8') as f:
        xml_response = f.read()
    print(f"   ✓ XML loaded ({len(xml_response)} chars)")

    # Parse XML
    print(f"\n🔍 Parsing XML response...")
    parsed_response = response_parser.parse_response(xml_response)
    print(f"   ✓ Response type: {parsed_response['type']}")

    if parsed_response['type'] == 'stages':
        stages = parsed_response['content']['stages']
        print(f"   ✓ Found {len(stages)} stages")
        for i, stage in enumerate(stages, 1):
            print(f"      {i}. {stage['stage_id']}: {stage['title']}")

    # Create state machine
    print(f"\n⚙️  Initializing state machine...")
    pipeline_store = PipelineStore()
    ai_context_store = AIPlanningContextStore()
    state_machine = WorkflowStateMachine(
        pipeline_store=pipeline_store,
        ai_context_store=ai_context_store
    )

    # Initialize variables from IDLE state
    variables = idle_state['state']['variables']
    for key, value in variables.items():
        ai_context_store.add_variable(key, value)
    print(f"   ✓ Variables initialized: {list(variables.keys())}")

    # Apply workflow updates
    print(f"\n🔄 Applying workflow updates...")
    workflow_updater.update_from_response(state_machine, parsed_response)

    # Get updated progress info
    progress_info = state_machine.get_progress_info()
    ctx = state_machine.execution_context.workflow_context

    print(f"   ✓ Current stage: {ctx.current_stage_id}")
    print(f"   ✓ Stages focus: {len(progress_info['progress']['stages'].get('focus', ''))} chars")

    # Build final state with correct format
    print(f"\n📝 Building STAGE_RUNNING state...")

    # Build proper progress structure from parsed XML data
    all_stages_data = parsed_response['content']['stages']

    # Find current stage index
    current_stage_idx = next((i for i, s in enumerate(all_stages_data) if s['stage_id'] == ctx.current_stage_id), 0)
    current_stage_data = all_stages_data[current_stage_idx] if current_stage_idx < len(all_stages_data) else None

    # Build stages progress with full objects from XML
    stages_progress = {
        "completed": [],
        "current": current_stage_data,
        "remaining": all_stages_data[current_stage_idx + 1:],
        "focus": parsed_response['content'].get('focus', ''),
        "current_outputs": {
            "expected": [],
            "produced": [],
            "in_progress": []
        }
    }

    # Build full progress structure
    full_progress = {
        "stages": stages_progress,
        "steps": {
            "completed": [],
            "current": None,
            "remaining": [],
            "focus": "",
            "current_outputs": {
                "expected": [],
                "produced": [],
                "in_progress": []
            }
        },
        "behaviors": {
            "completed": [],
            "current": None,
            "iteration": None,
            "focus": "",
            "current_outputs": {
                "expected": [],
                "produced": [],
                "in_progress": []
            }
        }
    }

    # Build goals string
    stage_info = stages_progress['current']
    goals_text = f"The user proposed the problem '{variables.get('user_problem', '')},' and uploaded the file '{variables.get('user_submit_files', [''])[0]}'. The workflow now follows an 8-stage PCS-compliant data science lifecycle: (1) Data Existence Establishment, (2) Data Integrity Assurance, (3) Exploratory Data Analysis, (4) Methodology Strategy Formulation, (5) Model Implementation Execution, (6) Predictability Validation, (7) Stability Assessment, (8) Results Communication. The current stage is '{ctx.current_stage_id},' with the goal of verifying data availability, understanding structure, analyzing variable relevance, and generating PCS testable hypotheses."

    converted_state = {
        "observation": {
            "location": {
                "current": {
                    "stage_id": ctx.current_stage_id,
                    "step_id": ctx.current_step_id,
                    "behavior_id": ctx.current_behavior_id,
                    "behavior_iteration": ctx.behavior_iteration
                },
                "progress": full_progress,
                "goals": goals_text
            }
        },
        "state": {
            "variables": ai_context_store.get_context().variables,
            "effects": ai_context_store.get_context().effect,
            "notebook": {
                "title": None,
                "cell_count": 0,
                "last_cell_type": None,
                "last_output": None
            },
            "FSM": {
                "state": "STAGE_RUNNING",
                "last_transition": "START_WORKFLOW",
                "timestamp": datetime.now().isoformat() + "Z"
            }
        }
    }

    print(f"   ✓ State built successfully")

    # Output result
    if output_path:
        print(f"\n💾 Saving to: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(converted_state, f, indent=2, ensure_ascii=False)
        print(f"   ✓ Saved successfully")
    else:
        print(f"\n📄 Converted State (JSON):")
        print(json.dumps(converted_state, indent=2, ensure_ascii=False))

    # Summary
    print(f"\n" + "=" * 80)
    print("✅ Conversion Summary:")
    print("=" * 80)
    print(f"Initial State:      IDLE")
    print(f"Final State:        STAGE_RUNNING")
    print(f"Current Stage:      {ctx.current_stage_id}")
    print(f"Total Stages:       {len(parsed_response['content']['stages'])}")
    print(f"Variables:          {len(converted_state['state']['variables'])}")
    print(f"Timestamp:          {converted_state['state']['FSM']['timestamp']}")
    print("=" * 80)

    return converted_state


if __name__ == "__main__":
    idle_state_path = "./docs/examples/ames_housing/payloads/00_STATE_IDLE.json"
    xml_response_path = "./docs/examples/ames_housing/payloads/00_Transition_planning_START_WORKFLOW.xml"
    output_path = "./docs/examples/ames_housing/payloads/01_STATE_Stage_Running_CONVERTED.json"

    try:
        converted_state = convert_state(idle_state_path, xml_response_path, output_path)
        print(f"\n✨ Conversion completed successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
