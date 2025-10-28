"""
Configuration management for Notebook-BCC.
"""

import os
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, skip
    pass


class Config:
    """
    Configuration for the workflow system.
    Supports runtime configuration updates.
    """

    # ==============================================
    # API Endpoints
    # ==============================================

    # Backend base URL (from environment or default)
    BACKEND_BASE_URL = os.getenv('BACKEND_BASE_URL', 'http://localhost:18600')

    # DSLC (Data Science Lifecycle) base URL
    DSLC_BASE_URL = os.getenv('DSLC_BASE_URL', 'http://localhost:28600')

    # Initial notebook ID (can be overridden)
    NOTEBOOK_ID = os.getenv('NOTEBOOK_ID', None)

    @classmethod
    def set_backend_url(cls, url: str):
        """Update backend URL at runtime."""
        cls.BACKEND_BASE_URL = url
        cls._rebuild_api_urls()

    @classmethod
    def set_dslc_url(cls, url: str):
        """Update DSLC URL at runtime."""
        cls.DSLC_BASE_URL = url
        cls._rebuild_api_urls()

    @classmethod
    def set_notebook_id(cls, notebook_id: str):
        """Set notebook ID at runtime."""
        cls.NOTEBOOK_ID = notebook_id

    @classmethod
    def _rebuild_api_urls(cls):
        """Rebuild API URLs after base URL changes."""
        # Workflow API endpoints
        cls.FEEDBACK_API_URL = f"{cls.DSLC_BASE_URL}/planning"
        cls.BEHAVIOR_API_URL = f"{cls.DSLC_BASE_URL}/generating"
        cls.GENERATE_API_URL = f"{cls.DSLC_BASE_URL}/generate"

        # Code execution API endpoints
        cls.NOTEBOOK_INITIALIZE_URL = f"{cls.BACKEND_BASE_URL}/initialize"
        cls.NOTEBOOK_EXECUTE_URL = f"{cls.BACKEND_BASE_URL}/execute"
        cls.NOTEBOOK_STATUS_URL = f"{cls.BACKEND_BASE_URL}/get_status"
        cls.NOTEBOOK_CANCEL_URL = f"{cls.BACKEND_BASE_URL}/cancel"
        cls.NOTEBOOK_RESTART_URL = f"{cls.BACKEND_BASE_URL}/restart_kernel"

    # Workflow API endpoints
    FEEDBACK_API_URL = f"{DSLC_BASE_URL}/planning"
    BEHAVIOR_API_URL = f"{DSLC_BASE_URL}/generating"
    GENERATE_API_URL = f"{DSLC_BASE_URL}/generate"

    # Code execution API endpoints
    NOTEBOOK_INITIALIZE_URL = f"{BACKEND_BASE_URL}/initialize"
    NOTEBOOK_EXECUTE_URL = f"{BACKEND_BASE_URL}/execute"
    NOTEBOOK_STATUS_URL = f"{BACKEND_BASE_URL}/get_status"
    NOTEBOOK_CANCEL_URL = f"{BACKEND_BASE_URL}/cancel"
    NOTEBOOK_RESTART_URL = f"{BACKEND_BASE_URL}/restart_kernel"

    # ==============================================
    # Context Compression Settings
    # ==============================================

    MAX_CONTEXT_LENGTH = 18600  # Maximum context length for API calls
    MAX_HISTORY_ITEMS = 50     # Maximum history items to keep

    # ==============================================
    # Execution Settings
    # ==============================================

    # Code execution polling interval (seconds)
    STATUS_CHECK_INTERVAL = 1.0

    # Execution timeout (seconds)
    EXECUTION_TIMEOUT = 300

    # ==============================================
    # Storage Settings
    # ==============================================

    # Notebooks directory
    NOTEBOOKS_DIR = Path('notebooks')

    # Logs directory
    LOGS_DIR = Path('logs')

    # ==============================================
    # Logging Settings
    # ==============================================

    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # ==============================================
    # Workflow Control Settings
    # ==============================================

    # Maximum steps to execute (0 = unlimited)
    MAX_EXECUTION_STEPS = int(os.getenv('MAX_EXECUTION_STEPS', '0'))

    # Enable interactive mode (pause at breakpoints)
    INTERACTIVE_MODE = os.getenv('INTERACTIVE_MODE', 'false').lower() == 'true'

    # ==============================================
    # Feature Flags
    # ==============================================

    # Use remote code execution (True) or local execution (False)
    USE_REMOTE_EXECUTION = os.getenv('USE_REMOTE_EXECUTION', 'true').lower() == 'true'

    # Enable API call compression
    ENABLE_CONTEXT_COMPRESSION = True

    # Enable streaming for behavior API
    ENABLE_STREAMING = True

    @classmethod
    def ensure_directories(cls):
        """Ensure required directories exist."""
        cls.NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_api_config(cls):
        """Get API configuration as a dictionary."""
        return {
            'backend_base_url': cls.BACKEND_BASE_URL,
            'dslc_base_url': cls.DSLC_BASE_URL,
            'feedback_api_url': cls.FEEDBACK_API_URL,
            'behavior_api_url': cls.BEHAVIOR_API_URL,
            'generate_api_url': cls.GENERATE_API_URL,
        }

    @classmethod
    def get_execution_config(cls):
        """Get code execution configuration."""
        return {
            'initialize_url': cls.NOTEBOOK_INITIALIZE_URL,
            'execute_url': cls.NOTEBOOK_EXECUTE_URL,
            'status_url': cls.NOTEBOOK_STATUS_URL,
            'cancel_url': cls.NOTEBOOK_CANCEL_URL,
            'restart_url': cls.NOTEBOOK_RESTART_URL,
            'use_remote': cls.USE_REMOTE_EXECUTION,
            'timeout': cls.EXECUTION_TIMEOUT,
        }


# Initialize on import
Config.ensure_directories()
