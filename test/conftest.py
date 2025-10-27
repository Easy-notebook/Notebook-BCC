"""pytest configuration and fixtures"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture
def mock_workflow():
    """Create a mock workflow for testing"""
    from models.workflow import Workflow, Stage, Step

    workflow = Workflow(
        id="test-workflow",
        problem_name="Test Problem",
        user_goal="Test user goal",
        stages=[]
    )

    stage = Stage(id="stage-1", name="Test Stage", steps=[])
    step1 = Step(id="step-1", name="Test Step 1", description="First test step")
    step2 = Step(id="step-2", name="Test Step 2", description="Second test step")

    stage.steps = [step1, step2]
    workflow.stages = [stage]

    return workflow

@pytest.fixture
def ai_context_store():
    """Create an AIPlanningContextStore instance"""
    from stores.ai_context_store import AIPlanningContextStore
    return AIPlanningContextStore()

@pytest.fixture
def notebook_store():
    """Create a NotebookStore instance"""
    from stores.notebook_store import NotebookStore
    return NotebookStore()

@pytest.fixture
def code_executor():
    """Create a CodeExecutor instance"""
    from executors.code_executor import CodeExecutor
    return CodeExecutor()
