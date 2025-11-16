"""
Observation to TODO List Converter

This module provides utility functions to convert observation data into todo list formats.
"""

from typing import Dict, Any


def _format_checkbox(completed: bool) -> str:
    """Format checkbox marker

    Args:
        completed: Whether the task is completed

    Returns:
        str: '[x]' if completed, '[ ]' if not
    """
    return '[x]' if completed else '[ ]'


def format_global_task_plan(observation: Dict[str, Any]) -> str:
    """Convert observation to global task planning format

    This function extracts stage progress information from observation and generates
    a markdown-formatted global task plan showing all stages (completed, current, and remaining).

    Args:
        observation: Observation dictionary containing location and progress info

    Returns:
        str: Formatted global task plan in markdown format

    Example:
        Global Task Planning
        - [x] Data Existence Establishment
        - [ ] Data Integrity Assurance
        - [ ] Exploratory Data Analysis
        ...
    """
    try:
        location = observation.get('location', {})
        progress = location.get('progress', {})
        stages = progress.get('stages', {})

        lines = ['Global Task Planning']

        # Completed stages
        completed_stages = stages.get('completed', [])
        for stage in completed_stages:
            stage_title = stage.get('title', stage.get('stage_id', 'Unknown Stage'))
            lines.append(f'- {_format_checkbox(True)} {stage_title}')

        # Current stage
        current_stage = stages.get('current', {})
        if current_stage:
            stage_title = current_stage.get('title', current_stage.get('stage_id', 'Unknown Stage'))
            lines.append(f'- {_format_checkbox(False)} {stage_title}')

        # Remaining stages
        remaining_stages = stages.get('remaining', [])
        for stage in remaining_stages:
            stage_title = stage.get('title', stage.get('stage_id', 'Unknown Stage'))
            lines.append(f'- {_format_checkbox(False)} {stage_title}')

        return '\n'.join(lines)

    except Exception as e:
        return f'Global Task Planning\nError: Unable to parse observation data - {str(e)}'


def format_local_task_plan(observation: Dict[str, Any]) -> str:
    """Convert observation to local task planning and assignment format

    This function extracts current step and behavior details from observation and generates
    a markdown-formatted local task plan with agent assignments showing the current big goal
    and all related sub-goals with their assigned agents.

    Args:
        observation: Observation dictionary containing location and progress info

    Returns:
        str: Formatted local task plan in markdown format

    Example:
        Local Current Task Planning and Assignment

        Current Big Goal: Data Collection and Inventory
          Execute the data collection strategy to verify the reliability...

        Current Focused Sub-Goals List
        - [x] Execute the data collection strategy... (Agent: Explore Agent)
        - [ ] Verify data file accessibility... (Agent: Explore Agent, Iteration: 2)
          Expected Outputs:
            - initial_data_inventory: data inventory checklist...
            - data_catalog: metadata records...
    """
    try:
        location = observation.get('location', {})
        progress = location.get('progress', {})
        steps = progress.get('steps', {})
        behaviors = progress.get('behaviors', {})

        lines = ['Local Current Task Planning and Assignment', '']

        # Current big goal (current step's goal)
        current_step = steps.get('current', {})
        step_title = current_step.get('title', current_step.get('step_id', 'Unknown Step'))
        step_goal = current_step.get('goal', '')
        lines.append(f'Current Big Goal: {step_title}')
        if step_goal:
            # Extract brief description before "Artifacts:"
            goal_short = step_goal.split('Artifacts:')[0].strip()
            lines.append(f'  {goal_short}')

        lines.append('')
        lines.append('Current Focused Sub-Goals List')

        # Completed behaviors
        completed_behaviors = behaviors.get('completed', [])
        for behavior in completed_behaviors:
            task = behavior.get('task', behavior.get('behavior_id', 'Unknown Task'))
            agent = behavior.get('agent', 'Unknown Agent')
            # Truncate task to first 80 characters for readability
            task_short = task[:80] + '...' if len(task) > 80 else task
            lines.append(f'- {_format_checkbox(True)} {task_short} (Agent: {agent})')

        # Current behavior
        current_behavior = behaviors.get('current', {})
        if current_behavior:
            task = current_behavior.get('task', current_behavior.get('behavior_id', 'Unknown Task'))
            agent = current_behavior.get('agent', 'Unknown Agent')
            iteration = behaviors.get('iteration', 1)
            task_short = task[:80] + '...' if len(task) > 80 else task
            lines.append(f'- {_format_checkbox(False)} {task_short} (Agent: {agent}, Iteration: {iteration})')

            # Show expected outputs for current behavior
            current_outputs = behaviors.get('current_outputs', {})
            expected_outputs = current_outputs.get('expected', [])
            if expected_outputs:
                lines.append('  Expected Outputs:')
                for output in expected_outputs:
                    output_name = output.get('name', 'Unknown')
                    output_desc = output.get('description', '')
                    lines.append(f'    - {output_name}: {output_desc}')

        return '\n'.join(lines)

    except Exception as e:
        return f'Local Current Task Planning and Assignment\nError: Unable to parse observation data - {str(e)}'
