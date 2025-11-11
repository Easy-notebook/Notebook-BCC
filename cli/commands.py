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
from stores.state_builder import state_builder
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

    # =================================================================
    # CLI Helper Methods - Unified utilities to reduce code duplication
    # =================================================================

    def _load_state_file(self, state_file: str):
        """
        Load and parse state file (unified helper).

        Args:
            state_file: Path to state JSON file

        Returns:
            Tuple of (state_json, parsed_state)
        """
        from utils.state_file_loader import state_file_loader
        state_json = state_file_loader.load_state_file(state_file)
        parsed_state = state_file_loader.parse_state_for_api(state_json)
        return state_json, parsed_state

    def _infer_api_type(self, state_json, override=None):
        """
        Infer API type from state with optional override.

        Args:
            state_json: State JSON dict
            override: Optional explicit API type override

        Returns:
            API type string ('planning', 'generating', or 'reflecting')
        """
        from utils.state_file_loader import state_file_loader
        if override:
            return override
        return state_file_loader.infer_api_type(state_json)

    def _convert_action_to_step(self, action_data):
        """
        Convert action JSON to ExecutionStep.
        Uses ScriptStore._dict_to_execution_step to avoid code duplication.

        Args:
            action_data: Action dict from API response

        Returns:
            ExecutionStep object
        """
        # Debug: Log the incoming action_data structure
        self.script_store.debug(f"[Commands] Converting action_data keys: {list(action_data.keys())[:10]}")
        if 'action' in action_data:
            # Nested structure: {action: {type: ..., content: ...}}
            actual_action = action_data['action']
        else:
            # Flat structure: {type: ..., content: ...}
            actual_action = action_data

        self.script_store.debug(f"[Commands] Actual action keys: {list(actual_action.keys())[:10]}")
        return ScriptStore._dict_to_execution_step(actual_action)

    def _execute_actions_internal(self, actions, current_state):
        """
        Execute actions using ScriptStore and return updated state with effects.

        Args:
            actions: List of action dicts from API response
            current_state: Current state dict

        Returns:
            Updated state dict with executed actions and effects
        """
        # Execute all actions using ScriptStore
        for action_data in actions:
            step = self._convert_action_to_step(action_data)
            self.script_store.exec_action(step)

        # Build updated state from stores
        return self._build_state_from_stores(current_state)

    def _build_state_from_stores(self, base_state):
        """
        Build updated state from current store states.
        Uses StateBuilder to avoid code duplication.

        Args:
            base_state: Base state dict to update

        Returns:
            Updated state dict with current notebook and effects
        """
        # Use StateBuilder to avoid duplication
        return state_builder.build_state_from_stores(
            base_state,
            self.notebook_store,
            self.ai_context_store
        )

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
        start_parser.add_argument('--config', type=str, help='Path to config JSON file (e.g., housing_config.json)')
        start_parser.add_argument('--state-file', type=str, help='Path to initial state JSON file (e.g., 00_STATE_IDLE.json)')
        start_parser.add_argument('--idle-template', type=str, help='Path to IDLE state template JSON file')
        start_parser.add_argument('--iterate', action='store_true', help='Enable automatic iteration (loop through states)')
        start_parser.add_argument('--max-iterations', type=int, default=10, help='Maximum iterations in loop mode (default: 10)')

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

        # Test-actions command (NEW) - Execute actions from JSON with streaming display
        test_actions_parser = subparsers.add_parser('test-actions',
                                                    help='Execute actions from JSON file with rich streaming display')
        test_actions_parser.add_argument('--actions-file', type=str, required=True,
                                        help='Path to actions JSON file')
        test_actions_parser.add_argument('--state-file', type=str, required=True,
                                        help='Path to input state JSON file')
        test_actions_parser.add_argument('--output', type=str, required=True,
                                        help='Output file for updated state JSON')
        test_actions_parser.add_argument('--no-display', action='store_true',
                                        help='Disable rich display (faster execution)')
        test_actions_parser.add_argument('--delay', type=float, default=0.3,
                                        help='Delay between actions in seconds (default: 0.3)')

        # Export-markdown command - Export notebook from state to markdown
        export_md_parser = subparsers.add_parser('export-markdown',
                                                help='Export notebook from state file to markdown')
        export_md_parser.add_argument('--state-file', type=str, required=True,
                                     help='Path to state JSON file')
        export_md_parser.add_argument('--output', type=str, required=False,
                                     help='Output markdown file path (default: stdout)')

        return parser

    def cmd_start(self, args):
        """Start a new workflow."""
        import json

        # Determine input mode
        if args.state_file:
            # Mode 1: Start from state file
            print(f"📂 Loading initial state from: {args.state_file}")
            self._start_from_state_file(args)
        elif args.config:
            # Mode 2: Start from config file
            print(f"📂 Loading config from: {args.config}")
            self._start_from_config(args)
        else:
            # Mode 3: Traditional mode (--problem and --context)
            self._start_traditional(args)

        # Enter iteration loop if requested
        if args.iterate:
            print(f"\n🔄 Entering iteration mode (max: {args.max_iterations} iterations)")
            self._run_iteration_loop(args.max_iterations)

    def _start_traditional(self, args):
        """Traditional start mode with --problem and --context."""
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

    def _start_from_config(self, args):
        """Start workflow from config file (e.g., housing_config.json)."""
        import json
        from pathlib import Path

        config_path = Path(args.config)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {args.config}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        print(f"✓ Config loaded")

        # Extract config fields
        user_problem = config.get('user_problem', 'Data Analysis Task')
        user_submit_files = config.get('user_submit_files', [])

        print(f"  Problem: {user_problem}")
        print(f"  Files: {user_submit_files}")

        # Add to AI context
        self.ai_context_store.add_variable('user_problem', user_problem)
        self.ai_context_store.add_variable('user_submit_files', user_submit_files)

        # Build planning request
        planning_request = {
            'problem_name': 'Analysis',
            'user_goal': user_problem,
            'problem_description': user_problem,
            'context_description': f'Files: {user_submit_files}',
        }

        # Add planning variables
        for key, value in planning_request.items():
            self.ai_context_store.add_variable(key, value)

        # If iterate mode is enabled, build initial IDLE state instead of starting execution
        if args.iterate:
            print(f"✓ Building initial IDLE state for iteration")

            # Build initial state JSON in IDLE state (ready for planning API)
            template_path = getattr(args, 'idle_template', None)
            initial_state = self._build_idle_state(user_problem, user_submit_files, template_path)
            self._current_state = initial_state

            print(f"  FSM State: IDLE")
            print(f"  Ready for iteration")
        else:
            # Traditional mode: initialize workflow and start execution
            workflow = self.pipeline_store.initialize_workflow(planning_request)
            print(f"✓ Workflow initialized: {workflow.name}")
            print(f"  Stages: {len(workflow.stages)}")

            # Start execution
            self.pipeline_store.start_workflow_execution(self.state_machine)
            print(f"✓ Workflow started from config")
            print(f"  Current state: {self.state_machine.state.value}")

    def _build_idle_state(self, user_problem, user_submit_files, template_path=None):
        """Build an initial IDLE state JSON for iteration mode."""
        import json
        import uuid
        from pathlib import Path
        from datetime import datetime, timezone

        # Try multiple template locations in order of priority:
        # 1. Explicit template path from command line
        # 2. templates/STATE_IDLE.json in project root
        # 3. Any STATE_IDLE.json or 00_STATE_IDLE.json in current directory
        # 4. Search in docs/examples/**/payloads/

        template_candidates = []

        if template_path:
            template_candidates.append(Path(template_path))

        project_root = Path(__file__).parent.parent
        template_candidates.extend([
            project_root / 'templates/STATE_IDLE.json',
            Path.cwd() / 'STATE_IDLE.json',
            Path.cwd() / '00_STATE_IDLE.json',
        ])

        # Search in docs/examples
        examples_dir = project_root / 'docs/examples'
        if examples_dir.exists():
            template_candidates.extend(examples_dir.rglob('**/STATE_IDLE.json'))
            template_candidates.extend(examples_dir.rglob('**/00_STATE_IDLE.json'))

        # Find first existing template
        for candidate in template_candidates:
            if candidate.exists():
                print(f"  Using template: {candidate}")
                with open(candidate, 'r', encoding='utf-8') as f:
                    idle_state = json.load(f)

                # Replace user variables
                idle_state['state']['variables']['user_problem'] = user_problem
                idle_state['state']['variables']['user_submit_files'] = user_submit_files

                # Generate new notebook_id
                idle_state['state']['notebook']['notebook_id'] = uuid.uuid4().hex

                # Update timestamp
                idle_state['state']['FSM']['timestamp'] = datetime.now(timezone.utc).isoformat()

                return idle_state

        # No template found - require user to provide one
        raise FileNotFoundError(
            "No IDLE state template found. Please provide one of:\n"
            "  1. Use --idle-template <path> to specify template file\n"
            "  2. Create templates/STATE_IDLE.json in project root\n"
            "  3. Put STATE_IDLE.json in current directory\n"
            "  4. Use existing state file with --state-file instead of --config"
        )

    def _start_from_state_file(self, args):
        """Start workflow from state file (e.g., 00_STATE_IDLE.json)."""
        import json
        from pathlib import Path

        state_path = Path(args.state_file)
        if not state_path.exists():
            raise FileNotFoundError(f"State file not found: {args.state_file}")

        # Load state file using unified helper
        state_json, parsed_state = self._load_state_file(args.state_file)

        fsm_state = parsed_state.get('fsm_state', 'UNKNOWN')

        print(f"✓ State loaded")
        print(f"  FSM State: {fsm_state}")
        print(f"  Stage: {parsed_state.get('stage_id', 'None')}")
        print(f"  Step: {parsed_state.get('step_id', 'None')}")

        # Extract and restore context
        from utils.state_file_loader import state_file_loader
        context_data = state_file_loader.extract_context(state_json)

        # Restore variables
        variables = context_data.get('variables', {})
        self.ai_context_store.set_variables(variables)
        print(f"  Variables: {len(variables)}")

        # Restore effects
        effects = context_data.get('effects', {})
        self.ai_context_store.set_effect(effects)
        print(f"  Effects: {len(effects.get('current', []))}")

        # Restore notebook data
        notebook_data = state_json.get('state', {}).get('notebook', {})
        if notebook_data:
            self.notebook_store.from_dict(notebook_data)
            cell_count = len(notebook_data.get('cells', []))
            notebook_id = notebook_data.get('notebook_id')
            print(f"  Notebook: {cell_count} cells" + (f", ID: {notebook_id[:8]}..." if notebook_id else ""))

        # Store current state for iteration
        self._current_state = state_json
        # Store original state file path for generating output paths
        self._original_state_file = state_path.resolve()

        print(f"✓ Workflow started from state file")

        # Auto-enable iteration mode if state is not IDLE and --iterate not specified
        if not args.iterate and fsm_state.upper() != 'IDLE':
            print(f"  ⚠️  State is {fsm_state} (not IDLE)")
            print(f"  💡 Auto-enabling iteration mode to continue execution")
            print(f"     (Use --iterate explicitly or add '--no-auto-iterate' to disable)")
            # Auto-enable iteration mode
            args.iterate = True
        elif args.iterate:
            print(f"  Ready for iteration mode")
        else:
            print(f"  Ready for manual API calls")

    def _generate_output_path(self, new_fsm_state: str, iteration: int) -> str:
        """
        Generate output file path based on original state file and new FSM state.

        Args:
            new_fsm_state: New FSM state (e.g., 'BEHAVIOR_COMPLETE')
            iteration: Current iteration number

        Returns:
            Path to output file

        Examples:
            Input: 03_STATE_Behavior_Running.json
            FSM: BEHAVIOR_COMPLETE
            Output: 04_STATE_BEHAVIOR_COMPLETE.json (in same directory)
        """
        import re
        from pathlib import Path

        # Check if we have original state file path
        if not hasattr(self, '_original_state_file') or not self._original_state_file:
            # Fallback: use current directory with iteration number
            return f"state_iteration_{iteration:02d}.json"

        original_path = Path(self._original_state_file)
        original_name = original_path.stem  # Without extension
        original_dir = original_path.parent

        # Try to extract sequence number from original filename
        # Pattern: NN_STATE_... or just NN_...
        match = re.match(r'^(\d+)_', original_name)

        if match:
            # Found sequence number - increment it
            old_seq = int(match.group(1))
            new_seq = old_seq + 1

            # Build new filename with incremented sequence and new FSM state
            # Convert FSM state to uppercase and replace underscores
            fsm_normalized = new_fsm_state.upper().replace('_', '_')
            new_filename = f"{new_seq:02d}_STATE_{fsm_normalized}.json"
        else:
            # No sequence number found - use iteration-based naming
            fsm_normalized = new_fsm_state.upper().replace('_', '_')
            new_filename = f"state_iteration_{iteration:02d}_{fsm_normalized}.json"

        # Return full path in original directory
        output_path = original_dir / new_filename
        return str(output_path)

    def _run_iteration_loop(self, max_iterations):
        """Run automatic iteration loop: send API -> get response -> apply transition -> repeat."""
        import asyncio
        import json
        import logging
        from rich.console import Console
        from rich.panel import Panel
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
        from rich.table import Table
        from rich import box
        from utils.state_file_loader import state_file_loader
        from utils.api_client import workflow_api_client
        from utils.state_updater import state_updater
        from config import Config

        # Suppress verbose logging during iteration
        logging.getLogger('silantui').setLevel(logging.WARNING)

        if not hasattr(self, '_current_state'):
            print("❌ No state loaded. Cannot iterate without initial state.")
            print("   Use --state-file to provide initial state.")
            return

        console = Console()
        iteration = 0
        current_state = self._current_state
        parsed_next = None

        console.print(Panel.fit(
            "[bold cyan]🔄 ITERATION LOOP[/bold cyan]\n"
            f"Max iterations: {max_iterations}",
            border_style="cyan",
            box=box.ROUNDED
        ))

        # Create a single persistent event loop for all iterations
        async def run_all_iterations():
            nonlocal iteration, current_state, parsed_next

            while iteration < max_iterations:
                iteration += 1

                # Parse current state
                parsed_state = state_file_loader.parse_state_for_api(current_state)
                fsm_state = parsed_state.get('fsm_state', 'UNKNOWN')
                stage_id = parsed_state.get('stage_id')
                step_id = parsed_state.get('step_id')

                # Create iteration header
                header_table = Table(show_header=False, box=None, padding=(0, 1))
                header_table.add_column(style="bold cyan")
                header_table.add_column(style="white")
                header_table.add_row("Iteration", f"{iteration}/{max_iterations}")
                header_table.add_row("FSM State", f"[yellow]{fsm_state}[/yellow]")
                if stage_id:
                    header_table.add_row("Stage", stage_id)
                if step_id:
                    header_table.add_row("Step", step_id)

                console.print(Panel(
                    header_table,
                    title=f"[bold]🔁 Iteration {iteration}[/bold]",
                    border_style="blue",
                    box=box.ROUNDED
                ))

                # Check if we've reached a terminal state
                terminal_states = ['COMPLETE', 'ERROR', 'ABORTED']
                if fsm_state in terminal_states:
                    console.print(f"[green]✓ Reached terminal state: {fsm_state}[/green]")
                    break

                # Infer API type from FSM state
                api_type = state_file_loader.infer_api_type(current_state)

                try:
                    # Send API request with spinner
                    with console.status(f"[bold blue]Calling {api_type} API...[/bold blue]", spinner="dots"):
                        if api_type == 'planning':
                            response = await workflow_api_client.send_feedback(
                                stage_id=stage_id or 'initial',
                                step_index=step_id or 'none',
                                state=current_state
                            )
                        elif api_type == 'generating':
                            actions = []
                            async for action in workflow_api_client.fetch_behavior_actions(
                                stage_id=stage_id or 'unknown',
                                step_index=step_id or 'unknown',
                                state=current_state,
                                stream=False
                            ):
                                actions.append(action)
                            response = {'actions': actions, 'count': len(actions)}
                            current_state = self._execute_actions_internal(actions, current_state)
                        elif api_type == 'reflecting':
                            response = await workflow_api_client.send_reflecting(
                                stage_id=stage_id or 'unknown',
                                step_index=step_id or 'unknown',
                                state=current_state
                            )
                        else:
                            raise ValueError(f"Unknown API type: {api_type}")

                    console.print(f"[green]✓[/green] {api_type.capitalize()} response received")

                    # Show actions info and execution for generating
                    if api_type == 'generating':
                        num_actions = len(response['actions'])
                        console.print(f"  └─ Received [cyan]{num_actions}[/cyan] actions")
                        console.print(f"  └─ [yellow]⚙️  Executing actions...[/yellow]")

                    # Apply transition to get next state

                    # Convert response to format for state_updater
                    if api_type == 'planning':
                        # Planning response is already in XML format
                        transition_content = response
                    elif api_type == 'generating':
                        # Generating response needs to be converted
                        transition_content = json.dumps(response)
                    elif api_type == 'reflecting':
                        # Reflecting response is in XML format
                        transition_content = response
                    else:
                        transition_content = str(response)

                    # Apply transition to update state
                    next_state = state_updater.apply_transition(
                        state=current_state,
                        transition_response=transition_content,
                        transition_type=api_type
                    )

                    # Update current state for next iteration
                    current_state = next_state
                    self._current_state = next_state

                    # Parse and display new state
                    parsed_next = state_file_loader.parse_state_for_api(next_state)
                    new_fsm_state = parsed_next.get('fsm_state', 'UNKNOWN')
                    new_stage = parsed_next.get('stage_id')
                    new_step = parsed_next.get('step_id')

                    # Show transition result
                    result_table = Table(show_header=False, box=None, padding=(0, 1))
                    result_table.add_column(style="dim")
                    result_table.add_column(style="green")
                    result_table.add_row("→ New State", f"[bold]{new_fsm_state}[/bold]")
                    if new_stage and new_stage != stage_id:
                        result_table.add_row("→ Stage", new_stage)
                    if new_step and new_step != step_id:
                        result_table.add_row("→ Step", new_step)

                    console.print(result_table)

                    # Save state snapshot with smart path generation
                    snapshot_file = self._generate_output_path(new_fsm_state, iteration)
                    with open(snapshot_file, 'w', encoding='utf-8') as f:
                        json.dump(next_state, f, indent=2, ensure_ascii=False)
                    console.print(f"[dim]💾 Snapshot: {snapshot_file}[/dim]\n")

                except Exception as e:
                    console.print(f"[red]❌ Error: {e}[/red]")
                    logging.getLogger('silantui').setLevel(logging.INFO)  # Re-enable for traceback
                    self.error(f"Iteration failed: {e}", exc_info=True)
                    break


        asyncio.run(run_all_iterations())
        # Summary
        final_fsm = 'UNKNOWN'
        if parsed_next:
            final_fsm = parsed_next.get('fsm_state', 'UNKNOWN')
        else:
            final_parsed = state_file_loader.parse_state_for_api(current_state)
            final_fsm = final_parsed.get('fsm_state', 'UNKNOWN')

        summary = Table(show_header=False, box=None, padding=(0, 1))
        summary.add_column(style="bold cyan")
        summary.add_column(style="white")
        summary.add_row("Total Iterations", str(iteration))
        summary.add_row("Final State", f"[yellow]{final_fsm}[/yellow]")

        console.print(Panel(
            summary,
            title="[bold green]✅ Iteration Complete[/bold green]",
            border_style="green",
            box=box.ROUNDED
        ))

        # Restore logging
        logging.getLogger('silantui').setLevel(logging.INFO)

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
        from utils.api_client import workflow_api_client
        from utils.api_display import api_display
        from config import Config

        try:
            # Load state file using unified helper
            print(f"📂 Loading state from: {args.state_file}")
            state_json, parsed_state = self._load_state_file(args.state_file)

            # Display state info
            api_display.display_state_info(parsed_state)

            # Infer API type using unified helper
            api_type = self._infer_api_type(state_json, args.api_type)
            if args.api_type:
                print(f"\n🎯 Using specified API type: {api_type}")
            else:
                print(f"\n🔍 Auto-inferred API type: {api_type}")
                print(f"   (You can override with --api-type)")

            # Extract parameters
            stage_id = parsed_state['stage_id'] or 'none'
            step_id = parsed_state['step_id'] or 'none'
            # Use original state JSON directly (already has observation + state)
            state = state_json

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
        from utils.api_display import api_display

        try:
            # Load state file using unified helper
            print(f"📂 Loading state from: {args.state_file}")
            state_json, parsed_state = self._load_state_file(args.state_file)

            # Display state info
            api_display.display_state_info(parsed_state)

            # Extract context
            from utils.state_file_loader import state_file_loader
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
        from utils.api_display import api_display
        from config import Config

        try:
            # Load state file using unified helper
            print(f"📂 Loading state from: {args.state_file}")
            state_json, parsed_state = self._load_state_file(args.state_file)

            # Display state info
            api_display.display_state_info(parsed_state)

            # Infer API type using unified helper
            api_type = self._infer_api_type(state_json, args.api_type)
            if args.api_type:
                print(f"\n🎯 Using specified API type: {api_type}")
            else:
                print(f"\n🔍 Auto-inferred API type: {api_type}")
                print(f"   (You can override with --api-type)")

            # Extract parameters
            stage_id = parsed_state['stage_id'] or 'none'
            step_id = parsed_state['step_id'] or 'none'
            # Use original state JSON directly (already has observation + state)
            state = state_json

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
        from utils.state_updater import state_updater
        from utils.api_display import api_display

        try:
            # Load state file using unified helper
            print(f"📂 Loading state from: {args.state_file}")
            state_json, parsed_state = self._load_state_file(args.state_file)

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
            from utils.state_file_loader import state_file_loader
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

    def cmd_test_actions(self, args):
        """Execute actions from JSON file using ScriptStore (refactored to use existing tools)."""
        import json
        import time
        from datetime import datetime, timezone

        try:
            # Import rich for display
            from rich.console import Console
            from rich.panel import Panel
            from rich.table import Table
            from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
            from rich import box

            console = Console()

            # Load files using unified helper
            console.print("\n[bold cyan]📂 加载输入文件...[/bold cyan]")

            with open(args.actions_file, 'r', encoding='utf-8') as f:
                actions_data = json.load(f)

            state_json, parsed_state = self._load_state_file(args.state_file)

            # Extract and set notebook_id from state
            notebook_id = state_json.get('state', {}).get('notebook', {}).get('notebook_id')
            if notebook_id:
                console.print(f"[cyan]📓 Using notebook_id from state: {notebook_id}[/cyan]")
                self.code_executor.notebook_id = notebook_id
                self.code_executor.is_kernel_ready = True
                # CRITICAL: Also set notebook_id in notebook_store for consistency
                self.notebook_store.notebook_id = notebook_id
            else:
                console.print("[yellow]⚠️  Warning: No notebook_id found in state, will initialize new kernel[/yellow]")

            # Display info table
            table = Table(show_header=False, box=box.ROUNDED)
            table.add_row("Actions 文件", args.actions_file)
            table.add_row("Actions 数量", f"[green]{len(actions_data)}[/green]")
            table.add_row("State 文件", args.state_file)
            table.add_row("当前 FSM 状态", f"[yellow]{state_json['state']['FSM']['state']}[/yellow]")
            table.add_row("Notebook ID", f"[cyan]{notebook_id or 'Will initialize'}[/cyan]")
            table.add_row("输出文件", args.output)
            console.print(table)

            # Execution statistics
            stats = {'actions_executed': 0, 'errors': 0}

            # Execute actions using ScriptStore
            console.print(f"\n[bold cyan]⚙️  开始执行 {len(actions_data)} 个动作 (使用 ScriptStore)[/bold cyan]\n")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console
            ) as progress:
                task = progress.add_task("[cyan]执行动作...", total=len(actions_data))

                for idx, action_data in enumerate(actions_data):
                    action = action_data.get('action', {})
                    action_type = action.get('type')

                    progress.update(task, advance=1, description=f"[cyan]动作 {idx+1}/{len(actions_data)}: {action_type}")

                    try:
                        # Convert to ExecutionStep and execute using ScriptStore
                        step = self._convert_action_to_step(action_data)
                        self.script_store.exec_action(step)
                        stats['actions_executed'] += 1

                        # Optional: Display action result
                        if not args.no_display:
                            # Simple display for each action
                            console.print(f"  [green]✓[/green] {action_type}")

                    except Exception as e:
                        stats['errors'] += 1
                        if not args.no_display:
                            console.print(f"  [red]✗[/red] {action_type}: {str(e)}")
                        self.error(f"Action failed: {action_type} - {e}", exc_info=True)

                    # Delay between actions
                    if not args.no_display and args.delay > 0:
                        time.sleep(args.delay)

            console.print("\n[bold green]✅ 所有动作执行完成[/bold green]\n")

            # Build output state from stores (ScriptStore already updated everything)
            output_state = self._build_output_state_for_test_actions(state_json, stats, len(actions_data))

            # Save output
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(output_state, f, indent=2, ensure_ascii=False)

            # Display summary
            console.print(Panel(
                f"[green]✓[/green] 文件已保存: [cyan]{args.output}[/cyan]\n"
                f"[green]✓[/green] FSM 状态: [magenta]BEHAVIOR_COMPLETE[/magenta]",
                title="[bold green]💾 输出已保存[/bold green]",
                border_style="green",
                box=box.DOUBLE
            ))

            # Summary table
            summary_table = Table(box=box.DOUBLE, title="执行摘要", title_style="bold cyan")
            summary_table.add_column("项目", style="cyan", width=30)
            summary_table.add_column("数值", style="green", justify="right")

            summary_table.add_row("FSM 状态转换", "BEHAVIOR_RUNNING → BEHAVIOR_COMPLETE")
            summary_table.add_row("执行的动作数", str(stats['actions_executed']))
            summary_table.add_row("创建的单元格数", str(len(self.notebook_store.cells)))
            summary_table.add_row("执行的代码数", str(self.notebook_store.execution_count))
            summary_table.add_row("错误数", str(stats['errors']))
            summary_table.add_row("验收检查", "✓ 全部通过" if stats['errors'] == 0 else "✗ 有错误")

            console.print(summary_table)
            console.print("\n[bold green]🎉 执行完成！[/bold green]\n")

        except FileNotFoundError as e:
            print(f"\n❌ Error: File not found - {e}")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            self.error(f"test-actions failed: {e}", exc_info=True)
            sys.exit(1)

    def _build_output_state_for_test_actions(self, base_state, stats, total_actions):
        """
        Build output state for test-actions command.
        Uses StateBuilder to avoid code duplication.
        """
        # Prepare transition data
        transition_data = {
            "transition_type": "COMPLETE_ACTION",
            "actions_applied": total_actions,
            "cells_added": len(self.notebook_store.cells),
            "code_executed": self.notebook_store.execution_count,
            "acceptance_checks_passed": stats['errors'] == 0
        }

        # Use StateBuilder to avoid duplication
        return state_builder.build_complete_state(
            base_state,
            self.notebook_store,
            self.ai_context_store,
            "BEHAVIOR_COMPLETE",
            transition_data
        )

    def cmd_export_markdown(self, args):
        """Export notebook from state file to markdown."""
        try:
            from utils.notebook_exporter import NotebookExporter

            print(f"\n📂 Loading state file: {args.state_file}")

            # Export to markdown
            markdown = NotebookExporter.export_from_state_file(
                args.state_file,
                args.output
            )

            if args.output:
                print(f"✅ Markdown exported to: {args.output}")
            else:
                print("\n" + "="*60)
                print(markdown)
                print("="*60)

        except FileNotFoundError as e:
            print(f"\n❌ Error: File not found - {e}")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            self.error(f"export-markdown failed: {e}", exc_info=True)
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
            'test-actions': self.cmd_test_actions,
            'export-markdown': self.cmd_export_markdown,
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
