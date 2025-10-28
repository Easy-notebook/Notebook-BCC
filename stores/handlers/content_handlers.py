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

        action_id = step.store_id or str(uuid.uuid4())
        cell_type = 'code' if step.shot_type == 'action' else 'text'
        cleaned_content = clean_content(step.content or '', cell_type)

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
    Handle NEW_CHAPTER type.

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
            content=f"## {step.content}",
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
    Handle NEW_SECTION type.

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
            content=f"### {step.content}",
            metadata=step.metadata or ActionMetadata()
        ))
        script_store.section_counter += 1
        return action_id

    except Exception as e:
        if hasattr(script_store, 'error'):
            script_store.error(f"[ContentHandler] Error handling NEW_SECTION: {e}", exc_info=True)
        return None
