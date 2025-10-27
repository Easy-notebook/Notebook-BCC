#!/usr/bin/env python3
"""
Quick validation script for the new architecture changes.
Tests the new fields and functionality added according to FINAL_DESIGN.md
"""

import sys
sys.path.insert(0, '/Users/macbook.silan.tech/Documents/GitHub/Notebook-BCC')

from core.context import WorkflowContext, SectionProgress
from stores.ai_context_store import AIPlanningContextStore
from models.action import ActionMetadata

def test_section_progress():
    """Test SectionProgress data structure"""
    print("Testing SectionProgress...")

    section_progress = SectionProgress(
        current_section_id="data_loading",
        current_section_number=2,
        completed_sections=["introduction"]
    )

    assert section_progress.current_section_id == "data_loading"
    assert section_progress.current_section_number == 2
    assert "introduction" in section_progress.completed_sections

    # Test to_dict
    progress_dict = section_progress.to_dict()
    assert progress_dict['current_section_id'] == "data_loading"
    assert progress_dict['current_section_number'] == 2

    print("✓ SectionProgress works correctly")


def test_workflow_context_behavior():
    """Test WorkflowContext behavior tracking"""
    print("\nTesting WorkflowContext behavior tracking...")

    ctx = WorkflowContext()
    ctx.current_stage_id = "chapter_0"
    ctx.current_step_id = "section_1"

    # Test behavior iteration
    assert ctx.behavior_iteration == 0
    ctx.behavior_iteration += 1
    ctx.current_behavior_id = f"behavior_{ctx.behavior_iteration:03d}"

    assert ctx.behavior_iteration == 1
    assert ctx.current_behavior_id == "behavior_001"

    # Test reset
    ctx.reset_for_new_step()
    assert ctx.behavior_iteration == 0
    assert ctx.current_behavior_id is None

    print("✓ WorkflowContext behavior tracking works correctly")


def test_ai_context_store_section():
    """Test AIContext Store section progress management"""
    print("\nTesting AIContext Store section progress...")

    store = AIPlanningContextStore()

    # Test section progress update
    store.update_current_section("data_assessment", 2)
    progress = store.get_section_progress()

    assert progress is not None
    assert progress.current_section_id == "data_assessment"
    assert progress.current_section_number == 2

    # Test section completion
    store.complete_section("data_assessment")
    assert "data_assessment" in progress.completed_sections

    # Test to_dict includes section_progress
    context_dict = store.get_context().to_dict()
    assert 'section_progress' in context_dict
    assert context_dict['section_progress'] is not None

    # Test new naming conventions
    assert 'todo_list' in context_dict
    assert 'effects' in context_dict

    # Test backward compatibility
    assert 'toDoList' in context_dict
    assert 'effect' in context_dict

    print("✓ AIContext Store section progress works correctly")


def test_action_metadata_section():
    """Test ActionMetadata section fields"""
    print("\nTesting ActionMetadata section fields...")

    metadata = ActionMetadata(
        is_section=True,
        section_id="data_loading",
        section_number=2
    )

    assert metadata.is_section is True
    assert metadata.section_id == "data_loading"
    assert metadata.section_number == 2

    # Test to_dict
    metadata_dict = metadata.to_dict()
    assert metadata_dict['is_section'] is True
    assert metadata_dict['section_id'] == "data_loading"
    assert metadata_dict['section_number'] == 2

    print("✓ ActionMetadata section fields work correctly")


def main():
    """Run all tests"""
    print("=" * 60)
    print("VALIDATING NEW ARCHITECTURE FEATURES")
    print("=" * 60)

    try:
        test_section_progress()
        test_workflow_context_behavior()
        test_ai_context_store_section()
        test_action_metadata_section()

        print("\n" + "=" * 60)
        print("✓ ALL VALIDATION TESTS PASSED!")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
