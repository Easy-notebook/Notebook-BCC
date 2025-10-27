"""
Workflow API Client
Handles communication with the workflow backend API.
Replicates the TypeScript WorkflowAPIClient.
"""

import json
from silantui import ModernLogger
import aiohttp
import asyncio
from typing import Dict, Any, List, AsyncIterator, Optional
from .context_compressor import ContextCompressor
from config import Config



class WorkflowAPIClient(ModernLogger):
    """
    API client for workflow operations.
    Replicates TypeScript WorkflowAPIClient functionality.
    """

    def __init__(self):
        """Initialize the API client."""
        super().__init__("WorkflowAPIClient")
        self.compressor = ContextCompressor(
            max_context_length=Config.MAX_CONTEXT_LENGTH,
            max_history_items=Config.MAX_HISTORY_ITEMS
        )
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def send_feedback(
        self,
        stage_id: str,
        step_index: str,
        state: Dict[str, Any],
        notebook_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send feedback to get next workflow command.

        Args:
            stage_id: Current stage ID
            step_index: Current step ID/index
            state: Current workflow state/context
            notebook_id: Optional notebook ID

        Returns:
            Feedback response containing next command
        """
        try:
            # Compress state
            compressed_state = self.compressor.compress_context(state)

            # Prepare request
            payload = {
                'stage_id': stage_id,
                'step_index': step_index,
                'state': compressed_state,
            }

            if notebook_id:
                payload['notebook_id'] = notebook_id

            self.info(f"[API] Sending feedback for stage={stage_id}, step={step_index}")
            self.debug(f"[API] Payload size: {len(json.dumps(payload))} chars")

            # Send request
            session = await self._get_session()
            async with session.post(
                Config.FEEDBACK_API_URL,
                json=payload,
                headers={'Content-Type': 'application/json'}
            ) as response:
                response.raise_for_status()
                result = await response.json()

                self.info(f"[API] Feedback response: targetAchieved={result.get('targetAchieved')}")
                return result

        except aiohttp.ClientError as e:
            self.error(f"[API] Failed to send feedback: {e}")
            raise Exception(f"Feedback API error: {str(e)}")
        except Exception as e:
            self.error(f"[API] Unexpected error sending feedback: {e}", exc_info=True)
            raise

    async def fetch_behavior_actions(
        self,
        stage_id: str,
        step_index: str,
        state: Dict[str, Any],
        stream: bool = True
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Fetch actions for a behavior (streaming).

        Args:
            stage_id: Current stage ID
            step_index: Current step ID/index
            state: Current workflow state/context
            stream: Whether to use streaming

        Yields:
            Action dictionaries
        """
        try:
            # Compress state
            compressed_state = self.compressor.compress_context(state)

            # Prepare request
            payload = {
                'stage_id': stage_id,
                'step_index': step_index,
                'state': compressed_state,
                'stream': stream,
            }

            self.info(f"[API] Fetching behavior actions for stage={stage_id}, step={step_index}")

            session = await self._get_session()
            async with session.post(
                Config.BEHAVIOR_API_URL,
                json=payload,
                headers={'Content-Type': 'application/json'}
            ) as response:
                response.raise_for_status()

                if stream:
                    # Handle streaming response
                    buffer = ""
                    async for chunk in response.content.iter_any():
                        if chunk:
                            buffer += chunk.decode('utf-8')
                            lines = buffer.split('\n')
                            buffer = lines.pop()  # Keep incomplete line in buffer

                            for line in lines:
                                line = line.strip()
                                if line:
                                    try:
                                        message = json.loads(line)
                                        if 'action' in message:
                                            self.debug(f"[API] Received action: {message['action'].get('action')}")
                                            yield message['action']
                                    except json.JSONDecodeError as e:
                                        self.warning(f"[API] Failed to parse line: {line[:100]}")
                else:
                    # Handle non-streaming response
                    result = await response.json()
                    if 'actions' in result:
                        for action in result['actions']:
                            yield action

        except aiohttp.ClientError as e:
            self.error(f"[API] Failed to fetch behavior actions: {e}")
            raise Exception(f"Behavior API error: {str(e)}")
        except Exception as e:
            self.error(f"[API] Unexpected error fetching actions: {e}", exc_info=True)
            raise

    def send_feedback_sync(
        self,
        stage_id: str,
        step_index: str,
        state: Dict[str, Any],
        notebook_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Synchronous wrapper for send_feedback."""
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If event loop is already running, we need to use run_in_executor
            future = asyncio.ensure_future(
                self.send_feedback(stage_id, step_index, state, notebook_id)
            )
            return asyncio.get_event_loop().run_until_complete(future)
        else:
            return loop.run_until_complete(
                self.send_feedback(stage_id, step_index, state, notebook_id)
            )

    def fetch_behavior_actions_sync(
        self,
        stage_id: str,
        step_index: str,
        state: Dict[str, Any],
        stream: bool = True
    ) -> List[Dict[str, Any]]:
        """Synchronous wrapper for fetch_behavior_actions."""
        async def collect_actions():
            actions = []
            async for action in self.fetch_behavior_actions(stage_id, step_index, state, stream):
                actions.append(action)
            return actions

        loop = asyncio.get_event_loop()
        if loop.is_running():
            future = asyncio.ensure_future(collect_actions())
            return loop.run_until_complete(future)
        else:
            return loop.run_until_complete(collect_actions())


# Create singleton instance
workflow_api_client = WorkflowAPIClient()
