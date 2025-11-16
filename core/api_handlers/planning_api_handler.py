"""
Planning API Handler

Handles calls to the Planning API (/planning endpoint).
Used to check if stage/step goals are achieved.
"""

from typing import Dict, Any, Optional
from .base_api_handler import BaseAPIHandler


class PlanningAPIHandler(BaseAPIHandler):
    """
    Handler for Planning API calls.

    The Planning API is called in two scenarios:
    1. STAGE_RUNNING state: Check if stage goal is achieved
    2. STEP_RUNNING state: Check if step goal is achieved

    Returns:
        - targetAchieved: bool - Whether goal is achieved
        - transition: dict - Server control signals
        - context_update: dict - Updates to apply
        - context_filter: dict - (Optional) Filtering instructions
    """

    def __init__(self, api_client, handler_name: str = None):
        """
        Initialize the Planning API handler.

        Args:
            api_client: AsyncWorkflowAPIClient instance
            handler_name: Name for logging (defaults to 'PlanningAPIHandler')
        """
        super().__init__(api_client, handler_name or 'PlanningAPIHandler')

    async def call(
        self,
        state_data: Dict[str, Any],
        stage_id: str = None,
        step_id: str = None,
        notebook_id: Optional[str] = None,
        transition_name: Optional[str] = None,
        behavior_feedback: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call the Planning API.

        Args:
            state_data: Current state JSON (containing observation and state)
            stage_id: Current stage ID (optional, extracted if not provided)
            step_id: Current step ID (optional, extracted if not provided)
            notebook_id: Optional notebook ID
            transition_name: Optional transition name for logging
            behavior_feedback: Optional behavior execution feedback
            **kwargs: Additional parameters (ignored)

        Returns:
            Planning API response dict
        """
        # Extract location info if not provided
        if not stage_id or not step_id:
            extracted_stage_id, extracted_step_id = self._extract_location_info(state_data)
            stage_id = stage_id or extracted_stage_id
            step_id = step_id or extracted_step_id

        self.info(f"[PlanningAPI] Calling Planning API (stage={stage_id}, step={step_id})")

        # Delegate to api_client
        try:
            response = await self.api_client.send_feedback(
                stage_id=stage_id,
                step_index=step_id,  # API client uses step_index parameter
                state=state_data,
                notebook_id=notebook_id,
                transition_name=transition_name,
                behavior_feedback=behavior_feedback
            )

            # Handle both JSON dict and XML string responses
            if isinstance(response, dict):
                self.info(f"[PlanningAPI] Response received (targetAchieved={response.get('targetAchieved')})")
            else:
                # XML or string response
                self.info(f"[PlanningAPI] Response received (XML/text, {len(str(response))} chars)")

            return response

        except Exception as e:
            self.error(f"[PlanningAPI] API call failed: {e}")
            raise
