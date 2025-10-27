#!/usr/bin/env python3
"""
Example usage of Notebook-BCC Python Workflow System.

This demonstrates the complete workflow system including:
- State machine initialization
- Workflow execution
- Variable management
- TODO list tracking
- Code execution
- Notebook persistence
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core import WorkflowStateMachine, WorkflowEvent
from stores import (
    AIPlanningContextStore,
    PipelineStore,
    ScriptStore,
    NotebookStore
)
from executors import CodeExecutor
from notebook import NotebookManager, CellRenderer
from models import ScriptAction, ExecutionStep


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def main():
    """Main example function."""
    print("\n🚀 Notebook-BCC Example Workflow\n")

    # ==============================================
    # 1. Initialize All Components
    # ==============================================
    print_section("1. Initializing Components")

    # Create stores
    pipeline_store = PipelineStore()
    notebook_store = NotebookStore()
    ai_context_store = AIPlanningContextStore()

    # Create executors
    code_executor = CodeExecutor()

    # Create script store (connects everything)
    script_store = ScriptStore(
        notebook_store=notebook_store,
        ai_context_store=ai_context_store,
        code_executor=code_executor
    )

    # Create state machine
    state_machine = WorkflowStateMachine(
        pipeline_store=pipeline_store,
        script_store=script_store,
        ai_context_store=ai_context_store
    )

    # Create managers
    notebook_manager = NotebookManager()
    cell_renderer = CellRenderer()

    print("✓ All components initialized")

    # ==============================================
    # 2. Initialize Workflow
    # ==============================================
    print_section("2. Initializing Workflow")

    planning_request = {
        'problem_name': 'Data Analysis Example',
        'user_goal': 'Demonstrate the workflow system',
        'problem_description': 'Example workflow with Python code execution',
        'context_description': 'Educational example',
    }

    workflow = pipeline_store.initialize_workflow(planning_request)

    print(f"✓ Workflow created: {workflow.name}")
    print(f"  - ID: {workflow.id}")
    print(f"  - Stages: {len(workflow.stages)}")
    print(f"  - First stage: {workflow.stages[0].title}")

    # ==============================================
    # 3. Set Up Context Variables
    # ==============================================
    print_section("3. Setting Up Context")

    # Add variables
    ai_context_store.add_variable("dataset_name", "sales_data.csv")
    ai_context_store.add_variable("analysis_date", "2024-01-01")
    ai_context_store.add_variable("output_dir", "/output/analysis")

    print("✓ Variables set:")
    context = ai_context_store.get_context()
    for key, value in context.variables.items():
        print(f"  - {key} = {value}")

    # Add TODOs
    ai_context_store.add_to_do_list("Load dataset")
    ai_context_store.add_to_do_list("Explore data structure")
    ai_context_store.add_to_do_list("Generate summary statistics")

    print("\n✓ TODO list created:")
    for i, todo in enumerate(context.to_do_list, 1):
        print(f"  {i}. {todo}")

    # ==============================================
    # 4. Add Notebook Cells
    # ==============================================
    print_section("4. Creating Notebook Content")

    # Add markdown cell
    markdown_action = ScriptAction(
        id="cell_intro",
        type="text",
        content="# Data Analysis Workflow\n\nThis notebook demonstrates the workflow system."
    )
    script_store.add_action(markdown_action)
    print("✓ Added markdown cell: Introduction")

    # Add code cell
    code_action = ScriptAction(
        id="cell_code1",
        type="code",
        content="""import pandas as pd
import numpy as np

# Generate sample data
data = {
    'product': ['A', 'B', 'C', 'D', 'E'],
    'sales': [100, 150, 120, 180, 90],
    'profit': [20, 35, 25, 40, 15]
}

df = pd.DataFrame(data)
print(df)
print(f"\\nTotal sales: {df['sales'].sum()}")
print(f"Average profit: {df['profit'].mean():.2f}")
"""
    )
    script_store.add_action(code_action)
    print("✓ Added code cell: Data analysis")

    # ==============================================
    # 5. Execute Code
    # ==============================================
    print_section("5. Executing Code")

    print("Executing Python code...")
    result = code_executor.execute(code_action.content, cell_id="cell_code1")

    if result['success']:
        print("✓ Code executed successfully")
        print("\nOutput:")
        print("-" * 40)
        for output in result['outputs']:
            print(output.content or output.text or '')
        print("-" * 40)

        # Add outputs to notebook cell
        for output in result['outputs']:
            notebook_store.add_cell_output("cell_code1", output)

        # Track effect
        ai_context_store.add_effect("Data loaded successfully")
        ai_context_store.add_effect(f"Analyzed {5} products")
    else:
        print(f"✗ Execution failed: {result['error']}")

    # ==============================================
    # 6. Check Namespace
    # ==============================================
    print_section("6. Checking Python Namespace")

    variables = code_executor.get_all_variables()
    print("✓ User-defined variables:")
    for name, value in variables.items():
        print(f"  - {name} = {value}")

    # ==============================================
    # 7. View State Machine Status
    # ==============================================
    print_section("7. State Machine Status")

    state_info = state_machine.get_state_info()
    print(f"Current State: {state_info['current_state']}")
    print(f"Stage ID: {state_info['stage_id']}")
    print(f"Step ID: {state_info['step_id']}")

    # ==============================================
    # 8. Render Notebook
    # ==============================================
    print_section("8. Notebook Preview")

    notebook_data = notebook_store.to_dict()
    print(cell_renderer.render_notebook_summary(notebook_data))

    from models.cell import Cell
    cells = [Cell.from_dict(c) for c in notebook_data['cells']]
    print(cell_renderer.render_cells(cells))

    # ==============================================
    # 9. Save Notebook
    # ==============================================
    print_section("9. Saving Notebook")

    saved_path = notebook_manager.save_notebook(
        notebook_data,
        filename="example_workflow.json"
    )
    print(f"✓ Notebook saved: {saved_path}")

    # Export to markdown
    md_path = notebook_manager.export_to_markdown(
        notebook_data,
        output_file="example_workflow.md"
    )
    print(f"✓ Exported to markdown: {md_path}")

    # ==============================================
    # 10. Summary
    # ==============================================
    print_section("10. Summary")

    print(f"✓ Workflow: {workflow.name}")
    print(f"✓ Cells created: {len(notebook_data['cells'])}")
    print(f"✓ Variables: {len(context.variables)}")
    print(f"✓ TODOs: {len(context.to_do_list)}")
    print(f"✓ Effects: {len(context.effect['current'])}")
    print(f"✓ Code executed successfully")
    print(f"✓ Files saved:")
    print(f"  - {saved_path}")
    print(f"  - {md_path}")

    print("\n✨ Example completed successfully!\n")


if __name__ == '__main__':
    main()
