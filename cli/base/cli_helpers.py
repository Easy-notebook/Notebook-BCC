"""
CLI helper methods - unified utilities to reduce code duplication.

All legacy methods have been removed (2025-11-12).
Commands now use AsyncStateMachineAdapter from core/async_state_machine.py
or state_machine methods directly.
"""


class CLIHelpers:
    """
    Mixin class providing helper methods for CLI operations.
    """

    def _load_state_file(self, state_file: str):
        """
        Load and parse state file (unified helper).

        Args:
            state_file: Path to state JSON file

        Returns:
            Tuple of (state_json, parsed_state)
        """
        from utils.state_file_loader import state_file_loader
        state_json = state_file_loader.load_state_file(state_file)
        parsed_state = state_file_loader.parse_state_for_api(state_json)
        return state_json, parsed_state

    def _sync_state_to_stores(self, state):
        """
        Sync state dict to stores (notebook_store and ai_context_store).
        This is the ONLY place where notebook_id should be synced from State to Stores.

        Single Source of Truth: State JSON → Stores (read-only sync)

        Args:
            state: State dict containing notebook and effects data
        """
        if 'state' not in state:
            return

        state_data = state['state']

        # Sync notebook
        if 'notebook' in state_data:
            notebook_data = state_data['notebook']

            # Clear existing cells
            self.notebook_store.cells.clear()

            # Load cells from state
            last_code_cell_id = None
            for cell_data in notebook_data.get('cells', []):
                cell = self.notebook_store.add_cell(cell_data)
                # Track last code cell for lastAddedCellId reference
                if cell and cell.type.value == 'code':  # CellType.CODE
                    last_code_cell_id = cell.id

            # Update script_store's last_added_action_id to point to last code cell
            if last_code_cell_id:
                self.script_store.last_added_action_id = last_code_cell_id

            # Update metadata
            if 'title' in notebook_data:
                self.notebook_store.title = notebook_data['title']
            if 'execution_count' in notebook_data:
                self.notebook_store.execution_count = notebook_data['execution_count']

            # CRITICAL: Sync notebook_id from State (Single Source of Truth)
            notebook_id = notebook_data.get('notebook_id')
            if notebook_id:
                # Sync to NotebookStore
                self.notebook_store.notebook_id = notebook_id
                # Sync to CodeExecutor
                if self.code_executor:
                    self.code_executor.notebook_id = notebook_id
                    self.code_executor.is_kernel_ready = True
                    self.debug(f"[Sync] notebook_id: {notebook_id[:16]}...")
            else:
                # No notebook_id in state - will create new notebook on first execution
                self.notebook_store.notebook_id = None
                if self.code_executor:
                    self.code_executor.notebook_id = None
                    self.code_executor.is_kernel_ready = False

        # Sync effects to AI context
        if 'effects' in state_data:
            effects = state_data['effects']
            self.ai_context_store.set_effect(effects)
