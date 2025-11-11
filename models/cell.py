"""
Cell data models for the notebook.
Replicates the cell types and structures from the frontend.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class CellType(Enum):
    """Cell types supported in the notebook."""
    MARKDOWN = 'markdown'
    CODE = 'code'
    THINKING = 'thinking'
    HYBRID = 'Hybrid'
    OUTCOME = 'outcome'
    ERROR = 'error'


@dataclass
class CellOutput:
    """Represents output from a code cell."""
    output_type: str  # 'stream', 'execute_result', 'error', 'display_data'
    content: str = ''
    text: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    execution_count: Optional[int] = None

    # For error outputs
    ename: Optional[str] = None
    evalue: Optional[str] = None
    traceback: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {'output_type': self.output_type}

        # Only include text field (not content) for consistency with frontend
        if self.text:
            result['text'] = self.text
        if self.data:
            result['data'] = self.data
        if self.execution_count is not None:
            result['execution_count'] = self.execution_count
        if self.ename:
            result['ename'] = self.ename
        if self.evalue:
            result['evalue'] = self.evalue
        if self.traceback:
            result['traceback'] = self.traceback

        return result


@dataclass
class Cell:
    """
    Represents a notebook cell.
    Maps to the frontend's cell structure.
    """
    id: str
    type: CellType
    content: str = ''
    outputs: List[CellOutput] = field(default_factory=list)
    enable_edit: bool = True
    phase_id: Optional[str] = None  # Links to workflow step
    description: str = ''
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Code-specific
    language: str = 'python'
    execution_count: Optional[int] = None

    # Thinking-specific
    agent_name: str = 'AI'
    custom_text: Optional[str] = None
    text_array: List[str] = field(default_factory=list)
    use_workflow_thinking: bool = False

    # UI-related
    could_visible_in_writing_mode: bool = True

    def __post_init__(self):
        """Ensure type is CellType enum."""
        if isinstance(self.type, str):
            self.type = CellType(self.type)

    def add_output(self, output: CellOutput):
        """Add an output to the cell."""
        self.outputs.append(output)

    def clear_outputs(self):
        """Clear all outputs."""
        self.outputs = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            'id': self.id,
            'type': self.type.value,
            'content': self.content,
            'outputs': [out.to_dict() for out in self.outputs],
            'enable_edit': self.enable_edit,
            'description': self.description,
            'metadata': self.metadata,
            'language': self.language,
            'could_visible_in_writing_mode': self.could_visible_in_writing_mode,
        }

        if self.phase_id:
            result['phase_id'] = self.phase_id
        if self.execution_count is not None:
            result['execution_count'] = self.execution_count

        # Add thinking-specific fields
        if self.type == CellType.THINKING:
            result['agent_name'] = self.agent_name
            if self.custom_text is not None:
                result['custom_text'] = self.custom_text
            if self.text_array:
                result['text_array'] = self.text_array
            result['use_workflow_thinking'] = self.use_workflow_thinking

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Cell':
        """Create a Cell from a dictionary."""
        cell_type = CellType(data['type'])
        outputs = [CellOutput(**out) if isinstance(out, dict) else out
                   for out in data.get('outputs', [])]

        return cls(
            id=data['id'],
            type=cell_type,
            content=data.get('content', ''),
            outputs=outputs,
            enable_edit=data.get('enable_edit', True),
            phase_id=data.get('phase_id'),
            description=data.get('description', ''),
            metadata=data.get('metadata', {}),
            language=data.get('language', 'python'),
            execution_count=data.get('execution_count'),
            agent_name=data.get('agent_name', 'AI'),
            custom_text=data.get('custom_text'),
            text_array=data.get('text_array', []),
            use_workflow_thinking=data.get('use_workflow_thinking', False),
            could_visible_in_writing_mode=data.get('could_visible_in_writing_mode', True),
        )
