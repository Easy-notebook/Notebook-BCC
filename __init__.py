"""
Notebook-BCC: Python Workflow System
Complete Python implementation of the Easy-notebook-advance frontend Workflow system.

This package provides:
- State machine-driven workflow execution
- Variable and TODO list management
- Notebook cell management and rendering
- Code execution with context tracking
- Command-line interface
"""

__version__ = '1.0.0'
__author__ = 'Hu Silan'

from core import (
    WorkflowStateMachine,
    WorkflowContext,
    WorkflowState,
    WorkflowEvent,
    WORKFLOW_STATES,
    EVENTS,
)

from stores import (
    AIPlanningContextStore,
    PipelineStore,
    ScriptStore,
    NotebookStore,
)

from models import (
    WorkflowTemplate,
    WorkflowStage,
    WorkflowStep,
    ScriptAction,
    ActionMetadata,
    ExecutionStep,
    Cell,
    CellType,
)

from executors import (
    CodeExecutor,
    ActionExecutor,
)

from notebook import (
    NotebookManager,
    MarkdownRenderer,
    CellRenderer,
)

__all__ = [
    # Core
    'WorkflowStateMachine',
    'WorkflowContext',
    'WorkflowState',
    'WorkflowEvent',
    'WORKFLOW_STATES',
    'EVENTS',
    # Stores
    'AIPlanningContextStore',
    'PipelineStore',
    'ScriptStore',
    'NotebookStore',
    # Models
    'WorkflowTemplate',
    'WorkflowStage',
    'WorkflowStep',
    'ScriptAction',
    'ActionMetadata',
    'ExecutionStep',
    'Cell',
    'CellType',
    # Executors
    'CodeExecutor',
    'ActionExecutor',
    # Notebook
    'NotebookManager',
    'MarkdownRenderer',
    'CellRenderer',
]
