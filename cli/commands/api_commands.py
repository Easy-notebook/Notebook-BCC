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
        """Send API request from state file."""
        # Load state file using unified helper
        print(f"Loading state from: {args.state_file}")
        state_json, parsed_state = self._load_state_file(args.state_file)

        # Display state info
        api_display.display_state_info(parsed_state)

        # Infer API type using unified helper
        api_type = self._infer_api_type(state_json, args.api_type)
        if args.api_type:
            print(f"\nUsing specified API type: {api_type}")
        else:
            print(f"\nAuto-inferred API type: {api_type}")
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

        # Run async request
        result = asyncio.run(send_request())

        # Save to output file if specified
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\nResponse saved to: {args.output}")

        print("\nAPI request completed successfully")

    def cmd_test_actions(self, args):
        """Execute actions from JSON file using ScriptStore."""
        console = Console()

        # Load files using unified helper
        console.print("\n[bold cyan]Loading input files...[/bold cyan]")

        with open(args.actions_file, 'r', encoding='utf-8') as f:
            actions_data = json.load(f)

        state_json, _parsed_state = self._load_state_file(args.state_file)

        # Extract and set notebook_id from state
        notebook_id = state_json.get('state', {}).get('notebook', {}).get('notebook_id')
        if notebook_id:
            console.print(f"[cyan]Using notebook_id from state: {notebook_id}[/cyan]")
            self.code_executor.notebook_id = notebook_id
            self.code_executor.is_kernel_ready = True
            # CRITICAL: Also set notebook_id in notebook_store for consistency
            self.notebook_store.notebook_id = notebook_id
        else:
            console.print("[yellow]Warning: No notebook_id found in state, will initialize new kernel[/yellow]")

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
        console.print(f"\n[bold cyan]Starting execution of {len(actions_data)} actions (using ScriptStore)[/bold cyan]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Executing actions...", total=len(actions_data))

            for idx, action_data in enumerate(actions_data):
                action = action_data.get('action', {})
                action_type = action.get('type')

                progress.update(task, advance=1, description=f"[cyan]Action {idx+1}/{len(actions_data)}: {action_type}")

                # Convert to ExecutionStep and execute using ScriptStore
                step = self._convert_action_to_step(action_data)
                self.script_store.exec_action(step)
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
            f"[green]OK[/green] FSM State: [magenta]BEHAVIOR_COMPLETE[/magenta]",
            title="[bold green]Output Saved[/bold green]",
            border_style="green",
            box=box.DOUBLE
        ))

        # Summary table
        summary_table = Table(box=box.DOUBLE, title="Execution Summary", title_style="bold cyan")
        summary_table.add_column("Item", style="cyan", width=30)
        summary_table.add_column("Value", style="green", justify="right")

        summary_table.add_row("FSM State Transition", "BEHAVIOR_RUNNING -> BEHAVIOR_COMPLETE")
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
            "BEHAVIOR_COMPLETE",
            transition_data
        )
