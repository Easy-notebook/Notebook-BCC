"""
Start command - handles workflow initialization and iteration loop.

Uses AsyncStateMachineAdapter for event-driven execution.
"""

import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timezone
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from utils.state_file_loader import state_file_loader
from utils.api_client import workflow_api_client
from utils.transition_logger import get_transition_logger


class StartCommand:
    """
    Handles 'start' command and iteration loop.
    """

    def _create_session_log_dir(self, args) -> Path:
        """
        Create session-specific log directory.

        Directory name format: YYYYMMDD_HHMMSS_command_args
        Example: 20251112_200026_start_config

        Args:
            args: Command arguments

        Returns:
            Path to session log directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Build command description
        cmd_parts = ["start"]

        if args.state_file:
            cmd_parts.append("state")
        elif args.config:
            cmd_parts.append("config")
        else:
            cmd_parts.append("traditional")

        if args.iterate:
            cmd_parts.append("iterate")

        cmd_name = "_".join(cmd_parts)

        # Create directory: logs/YYYYMMDD_HHMMSS_command/
        session_dir = Path("logs") / f"{timestamp}_{cmd_name}"
        session_dir.mkdir(parents=True, exist_ok=True)

        return session_dir

    def cmd_start(self, args):
        """Start a new workflow."""
        # Create session log directory
        self._session_log_dir = self._create_session_log_dir(args)
        print(f"📁 Session logs: {self._session_log_dir}")

        # Set transition logger to use session directory
        transition_logger = get_transition_logger()
        transition_logger.set_log_dir(str(self._session_log_dir))

        # Determine input mode
        if args.state_file:
            # Mode 1: Start from state file
            print(f"Loading initial state from: {args.state_file}")
            self._start_from_state_file(args)
        elif args.config:
            # Mode 2: Start from config file
            print(f"Loading config from: {args.config}")
            self._start_from_config(args)
        else:
            # Mode 3: Traditional mode (--problem and --context)
            self._start_traditional(args)

        # Enter iteration loop if requested
        if args.iterate:
            print(f"\nEntering iteration mode (max: {args.max_iterations} iterations)")
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

        print(f"Workflow initialized: {workflow.name}")
        print(f"  Stages: {len(workflow.stages)}")

        # Only add planning variables if they're not already set
        # This prevents overwriting custom context variables
        for key, value in planning_request.items():
            if key not in existing_vars:
                self.ai_context_store.add_variable(key, value)

        # Start execution
        self.pipeline_store.start_workflow_execution(self.state_machine)

        print(f"Workflow started")
        print(f"  Current state: {self.state_machine.state.value}")
        print(f"Notebook will be saved to: {self.notebook_manager.notebooks_dir}/")

    def _start_from_config(self, args):
        """Start workflow from config file (e.g., housing_config.json)."""
        config_path = Path(args.config)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {args.config}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        print(f"Config loaded")

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
            print(f"Building initial IDLE state for iteration")

            # Build initial state JSON in IDLE state (ready for planning API)
            template_path = getattr(args, 'idle_template', None)
            initial_state = self._build_idle_state(user_problem, user_submit_files, template_path)
            self._current_state = initial_state

            print(f"  FSM State: IDLE")
            print(f"  Ready for iteration")
        else:
            # Traditional mode: initialize workflow and start execution
            workflow = self.pipeline_store.initialize_workflow(planning_request)
            print(f"Workflow initialized: {workflow.name}")
            print(f"  Stages: {len(workflow.stages)}")

            # Start execution
            self.pipeline_store.start_workflow_execution(self.state_machine)
            print(f"Workflow started from config")
            print(f"  Current state: {self.state_machine.state.value}")

    def _build_idle_state(self, user_problem, user_submit_files, template_path=None):
        """Build an initial IDLE state JSON for iteration mode."""
        import uuid

        # Try multiple template locations in order of priority
        template_candidates = []

        if template_path:
            template_candidates.append(Path(template_path))

        project_root = Path(__file__).parent.parent.parent
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

                # Use existing notebook_id from code_executor if available, otherwise generate new one
                if self.code_executor.notebook_id:
                    idle_state['state']['notebook']['notebook_id'] = self.code_executor.notebook_id
                    print(f"  Using existing notebook_id: {self.code_executor.notebook_id[:16]}...")
                else:
                    new_notebook_id = uuid.uuid4().hex
                    idle_state['state']['notebook']['notebook_id'] = new_notebook_id
                    print(f"  Generated new notebook_id: {new_notebook_id[:16]}...")

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
        state_path = Path(args.state_file)
        if not state_path.exists():
            raise FileNotFoundError(f"State file not found: {args.state_file}")

        # Load state file using unified helper
        state_json, parsed_state = self._load_state_file(args.state_file)

        fsm_state = parsed_state.get('fsm_state', 'UNKNOWN')

        print(f"State loaded")
        print(f"  FSM State: {fsm_state}")
        print(f"  Stage: {parsed_state.get('stage_id', 'None')}")
        print(f"  Step: {parsed_state.get('step_id', 'None')}")

        # Extract and restore context
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

            # Set notebook_id on code_executor to reuse existing notebook
            if notebook_id:
                # Sync to both notebook_store and code_executor
                self.notebook_store.notebook_id = notebook_id
                self.code_executor.notebook_id = notebook_id
                self.code_executor.is_kernel_ready = True
                print(f"  Notebook: {cell_count} cells, ID: {notebook_id[:8]}... (reusing existing notebook)")
            else:
                print(f"  Notebook: {cell_count} cells (no notebook_id, will create new)")

        # Store current state for iteration
        self._current_state = state_json
        # Store original state file path for generating output paths
        self._original_state_file = state_path.resolve()

        print(f"Workflow started from state file")

        # Auto-enable iteration mode if state is not IDLE and --iterate not specified
        if not args.iterate and fsm_state.upper() != 'IDLE':
            print(f"  Warning: State is {fsm_state} (not IDLE)")
            print(f"  Auto-enabling iteration mode to continue execution")
            print(f"     (Use --iterate explicitly or add '--no-auto-iterate' to disable)")
            # Auto-enable iteration mode
            args.iterate = True
        elif args.iterate:
            print(f"  Ready for iteration mode")
        else:
            print(f"  Ready for manual API calls")

    def _generate_output_path(self, new_fsm_state: str, iteration: int) -> str:
        """
        Generate output file path for state snapshot.

        Saves to session log directory if available, otherwise to current/original directory.

        Args:
            new_fsm_state: New FSM state name
            iteration: Current iteration number

        Returns:
            Full path for state snapshot file
        """
        import re

        # Normalize FSM state name
        fsm_normalized = new_fsm_state.upper().replace('_', '_')

        # If we have a session log directory, save there
        if hasattr(self, '_session_log_dir') and self._session_log_dir:
            filename = f"state_{iteration:02d}_{fsm_normalized}.json"
            output_path = self._session_log_dir / filename
            return str(output_path)

        # Check if we have original state file path
        if not hasattr(self, '_original_state_file') or not self._original_state_file:
            # Fallback: use current directory with iteration number and FSM state name
            return f"state_iteration_{iteration:02d}_{fsm_normalized}.json"

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
            new_filename = f"{new_seq:02d}_STATE_{fsm_normalized}.json"
        else:
            # No sequence number found - use iteration-based naming
            new_filename = f"state_iteration_{iteration:02d}_{fsm_normalized}.json"

        # Return full path in original directory
        output_path = original_dir / new_filename
        return str(output_path)

    def _run_iteration_loop(self, max_iterations):
        """
        Run automatic iteration loop using event-driven state machine.

        This is the NEW implementation using AsyncStateMachineAdapter.
        All API calls and state transitions are handled by the state machine.
        """
        # Suppress verbose logging during iteration
        logging.getLogger('silantui').setLevel(logging.WARNING)

        if not hasattr(self, '_current_state'):
            print("Error: No state loaded. Cannot iterate without initial state.")
            print("   Use --state-file to provide initial state.")
            return

        console = Console()
        iteration = 0
        current_state = self._current_state
        parsed_next = None

        console.print(Panel.fit(
            "[bold cyan]EVENT-DRIVEN ITERATION LOOP[/bold cyan]\n"
            f"Max iterations: {max_iterations}\n"
            "[dim]Using AsyncStateMachineAdapter[/dim]",
            border_style="cyan",
            box=box.ROUNDED
        ))

        # Set API client on async state machine (this will inject into StateFactory and TransitionCoordinator)
        self.async_state_machine.set_api_client(workflow_api_client)

        # Create a single persistent event loop for all iterations
        async def run_all_iterations():
            nonlocal iteration, current_state, parsed_next

            while iteration < max_iterations:
                iteration += 1

                # Sync current_state to stores before each iteration
                self._sync_state_to_stores(current_state)

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
                    title=f"[bold]Iteration {iteration}[/bold]",
                    border_style="blue",
                    box=box.ROUNDED
                ))

                # Check if we've reached a terminal state
                terminal_states = ['COMPLETE', 'ERROR', 'ABORTED', 'WORKFLOW_COMPLETED']
                if fsm_state in terminal_states:
                    console.print(f"[green]Reached terminal state: {fsm_state}[/green]")
                    break

                # ========================================
                # NEW: Use AsyncStateMachineAdapter to handle everything
                # ========================================
                with console.status(f"[bold blue]State Machine Step...[/bold blue]", spinner="dots"):
                    try:
                        # One single call handles: API inference, API call, state transition
                        # Returns (new_state, transition_name)
                        next_state, transition_name = await self.async_state_machine.step(current_state)
                    except Exception as e:
                        console.print(f"[red]Error during state machine step: {e}[/red]")
                        self.error(f"State machine error: {e}", exc_info=True)
                        break

                console.print(f"[green]OK[/green] State transition complete")

                # Parse new state
                parsed_next = state_file_loader.parse_state_for_api(next_state)
                new_fsm_state = parsed_next.get('fsm_state')
                new_stage = parsed_next.get('stage_id')
                new_step = parsed_next.get('step_id')

                # Display transition name (returned from state machine)
                if transition_name:
                    console.print(f"  └─ Transition: [yellow]{transition_name}[/yellow]")
                else:
                    # Fallback: 如果无法确定，显示状态转换
                    console.print(f"  └─ Transition: [yellow]{fsm_state}→{new_fsm_state}[/yellow]")

                # Update current state for next iteration
                current_state = next_state
                self._current_state = next_state

                # Show transition result
                result_table = Table(show_header=False, box=None, padding=(0, 1))
                result_table.add_column(style="dim")
                result_table.add_column(style="green")
                result_table.add_row("-> New State", f"[bold]{new_fsm_state}[/bold]")
                if new_stage and new_stage != stage_id:
                    result_table.add_row("-> Stage", new_stage)
                if new_step and new_step != step_id:
                    result_table.add_row("-> Step", new_step)

                console.print(result_table)

                # Save state snapshot with smart path generation
                snapshot_file = self._generate_output_path(new_fsm_state, iteration)
                with open(snapshot_file, 'w', encoding='utf-8') as f:
                    json.dump(next_state, f, indent=2, ensure_ascii=False)
                console.print(f"[dim]Snapshot: {snapshot_file}[/dim]\n")

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
            title="[bold green]Iteration Complete[/bold green]",
            border_style="green",
            box=box.ROUNDED
        ))

        # Restore logging
        logging.getLogger('silantui').setLevel(logging.INFO)
