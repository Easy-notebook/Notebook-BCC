"""
Action data models.
Replicates the TypeScript ScriptAction and ExecutionStep interfaces.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime


@dataclass
class ActionMetadata:
    """
    Metadata associated with an action.
    Maps to TypeScript's ActionMetadata interface.
    """
    is_step: bool = False
    is_chapter: bool = False
    is_section: bool = False
    chapter_id: Optional[str] = None
    section_id: Optional[str] = None
    chapter_number: Optional[int] = None
    section_number: Optional[int] = None
    finished_thinking: bool = False
    thinking_text: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            'is_step': self.is_step,
            'is_chapter': self.is_chapter,
            'is_section': self.is_section,
            'finished_thinking': self.finished_thinking,
        }
        if self.chapter_id:
            result['chapter_id'] = self.chapter_id
        if self.section_id:
            result['section_id'] = self.section_id
        if self.chapter_number is not None:
            result['chapter_number'] = self.chapter_number
        if self.section_number is not None:
            result['section_number'] = self.section_number
        if self.thinking_text:
            result['thinking_text'] = self.thinking_text
        result.update(self.extra)
        return result


@dataclass
class ScriptAction:
    """
    Represents a single action in the workflow.
    Maps to TypeScript's ScriptAction interface.
    """
    id: str
    type: str  # 'text', 'code', 'thinking', etc.
    content: str
    metadata: ActionMetadata = field(default_factory=ActionMetadata)
    description: Optional[str] = None
    is_modified: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    step_id: Optional[str] = None
    could_visible_in_writing_mode: bool = True

    # Thinking cell specific
    agent_name: Optional[str] = None
    custom_text: Optional[str] = None
    text_array: List[str] = field(default_factory=list)
    use_workflow_thinking: bool = False

    # Code cell specific
    language: str = 'python'

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            'id': self.id,
            'type': self.type,
            'content': self.content,
            'metadata': self.metadata.to_dict(),
            'is_modified': self.is_modified,
            'timestamp': self.timestamp,
            'step_id': self.step_id,
            'could_visible_in_writing_mode': self.could_visible_in_writing_mode,
            'language': self.language,
        }
        if self.description:
            result['description'] = self.description
        if self.agent_name:
            result['agent_name'] = self.agent_name
        if self.custom_text is not None:
            result['custom_text'] = self.custom_text
        if self.text_array:
            result['text_array'] = self.text_array
        if self.use_workflow_thinking:
            result['use_workflow_thinking'] = self.use_workflow_thinking
        return result


@dataclass
class ExecutionStep:
    """
    Represents a command to be executed by the workflow executor.
    Maps to TypeScript's ExecutionStep interface.
    """
    action: str  # The action type (e.g., 'add', 'exec', 'is_thinking')
    store_id: Optional[str] = None
    content_type: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[ActionMetadata] = None

    # For thinking cells
    agent_name: Optional[str] = None
    custom_text: Optional[str] = None
    text_array: List[str] = field(default_factory=list)
    thinking_text: Optional[str] = None

    # For general text updates
    text: Optional[str] = None
    title: Optional[str] = None

    # For code execution
    action_id_ref: Optional[str] = None
    step_id: Optional[str] = None
    phase_id: Optional[str] = None  # Legacy support
    keep_debug_button_visible: bool = False
    codecell_id: Optional[str] = None
    need_output: bool = True
    auto_debug: bool = False

    # For workflow updates
    updated_workflow: Optional[Dict[str, Any]] = None
    updated_steps: Optional[List[Dict[str, Any]]] = None
    stage_id: Optional[str] = None

    # Backend-provided shotType: 'action'=code, 'markdown'=text
    shot_type: Optional[str] = None

    # State synchronization
    state: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {'action': self.action}

        # Add all non-None fields
        for key, value in self.__dict__.items():
            if key != 'action' and value is not None:
                if key == 'metadata' and isinstance(value, ActionMetadata):
                    result[key] = value.to_dict()
                else:
                    result[key] = value

        return result
