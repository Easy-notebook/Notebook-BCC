"""
State Builder - Utility for building state dictionaries from stores.
Eliminates duplicated state building logic across the codebase.
"""

import copy
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from silantui import ModernLogger
from models.cell import CellType


class StateBuilder(ModernLogger):
    """
    Utility class for building state dictionaries from stores.
    Provides unified state construction to avoid code duplication.
    """

    def __init__(self):
        """Initialize the state builder."""
        super().__init__("StateBuilder")

    def build_state_from_stores(
        self,
        base_state: Dict[str, Any],
        notebook_store,
        ai_context_store
    ) -> Dict[str, Any]:
        """
        Build updated state from current store states.

        Args:
            base_state: Base state dict to update
            notebook_store: NotebookStore instance
            ai_context_store: AIPlanningContextStore instance

        Returns:
            Updated state dict with current notebook and effects
        """
        # Deep copy to avoid modifying original
        updated_state = copy.deepcopy(base_state)

        # Get current notebook state
        notebook_data = notebook_store.to_dict()

        # CRITICAL: Preserve notebook_id from base_state if not in notebook_data
        # This ensures notebook_id is never lost during state updates
        if 'notebook_id' not in notebook_data and 'state' in base_state:
            base_notebook_id = base_state.get('state', {}).get('notebook', {}).get('notebook_id')
            if base_notebook_id:
                notebook_data['notebook_id'] = base_notebook_id
                self.warning(f"[StateBuilder] ⚠️ Recovered notebook_id from base_state: {base_notebook_id}")

        # Get current effects from AI context
        context = ai_context_store.get_context()

        # Update state
        if 'state' not in updated_state:
            updated_state['state'] = {}

        updated_state['state']['notebook'] = notebook_data
        updated_state['state']['effects'] = context.effect

        return updated_state

    def build_effects_from_notebook(
        self,
        notebook_store,
        include_cell_ref: bool = True
    ) -> list:
        """
        Build OpenAI-compatible effects list from notebook cell outputs.

        Args:
            notebook_store: NotebookStore instance
            include_cell_ref: Whether to include cell_ref in effects

        Returns:
            List of effect dictionaries
        """
        effects_list = []

        for cell in notebook_store.cells:
            if cell.type == CellType.CODE and cell.outputs:
                for output in cell.outputs:
                    effect = self._convert_output_to_effect(output, cell.id if include_cell_ref else None)
                    if effect:
                        effects_list.append(effect)

        return effects_list

    def _convert_output_to_effect(
        self,
        output,
        cell_ref: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Convert a cell output to an effect dictionary.

        Args:
            output: CellOutput object or dict
            cell_ref: Optional cell ID reference

        Returns:
            Effect dictionary or None
        """
        # Handle both CellOutput objects and dict formats
        output_type = output.output_type if hasattr(output, 'output_type') else output.get('output_type')

        effect = None

        if output_type == 'stream':
            text = output.text or output.content if hasattr(output, 'text') else output.get('text', '')
            effect = {
                "type": "text",
                "text": text
            }

        elif output_type == 'execute_result':
            text = output.text or output.content if hasattr(output, 'text') else output.get('text', '')
            effect = {
                "type": "text",
                "text": str(text)
            }

        elif output_type == 'display_data':
            # Check if it's an image
            content = output.content if hasattr(output, 'content') else output.get('content', {})
            if isinstance(content, dict):
                if 'image/png' in content or 'image/jpeg' in content:
                    image_id = f"{cell_ref}-img" if cell_ref else "img"
                    effect = {
                        "type": "image_url",
                        "image_url": f"<image #{image_id} request-to-see>"
                    }
                else:
                    effect = {
                        "type": "text",
                        "text": str(content)
                    }
            else:
                effect = {
                    "type": "text",
                    "text": str(content)
                }

        elif output_type == 'error':
            ename = output.ename if hasattr(output, 'ename') else output.get('ename', 'Error')
            evalue = output.evalue if hasattr(output, 'evalue') else output.get('evalue', '')
            traceback = output.traceback if hasattr(output, 'traceback') else output.get('traceback', [])
            effect = {
                "type": "error",
                "error": {
                    "name": ename,
                    "message": evalue,
                    "traceback": traceback
                }
            }

        # Add cell reference if provided and effect was created
        if effect and cell_ref:
            effect["cell_ref"] = cell_ref

        return effect

    def build_complete_state(
        self,
        base_state: Dict[str, Any],
        notebook_store,
        ai_context_store,
        new_fsm_state: str,
        transition_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build a complete state with FSM transition.

        Args:
            base_state: Base state dict
            notebook_store: NotebookStore instance
            ai_context_store: AIPlanningContextStore instance
            new_fsm_state: New FSM state
            transition_data: Optional transition metadata

        Returns:
            Complete state dict
        """
        # Get updated state from stores
        notebook_data = notebook_store.to_dict()

        # Ensure notebook_id is preserved
        if 'notebook_id' not in notebook_data and 'state' in base_state:
            notebook_id = base_state.get('state', {}).get('notebook', {}).get('notebook_id')
            if notebook_id:
                notebook_data['notebook_id'] = notebook_id

        # Build effects from notebook
        effects_list = self.build_effects_from_notebook(notebook_store)

        # Get variables from context
        context = ai_context_store.get_context()

        # Build FSM state
        old_fsm = base_state.get('state', {}).get('FSM', {})
        new_fsm = {
            "state": new_fsm_state,
            "last_transition": transition_data.get('transition_type', 'UNKNOWN') if transition_data else 'UNKNOWN',
            "previous_state": old_fsm.get('state', 'UNKNOWN'),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Add transition data if provided
        if transition_data:
            new_fsm["transition_data"] = transition_data

        # Build complete state
        output_state = {
            "observation": base_state.get('observation', {}),
            "state": {
                "variables": context.variables,
                "effects": {"current": effects_list, "history": []},
                "notebook": notebook_data,
                "FSM": new_fsm
            },
            "metadata": base_state.get('metadata', {})
        }

        # Update metadata
        output_state['metadata'].update({
            "execution_timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "completed"
        })

        return output_state


# Global singleton instance
state_builder = StateBuilder()
