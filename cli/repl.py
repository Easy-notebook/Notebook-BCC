"""
Interactive REPL for the workflow system.
"""

import cmd
from silantui import ModernLogger



class WorkflowREPL(cmd.Cmd):
    """
    Interactive REPL for workflow control.
    """

    intro = """
╔═══════════════════════════════════════════════════════════╗
║         Notebook-BCC Interactive Workflow REPL            ║
║                                                           ║
║  Type 'help' for available commands                      ║
║  Type 'quit' or 'exit' to exit                           ║
╚═══════════════════════════════════════════════════════════╝
"""
    prompt = '(workflow) > '

    def __init__(self, cli):
        """
        Initialize the REPL.

        Args:
            cli: Reference to WorkflowCLI instance
        """
        super().__init__()
        self.cli = cli

    # ==============================================
    # Workflow Commands
    # ==============================================

    def do_status(self, arg):
        """Show current workflow status."""
        from argparse import Namespace
        self.cli.cmd_status(Namespace())

    def do_start(self, arg):
        """Start a new workflow. Usage: start [problem description]"""
        from argparse import Namespace
        self.cli.cmd_start(Namespace(problem=arg or None, notebook_id=None))

    def do_show(self, arg):
        """Show notebook content. Usage: show [notebook_filename]"""
        from argparse import Namespace
        self.cli.cmd_show(Namespace(notebook=arg or None))

    def do_list(self, arg):
        """List all notebooks."""
        from argparse import Namespace
        self.cli.cmd_list(Namespace())

    def do_export(self, arg):
        """Export notebook to markdown. Usage: export <notebook_filename> [output_file]"""
        args = arg.split()
        if not args:
            print("Usage: export <notebook_filename> [output_file]")
            return

        from argparse import Namespace
        notebook = args[0]
        output = args[1] if len(args) > 1 else None
        self.cli.cmd_export(Namespace(notebook=notebook, output=output))

    # ==============================================
    # State Machine Commands
    # ==============================================

    def do_transition(self, arg):
        """Manually trigger a state transition. Usage: transition <event_name>"""
        if not arg:
            print("Usage: transition <event_name>")
            print("Available events: START_WORKFLOW, START_STEP, COMPLETE_STEP, etc.")
            return

        from core.events import WorkflowEvent

        try:
            event = WorkflowEvent[arg.upper()]
            success = self.cli.state_machine.transition(event)
            if success:
                print(f"✓ Transitioned to: {self.cli.state_machine.state.value}")
            else:
                print(f"✗ Invalid transition: {arg}")
        except KeyError:
            print(f"✗ Unknown event: {arg}")

    def do_reset(self, arg):
        """Reset the state machine."""
        self.cli.state_machine.reset()
        print("✓ State machine reset")

    # ==============================================
    # Context Commands
    # ==============================================

    def do_var(self, arg):
        """Variable operations. Usage: var [list|set <key> <value>|get <key>]"""
        args = arg.split()

        if not args or args[0] == 'list':
            # List all variables
            context = self.cli.ai_context_store.get_context()
            if context.variables:
                print("\n📦 Variables:")
                for key, value in context.variables.items():
                    print(f"  {key} = {value}")
            else:
                print("No variables set.")

        elif args[0] == 'set' and len(args) >= 3:
            # Set a variable
            key = args[1]
            value = ' '.join(args[2:])
            self.cli.ai_context_store.add_variable(key, value)
            print(f"✓ Set {key} = {value}")

        elif args[0] == 'get' and len(args) >= 2:
            # Get a variable
            key = args[1]
            value = self.cli.ai_context_store.get_variable(key)
            if value is not None:
                print(f"{key} = {value}")
            else:
                print(f"Variable not found: {key}")

        else:
            print("Usage: var [list|set <key> <value>|get <key>]")

    def do_todo(self, arg):
        """TODO list operations. Usage: todo [list|add <item>|clear]"""
        args = arg.split(maxsplit=1)

        if not args or args[0] == 'list':
            # List TODOs
            context = self.cli.ai_context_store.get_context()
            if context.to_do_list:
                print("\n✅ TODO List:")
                for i, item in enumerate(context.to_do_list, 1):
                    print(f"  {i}. {item}")
            else:
                print("No pending TODOs.")

        elif args[0] == 'add' and len(args) >= 2:
            # Add TODO
            item = args[1]
            self.cli.ai_context_store.add_to_do_list(item)
            print(f"✓ Added TODO: {item}")

        elif args[0] == 'clear':
            # Clear TODOs
            self.cli.ai_context_store.clear_to_do_list()
            print("✓ Cleared TODO list")

        else:
            print("Usage: todo [list|add <item>|clear]")

    def do_effect(self, arg):
        """Show effect history."""
        context = self.cli.ai_context_store.get_context()

        print("\n💡 Current Effects:")
        if context.effect['current']:
            for i, effect in enumerate(context.effect['current'], 1):
                print(f"  {i}. {effect[:100]}...")
        else:
            print("  None")

        print("\n📜 Effect History:")
        if context.effect['history']:
            for i, effect in enumerate(context.effect['history'], 1):
                print(f"  {i}. {effect[:100]}...")
        else:
            print("  None")

    # ==============================================
    # Code Execution Commands
    # ==============================================

    def do_exec(self, arg):
        """Execute Python code. Usage: exec <code>"""
        if not arg:
            print("Usage: exec <code>")
            return

        result = self.cli.code_executor.execute(arg)

        if result['success']:
            print("✓ Execution successful")
            if result['outputs']:
                print("\nOutput:")
                for output in result['outputs']:
                    print(output.content or output.text or '')
        else:
            print(f"✗ Execution failed: {result['error']}")

    def do_namespace(self, arg):
        """Show code execution namespace variables."""
        variables = self.cli.code_executor.get_all_variables()

        if variables:
            print("\n🐍 Python Namespace:")
            for name, value in variables.items():
                print(f"  {name} = {value}")
        else:
            print("No user variables in namespace.")

    # ==============================================
    # State Management Commands (NEW)
    # ==============================================

    def do_load_state(self, arg):
        """Load workflow state from JSON file. Usage: load_state <file_path>"""
        if not arg:
            print("Usage: load_state <file_path>")
            return

        import json
        from utils.state_file_loader import state_file_loader
        from utils.api_display import api_display

        try:
            # Load state file
            print(f"📂 Loading state from: {arg}")
            state_json = state_file_loader.load_state_file(arg)
            parsed_state = state_file_loader.parse_state_for_api(state_json)

            # Display state info
            api_display.display_state_info(parsed_state)

            # Extract and restore context
            context_data = state_file_loader.extract_context(state_json)

            # Restore AI context
            print("\n📦 Restoring AI context...")
            self.cli.ai_context_store.set_variables(context_data.get('variables', {}))

            effects = context_data.get('effects', {})
            self.cli.ai_context_store.set_effect(effects)

            print(f"   ✓ Variables: {len(context_data.get('variables', {}))}")
            print(f"   ✓ Current Effects: {len(effects.get('current', []))}")
            print(f"   ✓ Effect History: {len(effects.get('history', []))}")

            # Store parsed state for send_api command and original JSON for apply_transition
            self._loaded_state = parsed_state
            self._loaded_state_json = state_json

            print("\n✅ State loaded successfully")
            print("   Use 'send_api' to send API requests from this state")
            print("   Use 'apply_transition' to apply transition XML and update state")

        except FileNotFoundError:
            print(f"❌ File not found: {arg}")
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")

    def do_send_api(self, arg):
        """Send API request from loaded state. Usage: send_api [planning|generating|reflecting] [--stream]"""
        import asyncio
        from utils.api_client import workflow_api_client
        from utils.api_display import api_display
        from utils.state_file_loader import state_file_loader
        from config import Config
        from cli.commands import DummyContext

        # Check if state is loaded
        if not hasattr(self, '_loaded_state'):
            print("❌ No state loaded. Use 'load_state <file>' first")
            return

        # Parse arguments
        args = arg.split() if arg else []

        # Determine API type (specified or auto-inferred)
        api_type = None
        if args and args[0] in ['planning', 'generating', 'reflecting']:
            api_type = args[0]
            print(f"\n🎯 Using specified API type: {api_type}")
        else:
            # Auto-infer API type from state
            api_type = state_file_loader.infer_api_type(self._loaded_state_json)
            print(f"\n🤖 Auto-inferred API type: {api_type}")
            print(f"   (You can override with: send_api <planning|generating|reflecting>)")

        use_stream = '--stream' in args

        try:
            parsed_state = self._loaded_state
            stage_id = parsed_state['stage_id'] or 'none'
            step_id = parsed_state['step_id'] or 'none'
            state = parsed_state['state']

            # Determine API URL
            api_url_map = {
                'planning': Config.FEEDBACK_API_URL,
                'generating': Config.BEHAVIOR_API_URL,
                'reflecting': Config.REFLECTING_API_URL
            }
            api_url = api_url_map[api_type]

            # Display request info
            import json
            payload_json = json.dumps(state, ensure_ascii=False)
            api_display.display_api_request(
                api_type=api_type,
                api_url=api_url,
                stage_id=stage_id,
                step_id=step_id,
                payload_size=len(payload_json)
            )

            # Send request
            async def send_request():
                try:
                    if api_type == 'planning':
                        with api_display.display_sending_progress('planning') or DummyContext():
                            result = await workflow_api_client.send_feedback(
                                stage_id=stage_id,
                                step_index=step_id,
                                state=state
                            )
                        api_display.display_api_response('planning', result, success=True)
                        return result

                    elif api_type == 'generating':
                        actions = []
                        with api_display.display_sending_progress('generating') or DummyContext():
                            async for action in workflow_api_client.fetch_behavior_actions(
                                stage_id=stage_id,
                                step_index=step_id,
                                state=state,
                                stream=use_stream
                            ):
                                actions.append(action)

                        api_display.display_actions(actions)
                        result = {'actions': actions, 'count': len(actions)}
                        api_display.display_api_response('generating', result, success=True)
                        return result

                    elif api_type == 'reflecting':
                        with api_display.display_sending_progress('reflecting') or DummyContext():
                            result = await workflow_api_client.send_reflecting(
                                stage_id=stage_id,
                                step_index=step_id,
                                state=state
                            )
                        api_display.display_api_response('reflecting', result, success=True)
                        return result

                except Exception as e:
                    api_display.display_api_response(api_type, {}, success=False, error=str(e))
                    raise

            # Run async request
            result = asyncio.run(send_request())
            print("\n✅ API request completed successfully")

        except Exception as e:
            print(f"\n❌ Error: {e}")

    def do_test_request(self, arg):
        """Preview API request without sending. Usage: test_request [planning|generating|reflecting] [--output <file>] [--format <json|pretty>]"""
        import json
        from utils.api_display import api_display
        from utils.state_file_loader import state_file_loader
        from config import Config

        # Check if state is loaded
        if not hasattr(self, '_loaded_state'):
            print("❌ No state loaded. Use 'load_state <file>' first")
            return

        # Parse arguments
        args = arg.split() if arg else []

        # Determine API type (specified or auto-inferred)
        api_type = None
        start_idx = 0
        if args and args[0] in ['planning', 'generating', 'reflecting']:
            api_type = args[0]
            print(f"\n🎯 Using specified API type: {api_type}")
            start_idx = 1
        else:
            # Auto-infer API type from state
            api_type = state_file_loader.infer_api_type(self._loaded_state_json)
            print(f"\n🤖 Auto-inferred API type: {api_type}")
            print(f"   (You can override with: test_request <planning|generating|reflecting>)")
            start_idx = 0

        # Parse optional arguments
        output_file = None
        output_format = 'pretty'

        i = start_idx
        while i < len(args):
            if args[i] == '--output' and i + 1 < len(args):
                output_file = args[i + 1]
                i += 2
            elif args[i] == '--format' and i + 1 < len(args):
                output_format = args[i + 1]
                i += 2
            else:
                i += 1

        try:
            parsed_state = self._loaded_state
            stage_id = parsed_state['stage_id'] or 'none'
            step_id = parsed_state['step_id'] or 'none'
            state = parsed_state['state']

            # Determine API URL
            api_url_map = {
                'planning': Config.FEEDBACK_API_URL,
                'generating': Config.BEHAVIOR_API_URL,
                'reflecting': Config.REFLECTING_API_URL
            }
            api_url = api_url_map[api_type]

            # Build payload
            progress_info = state.get('progress_info', {})
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

            if 'FSM' in state:
                payload['observation']['context']['FSM'] = state['FSM']

            # Display preview
            print("\n" + "="*70)
            print(" REQUEST PREVIEW (Will NOT be sent)")
            print("="*70)

            api_display.display_api_request(
                api_type=api_type,
                api_url=api_url,
                stage_id=stage_id,
                step_id=step_id,
                payload_size=len(json.dumps(payload, ensure_ascii=False))
            )

            # Format output
            if output_format == 'json':
                output_text = json.dumps(payload, ensure_ascii=False)
            else:
                output_text = json.dumps(payload, indent=2, ensure_ascii=False)

            # Display payload
            print("\n" + "="*70)
            print(" REQUEST PAYLOAD")
            print("="*70)

            try:
                from rich.syntax import Syntax
                from rich.console import Console
                console = Console()
                syntax = Syntax(output_text, "json", theme="monokai", line_numbers=True)
                console.print(syntax)
            except ImportError:
                print(output_text)

            # Display statistics
            print("\n" + "="*70)
            print("📊 REQUEST STATISTICS")
            print("="*70)
            print(f"API Type:        {api_type.upper()}")
            print(f"API URL:         {api_url}")
            print(f"Stage ID:        {stage_id}")
            print(f"Step ID:         {step_id}")
            print(f"Payload Size:    {len(output_text)} bytes ({len(output_text)/1024:.2f} KB)")
            print(f"Variables:       {len(state.get('variables', {}))}")
            print(f"Current Effects: {len(state.get('effects', {}).get('current', []))}")

            # Export if requested
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(output_text)
                print(f"\n💾 Exported to: {output_file}")

            print("\n" + "="*70)
            print("✅ Preview completed (NOT sent)")
            print("="*70)

        except Exception as e:
            print(f"\n❌ Error: {e}")

    def do_apply_transition(self, arg):
        """Apply transition to state. Usage: apply_transition <transition_file> --output <output_file> [--format <json|pretty>]"""
        if not arg:
            print("Usage: apply_transition <transition_file> --output <output_file> [--format <json|pretty>]")
            return

        import json
        from utils.state_file_loader import state_file_loader
        from utils.state_updater import state_updater
        from utils.api_display import api_display

        # Check if state is loaded
        if not hasattr(self, '_loaded_state'):
            print("❌ No state loaded. Use 'load_state <file>' first")
            return

        # Parse arguments
        args = arg.split()
        if len(args) < 1:
            print("❌ Missing transition file path")
            return

        transition_file = args[0]

        # Parse optional arguments
        output_file = None
        output_format = 'pretty'

        i = 1
        while i < len(args):
            if args[i] == '--output' and i + 1 < len(args):
                output_file = args[i + 1]
                i += 2
            elif args[i] == '--format' and i + 1 < len(args):
                output_format = args[i + 1]
                i += 2
            else:
                i += 1

        if not output_file:
            print("❌ Missing --output parameter")
            print("Usage: apply_transition <transition_file> --output <output_file> [--format <json|pretty>]")
            return

        try:
            # Get the loaded state JSON
            # We need to reconstruct the full state from _loaded_state
            # _loaded_state only has parsed info, we need the original JSON
            if not hasattr(self, '_loaded_state_json'):
                print("❌ No state JSON loaded. Use 'load_state <file>' first")
                return

            state_json = self._loaded_state_json

            # Display original state
            print("\n Original State:")
            api_display.display_state_info(self._loaded_state)

            # Load transition file
            print(f"\n📄 Loading transition from: {transition_file}")
            with open(transition_file, 'r', encoding='utf-8') as f:
                transition_content = f.read()

            print(f"   ✓ Loaded {len(transition_content)} bytes")

            # Apply transition
            print("\n🔄 Applying transition...")
            updated_state = state_updater.apply_transition(
                state=state_json,
                transition_response=transition_content,
                transition_type='auto'
            )

            # Display updated state info
            print("\n✅ Transition Applied Successfully!")
            parsed_updated = state_file_loader.parse_state_for_api(updated_state)
            print("\n Updated State:")
            api_display.display_state_info(parsed_updated)

            # Show what changed
            print("\n📊 Changes:")
            original_fsm = state_json.get('state', {}).get('FSM', {})
            updated_fsm = updated_state.get('state', {}).get('FSM', {})

            if original_fsm.get('state') != updated_fsm.get('state'):
                print(f"   FSM State: {original_fsm.get('state', 'UNKNOWN')} → {updated_fsm.get('state', 'UNKNOWN')}")

            if original_fsm.get('last_transition') != updated_fsm.get('last_transition'):
                print(f"   Last Transition: {original_fsm.get('last_transition', 'None')} → {updated_fsm.get('last_transition', 'None')}")

            original_stage = self._loaded_state.get('stage_id')
            updated_stage = parsed_updated.get('stage_id')
            if original_stage != updated_stage:
                print(f"   Stage ID: {original_stage or 'None'} → {updated_stage or 'None'}")

            original_step = self._loaded_state.get('step_id')
            updated_step = parsed_updated.get('step_id')
            if original_step != updated_step:
                print(f"   Step ID: {original_step or 'None'} → {updated_step or 'None'}")

            # Format output
            if output_format == 'json':
                output_text = json.dumps(updated_state, ensure_ascii=False)
            else:
                output_text = json.dumps(updated_state, indent=2, ensure_ascii=False)

            # Export to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output_text)

            print(f"\n💾 Updated state exported to: {output_file}")
            print(f"   Format: {output_format}")
            print(f"   Size: {len(output_text)} bytes ({len(output_text)/1024:.2f} KB)")

            print("\n" + "="*70)
            print("✅ Transition applied and state exported successfully")
            print("="*70)

            # Update the loaded state to the new state
            self._loaded_state_json = updated_state
            self._loaded_state = parsed_updated
            print("\n📌 Loaded state has been updated to the new state")

        except FileNotFoundError as e:
            print(f"❌ File not found: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")

    # ==============================================
    # Notebook Commands
    # ==============================================

    def do_save(self, arg):
        """Save current notebook. Usage: save [filename]"""
        notebook_data = self.cli.notebook_store.to_dict()
        filename = arg or None

        path = self.cli.notebook_manager.save_notebook(
            notebook_data,
            filename=filename
        )

        print(f"✓ Notebook saved: {path}")

    def do_cells(self, arg):
        """Show cell count and types."""
        print(f"\n📄 Cells: {self.cli.notebook_store.get_cell_count()}")

        from models.cell import CellType

        for cell_type in CellType:
            cells = self.cli.notebook_store.get_cells_by_type(cell_type)
            if cells:
                print(f"  {cell_type.value}: {len(cells)}")

    # ==============================================
    # System Commands
    # ==============================================

    def do_quit(self, arg):
        """Exit the REPL."""
        print("\n👋 Goodbye!")
        return True

    def do_exit(self, arg):
        """Exit the REPL (alias for quit)."""
        return self.do_quit(arg)

    def do_clear(self, arg):
        """Clear the screen."""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')

    def do_help(self, arg):
        """Show help for commands."""
        if arg:
            # Show help for specific command
            super().do_help(arg)
        else:
            # Show all commands
            print("\n📚 Available Commands:\n")
            print("Workflow:")
            print("  status          - Show workflow status")
            print("  start [desc]    - Start new workflow")
            print("  show [file]     - Show notebook content")
            print("  list            - List all notebooks")
            print("  export          - Export to markdown")
            print()
            print("State Machine:")
            print("  transition      - Trigger state transition")
            print("  reset           - Reset state machine")
            print()
            print("State Management: (NEW)")
            print("  load_state <file>              - Load state from JSON file")
            print("  send_api [type] [opts]         - Send API (auto-inferred or specify type)")
            print("  test_request [type] [opts]     - Preview API request (auto-inferred or specify type)")
            print("  apply_transition <xml> [opts]  - Apply transition XML to loaded state")
            print()
            print("Context:")
            print("  var             - Variable operations")
            print("  todo            - TODO list operations")
            print("  effect          - Show effect history")
            print()
            print("Code Execution:")
            print("  exec            - Execute Python code")
            print("  namespace       - Show namespace variables")
            print()
            print("Notebook:")
            print("  save [file]     - Save current notebook")
            print("  cells           - Show cell statistics")
            print()
            print("System:")
            print("  clear           - Clear screen")
            print("  help            - Show this help")
            print("  quit/exit       - Exit REPL")
            print()

    def default(self, line):
        """Handle unknown commands."""
        print(f"❌ Unknown command: {line}")
        print("Type 'help' for available commands.")

    def emptyline(self):
        """Handle empty line (don't repeat last command)."""
        pass

    def run(self):
        """Run the REPL."""
        try:
            self.cmdloop()
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            return
