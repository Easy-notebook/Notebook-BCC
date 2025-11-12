"""
Argument parser for CLI commands.
"""

import argparse
from config import Config


class CLIArgumentParser:
    """
    Creates and manages command-line argument parser.
    """

    @staticmethod
    def create_parser() -> argparse.ArgumentParser:
        """Create argument parser."""
        parser = argparse.ArgumentParser(
            description='Notebook-BCC: Python Workflow System',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        # Global configuration options
        parser.add_argument('--backend-url', type=str, help='Backend Jupyter kernel URL (default: http://localhost:18600)')
        parser.add_argument('--dslc-url', type=str, help='DSLC workflow API URL (default: http://localhost:28600)')
        parser.add_argument('--notebook-id', type=str, default=Config.NOTEBOOK_ID,
                          help='Notebook ID (default: from .env NOTEBOOK_ID or None)')

        # Execution control options
        parser.add_argument('--max-steps', type=int, default=0, help='Maximum steps to execute (0 = unlimited)')
        parser.add_argument('--interactive', action='store_true', help='Enable interactive mode (pause at breakpoints)')

        # Custom context option
        parser.add_argument('--custom-context', type=str, help='Custom context JSON string or file path')

        subparsers = parser.add_subparsers(dest='command', help='Commands')

        # Start command
        start_parser = subparsers.add_parser('start', help='Start a new workflow')
        start_parser.add_argument('--problem', type=str, help='Problem description')
        start_parser.add_argument('--context', type=str, help='Additional context for workflow initialization')
        start_parser.add_argument('--config', type=str, help='Path to config JSON file (e.g., housing_config.json)')
        start_parser.add_argument('--state-file', type=str, help='Path to initial state JSON file (e.g., 00_STATE_IDLE.json)')
        start_parser.add_argument('--idle-template', type=str, help='Path to IDLE state template JSON file')
        start_parser.add_argument('--iterate', action='store_true', help='Enable automatic iteration (loop through states)')
        start_parser.add_argument('--max-iterations', type=int, default=10, help='Maximum iterations in loop mode (default: 10)')

        # Status command
        subparsers.add_parser('status', help='Show workflow status')

        # Show command
        show_parser = subparsers.add_parser('show', help='Show notebook')
        show_parser.add_argument('--notebook', type=str, help='Notebook filename')

        # List command
        subparsers.add_parser('list', help='List notebooks')

        # Export command
        export_parser = subparsers.add_parser('export', help='Export notebook to markdown')
        export_parser.add_argument('notebook', type=str, help='Notebook filename')
        export_parser.add_argument('--output', type=str, help='Output filename')

        # REPL command
        subparsers.add_parser('repl', help='Start interactive REPL')

        # Send-API command
        send_api_parser = subparsers.add_parser('send-api', help='Send API request from state file')
        send_api_parser.add_argument('--state-file', type=str, required=True, help='Path to state JSON file')
        send_api_parser.add_argument('--api-type', type=str, required=False,
                                     choices=['planning', 'generating', 'reflecting'],
                                     help='API type to call (auto-inferred from FSM state if not specified)')
        send_api_parser.add_argument('--output', type=str, help='Output file for response (optional)')
        send_api_parser.add_argument('--stream', action='store_true', help='Use streaming for generating API')

        # Resume command
        resume_parser = subparsers.add_parser('resume', help='Resume workflow from state file')
        resume_parser.add_argument('--state-file', type=str, required=True, help='Path to state JSON file')
        resume_parser.add_argument('--continue', dest='continue_execution', action='store_true',
                                  help='Continue execution after loading state')

        # Test-request command
        test_req_parser = subparsers.add_parser('test-request', help='Preview API request without sending')
        test_req_parser.add_argument('--state-file', type=str, required=True, help='Path to state JSON file')
        test_req_parser.add_argument('--api-type', type=str, required=False,
                                     choices=['planning', 'generating', 'reflecting'],
                                     help='API type to preview (auto-inferred from FSM state if not specified)')
        test_req_parser.add_argument('--output', type=str, help='Export request payload to file')
        test_req_parser.add_argument('--format', type=str, choices=['json', 'pretty'], default='pretty',
                                     help='Output format (json or pretty)')

        # Apply-transition command
        apply_trans_parser = subparsers.add_parser('apply-transition',
                                                   help='Apply transition to state and export updated state')
        apply_trans_parser.add_argument('--state-file', type=str, required=True,
                                       help='Path to input state JSON file')
        apply_trans_parser.add_argument('--transition-file', type=str, required=True,
                                       help='Path to transition XML file')
        apply_trans_parser.add_argument('--output', type=str, required=True,
                                       help='Output file for updated state JSON')
        apply_trans_parser.add_argument('--format', type=str, choices=['json', 'pretty'], default='pretty',
                                       help='Output format (json or pretty)')

        # Test-actions command
        test_actions_parser = subparsers.add_parser('test-actions',
                                                    help='Execute actions from JSON file with rich streaming display')
        test_actions_parser.add_argument('--actions-file', type=str, required=True,
                                        help='Path to actions JSON file')
        test_actions_parser.add_argument('--state-file', type=str, required=True,
                                        help='Path to input state JSON file')
        test_actions_parser.add_argument('--output', type=str, required=True,
                                        help='Output file for updated state JSON')
        test_actions_parser.add_argument('--no-display', action='store_true',
                                        help='Disable rich display (faster execution)')
        test_actions_parser.add_argument('--delay', type=float, default=0.3,
                                        help='Delay between actions in seconds (default: 0.3)')

        # Export-markdown command
        export_md_parser = subparsers.add_parser('export-markdown',
                                                help='Export notebook from state file to markdown')
        export_md_parser.add_argument('--state-file', type=str, required=True,
                                     help='Path to state JSON file')
        export_md_parser.add_argument('--output', type=str, required=False,
                                     help='Output markdown file path (default: stdout)')

        return parser
