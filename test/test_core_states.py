"""Tests for core/states.py"""
import pytest
from core.states import WorkflowState, WORKFLOW_STATES

@pytest.mark.unit
class TestWorkflowState:
    """Tests for WorkflowState enum"""

    def test_idle_state_exists(self):
        """Test that IDLE state exists"""
        assert WorkflowState.IDLE.value == 'idle'

    def test_all_states_defined(self):
        """Test that all required states are defined"""
        expected_states = [
            'IDLE', 'STAGE_RUNNING', 'STAGE_COMPLETED',
            'STEP_RUNNING', 'STEP_COMPLETED',
            'BEHAVIOR_RUNNING', 'BEHAVIOR_COMPLETED',
            'ACTION_RUNNING', 'ACTION_COMPLETED',
            'WORKFLOW_COMPLETED', 'ERROR', 'CANCELLED'
        ]

        for state_name in expected_states:
            assert hasattr(WorkflowState, state_name), f"State {state_name} not defined"

    def test_state_values(self):
        """Test that state enum values are correct"""
        assert WorkflowState.IDLE.value == 'idle'
        assert WorkflowState.STAGE_RUNNING.value == 'stage_running'
        assert WorkflowState.ERROR.value == 'error'

    def test_workflow_states_dict(self):
        """Test that WORKFLOW_STATES dictionary is correctly populated"""
        assert 'IDLE' in WORKFLOW_STATES
        assert WORKFLOW_STATES['IDLE'] == WorkflowState.IDLE
