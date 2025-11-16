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


    async def send_reflecting(
        self,
        stage_id: str,
        step_index: str,
        state: Dict[str, Any],
        notebook_id: Optional[str] = None,
        behavior_feedback: Optional[Dict[str, Any]] = None,
        stream: bool = True,
        transition_name: Optional[str] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Send reflection to Reflecting API (/reflecting).

        This is the Reflecting API call for *_COMPLETED states.
        Used to reflect on completed stages/steps/behaviors and provide guidance for next actions.

        Now returns action stream (same format as generating API).

        Args:
            stage_id: Current stage ID
            step_index: Current step ID/index
            state: Current workflow state/context (contains progress_info per OBSERVATION_PROTOCOL.md)
            notebook_id: Optional notebook ID
            behavior_feedback: Optional behavior execution feedback
            stream: Whether to use streaming (default: True)

        Yields:
            Action dictionaries in the same format as generating API:
            - add-text: Add markdown content (streamed from <add-comment>)
            - mark_step_complete: Mark step as complete
            - mark_stage_complete: Mark stage as complete
            - complete_reflection: End of reflection
        """
        try:
            # State should already be in the correct format (observation + state)
            # Just add options field to the existing structure
            if 'observation' in state and 'state' in state:
                # State is already in correct format, use directly
                payload = {
                    'observation': state['observation'],
                    'state': state['state'],
                    'options': {
                        'stream': stream
                    }
                }
            else:
                # Legacy format: state contains progress_info
                compressed_state = self.compressor.compress_context(state)
                progress_info = state.get('progress_info')

                if not progress_info:
                    raise ValueError("Missing required 'progress_info' or 'observation' in state.")

                payload = {
                    'observation': {
                        'location': progress_info
                    },
                    'state': {
                        'variables': compressed_state.get('variables', {}),
                        'effects': compressed_state.get('effects', {'current': [], 'history': []}),
                        'notebook': compressed_state.get('notebook', {}),
                        'FSM': state.get('FSM', {})
                    },
                    'options': {
                        'stream': stream
                    }
                }

            # Add behavior_feedback if provided
            if behavior_feedback:
                payload['behavior_feedback'] = behavior_feedback

            if notebook_id:
                payload['notebook_id'] = notebook_id

            self.info(f"[API] Sending reflection for stage={stage_id}, step={step_index}, stream={stream}")
            self.debug(f"[API] Payload size: {len(json.dumps(payload))} chars")

            # Send request and capture response
            session = await self._get_session()

            try:
                async with session.post(
                    Config.REFLECTING_API_URL,
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    # Check for errors
                    if response.status >= 400:
                        error_body = await response.text()
                        self.error(f"[API] Reflecting API error {response.status}: {error_body}")
                        raise Exception(f"Reflecting API error {response.status}: {error_body}")

                    response.raise_for_status()

                    if stream:
                        # Handle streaming response (NDJSON format like generating API)
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
                                            # Response format: {"action": {"type": "...", ...}}
                                            if 'action' in message:
                                                action = message['action']
                                                action_type = action.get('type', 'unknown')
                                                self.debug(f"[API] Received reflection action: {action_type}")
                                                yield action
                                            else:
                                                # Fallback: if message is the action itself
                                                self.debug(f"[API] Received direct reflection action: {message.get('type', 'unknown')}")
                                                yield message
                                        except json.JSONDecodeError as e:
                                            self.warning(f"[API] Failed to parse reflection line: {line[:100]}")
                    else:
                        # Handle non-streaming response
                        result = await response.json()
                        if 'actions' in result:
                            for action in result['actions']:
                                yield action

            except aiohttp.ClientError as e:
                self.error(f"[API] Failed to send reflection: {e}")
                raise Exception(f"Reflecting API error: {str(e)}")

        except Exception as e:
            self.error(f"[API] Unexpected error sending reflection: {e}", exc_info=True)
            raise

    async def send_feedback(
        self,
        stage_id: str,
        step_index: str,
        state: Dict[str, Any],
        notebook_id: Optional[str] = None,
        transition_name: Optional[str] = None,
        behavior_feedback: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send feedback to Planning API (/planning).

        This is the Planning API call per STATE_MACHINE_PROTOCOL.md.
        Used in two scenarios:
        1. STAGE_RUNNING state: Check if stage goal is achieved (Planning First)
        2. STEP_RUNNING state: Check if step goal is achieved (Planning First)

        Args:
            stage_id: Current stage ID
            step_index: Current step ID/index (will be renamed to step_id in future)
            state: Current workflow state/context (contains progress_info per OBSERVATION_PROTOCOL.md)
            notebook_id: Optional notebook ID
            behavior_feedback: Optional behavior execution feedback (for scenario 2)

        Returns:
            Planning API response containing:
            - targetAchieved: bool - Whether goal is achieved
            - transition: dict - Server control signals (continue_behaviors, target_achieved)
            - context_update: dict - Updates to apply (variables, progress_update, etc.)
            - context_filter: dict - (Optional) Filtering instructions for next Generating API call
        """
        try:
            # State should already be in the correct format (observation + state)
            # as loaded from state files like 00_STATE_IDLE.json
            # Just add options field to the existing structure
            if 'observation' in state and 'state' in state:
                # State is already in correct format, but compress notebook to reduce payload size
                state_copy = {
                    'variables': state['state'].get('variables', {}),
                    'effects': state['state'].get('effects', {'current': [], 'history': []}),
                    'notebook': self.compressor.compress_notebook(
                        state['state'].get('notebook', {}),
                        max_cells=5  # Keep only last 5 cells
                    ),
                    'FSM': state['state'].get('FSM', {})
                }

                payload = {
                    'observation': state['observation'],
                    'state': state_copy,
                    'options': {
                        'stream': False
                    }
                }
            else:
                # Legacy format: state contains progress_info
                # Compress state
                compressed_state = self.compressor.compress_context(state)

                # Extract progress information
                progress_info = state.get('progress_info')

                if not progress_info:
                    raise ValueError("Missing required 'progress_info' or 'observation' in state.")

                # Build payload structure
                payload = {
                    'observation': {
                        'location': progress_info
                    },
                    'state': {
                        'variables': compressed_state.get('variables', {}),
                        'effects': compressed_state.get('effects', {'current': [], 'history': []}),
                        'notebook': compressed_state.get('notebook', {}),
                        'FSM': state.get('FSM', {})
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

            # Note: stage_id and step_index are only for logging/tracking
            # The actual state is sent via the 'observation' and 'state' fields in payload
            self.info(f"[API] Sending feedback (context: stage={stage_id}, step={step_index})")
            self.debug(f"[API] Payload size: {len(json.dumps(payload))} chars")

            # Send request and capture response
            session = await self._get_session()
            response_data = None
            response_status = None
            response_error = None

            try:
                async with session.post(
                    Config.FEEDBACK_API_URL,
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    response_status = response.status

                    # If error, try to read response body for details
                    if response_status >= 400:
                        try:
                            error_body = await response.text()
                            response_error = f"HTTP {response_status}: {error_body}"
                        except:
                            response_error = f"HTTP {response_status}: {response.reason}"

                        self.error(f"[API] Failed to send feedback: {response_error}")
                        raise Exception(f"Feedback API error: {response_error}")

                    response.raise_for_status()

                    # Check content type
                    content_type = response.headers.get('Content-Type', '')

                    if 'xml' in content_type or 'text' in content_type:
                        # XML response - return raw XML string
                        xml_text = await response.text()
                        response_data = xml_text  # Store raw XML for logging
                        result = xml_text  # Return raw XML directly
                        self.info(f"[API] Planning response: XML ({len(xml_text)} chars)")
                    else:
                        # JSON response - standard format
                        result = await response.json()
                        response_data = result  # Store JSON for logging
                        self.info(f"[API] Planning response: targetAchieved={result.get('targetAchieved')}")

                    return result

            except aiohttp.ClientError as e:
                response_error = str(e)
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
        transition_name: Optional[str] = None,
        behavior_feedback: Optional[Dict[str, Any]] = None  # Added: behavior feedback
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Fetch actions from Generating API (/generating).

        This is the Generating API call per STATE_MACHINE_PROTOCOL.md.
        Called in BEHAVIOR_RUNNING state after Planning API determines goal not achieved.

        The Generating API:
        - Receives filtered observation (may be affected by context_filter from Planning API)
        - Returns a list of Actions to execute
        - Actions can be streamed (recommended) or returned in batch

        Args:
            stage_id: Current stage ID
            step_index: Current step ID/index
            state: Current workflow state/context (contains progress_info per OBSERVATION_PROTOCOL.md)
            stream: Whether to use streaming (True recommended)
            behavior_feedback: Optional behavior execution feedback

        Yields:
            Action dictionaries per ACTION_PROTOCOL.md:
            - add: Add content to notebook
            - exec: Execute code cell
            - is_thinking/finish_thinking: Show thinking process
            - new_chapter/new_section: Create structure markers
            - update_title: Update notebook title
        """
        try:
            # State should already be in the correct format (observation + state)
            # Just add options field to the existing structure
            if 'observation' in state and 'state' in state:
                # State is already in correct format, but compress notebook to reduce payload size
                state_copy = {
                    'variables': state['state'].get('variables', {}),
                    'effects': state['state'].get('effects', {'current': [], 'history': []}),
                    'notebook': self.compressor.compress_notebook(
                        state['state'].get('notebook', {}),
                        max_cells=5  # Keep only last 5 cells
                    ),
                    'FSM': state['state'].get('FSM', {})
                }

                payload = {
                    'observation': state['observation'],
                    'state': state_copy,
                    'options': {
                        'stream': stream
                    }
                }
            else:
                # Legacy format: state contains progress_info
                compressed_state = self.compressor.compress_context(state)
                progress_info = state.get('progress_info')

                if not progress_info:
                    raise ValueError("Missing required 'progress_info' or 'observation' in state.")

                payload = {
                    'observation': {
                        'location': progress_info
                    },
                    'state': {
                        'variables': compressed_state.get('variables', {}),
                        'effects': compressed_state.get('effects', {'current': [], 'history': []}),
                        'notebook': compressed_state.get('notebook', {}),
                        'FSM': state.get('FSM', {})
                    },
                    'options': {
                        'stream': stream
                    }
                }

            # Add behavior_feedback if provided
            if behavior_feedback:
                payload['behavior_feedback'] = behavior_feedback

            self.info(f"[API] Fetching behavior actions for stage={stage_id}, step={step_index}")

            session = await self._get_session()
            async with session.post(
                Config.BEHAVIOR_API_URL,
                json=payload,
                headers={'Content-Type': 'application/json'}
            ) as response:
                response_status = response.status

                # If error, try to read response body for details
                if response_status >= 400:
                    try:
                        error_body = await response.text()
                        response_error = f"HTTP {response_status}: {error_body}"
                    except:
                        response_error = f"HTTP {response_status}: {response.reason}"

                    self.error(f"[API] Failed to fetch behavior actions: {response_error}")
                    raise Exception(f"Behavior API error: {response_error}")

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
                                        # Response format: {"action": {"type": "...", "content": "..."}}
                                        if 'action' in message:
                                            action = message['action']
                                            action_type = action.get('type') or action.get('action', 'unknown')
                                            self.debug(f"[API] Received action: {action_type}")
                                            yield action
                                        else:
                                            # Fallback: if message is the action itself
                                            self.debug(f"[API] Received direct action: {message.get('type', 'unknown')}")
                                            yield message
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


# Create singleton instance
workflow_api_client = WorkflowAPIClient()
