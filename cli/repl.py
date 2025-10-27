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
