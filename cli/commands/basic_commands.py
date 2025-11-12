"""
Basic commands - handles status and REPL.
"""


class BasicCommands:
    """
    Handles basic commands: status, repl.
    """

    def cmd_status(self, _args=None):
        """Show workflow status."""
        print("\nWorkflow Status")
        print("=" * 60)

        # State machine status
        state_info = self.state_machine.get_state_info()
        print(f"Current State: {state_info['current_state']}")
        print(f"Stage ID: {state_info['stage_id']}")
        print(f"Step ID: {state_info['step_id']}")
        print(f"Actions: {state_info['action_index'] + 1} / {state_info['total_actions']}")

        # Execution control status
        exec_status = self.state_machine.get_execution_status()
        print(f"\nExecution Control")
        print(f"Steps: {exec_status['current_step']}" + (f"/{exec_status['max_steps']}" if exec_status['max_steps'] > 0 else " (unlimited)"))
        print(f"Protocol: Planning First (always checks /planning API before execution)")
        print(f"Interactive: {'Yes' if exec_status['interactive'] else 'No'}")
        print(f"Paused: {'Yes' if exec_status['paused'] else 'No'}")

        print("\nNotebook Status")
        print(f"Title: {self.notebook_store.title}")
        print(f"Cells: {self.notebook_store.get_cell_count()}")

        print("\nAI Context")
        context = self.ai_context_store.get_context()
        print(f"Variables: {len(context.variables)}")
        print(f"TODO List: {len(context.to_do_list)}")
        print(f"Effects: {len(context.effect['current'])}")
        print(f"Custom Context: {len(context.custom_context)} keys" if context.custom_context else "Custom Context: None")

        if context.to_do_list:
            print("\nPending TODOs:")
            for todo in context.to_do_list:
                print(f"  - {todo}")

        print()

    def cmd_repl(self, _args=None):
        """Start interactive REPL."""
        from cli.repl import WorkflowREPL
        repl = WorkflowREPL(self)
        repl.run()
