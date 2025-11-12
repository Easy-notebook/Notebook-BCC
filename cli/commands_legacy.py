"""
Legacy commands.py - Preserved for backward compatibility.

This file has been refactored into a modular structure:
- cli/base/ - Base classes and helpers
- cli/commands/ - Individual command modules
- cli/workflow_cli.py - Main CLI class

For new code, import from cli.workflow_cli:
    from cli import WorkflowCLI, main
"""

# Re-export all classes and functions for backward compatibility
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
