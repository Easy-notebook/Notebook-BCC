"""
State File Loader
Load and parse workflow state from JSON files.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from silantui import ModernLogger


class StateFileLoader(ModernLogger):
    """
    Load workflow state from JSON files.
    Supports loading state files in the format used by the system.
    """

    def __init__(self):
        """Initialize the state file loader."""
        super().__init__("StateFileLoader")

    def load_state_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load state from a JSON file.

        Args:
            file_path: Path to the state JSON file

        Returns:
            Dictionary containing the state data

        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file is not valid JSON
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"State file not found: {file_path}")

        self.info(f"[Loader] Loading state from: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            state_json = json.load(f)

        self.info(f"[Loader] State loaded successfully")
        return state_json

    def parse_state_for_api(self, state_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse state JSON into format suitable for API calls.

        Args:
            state_json: Raw state JSON from file

        Returns:
            Dictionary with parsed state data including:
            - stage_id: Current stage ID
            - step_id: Current step ID (or None)
            - behavior_id: Current behavior ID (or None)
            - state: Full state object for API
        """
        # Extract observation and state sections
        observation = state_json.get('observation', {})
        state_data = state_json.get('state', {})

        location = observation.get('location', {})
        current = location.get('current', {})

        # Extract current position
        stage_id = current.get('stage_id')
        step_id = current.get('step_id')
        behavior_id = current.get('behavior_id')

        # Build full state for API
        full_state = {
            'progress_info': location,  # Contains current, progress, goals
            'variables': state_data.get('variables', {}),
            'effects': state_data.get('effects', {}),
            'notebook': state_data.get('notebook', {}),
            'FSM': state_data.get('FSM', {})
        }

        self.info(f"[Parser] Extracted position: stage={stage_id}, step={step_id}, behavior={behavior_id}")
        self.info(f"[Parser] Variables: {len(full_state['variables'])}")
        self.info(f"[Parser] FSM State: {full_state.get('FSM', {}).get('state')}")

        return {
            'stage_id': stage_id,
            'step_id': step_id,
            'behavior_id': behavior_id,
            'state': full_state,
            'raw': state_json
        }

    def extract_context(self, state_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract AI context from state JSON.

        Args:
            state_json: Raw state JSON

        Returns:
            Dictionary with variables, effects, etc.
        """
        state_data = state_json.get('state', {})

        return {
            'variables': state_data.get('variables', {}),
            'effects': state_data.get('effects', {'current': [], 'history': []}),
            'notebook': state_data.get('notebook', {}),
            'FSM': state_data.get('FSM', {})
        }

    def infer_api_type(self, state_json: Dict[str, Any]) -> str:
        """
        Infer the appropriate API type based on FSM state.

        Args:
            state_json: Raw state JSON

        Returns:
            API type: 'planning', 'generating', or 'reflecting'

        Logic (based on Planning First protocol):
        - IDLE → planning (START_WORKFLOW)
        - STAGE_RUNNING → planning (START_STEP)
        - STEP_RUNNING → planning (check if target achieved)
        - BEHAVIOR_RUNNING → reflecting (reflect on behavior execution)
        - *_COMPLETED → planning (next step or complete)
        """
        state_data = state_json.get('state', {})
        fsm = state_data.get('FSM', {})
        fsm_state = fsm.get('state', 'UNKNOWN')

        # Normalize state name
        fsm_state = fsm_state.upper()

        # Planning First Protocol:
        # - Most states use planning to check/decide next step
        # - Only BEHAVIOR_RUNNING uses reflecting
        # - generating is rarely the default (user can override)

        if 'BEHAVIOR' in fsm_state and 'RUNNING' in fsm_state:
            # BEHAVIOR_RUNNING → reflecting
            inferred = 'reflecting'
            self.info(f"[Infer] FSM={fsm_state} → API=reflecting (behavior execution feedback)")
        elif 'STEP' in fsm_state and 'RUNNING' in fsm_state:
            # STEP_RUNNING → planning (check target achieved)
            inferred = 'planning'
            self.info(f"[Infer] FSM={fsm_state} → API=planning (check target achieved)")
        elif 'STAGE' in fsm_state and 'RUNNING' in fsm_state:
            # STAGE_RUNNING → planning (start step)
            inferred = 'planning'
            self.info(f"[Infer] FSM={fsm_state} → API=planning (start step)")
        elif fsm_state == 'IDLE':
            # IDLE → planning (start workflow)
            inferred = 'planning'
            self.info(f"[Infer] FSM={fsm_state} → API=planning (start workflow)")
        else:
            # Default to planning for all other states
            inferred = 'planning'
            self.info(f"[Infer] FSM={fsm_state} → API=planning (default)")

        return inferred


# Global singleton
state_file_loader = StateFileLoader()
