"""
Content Handlers - Manage content addition and organization
Handles: add_action, new_chapter, new_section
"""

import uuid
from typing import Optional
from models.action import ExecutionStep, ScriptAction, ActionMetadata


# =====================================================================
# Content Cleaning Utilities
# =====================================================================

CONTENT_PREFIXES_TO_REMOVE = [
    'Add text to the notebook:',
    'Add text to the notebook: ',
    'Add code to the notebook:',
    'Add code to the notebook: ',
    'Add code to the notebook and run it:',
    'Add code to the notebook and run it: ',
    'Update the title of the notebook:',
    'Update the title of the notebook: ',
]


def clean_content(content: str, cell_type: str = 'text') -> str:
    """
    Clean content by removing meta-instruction prefixes.

    Args:
        content: Raw content from API
        cell_type: Type of cell ('text' or 'code')

    Returns:
        Cleaned content without meta-instruction prefixes
    """
    if not content:
        return content

    # Remove meta-instruction prefixes
    for prefix in CONTENT_PREFIXES_TO_REMOVE:
        if content.startswith(prefix):
            content = content[len(prefix):]
            break

    # For code cells, remove markdown code block markers if present
    if cell_type == 'code':
        content = content.strip()
        if content.startswith('```python\n'):
            content = content[10:]
        elif content.startswith('```\n'):
            content = content[4:]
        if content.endswith('\n```'):
            content = content[:-4]
        elif content.endswith('```'):
            content = content[:-3]

    return content.strip()


# =====================================================================
# Handler Functions
# =====================================================================

def handle_add_action(script_store, step: ExecutionStep) -> Optional[str]:
    """
    Handle ADD_ACTION type.

    For text cells with shot_type='markdown' or None (default to markdown):
    - If the last cell is a markdown cell and is NOT a heading (doesn't start with #),
      append content to the last cell instead of creating a new one
    - Otherwise, create a new cell as usual

    Args:
        script_store: Reference to ScriptStore instance
        step: Execution step containing action details

    Returns:
        Action ID if successful, None otherwise

    Raises:
        ValueError: If step is invalid
    """
    try:
        if not step:
            raise ValueError("Execution step cannot be None")

        cell_type = 'code' if step.shot_type == 'action' else 'text'
        cleaned_content = clean_content(step.content or '', cell_type)

        # Special logic for text cells with markdown shot_type or None (default to markdown)
        # When shot_type is None or 'markdown', treat as markdown content
        if cell_type == 'text' and (step.shot_type == 'markdown' or step.shot_type is None):
            # Check if we should append to the last cell
            if script_store.notebook_store:
                last_cell = script_store.notebook_store.get_last_cell()

                # Append to last cell if:
                # 1. Last cell exists
                # 2. Last cell is markdown type
                # 3. Last cell content doesn't start with # (not a heading)
                if last_cell and hasattr(last_cell, 'type'):
                    from models.cell import CellType
                    if (last_cell.type == CellType.MARKDOWN and
                        last_cell.content and
                        not last_cell.content.strip().startswith('#')):
                        # Append to existing cell
                        new_content = last_cell.content + '\n\n' + cleaned_content
                        script_store.notebook_store.update_cell(last_cell.id, new_content)
                        if hasattr(script_store, 'info'):
                            script_store.info(f"[ContentHandler] Appended to last markdown cell: {last_cell.id}")
                        return last_cell.id

        # Default behavior: create new cell
        action_id = step.store_id or str(uuid.uuid4())
        script_store.add_action(ScriptAction(
            id=action_id,
            type=cell_type,
            content=cleaned_content,
            metadata=step.metadata or ActionMetadata()
        ))
        return action_id

    except Exception as e:
        if hasattr(script_store, 'error'):
            script_store.error(f"[ContentHandler] Error handling ADD_ACTION: {e}", exc_info=True)
        return None


def handle_new_chapter(script_store, step: ExecutionStep) -> Optional[str]:
    """
    Handle NEW_CHAPTER type (Level 1 heading: #).

    Args:
        script_store: Reference to ScriptStore instance
        step: Execution step containing chapter title

    Returns:
        Action ID if successful, None otherwise
    """
    try:
        if not step or not step.content:
            if hasattr(script_store, 'warning'):
                script_store.warning("[ContentHandler] NEW_CHAPTER requires content")
            return None

        action_id = step.store_id or str(uuid.uuid4())
        script_store.add_action(ScriptAction(
            id=action_id,
            type='text',
            content=f"# {step.content}",  # Fixed: Level 1 heading
            metadata=step.metadata or ActionMetadata()
        ))
        script_store.chapter_counter += 1
        return action_id

    except Exception as e:
        if hasattr(script_store, 'error'):
            script_store.error(f"[ContentHandler] Error handling NEW_CHAPTER: {e}", exc_info=True)
        return None


def handle_new_section(script_store, step: ExecutionStep) -> Optional[str]:
    """
    Handle NEW_SECTION type (Level 2 heading: ##).

    Args:
        script_store: Reference to ScriptStore instance
        step: Execution step containing section title

    Returns:
        Action ID if successful, None otherwise
    """
    try:
        if not step or not step.content:
            if hasattr(script_store, 'warning'):
                script_store.warning("[ContentHandler] NEW_SECTION requires content")
            return None

        action_id = step.store_id or str(uuid.uuid4())
        script_store.add_action(ScriptAction(
            id=action_id,
            type='text',
            content=f"## {step.content}",  # Fixed: Level 2 heading
            metadata=step.metadata or ActionMetadata()
        ))
        script_store.section_counter += 1
        return action_id

    except Exception as e:
        if hasattr(script_store, 'error'):
            script_store.error(f"[ContentHandler] Error handling NEW_SECTION: {e}", exc_info=True)
        return None


def handle_new_step(script_store, step: ExecutionStep) -> Optional[str]:
    """
    Handle NEW_STEP type (Level 3 heading: ###).

    Args:
        script_store: Reference to ScriptStore instance
        step: Execution step containing step title

    Returns:
        Action ID if successful, None otherwise
    """
    try:
        if not step or not step.content:
            if hasattr(script_store, 'warning'):
                script_store.warning("[ContentHandler] NEW_STEP requires content")
            return None

        action_id = step.store_id or str(uuid.uuid4())
        script_store.add_action(ScriptAction(
            id=action_id,
            type='text',
            content=f"### {step.content}",  # Level 3 heading
            metadata=step.metadata or ActionMetadata()
        ))
        return action_id

    except Exception as e:
        if hasattr(script_store, 'error'):
            script_store.error(f"[ContentHandler] Error handling NEW_STEP: {e}", exc_info=True)
        return None


def handle_comment_result(script_store, step: ExecutionStep) -> Optional[str]:
    """
    Handle COMMENT_RESULT type.

    This action type works exactly like add_markdown (adding markdown content),
    but after execution it moves effect.current to effect.history.

    Args:
        script_store: Reference to ScriptStore instance
        step: Execution step containing comment content

    Returns:
        Action ID if successful, None otherwise
    """
    try:
        if not step:
            raise ValueError("Execution step cannot be None")

        # First, add the markdown content (same as add action with dialogue shot_type)
        cell_type = 'text'
        cleaned_content = clean_content(step.content or '', cell_type)

        # Create new markdown cell
        action_id = step.store_id or str(uuid.uuid4())
        script_store.add_action(ScriptAction(
            id=action_id,
            type=cell_type,
            content=cleaned_content,
            metadata=step.metadata or ActionMetadata()
        ))

        # After adding the content, move current effects to history
        if script_store.ai_context_store:
            script_store.ai_context_store.move_current_effects_to_history()
            if hasattr(script_store, 'info'):
                script_store.info("[ContentHandler] Moved effect.current to history after comment_result")

        return action_id

    except Exception as e:
        if hasattr(script_store, 'error'):
            script_store.error(f"[ContentHandler] Error handling COMMENT_RESULT: {e}", exc_info=True)
        return None
