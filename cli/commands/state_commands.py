"""
State commands - handles state management operations.
"""

import json
from utils.state_file_loader import state_file_loader
from utils.state_updater import state_updater
from utils.api_display import api_display


class StateCommands:
    """
    Handles state management commands: resume, test-request, apply-transition.
    """

    def cmd_resume(self, args):
        """Resume workflow from state file."""
        # Load state file using unified helper
        print(f"Loading state from: {args.state_file}")
        state_json, parsed_state = self._load_state_file(args.state_file)

        # Display state info
        api_display.display_state_info(parsed_state)

        # Extract context
        context_data = state_file_loader.extract_context(state_json)

        # Restore AI context
        print("\nRestoring AI context...")
        self.ai_context_store.set_variables(context_data.get('variables', {}))

        effects = context_data.get('effects', {})
        self.ai_context_store.set_effect(effects)

        print(f"   Variables: {len(context_data.get('variables', {}))}")
        print(f"   Current Effects: {len(effects.get('current', []))}")
        print(f"   Effect History: {len(effects.get('history', []))}")

        # Restore FSM state info
        fsm = context_data.get('FSM', {})
        fsm_state = fsm.get('state', 'UNKNOWN')
        print(f"   FSM State: {fsm_state}")

        # Extract workflow position
        stage_id = parsed_state.get('stage_id')
        step_id = parsed_state.get('step_id')

        print(f"\nWorkflow Position:")
        print(f"   Stage: {stage_id or 'None'}")
        print(f"   Step: {step_id or 'None'}")

        # Check if should continue execution
        if args.continue_execution:
            print("\nContinuing workflow execution...")
            # TODO: Implement workflow continuation logic
            print("Warning: Workflow continuation not fully implemented yet")
            print("   Use 'send-api' to manually send requests from this state")
        else:
            print("\nState loaded successfully")
            print("   Use --continue to resume execution")
            print("   Or use 'send-api' to send manual API requests")

    def cmd_test_request(self, args):
        """
        Preview API request without sending.

        Now uses state machine for API type inference.
        """
        from config import Config

        # Load state file using unified helper
        print(f"Loading state from: {args.state_file}")
        state_json, parsed_state = self._load_state_file(args.state_file)

        # Display state info
        api_display.display_state_info(parsed_state)

        # Use state machine to infer API type (NEW)
        api_type = self.state_machine.infer_api_type_from_state(state_json)

        # Allow override if specified
        if args.api_type:
            api_type = args.api_type
            print(f"\nUsing specified API type: {api_type}")
        else:
            print(f"\nAuto-inferred API type: {api_type}")
            print(f"   (You can override with --api-type)")

        # Extract parameters
        stage_id = parsed_state['stage_id'] or 'none'
        step_id = parsed_state['step_id'] or 'none'
        state = state_json

        # Determine API URL
        api_url_map = {
            'planning': Config.FEEDBACK_API_URL,
            'generating': Config.BEHAVIOR_API_URL,
            'reflecting': Config.REFLECTING_API_URL
        }
        api_url = api_url_map[api_type]

        # Build request payload
        progress_info = state.get('progress_info')
        if not progress_info:
            print("\nWarning: State does not contain progress_info")
            progress_info = {}

        # Build payload
        payload = {
            'observation': {
                'location': progress_info,
                'context': {
                    'variables': state.get('variables', {}),
                    'effects': state.get('effects', {'current': [], 'history': []}),
                    'notebook': state.get('notebook', {})
                }
            },
            'options': {
                'stream': False
            }
        }

        # Add FSM if present
        if 'FSM' in state:
            payload['observation']['context']['FSM'] = state['FSM']

        # Display request preview
        print("\n" + "="*70)
        print(" REQUEST PREVIEW (Will NOT be sent)")
        print("="*70)

        # Display request info
        api_display.display_api_request(
            api_type=api_type,
            api_url=api_url,
            stage_id=stage_id,
            step_id=step_id,
            payload_size=len(json.dumps(payload, ensure_ascii=False))
        )

        # Format output based on format argument
        if args.format == 'json':
            output_text = json.dumps(payload, ensure_ascii=False)
        else:
            output_text = json.dumps(payload, indent=2, ensure_ascii=False)

        # Display payload
        print("\n" + "="*70)
        print(" REQUEST PAYLOAD")
        print("="*70)

        from rich.syntax import Syntax
        from rich.console import Console
        console = Console()
        syntax = Syntax(output_text, "json", theme="monokai", line_numbers=True)
        console.print(syntax)

        # Display statistics
        print("\n" + "="*70)
        print("REQUEST STATISTICS")
        print("="*70)
        print(f"API Type:       {api_type.upper()}")
        print(f"API URL:        {api_url}")
        print(f"Stage ID:       {stage_id}")
        print(f"Step ID:        {step_id}")
        print(f"Payload Size:   {len(output_text)} bytes ({len(output_text)/1024:.2f} KB)")
        print(f"Variables:      {len(state.get('variables', {}))}")
        print(f"Current Effects: {len(state.get('effects', {}).get('current', []))}")
        print(f"Effect History:  {len(state.get('effects', {}).get('history', []))}")

        # Export to file if requested
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_text)
            print(f"\nRequest payload exported to: {args.output}")
            print(f"   Format: {args.format}")

        print("\n" + "="*70)
        print("Request preview completed (NOT sent to server)")
        print("="*70)
        print("\nTo actually send this request, use:")
        print(f"  python main.py send-api --state-file {args.state_file} --api-type {api_type}")

    def cmd_apply_transition(self, args):
        """Apply transition to state and export updated state."""
        # Load state file using unified helper
        print(f"Loading state from: {args.state_file}")
        state_json, parsed_state = self._load_state_file(args.state_file)

        # Display original state info
        print("\n Original State:")
        api_display.display_state_info(parsed_state)

        # Load transition file
        print(f"\nLoading transition from: {args.transition_file}")
        with open(args.transition_file, 'r', encoding='utf-8') as f:
            transition_content = f.read()

        # Display transition info
        print(f"   Loaded {len(transition_content)} bytes")

        # Apply transition
        print("\nApplying transition...")
        updated_state = state_updater.apply_transition(
            state=state_json,
            transition_response=transition_content,
            transition_type='auto'
        )

        # Display updated state info
        print("\nTransition Applied Successfully!")
        parsed_updated = state_file_loader.parse_state_for_api(updated_state)
        print("\n Updated State:")
        api_display.display_state_info(parsed_updated)

        # Show what changed
        print("\nChanges:")
        original_fsm = state_json.get('state', {}).get('FSM', {})
        updated_fsm = updated_state.get('state', {}).get('FSM', {})

        if original_fsm.get('state') != updated_fsm.get('state'):
            print(f"   FSM State: {original_fsm.get('state', 'UNKNOWN')} -> {updated_fsm.get('state', 'UNKNOWN')}")

        if original_fsm.get('last_transition') != updated_fsm.get('last_transition'):
            print(f"   Last Transition: {original_fsm.get('last_transition', 'None')} -> {updated_fsm.get('last_transition', 'None')}")

        original_stage = parsed_state.get('stage_id')
        updated_stage = parsed_updated.get('stage_id')
        if original_stage != updated_stage:
            print(f"   Stage ID: {original_stage or 'None'} -> {updated_stage or 'None'}")

        original_step = parsed_state.get('step_id')
        updated_step = parsed_updated.get('step_id')
        if original_step != updated_step:
            print(f"   Step ID: {original_step or 'None'} -> {updated_step or 'None'}")

        # Format output based on format argument
        if args.format == 'json':
            output_text = json.dumps(updated_state, ensure_ascii=False)
        else:
            output_text = json.dumps(updated_state, indent=2, ensure_ascii=False)

        # Export to file
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_text)

        print(f"\nUpdated state exported to: {args.output}")
        print(f"   Format: {args.format}")
        print(f"   Size: {len(output_text)} bytes ({len(output_text)/1024:.2f} KB)")

        print("\n" + "="*70)
        print("Transition applied and state exported successfully")
        print("="*70)
