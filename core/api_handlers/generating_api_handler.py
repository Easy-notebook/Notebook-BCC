"""
Generating API Handler

Handles calls to the Generating API (/generating endpoint).
Returns a stream of actions to execute in the notebook.
"""

from typing import Dict, Any, Optional, AsyncIterator
from .base_api_handler import BaseAPIHandler


class GeneratingAPIHandler(BaseAPIHandler):
    """
    Handler for Generating API calls.

    The Generating API is called in BEHAVIOR_RUNNING state after the
    Planning API determines the goal is not yet achieved.

    The API:
    - Receives filtered observation (may be affected by context_filter from Planning API)
    - Returns a list of Actions to execute
    - Actions can be streamed (recommended) or returned in batch

    Returns:
        AsyncIterator of Action dictionaries:
        - add: Add content to notebook
        - exec: Execute code cell
        - is_thinking/finish_thinking: Show thinking process
        - new_chapter/new_section: Create structure markers
        - update_title: Update notebook title
    """

    def __init__(self, api_client, handler_name: str = None):
        """
        Initialize the Generating API handler.

        Args:
            api_client: AsyncWorkflowAPIClient instance
            handler_name: Name for logging (defaults to 'GeneratingAPIHandler')
        """
        super().__init__(api_client, handler_name or 'GeneratingAPIHandler')

    async def call(
        self,
        state_data: Dict[str, Any],
        stage_id: str = None,
        step_id: str = None,
        stream: bool = True,
        transition_name: Optional[str] = None,
        behavior_feedback: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Call the Generating API.

        Args:
            state_data: Current state JSON (containing observation and state)
            stage_id: Current stage ID (optional, extracted if not provided)
            step_id: Current step ID (optional, extracted if not provided)
            stream: Whether to use streaming (True recommended)
            transition_name: Optional transition name for logging
            behavior_feedback: Optional behavior execution feedback
            **kwargs: Additional parameters (ignored)

        Yields:
            Action dictionaries from the API response stream
        """
        # Extract location info if not provided
        if not stage_id or not step_id:
            extracted_stage_id, extracted_step_id = self._extract_location_info(state_data)
            stage_id = stage_id or extracted_stage_id
            step_id = step_id or extracted_step_id

        self.info(f"[GeneratingAPI] Calling Generating API (stage={stage_id}, step={step_id}, stream={stream})")

        # Delegate to api_client (which returns an AsyncIterator)
        try:
            action_count = 0
            async for action in self.api_client.fetch_behavior_actions(
                stage_id=stage_id,
                step_index=step_id,  # API client uses step_index parameter
                state=state_data,
                stream=stream,
                transition_name=transition_name,
                behavior_feedback=behavior_feedback
            ):
                action_count += 1
                self.debug(f"[GeneratingAPI] Action {action_count} received: {action.get('type', 'unknown')}")
                yield action

            self.info(f"[GeneratingAPI] Completed streaming {action_count} actions")

        except Exception as e:
            self.error(f"[GeneratingAPI] API call failed: {e}")
            raise
