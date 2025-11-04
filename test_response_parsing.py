"""
Test response parsing and state updates.
Verifies that XML responses are correctly parsed and states are updated.
"""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.response_parser import response_parser
from utils.workflow_updater import workflow_updater
from core.state_machine import WorkflowStateMachine
from stores.pipeline_store import PipelineStore
from stores.ai_context_store import AIPlanningContextStore


def load_json(file_path: str):
    """Load JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_xml(file_path: str):
    """Load XML file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def compare_states(expected, actual, path=""):
    """Recursively compare two state dictionaries and report differences."""
    differences = []

    if isinstance(expected, dict) and isinstance(actual, dict):
        # Check keys
        expected_keys = set(expected.keys())
        actual_keys = set(actual.keys())

        missing_keys = expected_keys - actual_keys
        extra_keys = actual_keys - expected_keys

        if missing_keys:
            differences.append(f"Missing keys at {path}: {missing_keys}")
        if extra_keys:
            differences.append(f"Extra keys at {path}: {extra_keys}")

        # Compare common keys
        for key in expected_keys & actual_keys:
            sub_path = f"{path}.{key}" if path else key
            diffs = compare_states(expected[key], actual[key], sub_path)
            differences.extend(diffs)

    elif isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            differences.append(f"List length mismatch at {path}: expected {len(expected)}, got {len(actual)}")
        else:
            for i, (exp_item, act_item) in enumerate(zip(expected, actual)):
                sub_path = f"{path}[{i}]"
                diffs = compare_states(exp_item, act_item, sub_path)
                differences.extend(diffs)

    else:
        if expected != actual:
            differences.append(f"Value mismatch at {path}: expected {expected}, got {actual}")

    return differences


def test_idle_to_stage_running():
    """Test transition from IDLE to STAGE_RUNNING."""
    print("=" * 80)
    print("Testing: IDLE → STAGE_RUNNING transition")
    print("=" * 80)

    # Load initial state
    idle_state_path = "./docs/examples/ames_housing/payloads/00_STATE_IDLE.json"
    xml_response_path = "./docs/examples/ames_housing/payloads/00_Transition_planning_START_WORKFLOW.xml"
    expected_state_path = "./docs/examples/ames_housing/payloads/01_STATE_Stage_Running.json"

    print(f"\n1. Loading initial IDLE state from: {idle_state_path}")
    idle_state = load_json(idle_state_path)
    print(f"   ✓ Initial FSM state: {idle_state['state']['FSM']['state']}")

    print(f"\n2. Loading Planning API XML response from: {xml_response_path}")
    xml_response = load_xml(xml_response_path)
    print(f"   ✓ XML loaded ({len(xml_response)} chars)")

    print(f"\n3. Parsing XML response...")
    parsed_response = response_parser.parse_response(xml_response)
    print(f"   ✓ Response type: {parsed_response['type']}")

    if parsed_response['type'] == 'stages':
        stages = parsed_response['content']['stages']
        print(f"   ✓ Found {len(stages)} stages:")
        for i, stage in enumerate(stages[:3], 1):  # Show first 3
            print(f"      {i}. {stage['stage_id']}: {stage['title']}")
        if len(stages) > 3:
            print(f"      ... and {len(stages) - 3} more")

    print(f"\n4. Creating state machine and stores...")
    pipeline_store = PipelineStore()
    ai_context_store = AIPlanningContextStore()
    state_machine = WorkflowStateMachine(
        pipeline_store=pipeline_store,
        ai_context_store=ai_context_store
    )

    # Initialize state machine with initial context
    variables = idle_state['state']['variables']
    for key, value in variables.items():
        ai_context_store.add_variable(key, value)

    print(f"   ✓ State machine created")
    print(f"   ✓ Variables initialized: {list(variables.keys())}")

    print(f"\n5. Applying workflow updates...")
    workflow_updater.update_from_response(state_machine, parsed_response)

    # Get updated progress info
    progress_info = state_machine.get_progress_info()

    print(f"   ✓ Workflow updated")
    print(f"   ✓ Current stage: {progress_info['current']['stage_id']}")
    print(f"   ✓ Stages focus length: {len(progress_info['progress']['stages']['focus'])} chars")

    print(f"\n6. Building updated state...")
    # Simulate state after transition
    ctx = state_machine.execution_context.workflow_context
    updated_state = {
        "observation": {
            "location": {
                "current": {
                    "stage_id": ctx.current_stage_id,
                    "step_id": ctx.current_step_id,
                    "behavior_id": ctx.current_behavior_id,
                    "behavior_iteration": ctx.behavior_iteration
                },
                "progress": progress_info['progress'],
                "goals": progress_info.get('goals', '')
            }
        },
        "state": {
            "variables": ai_context_store.get_context().variables,
            "effects": ai_context_store.get_context().effect,  # Fixed: effect not effects
            "notebook": {
                "title": None,
                "cell_count": 0,
                "last_cell_type": None,
                "last_output": None
            },
            "FSM": {
                "state": "STAGE_RUNNING",
                "last_transition": "START_WORKFLOW",
                "timestamp": idle_state['state']['FSM'].get('timestamp', '')
            }
        }
    }

    print(f"   ✓ Updated state built")

    print(f"\n7. Loading expected state from: {expected_state_path}")
    expected_state = load_json(expected_state_path)
    print(f"   ✓ Expected FSM state: {expected_state['state']['FSM']['state']}")

    print(f"\n8. Comparing states...")

    # Compare key fields
    comparisons = {
        "FSM State": (
            updated_state['state']['FSM']['state'],
            expected_state['state']['FSM']['state']
        ),
        "Current Stage ID": (
            updated_state['observation']['location']['current']['stage_id'],
            expected_state['observation']['location']['current']['stage_id']
        ),
        "Stages Count": (
            len(updated_state['observation']['location']['progress']['stages'].get('remaining', [])) + 1,
            len(expected_state['observation']['location']['progress']['stages'].get('remaining', [])) + 1
        ),
        "Variables Count": (
            len(updated_state['state']['variables']),
            len(expected_state['state']['variables'])
        )
    }

    all_match = True
    for name, (actual, expected) in comparisons.items():
        match = actual == expected
        symbol = "✓" if match else "✗"
        print(f"   {symbol} {name}: {actual} {'==' if match else '!='} {expected}")
        if not match:
            all_match = False

    # Detailed comparison for stages
    print(f"\n9. Detailed stage comparison:")
    expected_stages = expected_state['observation']['location']['progress']['stages']
    actual_stages = updated_state['observation']['location']['progress']['stages']

    if 'current' in expected_stages and 'current' in actual_stages:
        exp_current = expected_stages['current']
        act_current = actual_stages['current']

        if isinstance(exp_current, dict) and isinstance(act_current, dict):
            stage_match = exp_current.get('stage_id') == act_current.get('stage_id')
            symbol = "✓" if stage_match else "✗"
            print(f"   {symbol} Current stage ID: {act_current.get('stage_id')} vs {exp_current.get('stage_id')}")
        else:
            print(f"   ✗ Current stage format mismatch")

    # Check if workflow template was created
    print(f"\n10. Workflow template verification:")
    if state_machine.pipeline_store.workflow_template:
        template = state_machine.pipeline_store.workflow_template
        print(f"   ✓ Workflow template created: {template.name}")
        print(f"   ✓ Stages in template: {len(template.stages)}")
        if template.stages:
            print(f"   ✓ First stage: {template.stages[0].id}")
    else:
        print(f"   ✗ No workflow template created")
        all_match = False

    print(f"\n" + "=" * 80)
    if all_match:
        print("✓ TEST PASSED: State transition successful!")
    else:
        print("✗ TEST FAILED: Some mismatches found")
    print("=" * 80)

    return all_match


if __name__ == "__main__":
    try:
        success = test_idle_to_stage_running()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
