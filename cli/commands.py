"""
CLI Commands for the workflow system.
"""

import argparse
import logging
from silantui import ModernLogger
import sys
from pathlib import Path
import warnings

# Suppress ResourceWarning for aiohttp sessions (they're cleaned up by GC)
warnings.filterwarnings('ignore', category=ResourceWarning)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.state_machine import WorkflowStateMachine
from stores.pipeline_store import PipelineStore
from stores.script_store import ScriptStore
from stores.notebook_store import NotebookStore
from stores.ai_context_store import AIPlanningContextStore
from executors.code_executor import CodeExecutor
from notebook.notebook_manager import NotebookManager
from notebook.cell_renderer import CellRenderer


class DummyContext:
    """Dummy context manager for when rich is not available."""
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass



class WorkflowCLI(ModernLogger):
    """
    Command-line interface for the workflow system.
    """

    def __init__(self, max_steps=0, interactive=False):
        """
        Initialize the CLI.

        Args:
            max_steps: Maximum steps to execute (0 = unlimited)
            interactive: Enable interactive mode
        """
        super().__init__("WorkflowCLI")
        self.setup_logging()

        # Initialize managers first
        self.notebook_manager = NotebookManager()
        self.cell_renderer = CellRenderer()

        # Initialize stores
        self.pipeline_store = PipelineStore()
        self.notebook_store = NotebookStore()
        self.ai_context_store = AIPlanningContextStore()
        self.code_executor = CodeExecutor()
        self.script_store = ScriptStore(
            notebook_store=self.notebook_store,
            ai_context_store=self.ai_context_store,
            code_executor=self.code_executor
        )

        # Initialize state machine with control parameters
        self.state_machine = WorkflowStateMachine(
            pipeline_store=self.pipeline_store,
            script_store=self.script_store,
            ai_context_store=self.ai_context_store,
            notebook_manager=self.notebook_manager,
            max_steps=max_steps,
            interactive=interactive
        )

    def setup_logging(self, level=logging.INFO):
        """Setup logging configuration."""
        # Only configure file handler, ModernLogger already handles console output
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        # Add file handler only if not already present
        if not any(isinstance(h, logging.FileHandler) for h in root_logger.handlers):
            file_handler = logging.FileHandler('workflow.log')
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            root_logger.addHandler(file_handler)

    def create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser."""
        parser = argparse.ArgumentParser(
            description='Notebook-BCC: Python Workflow System',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        # Global configuration options
        parser.add_argument('--backend-url', type=str, help='Backend Jupyter kernel URL (default: http://localhost:18600)')
        parser.add_argument('--dslc-url', type=str, help='DSLC workflow API URL (default: http://localhost:28600)')
        parser.add_argument('--notebook-id', type=str, help='Initial notebook ID')

        # Execution control options
        parser.add_argument('--max-steps', type=int, default=0, help='Maximum steps to execute (0 = unlimited)')
        parser.add_argument('--interactive', action='store_true', help='Enable interactive mode (pause at breakpoints)')

        # Custom context option
        parser.add_argument('--custom-context', type=str, help='Custom context JSON string or file path')

        subparsers = parser.add_subparsers(dest='command', help='Commands')

        # Start command
        start_parser = subparsers.add_parser('start', help='Start a new workflow')
        start_parser.add_argument('--problem', type=str, help='Problem description')
        start_parser.add_argument('--context', type=str, help='Additional context for workflow initialization')

        # Status command
        subparsers.add_parser('status', help='Show workflow status')

        # Show command
        show_parser = subparsers.add_parser('show', help='Show notebook')
        show_parser.add_argument('--notebook', type=str, help='Notebook filename')

        # List command
        subparsers.add_parser('list', help='List notebooks')

        # Export command
        export_parser = subparsers.add_parser('export', help='Export notebook to markdown')
        export_parser.add_argument('notebook', type=str, help='Notebook filename')
        export_parser.add_argument('--output', type=str, help='Output filename')

        # REPL command
        subparsers.add_parser('repl', help='Start interactive REPL')

        # Send-API command (NEW)
        send_api_parser = subparsers.add_parser('send-api', help='Send API request from state file')
        send_api_parser.add_argument('--state-file', type=str, required=True, help='Path to state JSON file')
        send_api_parser.add_argument('--api-type', type=str, required=False,
                                     choices=['planning', 'generating', 'reflecting'],
                                     help='API type to call (auto-inferred from FSM state if not specified)')
        send_api_parser.add_argument('--output', type=str, help='Output file for response (optional)')
        send_api_parser.add_argument('--stream', action='store_true', help='Use streaming for generating API')

        # Resume command (NEW)
        resume_parser = subparsers.add_parser('resume', help='Resume workflow from state file')
        resume_parser.add_argument('--state-file', type=str, required=True, help='Path to state JSON file')
        resume_parser.add_argument('--continue', dest='continue_execution', action='store_true',
                                  help='Continue execution after loading state')

        # Test-request command (NEW)
        test_req_parser = subparsers.add_parser('test-request', help='Preview API request without sending')
        test_req_parser.add_argument('--state-file', type=str, required=True, help='Path to state JSON file')
        test_req_parser.add_argument('--api-type', type=str, required=False,
                                     choices=['planning', 'generating', 'reflecting'],
                                     help='API type to preview (auto-inferred from FSM state if not specified)')
        test_req_parser.add_argument('--output', type=str, help='Export request payload to file')
        test_req_parser.add_argument('--format', type=str, choices=['json', 'pretty'], default='pretty',
                                     help='Output format (json or pretty)')

        # Apply-transition command (NEW)
        apply_trans_parser = subparsers.add_parser('apply-transition',
                                                   help='Apply transition to state and export updated state')
        apply_trans_parser.add_argument('--state-file', type=str, required=True,
                                       help='Path to input state JSON file')
        apply_trans_parser.add_argument('--transition-file', type=str, required=True,
                                       help='Path to transition XML file')
        apply_trans_parser.add_argument('--output', type=str, required=True,
                                       help='Output file for updated state JSON')
        apply_trans_parser.add_argument('--format', type=str, choices=['json', 'pretty'], default='pretty',
                                       help='Output format (json or pretty)')

        return parser

    def cmd_start(self, args):
        """Start a new workflow."""
        print("🚀 Starting new workflow...")

        # Get existing custom context (if set via --custom-context)
        existing_vars = self.ai_context_store.get_context().variables

        # Build default planning request - use existing variables from custom context if available
        problem_description = args.problem or existing_vars.get('problem_description') or existing_vars.get('user_goal') or "Data Analysis Task"
        context_description = args.context or existing_vars.get('context_description') or "Interactive workflow"
        problem_name = existing_vars.get('problem_name') or 'Analysis'

        planning_request = {
            'problem_name': problem_name,
            'user_goal': problem_description,
            'problem_description': problem_description,
            'context_description': context_description,
        }

        workflow = self.pipeline_store.initialize_workflow(planning_request)

        print(f"✓ Workflow initialized: {workflow.name}")
        print(f"  Stages: {len(workflow.stages)}")

        # Only add planning variables if they're not already set
        # This prevents overwriting custom context variables
        for key, value in planning_request.items():
            if key not in existing_vars:
                self.ai_context_store.add_variable(key, value)

        # Start execution
        self.pipeline_store.start_workflow_execution(self.state_machine)

        print(f"✓ Workflow started")
        print(f"  Current state: {self.state_machine.state.value}")
        print(f"📝 Notebook will be saved to: {self.notebook_manager.notebooks_dir}/")

    def cmd_status(self, args=None):
        """Show workflow status."""
        _ = args  # Unused
        print("\n📊 Workflow Status")
        print("=" * 60)

        # State machine status
        state_info = self.state_machine.get_state_info()
        print(f"Current State: {state_info['current_state']}")
        print(f"Stage ID: {state_info['stage_id']}")
        print(f"Step ID: {state_info['step_id']}")
        print(f"Actions: {state_info['action_index'] + 1} / {state_info['total_actions']}")

        # Execution control status
        exec_status = self.state_machine.get_execution_status()
        print(f"\n🎮 Execution Control")
        print(f"Steps: {exec_status['current_step']}" + (f"/{exec_status['max_steps']}" if exec_status['max_steps'] > 0 else " (unlimited)"))
        print(f"Protocol: Planning First (always checks /planning API before execution)")
        print(f"Interactive: {'Yes' if exec_status['interactive'] else 'No'}")
        print(f"Paused: {'Yes' if exec_status['paused'] else 'No'}")

        print("\n📝 Notebook Status")
        print(f"Title: {self.notebook_store.title}")
        print(f"Cells: {self.notebook_store.get_cell_count()}")

        print("\n🎯 AI Context")
        context = self.ai_context_store.get_context()
        print(f"Variables: {len(context.variables)}")
        print(f"TODO List: {len(context.to_do_list)}")
        print(f"Effects: {len(context.effect['current'])}")
        print(f"Custom Context: {len(context.custom_context)} keys" if context.custom_context else "Custom Context: None")

        if context.to_do_list:
            print("\nPending TODOs:")
            for todo in context.to_do_list:
                print(f"  • {todo}")

        print()

    def cmd_show(self, args):
        """Show notebook content."""
        if args.notebook:
            # Load from file
            notebook_data = self.notebook_manager.load_notebook(args.notebook)
            if not notebook_data:
                print(f"❌ Notebook not found: {args.notebook}")
                return

            cells = [cell for cell in self.notebook_store.cells]
            self.notebook_store.from_dict(notebook_data)
        else:
            notebook_data = self.notebook_store.to_dict()

        # Render
        print(self.cell_renderer.render_notebook_summary(notebook_data))

        cells = notebook_data.get('cells', [])
        if cells:
            from models.cell import Cell
            cell_objects = [Cell.from_dict(c) for c in cells]
            print(self.cell_renderer.render_cells(cell_objects))
        else:
            print("No cells to display.")

    def cmd_list(self, args=None):
        """List all notebooks."""
        _ = args  # Unused
        notebooks = self.notebook_manager.list_notebooks()

        print(f"\n📚 Notebooks ({len(notebooks)})")
        print("=" * 60)

        if notebooks:
            for nb in notebooks:
                print(f"  • {nb}")
        else:
            print("  No notebooks found.")

        print()

    def cmd_export(self, args):
        """Export notebook to markdown."""
        notebook_data = self.notebook_manager.load_notebook(args.notebook)

        if not notebook_data:
            print(f"❌ Notebook not found: {args.notebook}")
            return

        output_path = self.notebook_manager.export_to_markdown(
            notebook_data,
            output_file=args.output
        )

        print(f"✓ Exported to: {output_path}")

    def cmd_repl(self, args=None):
        """Start interactive REPL."""
        _ = args  # Unused
        from .repl import WorkflowREPL
        repl = WorkflowREPL(self)
        repl.run()

    def cmd_send_api(self, args):
        """Send API request from state file."""
        import json
        import asyncio
        from utils.state_file_loader import state_file_loader
        from utils.api_client import workflow_api_client
        from utils.api_display import api_display
        from config import Config

        try:
            # Load state file
            print(f"📂 Loading state from: {args.state_file}")
            state_json = state_file_loader.load_state_file(args.state_file)
            parsed_state = state_file_loader.parse_state_for_api(state_json)

            # Display state info
            api_display.display_state_info(parsed_state)

            # Infer API type if not specified
            if args.api_type:
                api_type = args.api_type
                print(f"\n🎯 Using specified API type: {api_type}")
            else:
                api_type = state_file_loader.infer_api_type(state_json)
                print(f"\n Auto-inferred API type: {api_type}")
                print(f"   (You can override with --api-type)")

            # Extract parameters
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
            payload_json = json.dumps(state, ensure_ascii=False)
            api_display.display_api_request(
                api_type=api_type,
                api_url=api_url,
                stage_id=stage_id,
                step_id=step_id,
                payload_size=len(payload_json)
            )

            # Send request with progress display
            async def send_request():
                try:
                    if api_type == 'planning':
                        # Planning API
                        with api_display.display_sending_progress('planning') or DummyContext():
                            result = await workflow_api_client.send_feedback(
                                stage_id=stage_id,
                                step_index=step_id,
                                state=state
                            )
                        api_display.display_api_response('planning', result, success=True)
                        return result

                    elif api_type == 'generating':
                        # Generating API
                        actions = []
                        with api_display.display_sending_progress('generating') or DummyContext():
                            async for action in workflow_api_client.fetch_behavior_actions(
                                stage_id=stage_id,
                                step_index=step_id,
                                state=state,
                                stream=args.stream
                            ):
                                actions.append(action)

                        # Display actions
                        api_display.display_actions(actions)

                        result = {'actions': actions, 'count': len(actions)}
                        api_display.display_api_response('generating', result, success=True)
                        return result

                    elif api_type == 'reflecting':
                        # Reflecting API
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

            # Save to output file if specified
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"\n💾 Response saved to: {args.output}")

            print("\n✅ API request completed successfully")

        except FileNotFoundError as e:
            print(f"\n❌ Error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            self.error(f"send-api failed: {e}", exc_info=True)
            sys.exit(1)

    def cmd_resume(self, args):
        """Resume workflow from state file."""
        import json
        from utils.state_file_loader import state_file_loader
        from utils.api_display import api_display

        try:
            # Load state file
            print(f"📂 Loading state from: {args.state_file}")
            state_json = state_file_loader.load_state_file(args.state_file)
            parsed_state = state_file_loader.parse_state_for_api(state_json)

            # Display state info
            api_display.display_state_info(parsed_state)

            # Extract context
            context_data = state_file_loader.extract_context(state_json)

            # Restore AI context
            print("\n📦 Restoring AI context...")
            self.ai_context_store.set_variables(context_data.get('variables', {}))

            effects = context_data.get('effects', {})
            self.ai_context_store.set_effect(effects)

            print(f"   ✓ Variables: {len(context_data.get('variables', {}))}")
            print(f"   ✓ Current Effects: {len(effects.get('current', []))}")
            print(f"   ✓ Effect History: {len(effects.get('history', []))}")

            # Restore FSM state info
            fsm = context_data.get('FSM', {})
            fsm_state = fsm.get('state', 'UNKNOWN')
            print(f"   ✓ FSM State: {fsm_state}")

            # Extract workflow position
            stage_id = parsed_state.get('stage_id')
            step_id = parsed_state.get('step_id')

            print(f"\n📍 Workflow Position:")
            print(f"   Stage: {stage_id or 'None'}")
            print(f"   Step: {step_id or 'None'}")

            # Check if should continue execution
            if args.continue_execution:
                print("\n🚀 Continuing workflow execution...")
                # TODO: Implement workflow continuation logic
                # This would require restoring the full workflow state and resuming execution
                print("⚠️  Workflow continuation not fully implemented yet")
                print("   Use 'send-api' to manually send requests from this state")
            else:
                print("\n✅ State loaded successfully")
                print("   Use --continue to resume execution")
                print("   Or use 'send-api' to send manual API requests")

        except FileNotFoundError as e:
            print(f"\n❌ Error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            self.error(f"resume failed: {e}", exc_info=True)
            sys.exit(1)

    def cmd_test_request(self, args):
        """Preview API request without sending."""
        import json
        from utils.state_file_loader import state_file_loader
        from utils.api_display import api_display
        from config import Config

        try:
            # Load state file
            print(f"📂 Loading state from: {args.state_file}")
            state_json = state_file_loader.load_state_file(args.state_file)
            parsed_state = state_file_loader.parse_state_for_api(state_json)

            # Display state info
            api_display.display_state_info(parsed_state)

            # Infer API type if not specified
            if args.api_type:
                api_type = args.api_type
                print(f"\n🎯 Using specified API type: {api_type}")
            else:
                api_type = state_file_loader.infer_api_type(state_json)
                print(f"\n Auto-inferred API type: {api_type}")
                print(f"   (You can override with --api-type)")

            # Extract parameters
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

            # Build request payload (same as actual API call)
            # Extract progress information
            progress_info = state.get('progress_info')
            if not progress_info:
                print("\n⚠️  Warning: State does not contain progress_info")
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
                # Compact JSON
                output_text = json.dumps(payload, ensure_ascii=False)
            else:
                # Pretty formatted JSON
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
                # Fallback without rich
                print(output_text)

            # Display statistics
            print("\n" + "="*70)
            print("📊 REQUEST STATISTICS")
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
                print(f"\n💾 Request payload exported to: {args.output}")
                print(f"   Format: {args.format}")

            print("\n" + "="*70)
            print("✅ Request preview completed (NOT sent to server)")
            print("="*70)
            print("\nTo actually send this request, use:")
            print(f"  python main.py send-api --state-file {args.state_file} --api-type {api_type}")

        except FileNotFoundError as e:
            print(f"\n❌ Error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            self.error(f"test-request failed: {e}", exc_info=True)
            sys.exit(1)

    def cmd_apply_transition(self, args):
        """Apply transition to state and export updated state."""
        import json
        from utils.state_file_loader import state_file_loader
        from utils.state_updater import state_updater
        from utils.api_display import api_display

        try:
            # Load state file
            print(f"📂 Loading state from: {args.state_file}")
            state_json = state_file_loader.load_state_file(args.state_file)
            parsed_state = state_file_loader.parse_state_for_api(state_json)

            # Display original state info
            print("\n Original State:")
            api_display.display_state_info(parsed_state)

            # Load transition file
            print(f"\n📄 Loading transition from: {args.transition_file}")
            with open(args.transition_file, 'r', encoding='utf-8') as f:
                transition_content = f.read()

            # Display transition info
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

            original_stage = parsed_state.get('stage_id')
            updated_stage = parsed_updated.get('stage_id')
            if original_stage != updated_stage:
                print(f"   Stage ID: {original_stage or 'None'} → {updated_stage or 'None'}")

            original_step = parsed_state.get('step_id')
            updated_step = parsed_updated.get('step_id')
            if original_step != updated_step:
                print(f"   Step ID: {original_step or 'None'} → {updated_step or 'None'}")

            # Format output based on format argument
            if args.format == 'json':
                # Compact JSON
                output_text = json.dumps(updated_state, ensure_ascii=False)
            else:
                # Pretty formatted JSON
                output_text = json.dumps(updated_state, indent=2, ensure_ascii=False)

            # Export to file
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_text)

            print(f"\n💾 Updated state exported to: {args.output}")
            print(f"   Format: {args.format}")
            print(f"   Size: {len(output_text)} bytes ({len(output_text)/1024:.2f} KB)")

            print("\n" + "="*70)
            print("✅ Transition applied and state exported successfully")
            print("="*70)

        except FileNotFoundError as e:
            print(f"\n❌ Error: File not found - {e}")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            self.error(f"apply-transition failed: {e}", exc_info=True)
            sys.exit(1)

    def run(self, argv=None):
        """Run the CLI."""
        parser = self.create_parser()
        args = parser.parse_args(argv)

        # Apply runtime configuration
        from config import Config
        import json

        if args.backend_url:
            print(f"⚙️  Setting backend URL: {args.backend_url}")
            Config.set_backend_url(args.backend_url)

        if args.dslc_url:
            print(f"⚙️  Setting DSLC URL: {args.dslc_url}")
            Config.set_dslc_url(args.dslc_url)

        if args.notebook_id:
            print(f"⚙️  Setting notebook ID: {args.notebook_id}")
            Config.set_notebook_id(args.notebook_id)
            # Also set it on the code executor
            self.code_executor.notebook_id = args.notebook_id
            self.code_executor.is_kernel_ready = True

        # Apply execution control settings
        if args.max_steps:
            print(f"⚙️  Max steps: {args.max_steps}")
            self.state_machine.set_max_steps(args.max_steps)

        if args.interactive:
            print("⚙️  Interactive mode: enabled")
            self.state_machine.interactive = True

        # Apply custom context
        if args.custom_context:
            try:
                # Try to parse as JSON string
                custom_ctx = json.loads(args.custom_context)
                print(f"⚙️  Custom context loaded: {list(custom_ctx.keys())}")
                self.ai_context_store.set_custom_context(custom_ctx)
                # Also add all custom context variables to the variables dict
                for key, value in custom_ctx.items():
                    self.ai_context_store.add_variable(key, value)
            except json.JSONDecodeError:
                # Try to read as file path
                try:
                    with open(args.custom_context, 'r') as f:
                        custom_ctx = json.load(f)
                    print(f"⚙️  Custom context loaded from file: {list(custom_ctx.keys())}")
                    self.ai_context_store.set_custom_context(custom_ctx)
                    # Also add all custom context variables to the variables dict
                    for key, value in custom_ctx.items():
                        self.ai_context_store.add_variable(key, value)
                except Exception as e:
                    print(f"⚠️  Failed to load custom context: {e}")

        if not args.command:
            parser.print_help()
            return

        # Dispatch to command handler
        command_handlers = {
            'start': self.cmd_start,
            'status': self.cmd_status,
            'show': self.cmd_show,
            'list': self.cmd_list,
            'export': self.cmd_export,
            'repl': self.cmd_repl,
            'send-api': self.cmd_send_api,
            'resume': self.cmd_resume,
            'test-request': self.cmd_test_request,
            'apply-transition': self.cmd_apply_transition,
        }

        handler = command_handlers.get(args.command)
        if handler:
            try:
                handler(args)
            except Exception as e:
                self.error(f"Command failed: {e}", exc_info=True)
                print(f"\n❌ Error: {e}")
                sys.exit(1)
        else:
            print(f"Unknown command: {args.command}")
            parser.print_help()


def main():
    """Main entry point."""
    # Get default config from environment
    from config import Config

    cli = WorkflowCLI(
        max_steps=Config.MAX_EXECUTION_STEPS,
        interactive=Config.INTERACTIVE_MODE
    )
    cli.run()


if __name__ == '__main__':
    main()
