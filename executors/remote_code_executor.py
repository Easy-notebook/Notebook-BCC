"""
Remote Code Executor
Executes Python code on a remote Jupyter kernel via HTTP API.
Replicates the frontend's NotebookApiService code execution.
"""

from silantui import ModernLogger
import time
import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
from models.cell import CellOutput
from config import Config



class RemoteCodeExecutor(ModernLogger):
    """
    Remote code executor that communicates with backend Jupyter kernel.
    Replicates TypeScript NotebookApiService functionality.
    """

    def __init__(self):
        """Initialize the remote executor."""
        super().__init__("RemoteCodeExecutor")
        self.session: Optional[aiohttp.ClientSession] = None
        self.notebook_id: Optional[str] = None
        self.is_kernel_ready = False

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def initialize_kernel(self) -> bool:
        """
        Initialize the Jupyter kernel.

        Returns:
            True if successful
        """
        if self.is_kernel_ready:
            self.info("[RemoteCodeExecutor] Kernel already initialized")
            return True

        try:
            self.info("[RemoteCodeExecutor] Initializing kernel...")
            session = await self._get_session()

            async with session.post(
                Config.NOTEBOOK_INITIALIZE_URL,
                json={},
                headers={'Content-Type': 'application/json'}
            ) as response:
                response.raise_for_status()
                result = await response.json()

                if result.get('status') == 'ok':
                    self.notebook_id = result.get('notebook_id')
                    self.is_kernel_ready = True
                    self.info(f"[RemoteCodeExecutor] Kernel initialized: {self.notebook_id}")
                    return True
                else:
                    raise Exception(result.get('message', 'Kernel initialization failed'))

        except aiohttp.ClientError as e:
            self.error(f"[RemoteCodeExecutor] Failed to initialize kernel: {e}")
            self.is_kernel_ready = False
            return False
        except Exception as e:
            self.error(f"[RemoteCodeExecutor] Unexpected error initializing kernel: {e}", exc_info=True)
            self.is_kernel_ready = False
            return False

    async def restart_kernel(self) -> bool:
        """
        Restart the Jupyter kernel.

        Returns:
            True if successful
        """
        if not self.notebook_id:
            self.error("[RemoteCodeExecutor] Cannot restart: no notebook ID")
            return False

        try:
            self.info("[RemoteCodeExecutor] Restarting kernel...")
            session = await self._get_session()

            async with session.post(
                Config.NOTEBOOK_RESTART_URL,
                json={'notebook_id': self.notebook_id},
                headers={'Content-Type': 'application/json'}
            ) as response:
                response.raise_for_status()
                result = await response.json()

                if result.get('status') == 'ok':
                    self.info("[RemoteCodeExecutor] Kernel restarted successfully")
                    return True
                else:
                    raise Exception(result.get('message', 'Kernel restart failed'))

        except Exception as e:
            self.error(f"[RemoteCodeExecutor] Failed to restart kernel: {e}", exc_info=True)
            return False

    async def execute(self, code: str, codecell_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute Python code remotely.

        Args:
            code: The Python code to execute
            codecell_id: Optional code cell ID for tracking

        Returns:
            Execution result dictionary
        """
        # Ensure kernel is initialized
        if not self.is_kernel_ready:
            await self.initialize_kernel()

        if not self.notebook_id:
            return {
                'success': False,
                'error': 'Kernel not initialized',
                'outputs': []
            }

        try:
            self.info(f"[RemoteCodeExecutor] Executing code (cell: {codecell_id})")
            session = await self._get_session()

            # Start execution
            async with session.post(
                Config.NOTEBOOK_EXECUTE_URL,
                json={
                    'code': code,
                    'notebook_id': self.notebook_id,
                    'codecell_id': codecell_id  # Pass codecell_id to backend
                },
                headers={'Content-Type': 'application/json'}
            ) as response:
                response.raise_for_status()
                result = await response.json()

                # Check if execution started
                if result.get('status') == 'ok':
                    # Poll for completion
                    outputs = await self._poll_execution_status()

                    return {
                        'success': True,
                        'outputs': outputs,
                        'result': None,
                        'error': None
                    }
                else:
                    error_msg = result.get('message', 'Execution failed')
                    self.error(f"[RemoteCodeExecutor] Execution error: {error_msg}")

                    return {
                        'success': False,
                        'error': error_msg,
                        'outputs': []
                    }

        except aiohttp.ClientError as e:
            self.error(f"[RemoteCodeExecutor] HTTP error: {e}")
            return {
                'success': False,
                'error': str(e),
                'outputs': []
            }
        except Exception as e:
            self.error(f"[RemoteCodeExecutor] Unexpected error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'outputs': []
            }

    async def _poll_execution_status(self) -> List[CellOutput]:
        """
        Poll the execution status until completion.

        Returns:
            List of cell outputs
        """
        outputs = []
        start_time = time.time()
        session = await self._get_session()

        while True:
            # Check timeout
            if time.time() - start_time > Config.EXECUTION_TIMEOUT:
                self.error("[RemoteCodeExecutor] Execution timeout")
                break

            try:
                # Get status
                async with session.get(
                    Config.NOTEBOOK_STATUS_URL,
                    params={'notebook_id': self.notebook_id}
                ) as response:
                    response.raise_for_status()
                    status = await response.json()

                    # Check if still running
                    if status.get('status') == 'idle':
                        # Execution complete
                        if status.get('outputs'):
                            outputs = self._parse_outputs(status['outputs'])
                        break

                    # Update outputs if available
                    if status.get('outputs'):
                        outputs = self._parse_outputs(status['outputs'])

                    # Wait before next poll
                    await asyncio.sleep(Config.STATUS_CHECK_INTERVAL)

            except Exception as e:
                self.error(f"[RemoteCodeExecutor] Status check error: {e}")
                break

        return outputs

    def _parse_outputs(self, raw_outputs: List[Dict[str, Any]]) -> List[CellOutput]:
        """Parse raw outputs into CellOutput objects."""
        parsed = []

        for output in raw_outputs:
            output_type = output.get('type', 'text')
            content = output.get('content', '')

            cell_output = CellOutput(
                output_type=output_type,
                content=content,
                text=output.get('text', content)
            )

            # Handle errors
            if output_type == 'error':
                cell_output.ename = output.get('ename')
                cell_output.evalue = output.get('evalue')
                cell_output.traceback = output.get('traceback', [])

            parsed.append(cell_output)

        return parsed

    async def cancel_execution(self) -> bool:
        """Cancel current execution."""
        if not self.notebook_id:
            return False

        try:
            self.info("[RemoteCodeExecutor] Canceling execution...")
            session = await self._get_session()

            async with session.post(
                Config.NOTEBOOK_CANCEL_URL,
                json={'notebook_id': self.notebook_id},
                headers={'Content-Type': 'application/json'}
            ) as response:
                response.raise_for_status()
                result = await response.json()

                return result.get('status') == 'ok'

        except Exception as e:
            self.error(f"[RemoteCodeExecutor] Failed to cancel execution: {e}")
            return False

    # ==============================================
    # Synchronous Wrappers
    # ==============================================

    def execute_sync(self, code: str, codecell_id: Optional[str] = None) -> Dict[str, Any]:
        """Synchronous wrapper for execute."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.execute(code, codecell_id))

    def initialize_kernel_sync(self) -> bool:
        """Synchronous wrapper for initialize_kernel."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.initialize_kernel())

    def restart_kernel_sync(self) -> bool:
        """Synchronous wrapper for restart_kernel."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.restart_kernel())

    def cancel_execution_sync(self) -> bool:
        """Synchronous wrapper for cancel_execution."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.cancel_execution())


# Create singleton instance
remote_code_executor = RemoteCodeExecutor()
