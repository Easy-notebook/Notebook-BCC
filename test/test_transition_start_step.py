#!/usr/bin/env python3
"""
Test script to simulate START_STEP transition.

This script:
1. Loads the initial state (01_STATE_Stage_Running.json)
2. Parses the transition XML (01_Transition_planning_START_STEP.xml)
3. Simulates the workflow_updater logic
4. Generates the expected output state
5. Compares with actual 02_STATE_Step_Running.json
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any
from copy import deepcopy

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.response_parser import response_parser


def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_xml_file(file_path: str) -> str:
    """Load XML file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def simulate_workflow_update(initial_state: Dict[str, Any], parsed_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate workflow_updater logic to update state.

    Based on workflow_updater.py:_update_steps()
    """
    result_state = deepcopy(initial_state)

    response_type = parsed_response.get('type')
    content = parsed_response.get('content', {})

    print(f"\n[Simulator] Response type: {response_type}")

    if response_type != 'steps':
        print(f"[Simulator] ERROR: Expected 'steps' response, got '{response_type}'")
        return result_state

    # Extract steps data
    steps = content.get('steps', [])
    focus = content.get('focus', '')
    goals = content.get('goals', '')

    print(f"[Simulator] Processing {len(steps)} steps")
    print(f"[Simulator] Focus: {focus[:100]}...")
    print(f"[Simulator] Goals: {goals[:100]}...")

    # Update the observation section
    obs = result_state.get('observation', {})
    location = obs.get('location', {})
    progress = location.get('progress', {})
    steps_progress = progress.get('steps', {})

    # Build current step from first step
    if len(steps) > 0:
        first_step = steps[0]
        current_step = {
            'step_id': first_step.get('step_id'),
            'title': first_step.get('title', ''),
            'goal': first_step.get('goal', ''),
            'verified_artifacts': first_step.get('verified_artifacts', {}),
            'required_variables': first_step.get('required_variables', {}),
            'pcs_considerations': first_step.get('pcs_considerations', {})
        }

        # Update location.current
        location['current']['step_id'] = first_step.get('step_id')

        # Update steps progress
        steps_progress['current'] = current_step
        steps_progress['completed'] = []

        # Build remaining steps
        remaining_steps = []
        for step_data in steps[1:]:
            remaining_step = {
                'step_id': step_data.get('step_id'),
                'title': step_data.get('title', ''),
                'goal': step_data.get('goal', ''),
                'verified_artifacts': step_data.get('verified_artifacts', {}),
                'required_variables': step_data.get('required_variables', {}),
                'pcs_considerations': step_data.get('pcs_considerations', {})
            }
            remaining_steps.append(remaining_step)

        steps_progress['remaining'] = remaining_steps
        steps_progress['focus'] = focus

        # Update current_outputs for steps
        current_outputs = {
            'expected': [],
            'produced': [],
            'in_progress': []
        }

        # Add expected outputs from current step's verified_artifacts
        for artifact_name, artifact_desc in first_step.get('verified_artifacts', {}).items():
            current_outputs['expected'].append({artifact_name: artifact_desc})

        steps_progress['current_outputs'] = current_outputs

        # Update location.goals with refined goals
        if goals:
            location['goals'] = goals

        print(f"[Simulator] Set current step: {first_step.get('step_id')}")
        print(f"[Simulator] Current step title: {first_step.get('title')}")
        print(f"[Simulator] Remaining steps: {len(remaining_steps)}")

    # Update FSM state
    fsm = result_state.get('state', {}).get('FSM', {})
    fsm['state'] = 'STEP_RUNNING'
    fsm['last_transition'] = 'START_STEP'

    return result_state


def compare_states(generated: Dict[str, Any], expected: Dict[str, Any], path: str = "root") -> list:
    """
    Compare two state objects and report differences.

    Returns list of differences.
    """
    differences = []

    if type(generated) != type(expected):
        differences.append(f"{path}: Type mismatch - generated={type(generated).__name__}, expected={type(expected).__name__}")
        return differences

    if isinstance(generated, dict):
        # Check for missing keys
        gen_keys = set(generated.keys())
        exp_keys = set(expected.keys())

        missing_in_gen = exp_keys - gen_keys
        extra_in_gen = gen_keys - exp_keys

        if missing_in_gen:
            differences.append(f"{path}: Missing keys in generated: {missing_in_gen}")
        if extra_in_gen:
            differences.append(f"{path}: Extra keys in generated: {extra_in_gen}")

        # Compare common keys
        for key in gen_keys & exp_keys:
            differences.extend(compare_states(generated[key], expected[key], f"{path}.{key}"))

    elif isinstance(generated, list):
        if len(generated) != len(expected):
            differences.append(f"{path}: List length mismatch - generated={len(generated)}, expected={len(expected)}")
        else:
            for i, (gen_item, exp_item) in enumerate(zip(generated, expected)):
                differences.extend(compare_states(gen_item, exp_item, f"{path}[{i}]"))

    else:
        # Simple value comparison
        if generated != expected:
            differences.append(f"{path}: Value mismatch - generated={repr(generated)}, expected={repr(expected)}")

    return differences


def main():
    """Main test function."""
    print("=" * 80)
    print("Testing START_STEP Transition")
    print("=" * 80)

    # File paths
    base_path = Path("/Users/silan/Documents/github/Notebook-BCC/docs/examples/ames_housing/payloads")
    initial_state_path = base_path / "01_STATE_Stage_Running.json"
    xml_transition_path = base_path / "01_Transition_planning_START_STEP.xml"
    expected_state_path = base_path / "02_STATE_Step_Running.json"

    # Load files
    print("\n[1] Loading input files...")
    initial_state = load_json_file(str(initial_state_path))
    print(f"    ✓ Loaded initial state: {initial_state_path.name}")

    xml_content = load_xml_file(str(xml_transition_path))
    print(f"    ✓ Loaded XML transition: {xml_transition_path.name}")

    expected_state = load_json_file(str(expected_state_path))
    print(f"    ✓ Loaded expected state: {expected_state_path.name}")

    # Parse XML using response_parser
    print("\n[2] Parsing XML transition...")
    parsed_response = response_parser.parse_response(xml_content)
    print(f"    ✓ Parsed response type: {parsed_response.get('type')}")

    if parsed_response.get('type') == 'steps':
        steps = parsed_response.get('content', {}).get('steps', [])
        print(f"    ✓ Found {len(steps)} steps:")
        for i, step in enumerate(steps, 1):
            print(f"       {i}. {step.get('step_id')} - {step.get('title')}")

    # Simulate workflow update
    print("\n[3] Simulating workflow update...")
    generated_state = simulate_workflow_update(initial_state, parsed_response)
    print("    ✓ Generated new state")

    # Save generated state for inspection
    output_path = base_path / "02_STATE_Step_Running_GENERATED.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(generated_state, f, indent=2, ensure_ascii=False)
    print(f"    ✓ Saved generated state: {output_path.name}")

    # Compare with expected state
    print("\n[4] Comparing generated vs expected state...")
    differences = compare_states(generated_state, expected_state)

    if not differences:
        print("    ✓ ✅ PERFECT MATCH! Generated state matches expected state exactly.")
    else:
        print(f"    ⚠️  Found {len(differences)} differences:")
        for i, diff in enumerate(differences[:20], 1):  # Show first 20
            print(f"       {i}. {diff}")

        if len(differences) > 20:
            print(f"       ... and {len(differences - 20)} more differences")

    # Key comparisons
    print("\n[5] Key field comparisons:")

    # Current step ID
    gen_step_id = generated_state.get('observation', {}).get('location', {}).get('current', {}).get('step_id')
    exp_step_id = expected_state.get('observation', {}).get('location', {}).get('current', {}).get('step_id')
    match = "✓" if gen_step_id == exp_step_id else "✗"
    print(f"    {match} Current step_id:")
    print(f"       Generated: {gen_step_id}")
    print(f"       Expected:  {exp_step_id}")

    # Number of remaining steps
    gen_remaining = len(generated_state.get('observation', {}).get('location', {}).get('progress', {}).get('steps', {}).get('remaining', []))
    exp_remaining = len(expected_state.get('observation', {}).get('location', {}).get('progress', {}).get('steps', {}).get('remaining', []))
    match = "✓" if gen_remaining == exp_remaining else "✗"
    print(f"    {match} Remaining steps count:")
    print(f"       Generated: {gen_remaining}")
    print(f"       Expected:  {exp_remaining}")

    # FSM state
    gen_fsm_state = generated_state.get('state', {}).get('FSM', {}).get('state')
    exp_fsm_state = expected_state.get('state', {}).get('FSM', {}).get('state')
    match = "✓" if gen_fsm_state == exp_fsm_state else "✗"
    print(f"    {match} FSM state:")
    print(f"       Generated: {gen_fsm_state}")
    print(f"       Expected:  {exp_fsm_state}")

    # List step IDs
    print("\n[6] Step ID comparison:")
    gen_step_ids = [gen_step_id] + [s.get('step_id') for s in generated_state.get('observation', {}).get('location', {}).get('progress', {}).get('steps', {}).get('remaining', [])]
    exp_step_ids = [exp_step_id] + [s.get('step_id') for s in expected_state.get('observation', {}).get('location', {}).get('progress', {}).get('steps', {}).get('remaining', [])]

    print("    Generated step IDs:")
    for i, sid in enumerate(gen_step_ids, 1):
        print(f"       {i}. {sid}")

    print("    Expected step IDs:")
    for i, sid in enumerate(exp_step_ids, 1):
        print(f"       {i}. {sid}")

    print("\n" + "=" * 80)
    print("Test Complete")
    print("=" * 80)


if __name__ == '__main__':
    main()
