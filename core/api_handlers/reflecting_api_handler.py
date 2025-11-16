"""
Reflecting API Handler

Handles calls to the Reflecting API (/reflecting endpoint).
Returns a stream of actions for reflection on completed work.
"""

from typing import Dict, Any, Optional, AsyncIterator
from .base_api_handler import BaseAPIHandler


class ReflectingAPIHandler(BaseAPIHandler):
    """
    Handler for Reflecting API calls.

    The Reflecting API is called for *_COMPLETED states to reflect on
    completed stages/steps/behaviors and provide guidance for next actions.

    Returns:
        AsyncIterator of Action dictionaries:
        - add-text: Add markdown content (streamed from <add-comment>)
        - mark_step_complete: Mark step as complete
        - mark_stage_complete: Mark stage as complete
        - complete_reflection: End of reflection
    """

    def __init__(self, api_client, handler_name: str = None):
        """
        Initialize the Reflecting API handler.

        Args:
            api_client: AsyncWorkflowAPIClient instance
            handler_name: Name for logging (defaults to 'ReflectingAPIHandler')
        """
        super().__init__(api_client, handler_name or 'ReflectingAPIHandler')

    async def call(
        self,
        state_data: Dict[str, Any],
        stage_id: str = None,
        step_id: str = None,
        notebook_id: Optional[str] = None,
        behavior_feedback: Optional[Dict[str, Any]] = None,
        stream: bool = True,
        transition_name: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Call the Reflecting API.

        Args:
            state_data: Current state JSON (containing observation and state)
            stage_id: Current stage ID (optional, extracted if not provided)
            step_id: Current step ID (optional, extracted if not provided)
            notebook_id: Optional notebook ID
            behavior_feedback: Optional behavior execution feedback
            stream: Whether to use streaming (default: True)
            **kwargs: Additional parameters (ignored)

        Yields:
            Action dictionaries from the API response stream
        """
        # Extract location info if not provided
        if not stage_id or not step_id:
            extracted_stage_id, extracted_step_id = self._extract_location_info(state_data)
            stage_id = stage_id or extracted_stage_id
            step_id = step_id or extracted_step_id

        self.info(f"[ReflectingAPI] Calling Reflecting API (stage={stage_id}, step={step_id}, stream={stream})")

        # Delegate to api_client (which returns an AsyncIterator)
        try:
            action_count = 0
            async for action in self.api_client.send_reflecting(
                stage_id=stage_id,
                step_index=step_id,  # API client uses step_index parameter
                state=state_data,
                notebook_id=notebook_id,
                behavior_feedback=behavior_feedback,
                stream=stream,
                transition_name=transition_name
            ):
                action_count += 1
                self.debug(f"[ReflectingAPI] Action {action_count} received: {action.get('type', 'unknown')}")
                yield action

            self.info(f"[ReflectingAPI] Completed streaming {action_count} actions")

        except Exception as e:
            self.error(f"[ReflectingAPI] API call failed: {e}")
            raise
