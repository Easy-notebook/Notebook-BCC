"""
CLI Commands - Refactored into modular structure.

This file maintains backward compatibility by re-exporting the main classes.

New modular structure:
- cli/base/ - Base classes (BaseCommand, CLIHelpers, DummyContext)
- cli/commands/ - Command modules (StartCommand, StateCommands, NotebookCommands, APICommands, BasicCommands)
- cli/workflow_cli.py - Main WorkflowCLI class combining all functionality

Import hierarchy:
    WorkflowCLI inherits from:
    ├── BaseCommand (core initialization, stores, logging)
    ├── CLIHelpers (helper methods for state/action handling)
    ├── StartCommand (start command and iteration loop)
    ├── StateCommands (resume, test-request, apply-transition)
    ├── NotebookCommands (show, list, export, export-markdown)
    ├── APICommands (send-api, test-actions)
    └── BasicCommands (status, repl)
"""

# Re-export for backward compatibility
from cli.workflow_cli import WorkflowCLI, main
from cli.base.dummy_context import DummyContext

__all__ = [
    'WorkflowCLI',
    'DummyContext',
    'main',
]

# If this file is run directly, execute main()
if __name__ == '__main__':
    main()
