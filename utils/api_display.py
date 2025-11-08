"""
API Display Helper
Beautiful CLI display for API requests using Rich library.
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.json import JSON
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.syntax import Syntax
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️  Rich library not installed. Install with: pip install rich>=13.7.0")


class APIDisplayHelper:
    """
    Helper class for displaying API requests and responses beautifully.
    """

    def __init__(self):
        """Initialize the API display helper."""
        if RICH_AVAILABLE:
            self.console = Console()
        else:
            self.console = None

    def display_api_request(
        self,
        api_type: str,
        api_url: str,
        stage_id: Optional[str] = None,
        step_id: Optional[str] = None,
        behavior_id: Optional[str] = None,
        payload_size: Optional[int] = None
    ):
        """
        Display API request information.

        Args:
            api_type: Type of API (planning, generating, reflecting)
            api_url: Full API URL
            stage_id: Current stage ID
            step_id: Current step ID
            behavior_id: Current behavior ID
            payload_size: Size of payload in bytes
        """
        if not RICH_AVAILABLE or not self.console:
            # Fallback to simple print
            print(f"\n Sending {api_type.upper()} API Request")
            print(f"   URL: {api_url}")
            if stage_id:
                print(f"   Stage: {stage_id}")
            if step_id:
                print(f"   Step: {step_id}")
            if behavior_id:
                print(f"   Behavior: {behavior_id}")
            return

        # Create info table
        table = Table(box=box.ROUNDED, show_header=False, padding=(0, 1))
        table.add_column("Key", style="cyan bold")
        table.add_column("Value", style="white")

        table.add_row("API Type", f"[yellow]{api_type.upper()}[/yellow]")
        table.add_row("URL", api_url)

        if stage_id:
            table.add_row("Stage ID", stage_id)
        if step_id:
            table.add_row("Step ID", step_id or "[dim]None[/dim]")
        if behavior_id:
            table.add_row("Behavior ID", behavior_id or "[dim]None[/dim]")
        if payload_size:
            table.add_row("Payload Size", f"{payload_size} bytes ({payload_size/1024:.2f} KB)")

        table.add_row("Time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        self.console.print()
        self.console.print(Panel(
            table,
            title="[bold blue] API Request[/bold blue]",
            border_style="blue"
        ))

    def display_sending_progress(self, api_type: str):
        """
        Display a spinner while sending request.

        Args:
            api_type: Type of API

        Returns:
            Progress context manager (use with 'with' statement)
        """
        if not RICH_AVAILABLE or not self.console:
            print(f"⏳ Sending {api_type} request...")
            return None

        progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Sending {task.description}...[/bold blue]"),
            console=self.console
        )
        progress.add_task(f"{api_type.upper()} API request", total=None)
        return progress

    def display_api_response(
        self,
        api_type: str,
        response: Dict[str, Any],
        success: bool = True,
        error: Optional[str] = None
    ):
        """
        Display API response.

        Args:
            api_type: Type of API
            response: Response data
            success: Whether the request was successful
            error: Error message if failed
        """
        if not RICH_AVAILABLE or not self.console:
            # Fallback to simple print
            if success:
                print(f"\n✅ {api_type.upper()} API Response:")
                print(json.dumps(response, indent=2, ensure_ascii=False))
            else:
                print(f"\n❌ {api_type.upper()} API Failed:")
                print(f"   Error: {error}")
            return

        if success:
            # Success response
            self.console.print()

            # Create summary table
            table = Table(box=box.ROUNDED, show_header=False, padding=(0, 1))
            table.add_column("Key", style="green bold")
            table.add_column("Value", style="white")

            # Extract key information based on response type
            if 'targetAchieved' in response:
                table.add_row("Target Achieved",
                             "[green]✓ Yes[/green]" if response['targetAchieved'] else "[yellow]○ No[/yellow]")

            if 'transition' in response:
                transition = response['transition']
                if 'continue_behaviors' in transition:
                    table.add_row("Continue Behaviors",
                                 "[yellow]Yes[/yellow]" if transition['continue_behaviors'] else "[green]No[/green]")
                if 'target_achieved' in transition:
                    table.add_row("Target Status",
                                 "[green]Achieved[/green]" if transition['target_achieved'] else "[yellow]Pending[/yellow]")

            if 'context_update' in response:
                ctx_update = response['context_update']
                if 'variables' in ctx_update:
                    table.add_row("Variables Updated", str(len(ctx_update['variables'])))

            if 'type' in response:
                table.add_row("Response Type", f"[cyan]{response['type']}[/cyan]")

            self.console.print(Panel(
                table,
                title=f"[bold green]✅ {api_type.upper()} API Response Summary[/bold green]",
                border_style="green"
            ))

            # Full JSON response
            if response:
                json_str = json.dumps(response, indent=2, ensure_ascii=False)
                syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
                self.console.print(Panel(
                    syntax,
                    title="[bold white]Full Response[/bold white]",
                    border_style="white",
                    expand=False
                ))
        else:
            # Error response
            self.console.print()
            self.console.print(Panel(
                f"[bold red]{error}[/bold red]",
                title=f"[bold red]❌ {api_type.upper()} API Failed[/bold red]",
                border_style="red"
            ))

    def display_state_info(self, state_data: Dict[str, Any]):
        """
        Display state file information.

        Args:
            state_data: Parsed state data from loader
        """
        if not RICH_AVAILABLE or not self.console:
            # Fallback
            print(f"\n State Information:")
            print(f"   Stage: {state_data.get('stage_id')}")
            print(f"   Step: {state_data.get('step_id')}")
            print(f"   Behavior: {state_data.get('behavior_id')}")
            state = state_data.get('state', {})
            print(f"   Variables: {len(state.get('variables', {}))}")
            print(f"   FSM State: {state.get('FSM', {}).get('state')}")
            return

        table = Table(box=box.ROUNDED, show_header=False, padding=(0, 1))
        table.add_column("Key", style="cyan bold")
        table.add_column("Value", style="white")

        table.add_row("Stage ID", state_data.get('stage_id') or "[dim]None[/dim]")
        table.add_row("Step ID", state_data.get('step_id') or "[dim]None[/dim]")
        table.add_row("Behavior ID", state_data.get('behavior_id') or "[dim]None[/dim]")

        state = state_data.get('state', {})
        table.add_row("Variables", str(len(state.get('variables', {}))))

        effects = state.get('effects', {})
        table.add_row("Current Effects", str(len(effects.get('current', []))))
        table.add_row("Effect History", str(len(effects.get('history', []))))

        fsm = state.get('FSM', {})
        table.add_row("FSM State", f"[yellow]{fsm.get('state', 'Unknown')}[/yellow]")
        table.add_row("Last Transition", fsm.get('last_transition') or "[dim]None[/dim]")

        self.console.print()
        self.console.print(Panel(
            table,
            title="[bold cyan] Loaded State Information[/bold cyan]",
            border_style="cyan"
        ))

    def display_actions(self, actions: list):
        """
        Display actions from generating API.

        Args:
            actions: List of action dictionaries
        """
        if not RICH_AVAILABLE or not self.console:
            print(f"\n📝 Received {len(actions)} actions:")
            for i, action in enumerate(actions, 1):
                print(f"   {i}. {action.get('action')} - {action.get('cell_type', 'unknown')}")
            return

        table = Table(box=box.ROUNDED)
        table.add_column("#", style="cyan", width=4)
        table.add_column("Action", style="yellow bold", width=15)
        table.add_column("Type", style="green", width=12)
        table.add_column("Content Preview", style="white")

        for i, action in enumerate(actions, 1):
            content = action.get('content', '')
            preview = content[:50] + "..." if len(content) > 50 else content
            preview = preview.replace('\n', ' ')

            table.add_row(
                str(i),
                action.get('action', 'unknown'),
                action.get('cell_type', 'unknown'),
                preview
            )

        self.console.print()
        self.console.print(Panel(
            table,
            title=f"[bold magenta]📝 Received {len(actions)} Actions[/bold magenta]",
            border_style="magenta"
        ))


# Global singleton
api_display = APIDisplayHelper()
