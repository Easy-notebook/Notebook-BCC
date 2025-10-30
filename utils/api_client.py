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
from .api_logger import get_api_logger
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
        self.api_logger = get_api_logger()  # API 调用日志记录器

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()

    def close_sync(self):
        """
        Close the HTTP session synchronously (for cleanup).

        Note: Properly closing an aiohttp session requires the same event loop
        it was created in. Since this may not be available during cleanup,
        we rely on Python's garbage collector. ResourceWarnings are suppressed
        globally in the CLI.
        """
        # Session will be garbage collected automatically
        # ResourceWarnings are suppressed globally
        pass

    async def send_feedback(
        self,
        stage_id: str,
        step_index: str,
        state: Dict[str, Any],
        notebook_id: Optional[str] = None,
        behavior_feedback: Optional[Dict[str, Any]] = None  # Added: behavior feedback
    ) -> Dict[str, Any]:
        """
        Send feedback to get next workflow command.

        Args:
            stage_id: Current stage ID
            step_index: Current step ID/index (will be renamed to step_id in future)
            state: Current workflow state/context
            notebook_id: Optional notebook ID
            behavior_feedback: Optional behavior execution feedback

        Returns:
            Feedback response containing next command
        """
        try:
            # Compress state
            compressed_state = self.compressor.compress_context(state)

            # Extract progress information from state (new hierarchical format)
            progress_info = state.get('progress_info')
            fsm_info = state.get('FSM')

            # Require progress_info (no backward compatibility)
            if not progress_info:
                raise ValueError("Missing required 'progress_info' in state. New POMDP protocol requires hierarchical progress information.")

            # Build location with hierarchical progress structure
            location = progress_info

            # Build clean context (simplified format after refactoring)
            # Note: Progress and focus are now in observation.location.progress.*.focus
            clean_context = {
                'variables': compressed_state.get('variables', {}),
                'effects': compressed_state.get('effects', {'current': [], 'history': []}),
                'notebook': compressed_state.get('notebook', {})
            }

            # Add FSM info to context
            if fsm_info:
                clean_context['FSM'] = fsm_info

            # Build new payload structure (POMDP-compatible)
            payload = {
                'observation': {
                    'location': location,
                    'context': clean_context
                },
                'options': {
                    'stream': False
                }
            }

            # Add behavior_feedback if provided
            if behavior_feedback:
                payload['behavior_feedback'] = behavior_feedback

            if notebook_id:
                payload['notebook_id'] = notebook_id

            # 📝 记录 API 调用详情到独立日志文件
            log_file = self.api_logger.log_api_call(
                api_url=Config.FEEDBACK_API_URL,
                method='POST',
                payload=payload,
                context_state=state,
                extra_info={
                    'api_type': 'feedback',
                    'stage_id': stage_id,
                    'step_index': step_index,
                    'notebook_id': notebook_id
                }
            )
            if log_file:
                self.info(f"[API] 调用日志已保存: {log_file}")

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
        stream: bool = True,
        behavior_feedback: Optional[Dict[str, Any]] = None  # Added: behavior feedback
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Fetch actions for a behavior (streaming).

        Args:
            stage_id: Current stage ID
            step_index: Current step ID/index
            state: Current workflow state/context
            stream: Whether to use streaming
            behavior_feedback: Optional behavior execution feedback

        Yields:
            Action dictionaries
        """
        try:
            # Compress state
            compressed_state = self.compressor.compress_context(state)

            # Extract progress information from state (new hierarchical format)
            progress_info = state.get('progress_info')
            fsm_info = state.get('FSM')

            # Require progress_info (no backward compatibility)
            if not progress_info:
                raise ValueError("Missing required 'progress_info' in state. New POMDP protocol requires hierarchical progress information.")

            # Build location with hierarchical progress structure
            location = progress_info

            # Build clean context (simplified format after refactoring)
            # Note: Progress and focus are now in observation.location.progress.*.focus
            clean_context = {
                'variables': compressed_state.get('variables', {}),
                'effects': compressed_state.get('effects', {'current': [], 'history': []}),
                'notebook': compressed_state.get('notebook', {})
            }

            # Add FSM info to context
            if fsm_info:
                clean_context['FSM'] = fsm_info

            # Build new payload structure (POMDP-compatible)
            payload = {
                'observation': {
                    'location': location,
                    'context': clean_context
                },
                'options': {
                    'stream': stream
                }
            }

            # Add behavior_feedback if provided
            if behavior_feedback:
                payload['behavior_feedback'] = behavior_feedback

            # 📝 记录 API 调用详情到独立日志文件
            log_file = self.api_logger.log_api_call(
                api_url=Config.BEHAVIOR_API_URL,
                method='POST',
                payload=payload,
                context_state=state,
                extra_info={
                    'api_type': 'behavior_actions',
                    'stage_id': stage_id,
                    'step_index': step_index,
                    'stream': stream
                }
            )
            if log_file:
                self.info(f"[API] 调用日志已保存: {log_file}")

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
        notebook_id: Optional[str] = None,
        behavior_feedback: Optional[Dict[str, Any]] = None  # Added
    ) -> Dict[str, Any]:
        """Synchronous wrapper for send_feedback."""
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If event loop is already running, we need to use run_in_executor
            future = asyncio.ensure_future(
                self.send_feedback(stage_id, step_index, state, notebook_id, behavior_feedback)
            )
            return asyncio.get_event_loop().run_until_complete(future)
        else:
            return loop.run_until_complete(
                self.send_feedback(stage_id, step_index, state, notebook_id, behavior_feedback)
            )

    def fetch_behavior_actions_sync(
        self,
        stage_id: str,
        step_index: str,
        state: Dict[str, Any],
        stream: bool = True,
        behavior_feedback: Optional[Dict[str, Any]] = None  # Added
    ) -> List[Dict[str, Any]]:
        """Synchronous wrapper for fetch_behavior_actions."""
        async def collect_actions():
            actions = []
            async for action in self.fetch_behavior_actions(stage_id, step_index, state, stream, behavior_feedback):
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
