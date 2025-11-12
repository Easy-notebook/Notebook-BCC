"""
Base command class providing core functionality for all CLI commands.
"""

import logging
from silantui import ModernLogger
from stores.pipeline_store import PipelineStore
from stores.script_store import ScriptStore
from stores.notebook_store import NotebookStore
from stores.ai_context_store import AIPlanningContextStore
from executors.code_executor import CodeExecutor
from notebook.notebook_manager import NotebookManager
from notebook.cell_renderer import CellRenderer
from core.state_machine import WorkflowStateMachine
from core.async_state_machine import AsyncStateMachineAdapter


class BaseCommand(ModernLogger):
    """
    Base class for all CLI commands.
    Provides common initialization and setup.
    """

    def __init__(self, max_steps=0, interactive=False):
        """
        Initialize the base command.

        Args:
            max_steps: Maximum steps to execute (0 = unlimited)
            interactive: Enable interactive mode
        """
        super().__init__("WorkflowCLI")
        self.setup_logging()

        # Initialize managers first
        self.notebook_manager = NotebookManager()
        self.cell_renderer = CellRenderer()

        # Initialize stores
        self.pipeline_store = PipelineStore()
        self.notebook_store = NotebookStore()
        self.ai_context_store = AIPlanningContextStore()
        self.code_executor = CodeExecutor()
        self.script_store = ScriptStore(
            notebook_store=self.notebook_store,
            ai_context_store=self.ai_context_store,
            code_executor=self.code_executor
        )

        # Initialize state machine with control parameters
        self.state_machine = WorkflowStateMachine(
            pipeline_store=self.pipeline_store,
            script_store=self.script_store,
            ai_context_store=self.ai_context_store,
            notebook_manager=self.notebook_manager,
            max_steps=max_steps,
            interactive=interactive
        )

        # Initialize async state machine adapter
        # API client will be set later (in start command)
        self.async_state_machine = AsyncStateMachineAdapter(
            state_machine=self.state_machine,
            api_client=None,  # Will be set in start command
            script_store=self.script_store
        )

    def setup_logging(self, level=logging.INFO):
        """Setup logging configuration."""
        # Only configure file handler, ModernLogger already handles console output
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        # Add file handler only if not already present
        if not any(isinstance(h, logging.FileHandler) for h in root_logger.handlers):
            file_handler = logging.FileHandler('workflow.log')
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            root_logger.addHandler(file_handler)
