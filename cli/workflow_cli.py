"""
Main WorkflowCLI class - combines all command functionality.
"""

import json
from cli.base import BaseCommand, CLIHelpers
from cli.commands import (
    StartCommand,
    StateCommands,
    NotebookCommands,
    APICommands,
    BasicCommands
)
from cli.argument_parser import CLIArgumentParser


class WorkflowCLI(
    BaseCommand,
    CLIHelpers,
    StartCommand,
    StateCommands,
    NotebookCommands,
    APICommands,
    BasicCommands
):
    """
    Command-line interface for the workflow system.
    Combines all command functionality through multiple inheritance.

    Inheritance hierarchy:
    - BaseCommand: Core initialization and stores
    - CLIHelpers: Helper methods for state/action handling
    - StartCommand: start command and iteration loop
    - StateCommands: resume, test-request, apply-transition
    - NotebookCommands: show, list, export, export-markdown
    - APICommands: send-api, test-actions
    - BasicCommands: status, repl
    """

    def __init__(self, max_steps=0, interactive=False):
        """
        Initialize the CLI.

        Args:
            max_steps: Maximum steps to execute (0 = unlimited)
            interactive: Enable interactive mode
        """
        # Call BaseCommand's __init__ to initialize all stores
        BaseCommand.__init__(self, max_steps, interactive)

    def create_parser(self):
        """Create argument parser."""
        return CLIArgumentParser.create_parser()

    def run(self, argv=None):
        """Run the CLI."""
        parser = self.create_parser()
        args = parser.parse_args(argv)

        # Apply runtime configuration
        from config import Config

        if args.backend_url:
            print(f"Setting backend URL: {args.backend_url}")
            Config.set_backend_url(args.backend_url)

        if args.dslc_url:
            print(f"Setting DSLC URL: {args.dslc_url}")
            Config.set_dslc_url(args.dslc_url)

        if args.notebook_id:
            print(f"Setting notebook ID: {args.notebook_id}")
            Config.set_notebook_id(args.notebook_id)
            # Also set it on the code executor
            self.code_executor.notebook_id = args.notebook_id
            self.code_executor.is_kernel_ready = True

        # Apply execution control settings
        if args.max_steps:
            print(f"Max steps: {args.max_steps}")
            self.state_machine.set_max_steps(args.max_steps)

        if args.interactive:
            print("Interactive mode: enabled")
            self.state_machine.interactive = True

        # Apply custom context
        if args.custom_context:
            # Parse as JSON string
            custom_ctx = json.loads(args.custom_context)
            if custom_ctx:
                print(f"Custom context loaded: {list(custom_ctx.keys())}")
                self.ai_context_store.set_custom_context(custom_ctx)
                # Also add all custom context variables to the variables dict
                for key, value in custom_ctx.items():
                    self.ai_context_store.add_variable(key, value)

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
            handler(args)
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
