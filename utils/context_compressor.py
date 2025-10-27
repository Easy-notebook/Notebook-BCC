"""
Context Compressor
Compresses context data for API calls to avoid excessive payload size.
Replicates the TypeScript WorkflowAPIClient compression logic.
"""

import json
from silantui import ModernLogger
from typing import Dict, Any, List



class ContextCompressor(ModernLogger):
    """
    Compresses context data for API calls.
    Replicates TypeScript WorkflowAPIClient compression logic.
    """

    def __init__(self, max_context_length: int = 18600, max_history_items: int = 50):
        """
        Initialize the compressor.

        Args:
            max_context_length: Maximum context length in characters
            max_history_items: Maximum number of history items to keep
        """
        super().__init__("ContextCompressor")
        self.max_context_length = max_context_length
        self.max_history_items = max_history_items

    def compress_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compress context data to avoid exceeding size limits.

        Args:
            context: The context to compress

        Returns:
            Compressed context
        """
        if not context:
            return context

        compressed = dict(context)

        # Compress thinking history
        if 'thinking' in compressed and isinstance(compressed['thinking'], list):
            if len(compressed['thinking']) > self.max_history_items:
                # Keep only recent items
                compressed['thinking'] = compressed['thinking'][-self.max_history_items:]

        # Compress effect history
        if 'effect' in compressed and isinstance(compressed['effect'], dict):
            if 'history' in compressed['effect'] and len(compressed['effect']['history']) > self.max_history_items:
                compressed['effect']['history'] = compressed['effect']['history'][-self.max_history_items:]

        # Compress variables (remove large values)
        if 'variables' in compressed:
            compressed['variables'] = self._compress_variables(compressed['variables'])

        # Check total length
        context_str = json.dumps(compressed)
        if len(context_str) > self.max_context_length:
            self.warning(f"Context still too large ({len(context_str)} chars), applying aggressive compression")
            compressed = self._aggressive_compress(compressed)

        return compressed

    def _compress_variables(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Compress variables by truncating large values."""
        compressed = {}

        for key, value in variables.items():
            if isinstance(value, str) and len(value) > 200:
                compressed[key] = value[:200] + '...'
            elif isinstance(value, (list, dict)):
                value_str = str(value)
                if len(value_str) > 200:
                    compressed[key] = value_str[:200] + '...'
                else:
                    compressed[key] = value
            else:
                compressed[key] = value

        return compressed

    def _aggressive_compress(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply aggressive compression when normal compression is not enough."""
        compressed = {}

        # Only keep essential fields
        essential_fields = ['variables', 'toDoList', 'effect', 'stageStatus']

        for field in essential_fields:
            if field in context:
                compressed[field] = context[field]

        # Further compress
        if 'thinking' in compressed:
            compressed['thinking'] = compressed['thinking'][-10:] if isinstance(compressed['thinking'], list) else []

        if 'effect' in compressed and isinstance(compressed['effect'], dict):
            if 'history' in compressed['effect']:
                compressed['effect']['history'] = compressed['effect']['history'][-10:]
            if 'current' in compressed['effect']:
                compressed['effect']['current'] = compressed['effect']['current'][-10:]

        return compressed

    def summarize_step_result(self, result: Any) -> str:
        """Create a summary for step results."""
        if not result:
            return 'No result'

        if isinstance(result, dict):
            if 'code' in result:
                outputs_count = len(result.get('outputs', []))
                return f"Executed code with {outputs_count} outputs"

            if 'analysis' in result:
                analysis = str(result['analysis'])
                return analysis[:200] + '...' if len(analysis) > 200 else analysis

        result_str = str(result)
        return result_str[:100] + '...' if len(result_str) > 100 else result_str
