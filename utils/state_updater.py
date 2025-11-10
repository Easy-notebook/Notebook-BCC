"""
State Updater
Apply transition (API response) to state and generate updated state.
"""

import json
from typing import Dict, Any, List
from copy import deepcopy
from silantui import ModernLogger
from .response_parser import ResponseParser


class StateUpdater(ModernLogger):
    """
    Apply transition responses to workflow states.
    Generates updated state based on API responses (stages, steps, behaviors).
    """

    def __init__(self):
        """Initialize the state updater."""
        super().__init__("StateUpdater")
        self.parser = ResponseParser()

    def apply_transition(
        self,
        state: Dict[str, Any],
        transition_response: str,
        transition_type: str = 'auto'
    ) -> Dict[str, Any]:
        """
        Apply transition response to state.

        Args:
            state: Current state (loaded from state JSON)
            transition_response: Transition response (XML or JSON string)
            transition_type: Type of transition ('stages', 'steps', 'auto')

        Returns:
            Updated state
        """
        # Parse the transition response
        parsed = self.parser.parse_response(transition_response)

        self.info(f"[StateUpdater] Parsed transition type: {parsed['type']}")

        # Apply based on type
        if parsed['type'] == 'stages':
            return self._apply_stages_transition(state, parsed['content'])
        elif parsed['type'] == 'steps':
            return self._apply_steps_transition(state, parsed['content'])
        elif parsed['type'] == 'behavior':
            return self._apply_behavior_transition(state, parsed['content'])
        elif parsed['type'] == 'reflection':
            return self._apply_reflection_transition(state, parsed['content'])
        elif parsed['type'] == 'json':
            # Standard JSON response (from planning/reflecting API)
            return self._apply_json_transition(state, parsed['content'])
        else:
            self.warning(f"[StateUpdater] Unknown transition type: {parsed['type']}")
            return state

    def _apply_stages_transition(
        self,
        state: Dict[str, Any],
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply stages transition (START_WORKFLOW).

        Updates:
        - location.progress.stages with new stages list
        - location.current with first stage
        - FSM state to STAGE_RUNNING
        """
        new_state = deepcopy(state)

        stages_data = content.get('stages', [])
        focus = content.get('focus', '')

        self.info(f"[StateUpdater] Applying {len(stages_data)} stages")

        # Get observation structure
        observation = new_state.get('observation', {})
        location = observation.get('location', {})
        progress = location.get('progress', {})
        stages_progress = progress.get('stages', {})

        # Build stages list
        if len(stages_data) > 0:
            first_stage = stages_data[0]
            current_stage = {
                'stage_id': first_stage.get('stage_id'),
                'title': first_stage.get('title', ''),
                'goal': first_stage.get('goal', ''),
                'verified_artifacts': first_stage.get('verified_artifacts', {})
            }

            # Update current stage
            stages_progress['current'] = current_stage
            stages_progress['completed'] = []

            # Build remaining stages
            remaining_stages = []
            for stage_data in stages_data[1:]:
                remaining_stage = {
                    'stage_id': stage_data.get('stage_id'),
                    'title': stage_data.get('title', ''),
                    'goal': stage_data.get('goal', ''),
                    'verified_artifacts': stage_data.get('verified_artifacts', {})
                }
                # Add required_variables if present
                if 'required_variables' in stage_data:
                    remaining_stage['required_variables'] = stage_data['required_variables']
                remaining_stages.append(remaining_stage)

            stages_progress['remaining'] = remaining_stages
            stages_progress['focus'] = focus

            # Initialize current_outputs for stages
            stages_progress['current_outputs'] = {
                'expected': list({'name': k, 'description': v} for k, v in first_stage.get('verified_artifacts', {}).items()),
                'produced': [],
                'in_progress': []
            }

            # Update location.current
            location['current']['stage_id'] = first_stage.get('stage_id')
            location['current']['step_id'] = None
            location['current']['behavior_id'] = None

            self.info(f"[StateUpdater] Set current stage: {first_stage.get('stage_id')}")

        # Update FSM state
        fsm = new_state.get('state', {}).get('FSM', {})
        fsm['state'] = 'STAGE_RUNNING'
        fsm['last_transition'] = 'START_WORKFLOW'

        return new_state

    def _apply_steps_transition(
        self,
        state: Dict[str, Any],
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply steps transition (START_STEP).

        Updates:
        - location.progress.steps with new steps list
        - location.current with first step
        - FSM state to STEP_RUNNING
        """
        new_state = deepcopy(state)

        steps_data = content.get('steps', [])
        focus = content.get('focus', '')
        goals = content.get('goals', '')

        self.info(f"[StateUpdater] Applying {len(steps_data)} steps")

        # Get observation structure
        observation = new_state.get('observation', {})
        location = observation.get('location', {})
        progress = location.get('progress', {})
        steps_progress = progress.get('steps', {})

        # Build steps list
        if len(steps_data) > 0:
            first_step = steps_data[0]
            current_step = {
                'step_id': first_step.get('step_id'),
                'title': first_step.get('title', ''),
                'goal': first_step.get('goal', ''),
                'verified_artifacts': first_step.get('verified_artifacts', {}),
                'required_variables': first_step.get('required_variables', {}),
                'pcs_considerations': first_step.get('pcs_considerations', {})
            }

            # Update current step
            steps_progress['current'] = current_step
            steps_progress['completed'] = []

            # Build remaining steps
            remaining_steps = []
            for step_data in steps_data[1:]:
                remaining_step = {
                    'step_id': step_data.get('step_id'),
                    'title': step_data.get('title', ''),
                    'goal': step_data.get('goal', ''),
                    'verified_artifacts': step_data.get('verified_artifacts', {}),
                    'required_variables': step_data.get('required_variables', {}),
                    'pcs_considerations': step_data.get('pcs_considerations', {})
                }
                remaining_steps.append(remaining_step)

            steps_progress['remaining'] = remaining_steps
            steps_progress['focus'] = focus

            # Initialize current_outputs for steps
            steps_progress['current_outputs'] = {
                'expected': list({'name': k, 'description': v} for k, v in first_step.get('verified_artifacts', {}).items()),
                'produced': [],
                'in_progress': []
            }

            # Update location.current
            location['current']['step_id'] = first_step.get('step_id')
            location['current']['behavior_id'] = None

            # Update location.goals if goals provided
            if goals:
                location['goals'] = goals

            self.info(f"[StateUpdater] Set current step: {first_step.get('step_id')}")

        # Update FSM state
        fsm = new_state.get('state', {}).get('FSM', {})
        fsm['state'] = 'STEP_RUNNING'
        fsm['last_transition'] = 'START_STEP'

        return new_state

    def _apply_behavior_transition(
        self,
        state: Dict[str, Any],
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply behavior transition (START_BEHAVIOR).

        Updates:
        - location.progress.behaviors with new behavior
        - location.current with behavior_id and iteration
        - location.goals with behavior task description
        - FSM state to BEHAVIOR_RUNNING
        """
        new_state = deepcopy(state)

        # Content is the behavior data itself (not nested under 'behavior' key)
        behavior_id = content.get('behavior_id')
        step_id = content.get('step_id')
        agent = content.get('agent')
        task = content.get('task', '').strip()  # Clean up whitespace
        inputs = content.get('inputs', {})
        outputs = content.get('outputs', {})
        acceptance = content.get('acceptance', [])
        whathappened = content.get('whathappened', {})

        self.info(f"[StateUpdater] Applying behavior: {behavior_id}")

        # Get observation structure
        observation = new_state.get('observation', {})
        location = observation.get('location', {})
        progress = location.get('progress', {})
        behaviors_progress = progress.get('behaviors', {})

        # Build current behavior
        current_behavior = {
            'behavior_id': behavior_id,
            'step_id': step_id,
            'agent': agent,
            'task': task,
            'inputs': inputs,
            'outputs': outputs,
            'acceptance': acceptance
        }

        # Add whathappened if present
        if whathappened:
            current_behavior['whathappened'] = whathappened

        # Update current behavior
        behaviors_progress['current'] = current_behavior
        behaviors_progress['completed'] = []
        behaviors_progress['iteration'] = 1

        # Initialize current_outputs for behaviors
        expected_outputs = []
        for artifact_name, artifact_desc in outputs.items():
            expected_outputs.append({
                'name': artifact_name,
                'description': artifact_desc
            })

        behaviors_progress['current_outputs'] = {
            'expected': expected_outputs,
            'produced': [],
            'in_progress': []
        }

        # Update behaviors focus with task description
        behaviors_progress['focus'] = task

        # Update location.current
        location['current']['behavior_id'] = behavior_id
        location['current']['behavior_iteration'] = 1

        # Update location.goals with behavior task
        if task:
            location['goals'] = task

        self.info(f"[StateUpdater] Set current behavior: {behavior_id}, iteration: 1")

        # Update FSM state
        fsm = new_state.get('state', {}).get('FSM', {})
        fsm['state'] = 'BEHAVIOR_RUNNING'
        fsm['last_transition'] = 'START_BEHAVIOR'

        return new_state

    def _apply_reflection_transition(
        self,
        state: Dict[str, Any],
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply reflection transition (behavior completion reflection).

        Updates:
        - FSM state to next_state
        - Add new variables to state.variables
        - Update behaviors.completed list
        - Update outputs tracking (produced/in_progress/remaining)
        - Transition to next step if behavior_is_complete
        """
        new_state = deepcopy(state)

        behavior_is_complete = content.get('behavior_is_complete', False)
        next_state = content.get('next_state')
        variables_produced = content.get('variables_produced', {})
        artifacts_produced = content.get('artifacts_produced', [])
        outputs_tracking = content.get('outputs_tracking', {})

        self.info(f"[StateUpdater] Applying reflection: behavior_complete={behavior_is_complete}, next_state={next_state}")

        # Get structures
        observation = new_state.get('observation', {})
        location = observation.get('location', {})
        progress = location.get('progress', {})
        state_data = new_state.get('state', {})

        # Add new variables
        if variables_produced:
            current_vars = state_data.get('variables', {})
            current_vars.update(variables_produced)
            self.info(f"[StateUpdater] Added {len(variables_produced)} new variables")

        # Update FSM state
        fsm = state_data.get('FSM', {})
        old_state = fsm.get('state', 'UNKNOWN')

        if next_state:
            fsm['previous_state'] = old_state
            fsm['state'] = next_state
            self.info(f"[StateUpdater] FSM transition: {old_state} → {next_state}")

            # Determine transition name based on state change
            if 'Step' in next_state:
                fsm['last_transition'] = 'TRANSITION_TO_Step_Running'
            elif 'BEHAVIOR' in next_state:
                fsm['last_transition'] = 'TRANSITION_TO_Behavior_Running'
            elif 'STAGE' in next_state:
                fsm['last_transition'] = 'TRANSITION_TO_Stage_Running'
            else:
                fsm['last_transition'] = f'TRANSITION_TO_{next_state}'

        # Update behaviors if behavior is complete
        if behavior_is_complete:
            behaviors_progress = progress.get('behaviors', {})
            current_behavior = behaviors_progress.get('current')

            if current_behavior:
                # Move current behavior to completed
                if 'completed' not in behaviors_progress:
                    behaviors_progress['completed'] = []

                # Add completion info
                completed_behavior = deepcopy(current_behavior)
                completed_behavior['completion_status'] = 'success'
                completed_behavior['artifacts_produced'] = [a['name'] for a in artifacts_produced]

                behaviors_progress['completed'].append(completed_behavior)
                behaviors_progress['current'] = None
                self.info(f"[StateUpdater] Behavior completed: {current_behavior.get('behavior_id')}")

            # Update behavior outputs tracking
            behavior_outputs = behaviors_progress.get('current_outputs', {})
            if outputs_tracking.get('produced'):
                behavior_outputs['produced'] = outputs_tracking['produced']
            behavior_outputs['in_progress'] = outputs_tracking.get('in_progress', [])
            behavior_outputs['remaining'] = outputs_tracking.get('remaining', [])

        # If transitioning to Step_Running, update step progress
        if next_state == 'STATE_Step_Running':
            steps_progress = progress.get('steps', {})
            current_step = steps_progress.get('current')

            if current_step:
                # Mark current step as complete and move to next step
                if 'completed' not in steps_progress:
                    steps_progress['completed'] = []

                completed_step = deepcopy(current_step)
                completed_step['artifacts_produced'] = outputs_tracking.get('produced', [])
                completed_step['completion_status'] = 'all_acceptance_criteria_passed'

                steps_progress['completed'].append(completed_step)
                self.info(f"[StateUpdater] Step completed: {current_step.get('step_id')}")

                # Move to next step if available
                remaining_steps = steps_progress.get('remaining', [])
                if remaining_steps:
                    next_step = remaining_steps[0]
                    steps_progress['current'] = next_step
                    steps_progress['remaining'] = remaining_steps[1:]

                    # Update location
                    location['current']['step_id'] = next_step.get('step_id')
                    location['current']['behavior_id'] = None
                    location['goals'] = next_step.get('goal', '')

                    # Update step outputs
                    steps_progress['current_outputs'] = {
                        'expected': [{'name': k, 'description': v} for k, v in next_step.get('verified_artifacts', {}).items()],
                        'produced': [],
                        'in_progress': []
                    }

                    self.info(f"[StateUpdater] Advanced to next step: {next_step.get('step_id')}")

            # Update stage outputs tracking
            stages_progress = progress.get('stages', {})
            stage_outputs = stages_progress.get('current_outputs', {})
            if outputs_tracking.get('produced'):
                # Add to produced list (don't replace)
                if 'produced' not in stage_outputs:
                    stage_outputs['produced'] = []
                for artifact_name in outputs_tracking['produced']:
                    if not any(item.get('name') == artifact_name for item in stage_outputs['produced']):
                        # Find description from artifacts_produced
                        description = next((a.get('name') for a in artifacts_produced if a.get('name') == artifact_name), artifact_name)
                        stage_outputs['produced'].append({
                            'name': artifact_name,
                            'description': description
                        })

        return new_state

    def _apply_json_transition(
        self,
        state: Dict[str, Any],
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply JSON transition (planning/reflecting API response).

        Updates based on context_update in the response.
        """
        new_state = deepcopy(state)

        # Check for context_update
        if 'context_update' in content:
            context_update = content['context_update']

            # Update variables if present
            if 'variables' in context_update:
                new_vars = context_update['variables']
                current_vars = new_state.get('state', {}).get('variables', {})
                current_vars.update(new_vars)
                self.info(f"[StateUpdater] Updated {len(new_vars)} variables")

            # Update progress if present
            if 'progress_update' in context_update:
                # TODO: Implement progress update logic
                self.info("[StateUpdater] Progress update not implemented")

        # Update transition info if present
        if 'transition' in content:
            transition = content['transition']

            # Update FSM based on transition
            fsm = new_state.get('state', {}).get('FSM', {})

            if transition.get('target_achieved'):
                # Move to completed state
                current_state = fsm.get('state', 'UNKNOWN')
                if 'STEP' in current_state:
                    fsm['state'] = 'STEP_COMPLETED'
                elif 'BEHAVIOR' in current_state:
                    fsm['state'] = 'BEHAVIOR_COMPLETED'
                elif 'STAGE' in current_state:
                    fsm['state'] = 'STAGE_COMPLETED'

        return new_state


# Global singleton
state_updater = StateUpdater()
