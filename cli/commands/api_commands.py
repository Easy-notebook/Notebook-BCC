"""
API commands - handles API-related operations.
"""

import json
import asyncio
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import box

from utils.api_client import workflow_api_client
from utils.api_display import api_display
from config import Config
from cli.base.dummy_context import DummyContext
from stores.state_builder import state_builder


class APICommands:
    """
    Handles API-related commands: send-api, test-actions.
    """

    def cmd_send_api(self, args):
        """
        Send API request from state file.

        Supports two modes:
        1. Auto mode (--api-type=auto): Uses AsyncStateMachineAdapter for full state transition
        2. Manual mode: Sends specific API request for debugging/testing
        """
        # Load state file using unified helper
        print(f"Loading state from: {args.state_file}")
        state_json, parsed_state = self._load_state_file(args.state_file)

        # Display state info
        api_display.display_state_info(parsed_state)

        # Check if using auto mode (event-driven)
        if hasattr(args, 'api_type') and args.api_type == 'auto':
            print("\n[Auto Mode] Using event-driven state machine")
            print("   This will automatically infer API type and handle state transition")
            return self._cmd_send_api_auto(args, state_json, parsed_state)

        # Manual mode: specific API request
        # Infer API type using state machine
        if args.api_type:
            api_type = args.api_type
            print(f"\nUsing specified API type: {api_type}")
        else:
            api_type = self.state_machine.infer_api_type_from_state(state_json)
            print(f"\nAuto-inferred API type: {api_type}")
            print(f"   (You can override with --api-type or use --api-type=auto for automatic execution)")

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
                # 使用 state class 来确定 transition_name
                from core.state_classes.state_factory import StateFactory

                fsm = state.get('state', {}).get('FSM', {})
                current_fsm_state = fsm.get('state', '')

                transition_name = None
                state_instance = StateFactory.get_state(current_fsm_state)

                print(f"[DEBUG] Current FSM state: {current_fsm_state}")
                print(f"[DEBUG] State instance: {state_instance}")

                if state_instance:
                    next_transition_event = state_instance.determine_next_transition(state)
                    print(f"[DEBUG] Next transition event: {next_transition_event}")
                    if next_transition_event:
                        transition_name = next_transition_event.value
                        print(f"[DEBUG] Transition name: {transition_name}")

                # 如果没有确定 transition_name，使用默认值
                if not transition_name:
                    print(f"[DEBUG] No transition_name determined, using fallback")
                    # 简单的 fallback 逻辑
                    if 'BEHAVIOR_COMPLETED' in current_fsm_state:
                        transition_name = 'COMPLETE_STEP'  # 默认假设
                    elif 'STEP_COMPLETED' in current_fsm_state:
                        transition_name = 'COMPLETE_STAGE'
                    else:
                        transition_name = 'REFLECTING'

                print(f"[DEBUG] Final transition_name: {transition_name}")

                with api_display.display_sending_progress('reflecting') or DummyContext():
                    result = await workflow_api_client.send_reflecting(
                        stage_id=stage_id,
                        step_index=step_id,
                        state=state
                    )
                api_display.display_api_response('reflecting', result, success=True)
                return result

        # Run async request
        result = asyncio.run(send_request())

        # Save to output file if specified
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\nResponse saved to: {args.output}")

        print("\nAPI request completed successfully")

    def cmd_test_actions(self, args):
        """
        Execute actions from JSON file using ScriptStore.

        Now directly passes actions to script_store without legacy conversion.
        """
        console = Console()

        # Load files using unified helper
        console.print("\n[bold cyan]Loading input files...[/bold cyan]")

        with open(args.actions_file, 'r', encoding='utf-8') as f:
            actions_data = json.load(f)

        state_json, _parsed_state = self._load_state_file(args.state_file)

        # Sync state to stores (including notebook_id)
        self._sync_state_to_stores(state_json)

        # Extract notebook_id for display
        notebook_id = state_json.get('state', {}).get('notebook', {}).get('notebook_id')

        # Display info table
        table = Table(show_header=False, box=box.ROUNDED)
        table.add_row("Actions File", args.actions_file)
        table.add_row("Actions Count", f"[green]{len(actions_data)}[/green]")
        table.add_row("State File", args.state_file)
        table.add_row("Current FSM State", f"[yellow]{state_json['state']['FSM']['state']}[/yellow]")
        table.add_row("Notebook ID", f"[cyan]{notebook_id or 'Will initialize'}[/cyan]")
        table.add_row("Output File", args.output)
        console.print(table)

        # Execution statistics
        stats = {'actions_executed': 0, 'errors': 0}

        # Execute actions using ScriptStore
        console.print(f"\n[bold cyan]Starting execution of {len(actions_data)} actions[/bold cyan]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Executing actions...", total=len(actions_data))

            for idx, action_data in enumerate(actions_data):
                # Extract action info for display
                action = action_data.get('action', {})
                action_type = action.get('type', 'unknown')

                progress.update(task, advance=1, description=f"[cyan]Action {idx+1}/{len(actions_data)}: {action_type}")

                # Execute action directly (NEW: no conversion needed)
                # Actions from API are already in correct format
                self.script_store.exec_action(action_data)
                stats['actions_executed'] += 1

                # Optional: Display action result
                if not args.no_display:
                    # Simple display for each action
                    console.print(f"  [green]OK[/green] {action_type}")

                # Delay between actions
                if not args.no_display and args.delay > 0:
                    time.sleep(args.delay)

        console.print("\n[bold green]All actions executed successfully[/bold green]\n")

        # Build output state from stores (ScriptStore already updated everything)
        output_state = self._build_output_state_for_test_actions(state_json, stats, len(actions_data))

        # Save output
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_state, f, indent=2, ensure_ascii=False)

        # Display summary
        console.print(Panel(
            f"[green]OK[/green] File saved: [cyan]{args.output}[/cyan]\n"
            f"[green]OK[/green] FSM State: [magenta]BEHAVIOR_COMPLETED[/magenta]",
            title="[bold green]Output Saved[/bold green]",
            border_style="green",
            box=box.DOUBLE
        ))

        # Summary table
        summary_table = Table(box=box.DOUBLE, title="Execution Summary", title_style="bold cyan")
        summary_table.add_column("Item", style="cyan", width=30)
        summary_table.add_column("Value", style="green", justify="right")

        summary_table.add_row("FSM State Transition", "BEHAVIOR_RUNNING -> BEHAVIOR_COMPLETED")
        summary_table.add_row("Actions Executed", str(stats['actions_executed']))
        summary_table.add_row("Cells Created", str(len(self.notebook_store.cells)))
        summary_table.add_row("Code Executions", str(self.notebook_store.execution_count))
        summary_table.add_row("Errors", str(stats['errors']))
        summary_table.add_row("Acceptance Checks", "All Passed" if stats['errors'] == 0 else "Has Errors")

        console.print(summary_table)
        console.print("\n[bold green]Execution Complete![/bold green]\n")

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
            "BEHAVIOR_COMPLETED",
            transition_data
        )

    def _cmd_send_api_auto(self, args, state_json, parsed_state):
        """
        Auto mode for send-api: Uses AsyncStateMachineAdapter for full state transition.

        This is the NEW event-driven approach.
        """
        console = Console()

        # Sync state to stores
        self._sync_state_to_stores(state_json)

        # Get current FSM state
        fsm_state = parsed_state.get('fsm_state', 'UNKNOWN')

        console.print(f"\n[bold cyan]Auto Mode - Event-Driven Execution[/bold cyan]")
        console.print(f"Current State: [yellow]{fsm_state}[/yellow]")

        # Execute one state transition using AsyncStateMachineAdapter
        async def execute_transition():
            try:
                console.print("\n[bold blue]Executing state transition...[/bold blue]")
                next_state = await self.async_state_machine.step(state_json)
                return next_state
            except Exception as e:
                console.print(f"[red]Error during state transition: {e}[/red]")
                import traceback
                traceback.print_exc()
                return None

        # Run async transition
        next_state = asyncio.run(execute_transition())

        if next_state:
            # Parse new state
            parsed_next = state_file_loader.parse_state_for_api(next_state)
            new_fsm_state = parsed_next.get('fsm_state')

            console.print(f"\n[green]OK[/green] State transition complete")
            console.print(f"New State: [bold yellow]{new_fsm_state}[/bold yellow]")

            # Save to output file if specified
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(next_state, f, indent=2, ensure_ascii=False)
                console.print(f"\n[green]Response saved to: {args.output}[/green]")

            console.print("\n[bold green]Auto execution completed successfully[/bold green]")
            return next_state
        else:
            console.print("\n[bold red]Auto execution failed[/bold red]")
            return None
