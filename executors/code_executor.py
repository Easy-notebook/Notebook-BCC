"""
Code Executor
Executes Python code by calling the backend Jupyter kernel API.
Replicates the frontend's NotebookApiService and codeStore logic.
"""

import time
import requests
from typing import Dict, Any, List, Optional
from silantui import ModernLogger
from models.cell import CellOutput
from config import Config


class CodeExecutor(ModernLogger):
    """
    Code executor that communicates with backend Jupyter kernel via HTTP API.
    Completely replicates TypeScript NotebookApiService functionality.
    """

    def __init__(self):
        """Initialize the executor."""
        super().__init__("CodeExecutor")
        self.notebook_id: Optional[str] = None
        self.is_kernel_ready = False
        self.execution_count = 0

    def initialize_kernel(self) -> bool:
        """
        Initialize the Jupyter kernel.
        Replicates: NotebookApiService.initializeNotebook()

        Returns:
            True if successful
        """
        if self.is_kernel_ready and self.notebook_id:
            self.info(f"[CodeExecutor] Kernel already initialized: {self.notebook_id}")
            return True

        try:
            self.info("[CodeExecutor] Initializing kernel...")
            response = requests.post(
                f"{Config.BACKEND_BASE_URL}/initialize",
                json={},
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            result = response.json()

            if result.get('status') == 'ok':
                self.notebook_id = result.get('notebook_id')
                self.is_kernel_ready = True
                self.info(f"[CodeExecutor] Kernel initialized successfully: {self.notebook_id}")
                return True
            else:
                raise Exception(result.get('message', 'Kernel initialization failed'))

        except requests.RequestException as e:
            self.error(f"[CodeExecutor] Failed to initialize kernel: {e}")
            self.is_kernel_ready = False
            return False
        except Exception as e:
            self.error(f"[CodeExecutor] Unexpected error: {e}", exc_info=True)
            self.is_kernel_ready = False
            return False

    def restart_kernel(self) -> bool:
        """
        Restart the Jupyter kernel.
        Replicates: NotebookApiService.restartNotebook()

        Returns:
            True if successful
        """
        if not self.notebook_id:
            self.error("[CodeExecutor] Cannot restart: no notebook ID")
            return False

        try:
            self.info("[CodeExecutor] Restarting kernel...")
            response = requests.post(
                f"{Config.BACKEND_BASE_URL}/restart_kernel",
                json={'notebook_id': self.notebook_id},
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            result = response.json()

            if result.get('status') == 'ok':
                self.info("[CodeExecutor] Kernel restarted successfully")
                self.execution_count = 0
                return True
            else:
                raise Exception(result.get('message', 'Kernel restart failed'))

        except Exception as e:
            self.error(f"[CodeExecutor] Failed to restart kernel: {e}", exc_info=True)
            return False

    def execute(self, code: str, cell_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute Python code on the remote kernel.
        Replicates: NotebookApiService.executeCode() + codeStore.executeCell()

        Args:
            code: The Python code to execute
            cell_id: Optional cell ID for tracking

        Returns:
            Dict containing execution results
        """
        # Ensure kernel is initialized
        if not self.is_kernel_ready:
            if not self.initialize_kernel():
                return {
                    'success': False,
                    'error': 'Failed to initialize kernel',
                    'outputs': [],
                    'execution_count': 0
                }

        if not self.notebook_id:
            return {
                'success': False,
                'error': 'No notebook ID',
                'outputs': [],
                'execution_count': 0
            }

        try:
            self.info(f"[CodeExecutor] Executing code on remote kernel (cell: {cell_id})")

            # Start execution
            response = requests.post(
                f"{Config.BACKEND_BASE_URL}/execute",
                json={
                    'code': code,
                    'notebook_id': self.notebook_id
                },
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            result = response.json()

            if result.get('status') != 'ok':
                error_msg = result.get('message', 'Execution failed')
                self.error(f"[CodeExecutor] Execution error: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'outputs': [],
                    'execution_count': self.execution_count
                }

            # Poll for completion
            outputs = self._poll_execution_status()
            self.execution_count += 1

            return {
                'success': True,
                'outputs': outputs,
                'result': None,
                'execution_count': self.execution_count,
                'error': None
            }

        except requests.RequestException as e:
            self.error(f"[CodeExecutor] HTTP error: {e}")
            return {
                'success': False,
                'error': str(e),
                'outputs': [],
                'execution_count': self.execution_count
            }
        except Exception as e:
            self.error(f"[CodeExecutor] Unexpected error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'outputs': [],
                'execution_count': self.execution_count
            }

    def _poll_execution_status(self, timeout: int = 300) -> List[CellOutput]:
        """
        Poll the execution status until completion.
        Replicates: codeStore.startStatusCheck()

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            List of cell outputs
        """
        outputs = []
        start_time = time.time()
        interval = Config.STATUS_CHECK_INTERVAL  # Default 1 second

        while True:
            # Check timeout
            if time.time() - start_time > timeout:
                self.error("[CodeExecutor] Execution timeout")
                break

            try:
                # Get status
                response = requests.get(
                    f"{Config.BACKEND_BASE_URL}/execution_status/{self.notebook_id}"
                )
                response.raise_for_status()
                status = response.json()

                # Check if execution is complete
                if not status.get('is_running', False):
                    # Execution complete
                    if status.get('data', {}).get('outputs'):
                        outputs = self._parse_outputs(status['data']['outputs'])
                    self.info(f"[CodeExecutor] Execution complete, {len(outputs)} outputs")
                    break

                # Update outputs if available
                if status.get('data', {}).get('outputs'):
                    outputs = self._parse_outputs(status['data']['outputs'])

                # Wait before next poll
                time.sleep(interval)

            except Exception as e:
                self.error(f"[CodeExecutor] Status check error: {e}")
                break

        return outputs

    def _parse_outputs(self, raw_outputs: List[Dict[str, Any]]) -> List[CellOutput]:
        """
        Parse raw outputs into CellOutput objects.
        Replicates frontend output parsing logic.

        Args:
            raw_outputs: Raw outputs from API

        Returns:
            List of CellOutput objects
        """
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

            # Handle execution results
            if 'execution_count' in output:
                cell_output.execution_count = output['execution_count']

            parsed.append(cell_output)

        return parsed

    def cancel_execution(self) -> bool:
        """
        Cancel current execution.
        Replicates: NotebookApiService.cancelExecution()

        Returns:
            True if successful
        """
        if not self.notebook_id:
            self.error("[CodeExecutor] Cannot cancel: no notebook ID")
            return False

        try:
            self.info("[CodeExecutor] Canceling execution...")
            response = requests.post(
                f"{Config.BACKEND_BASE_URL}/cancel_execution/{self.notebook_id}",
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            result = response.json()

            return result.get('status') == 'ok'

        except Exception as e:
            self.error(f"[CodeExecutor] Failed to cancel execution: {e}")
            return False

    def reset_namespace(self):
        """Reset the execution namespace by restarting kernel."""
        self.info("[CodeExecutor] Resetting namespace (restarting kernel)")
        self.restart_kernel()

    def get_variable(self, name: str) -> Any:
        """
        Get a variable from the namespace.
        Note: This requires additional backend API support.
        """
        self.warning("[CodeExecutor] get_variable not implemented for remote execution")
        return None

    def set_variable(self, name: str, value: Any):
        """
        Set a variable in the namespace.
        Note: This requires additional backend API support.
        """
        self.warning("[CodeExecutor] set_variable not implemented for remote execution")

    def get_all_variables(self) -> Dict[str, Any]:
        """
        Get all user-defined variables.
        Note: This requires additional backend API support.
        """
        self.warning("[CodeExecutor] get_all_variables not implemented for remote execution")
        return {}
