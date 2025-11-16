"""
Action Utilities - Shared helper functions for actions
"""

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
