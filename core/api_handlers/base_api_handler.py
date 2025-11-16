"""
Base API Handler

Provides common functionality for all API handlers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncIterator, Union
from silantui import ModernLogger


class BaseAPIHandler(ABC, ModernLogger):
    """
    Base class for all API handlers.

    Each API handler is responsible for:
    1. Calling a specific API endpoint
    2. Handling request/response formatting
    3. Logging API calls
    4. Error handling and retries (future)

    This separates API calling logic from State logic,
    making it easier to maintain and test.
    """

    def __init__(self, api_client, handler_name: str = None):
        """
        Initialize the API handler.

        Args:
            api_client: AsyncWorkflowAPIClient instance
            handler_name: Name for logging (defaults to class name)
        """
        name = handler_name or self.__class__.__name__
        ModernLogger.__init__(self, name)
        self.api_client = api_client

    @abstractmethod
    async def call(
        self,
        state_data: Dict[str, Any],
        stage_id: str,
        step_id: str,
        **kwargs
    ) -> Union[Dict[str, Any], AsyncIterator[Dict[str, Any]]]:
        """
        Call the API endpoint.

        Args:
            state_data: Current state JSON
            stage_id: Current stage ID
            step_id: Current step ID
            **kwargs: Additional parameters specific to the API

        Returns:
            API response (dict for sync APIs, AsyncIterator for streaming APIs)
        """
        pass

    def _extract_location_info(self, state_data: Dict[str, Any]) -> tuple[str, str]:
        """
        Extract stage_id and step_id from state data.

        Args:
            state_data: Current state JSON

        Returns:
            Tuple of (stage_id, step_id)
        """
        observation = state_data.get('observation', {})
        location = observation.get('location', {})
        current = location.get('current', {})

        stage_id = current.get('stage_id', 'unknown')
        step_id = current.get('step_id', 'none')

        return stage_id, step_id

    def _should_log(self) -> bool:
        """
        Determine if this API call should be logged.

        Returns:
            True if logging is enabled (always False now, logging moved to TransitionHandlers)
        """
        # Logging is now handled by TransitionHandlers, not API client
        return False

    def __str__(self) -> str:
        return f"{self.__class__.__name__}"

    def __repr__(self) -> str:
        return self.__str__()
