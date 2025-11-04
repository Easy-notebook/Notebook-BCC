#!/usr/bin/env python3
"""
Update all goal.txt files with agent annotations for behaviors
"""
import os
import re
from pathlib import Path

def extract_agent_from_behavior(behavior_file):
    """Extract RECOMMENDED AGENT from behavior file"""
    try:
        with open(behavior_file, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'RECOMMENDED AGENT:\s*(.+)', content)
            if match:
                agent = match.group(1).strip()
                # Simplify agent name: "Explore-Agent" -> "Explore Agent"
                agent = agent.replace('-', ' ')
                return agent
            return None
    except Exception as e:
        print(f"Error reading {behavior_file}: {e}")
        return None

def extract_behavior_goal(behavior_file):
    """Extract GOAL from behavior file"""
    try:
        with open(behavior_file, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'GOAL:\s*(.+?)(?:\n\n|RECOMMENDED AGENT)', content, re.DOTALL)
            if match:
                goal = match.group(1).strip()
                # Take only the first sentence or line
                goal = goal.split('\n')[0].strip()
                # Remove trailing period if exists
                goal = goal.rstrip('.')
                return goal
            return None
    except Exception as e:
        print(f"Error reading {behavior_file}: {e}")
        return None

def update_goal_file(goal_file_path, step_dir):
    """Update goal.txt file with agent annotations"""
    try:
        # Read current goal.txt
        with open(goal_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find all behavior files in the step directory
        behavior_files = sorted([f for f in os.listdir(step_dir)
                                if f.startswith('behavior_') and f.endswith('.txt')])

        if not behavior_files:
            print(f"No behavior files found in {step_dir}")
            return False

        # Build new behaviors section
        new_behaviors = []
        for i, behavior_file in enumerate(behavior_files, 1):
            behavior_path = os.path.join(step_dir, behavior_file)
            agent = extract_agent_from_behavior(behavior_path)
            goal = extract_behavior_goal(behavior_path)

            if agent and goal:
                # Format: "1. behavior_1_xxx -> Agent Name"
                #         "   - Goal description"
                behavior_name = behavior_file.replace('.txt', '')
                new_behaviors.append(f"{i}. {behavior_name} -> {agent}")
                new_behaviors.append(f"   - {goal}")
                new_behaviors.append("")  # Empty line
            else:
                print(f"Warning: Could not extract agent or goal from {behavior_file}")

        # Remove trailing empty line
        if new_behaviors and new_behaviors[-1] == "":
            new_behaviors.pop()

        # Replace the BEHAVIORS section
        pattern = r'================================================================================\nBEHAVIORS IN THIS STEP you can choose from\(all build what you need\):\n================================================================================\n.*?\n================================================================================'

        behaviors_text = '\n'.join(new_behaviors)
        replacement = ('================================================================================\n'
                      'BEHAVIORS IN THIS STEP you can choose from(all build what you need):\n'
                      '================================================================================\n'
                      + behaviors_text + '\n\n'
                      '================================================================================')

        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

        # Write updated content
        with open(goal_file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"✓ Updated: {goal_file_path}")
        return True

    except Exception as e:
        print(f"Error updating {goal_file_path}: {e}")
        return False

def main():
    strategy_dir = Path("/Users/silan/Documents/github/Notebook-BCC/docs/examples/strategy")

    # Find all step directories (they contain goal.txt and behavior files)
    step_dirs = []
    for stage_dir in sorted(strategy_dir.glob("stage_*")):
        for step_dir in sorted(stage_dir.glob("step_*")):
            if step_dir.is_dir():
                goal_file = step_dir / "goal.txt"
                if goal_file.exists():
                    step_dirs.append((step_dir, goal_file))

    print(f"Found {len(step_dirs)} step directories to update\n")

    success_count = 0
    for step_dir, goal_file in step_dirs:
        if update_goal_file(goal_file, step_dir):
            success_count += 1

    print(f"\n{'='*80}")
    print(f"Summary: Updated {success_count}/{len(step_dirs)} goal.txt files")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
