"""
Constants and Configuration for Store Modules
Centralized configuration to avoid scattered constants across modules.
"""

# =====================================================================
# Cell Type Mapping
# =====================================================================

CELL_TYPE_MAPPING = {
    'text': 'markdown',
    'code': 'code',
    'Hybrid': 'Hybrid',
    'outcome': 'outcome',
    'error': 'error',
    'thinking': 'thinking',
}

# =====================================================================
# Action Types
# =====================================================================

ACTION_TYPES = {
    'ADD_ACTION': 'add',
    'EXEC_CODE': 'exec',
    'IS_THINKING': 'is_thinking',
    'FINISH_THINKING': 'finish_thinking',
    'NEW_CHAPTER': 'new_chapter',
    'NEW_SECTION': 'new_section',
    'NEW_STEP': 'new_step',
    'UPDATE_TITLE': 'update_title',
    'COMMENT_RESULT': 'comment_result',
}

# =====================================================================
# Field Mappings for ExecutionStep Conversion
# =====================================================================

# Maps JSON camelCase keys to Python snake_case attributes
EXECUTION_STEP_FIELD_MAPPING = {
    'shotType': 'shot_type',
    'content': 'content',
    'storeId': 'store_id',
    'contentType': 'content_type',
    'codecellId': 'codecell_id',
    'needOutput': 'need_output',
    'autoDebug': 'auto_debug',
    'textArray': 'text_array',
    'agentName': 'agent_name',
    'customText': 'custom_text',
    'text': 'text',
    'title': 'title',
    'thinkingText': 'thinking_text',
    'updatedWorkflow': 'updated_workflow',
    'newSteps': 'updated_steps',
    'updatedSteps': 'updated_steps',
    'stageId': 'stage_id',
    'state': 'state',
    'actionIdRef': 'action_id_ref',
    'stepId': 'step_id',
    'phaseId': 'phase_id',
    'keepDebugButtonVisible': 'keep_debug_button_visible',
}

# Standard metadata fields (used for filtering extra fields)
METADATA_STANDARD_FIELDS = {
    'is_step', 'is_chapter', 'is_section',
    'chapter_id', 'section_id', 'chapter_number', 'section_number',
    'finished_thinking', 'thinking_text'
}

# =====================================================================
# Default Content by Type
# =====================================================================

DEFAULT_CONTENT = {
    'text': '',
    'code': '# Write your code here',
    'outcome': 'Results will be displayed here',
    'error': 'Error occurred',
    'thinking': 'AI is thinking...'
}
