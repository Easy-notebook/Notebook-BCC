"""
Command-line interface for the workflow system.
"""

from .workflow_cli import WorkflowCLI, main
from .repl import WorkflowREPL

# For backward compatibility
from .base.dummy_context import DummyContext

__all__ = [
    'WorkflowCLI',
    'WorkflowREPL',
    'DummyContext',
    'main',
]
