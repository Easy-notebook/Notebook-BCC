"""
异步状态机适配器
提供事件驱动的异步执行能力
"""

from typing import Dict, Any, Optional, Callable, Awaitable
from silantui import ModernLogger
from .state_machine import WorkflowStateMachine
from .events import WorkflowEvent
from .states import WorkflowState


class AsyncStateMachineAdapter(ModernLogger):
    """
    异步状态机适配器

    包装 WorkflowStateMachine，提供异步执行能力：
    - 异步 state effects
    - API 调用集成
    - 事件驱动的执行流程
    """

    def __init__(
        self,
        state_machine: WorkflowStateMachine,
        api_client=None,
        script_store=None
    ):
        """
        初始化异步适配器

        Args:
            state_machine: 被包装的状态机
            api_client: WorkflowAPIClient 实例
            script_store: ScriptStore 实例（用于执行 actions）
        """
        super().__init__("AsyncStateMachine")
        self.state_machine = state_machine
        self.api_client = api_client
        self.script_store = script_store

        # 当前状态 JSON（用于 API 调用）
        self.current_state_json: Optional[Dict[str, Any]] = None

        # 记录最后执行的 transition 名称
        self._last_transition_name: Optional[str] = None

        # 异步 state effects（只保留需要特殊逻辑的）
        self._async_state_effects: Dict[WorkflowState, Callable[..., Awaitable]] = {}

        # Inject API client into StateFactory for all states
        if api_client:
            from .state_classes.state_factory import StateFactory
            StateFactory.set_api_client(api_client)
            self.info("API client injected into StateFactory")

        # 注册需要特殊逻辑的 state effects
        self._register_default_effects()

    def _register_default_effects(self):
        """注册需要特殊逻辑的 state effects"""
        # 只注册需要复杂逻辑的状态
        # BEHAVIOR_COMPLETED → 调用 reflecting API，处理 actions
        self._async_state_effects[WorkflowState.BEHAVIOR_COMPLETED] = self._effect_behavior_completed

        # STEP_COMPLETED → 不需要 API 调用（auto-trigger）
        self._async_state_effects[WorkflowState.STEP_COMPLETED] = self._effect_step_completed

        # STAGE_COMPLETED → 调用 reflecting API，处理 actions
        self._async_state_effects[WorkflowState.STAGE_COMPLETED] = self._effect_stage_completed

    async def step(self, state_json: Dict[str, Any]) -> tuple[Dict[str, Any], Optional[str]]:
        """
        执行一步状态转换

        Args:
            state_json: 当前状态 JSON

        Returns:
            Tuple of (新的状态 JSON, transition 名称)
        """
        self.current_state_json = state_json

        # Reset transition name
        self._last_transition_name = None

        # 推断当前 FSM 状态
        fsm_state_str = state_json.get('state', {}).get('FSM', {}).get('state', 'UNKNOWN')

        # 转换为 WorkflowState 枚举
        # 需要处理：
        # 1. 大小写不匹配：JSON 中是大写，枚举值是小写
        # 2. 命名变体：BEHAVIOR_COMPLETED vs BEHAVIOR_COMPLETED

        # 先规范化命名（处理 COMPLETE vs COMPLETED 变体）
        normalized_state = fsm_state_str.upper()
        if normalized_state.endswith('_COMPLETE') and not normalized_state.endswith('_COMPLETED'):
            # BEHAVIOR_COMPLETED → BEHAVIOR_COMPLETED
            # STEP_COMPLETED → STEP_COMPLETED
            # STAGE_COMPLETED → STAGE_COMPLETED
            # WORKFLOW_COMPLETE → WORKFLOW_COMPLETED
            normalized_state = normalized_state + 'D'

        try:
            # 首先尝试直接匹配（小写）
            current_state = WorkflowState(normalized_state.lower())
        except ValueError:
            # 如果失败，尝试使用 WORKFLOW_STATES 字典匹配（大写）
            from .states import WORKFLOW_STATES
            if normalized_state in WORKFLOW_STATES:
                current_state = WORKFLOW_STATES[normalized_state]
            else:
                self.error(f"Unknown FSM state: {fsm_state_str} (normalized: {normalized_state})")
                return state_json, None

        # 检查是否有自定义 effect（需要特殊逻辑的状态）
        effect = self._async_state_effects.get(current_state)
        if effect:
            try:
                self.info(f"[AsyncFSM] Executing custom effect for state: {current_state.value}")
                new_state_json = await effect(state_json)
                return new_state_json, self._last_transition_name
            except Exception as e:
                self.error(f"[AsyncFSM] Effect error for {current_state}: {e}", exc_info=True)
                # 触发 FAIL 事件
                self.state_machine.transition(WorkflowEvent.FAIL, {'error': str(e)})
                return state_json, None

        # 检查 state 是否需要 API 调用（由 state 自己定义）
        from .state_classes.state_factory import StateFactory
        state_instance = StateFactory.get_state(normalized_state)

        if state_instance:
            api_type_enum = state_instance.get_required_api_type()

            if api_type_enum and api_type_enum.value != 'finish':
                try:
                    self.info(f"[AsyncFSM] Calling {api_type_enum.value} API for state: {current_state.value}")
                    new_state_json, transition_name = await self._call_state_api_and_apply_transition(
                        state_json=state_json,
                        state_name=normalized_state,
                        transition_type=api_type_enum.value
                    )
                    self._last_transition_name = transition_name
                    return new_state_json, transition_name
                except Exception as e:
                    self.error(f"[AsyncFSM] API call error for {current_state}: {e}", exc_info=True)
                    return state_json, None
            else:
                # State 不需要 API 调用（如 terminal states）
                self.info(f"[AsyncFSM] State {current_state.value} does not require API call")
                return state_json, None

        # 无法获取 state instance
        self.warning(f"[AsyncFSM] Failed to get state instance for: {current_state}")
        return state_json, None

    # ==============================================
    # State Effects Implementation (只保留需要特殊逻辑的)
    # ==============================================

    async def _effect_behavior_completed(self, state_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        BEHAVIOR_COMPLETED 状态的 effect
        调用 reflecting API (now returns action stream)，决定下一步

        Reflection now returns actions including:
        - add-text: markdown content (from <add-comment>)
        - mark_step_complete: triggers COMPLETE_STEP transition
        - complete_reflection: end of reflection
        """
        if not self.api_client or not self.script_store:
            self.error("[AsyncFSM] No API client or script_store configured")
            return state_json

        self.info("[AsyncFSM] BEHAVIOR_COMPLETED → calling reflecting API (action stream)")

        # Get state instance
        from .state_classes.state_factory import StateFactory
        state_instance = StateFactory.get_state('BEHAVIOR_COMPLETED')

        if not state_instance:
            self.error("[AsyncFSM] Failed to get BEHAVIOR_COMPLETED state instance")
            return state_json

        # Ensure API client is injected
        if not state_instance._api_client:
            state_instance.set_api_client(self.api_client)

        try:
            # Call reflecting API (returns async iterator of actions)
            action_stream = await state_instance.call_api(state_json, transition_name=None)

            # Collect actions from async iterator
            actions = []
            mark_step_complete_received = False

            async for action in action_stream:
                action_type = action.get('type', 'unknown')
                self.debug(f"[AsyncFSM] Reflection action: {action_type}")
                actions.append(action)

                # Check for mark_step_complete action
                if action_type == 'mark_step_complete':
                    mark_step_complete_received = True

                # Execute markdown actions (add-text)
                if action_type in ['add', 'add-text'] and action.get('shot_type') == 'markdown':
                    # Execute action to update stores
                    step = self._convert_action_to_step(action)
                    self.script_store.exec_action(step)

            self.info(f"[AsyncFSM] Received {len(actions)} reflection actions")

            # Build new state from stores
            new_state_json = self._build_state_from_stores(state_json)

            # Determine transition based on mark_step_complete action
            if mark_step_complete_received:
                # Trigger COMPLETE_STEP transition
                self.info("[AsyncFSM] mark_step_complete received → triggering COMPLETE_STEP")
                from utils.state_updater import state_updater
                if self.script_store:
                    state_updater.set_script_store(self.script_store)

                # Create a mock response for COMPLETE_STEP handler
                complete_step_response = {
                    'current_step_is_complete': True,
                    'next_state': 'STEP_COMPLETED',
                    'variables_produced': {},
                    'artifacts_produced': [],
                    'outputs_tracking': {
                        'produced': [],
                        'in_progress': [],
                        'remaining': []
                    }
                }

                import json
                new_state, transition_name = state_updater.apply_transition(
                    state=new_state_json,
                    transition_response=json.dumps(complete_step_response),
                    transition_type='reflecting'
                )
                self._last_transition_name = transition_name
                return new_state
            else:
                # No mark_step_complete → NEXT_BEHAVIOR
                self.info("[AsyncFSM] No mark_step_complete → triggering NEXT_BEHAVIOR")
                from utils.state_updater import state_updater
                if self.script_store:
                    state_updater.set_script_store(self.script_store)

                # Create a mock response for NEXT_BEHAVIOR handler
                next_behavior_response = {
                    'current_step_is_complete': False,
                    'next_state': 'BEHAVIOR_RUNNING',
                    'variables_produced': {},
                    'artifacts_produced': []
                }

                import json
                new_state, transition_name = state_updater.apply_transition(
                    state=new_state_json,
                    transition_response=json.dumps(next_behavior_response),
                    transition_type='reflecting'
                )
                self._last_transition_name = transition_name
                return new_state

        except Exception as e:
            self.error(f"[AsyncFSM] Error calling reflecting API for BEHAVIOR_COMPLETED: {e}", exc_info=True)
            return state_json

    async def _effect_step_completed(self, state_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        STEP_COMPLETED 状态的 effect

        STEP_COMPLETED is an intermediate state that auto-triggers NEXT_STEP or COMPLETE_STAGE.
        No API call needed here - the TransitionCoordinator's auto-trigger mechanism
        will handle the transition automatically.
        """
        self.info("[AsyncFSM] STEP_COMPLETED → auto-trigger will handle next transition")

        # Simply return the state - auto-trigger mechanism in TransitionCoordinator
        # will automatically call NEXT_STEP or COMPLETE_STAGE based on remaining steps
        return state_json

    async def _effect_stage_completed(self, state_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        STAGE_COMPLETED 状态的 effect
        调用 reflecting API (now returns action stream)，决定下一步

        First tries to transition current step to completed and remaining[0] to current.
        If remaining is empty, calls reflecting API.

        Reflection returns actions including:
        - add-text: markdown content (from <add-comment>)
        - mark_stage_complete: triggers COMPLETE_STAGE transition
        - complete_reflection: end of reflection
        """
        # First, try to advance to next step
        progress = state_json.get('observation', {}).get('location', {}).get('progress', {})
        steps_progress = progress.get('steps', {})
        remaining_steps = steps_progress.get('remaining', [])

        if remaining_steps:
            # There are remaining steps, trigger NEXT_STEP
            self.info("[AsyncFSM] STEP_COMPLETED → remaining steps exist → triggering NEXT_STEP")
            from utils.state_updater import state_updater
            if self.script_store:
                state_updater.set_script_store(self.script_store)

            # Create auto-trigger response for NEXT_STEP
            next_step_response = {
                '_auto_trigger': 'NEXT_STEP',
                'transition': 'NEXT_STEP'
            }

            import json
            new_state, transition_name = state_updater.apply_transition(
                state=state_json,
                transition_response=json.dumps(next_step_response),
                transition_type='reflecting'
            )
            self._last_transition_name = transition_name
            return new_state

        # No remaining steps, call reflecting API
        if not self.api_client or not self.script_store:
            self.error("[AsyncFSM] No API client or script_store configured")
            return state_json

        self.info("[AsyncFSM] STAGE_COMPLETED → no remaining steps → calling reflecting API (action stream)")

        # Get state instance
        from .state_classes.state_factory import StateFactory
        state_instance = StateFactory.get_state('STAGE_COMPLETED')

        if not state_instance:
            self.error("[AsyncFSM] Failed to get STAGE_COMPLETED state instance")
            return state_json

        # Ensure API client is injected
        if not state_instance._api_client:
            state_instance.set_api_client(self.api_client)

        try:
            # Call reflecting API (returns action stream)
            # call_api returns AsyncIterator, don't await it
            action_stream = state_instance.call_api(state_json, transition_name=None)

            # Collect actions from async iterator
            actions = []
            mark_stage_complete_received = False

            async for action in action_stream:
                action_type = action.get('type', 'unknown')
                self.debug(f"[AsyncFSM] Reflection action: {action_type}")
                actions.append(action)

                # Check for mark_stage_complete action
                if action_type == 'mark_stage_complete':
                    mark_stage_complete_received = True

                # Execute markdown actions (add-text)
                if action_type in ['add', 'add-text'] and action.get('shot_type') == 'markdown':
                    # Execute action to update stores
                    step = self._convert_action_to_step(action)
                    self.script_store.exec_action(step)

            self.info(f"[AsyncFSM] Received {len(actions)} reflection actions")

            # Build new state from stores
            new_state_json = self._build_state_from_stores(state_json)

            # Determine transition based on mark_stage_complete action
            if mark_stage_complete_received:
                # Trigger COMPLETE_STAGE transition
                self.info("[AsyncFSM] mark_stage_complete received → triggering COMPLETE_STAGE")
                from utils.state_updater import state_updater
                if self.script_store:
                    state_updater.set_script_store(self.script_store)

                # Create a mock response for COMPLETE_STAGE handler
                complete_stage_response = {
                    'next_state': 'STAGE_COMPLETED',
                    'stage_completed': True
                }

                import json
                new_state, transition_name = state_updater.apply_transition(
                    state=new_state_json,
                    transition_response=json.dumps(complete_stage_response),
                    transition_type='reflecting'
                )
                self._last_transition_name = transition_name
                return new_state
            else:
                # No mark_stage_complete received - this shouldn't happen
                self.warning("[AsyncFSM] No mark_stage_complete received in STAGE_COMPLETED state")
                return new_state_json

        except Exception as e:
            self.error(f"[AsyncFSM] Error calling reflecting API for STAGE_COMPLETED: {e}", exc_info=True)
            return state_json

    # ==============================================
    # Helper Methods
    # ==============================================

    async def _call_state_api_and_apply_transition(
        self,
        state_json: Dict[str, Any],
        state_name: str,
        transition_type: str
    ) -> tuple[Dict[str, Any], str]:
        """
        通用方法：调用 state 的 API 并应用 transition

        Args:
            state_json: 当前状态 JSON
            state_name: 状态名称
            transition_type: transition 类型 ('planning', 'generating', 'reflecting')

        Returns:
            Tuple of (更新后的状态 JSON, 实际使用的 transition 名称)
        """
        if not self.api_client:
            self.error("[AsyncFSM] No API client configured")
            return state_json, None

        self.info(f"[AsyncFSM] {state_name} → calling {transition_type} API")

        # Get state instance
        from .state_classes.state_factory import StateFactory
        state_instance = StateFactory.get_state(state_name)

        if not state_instance:
            self.error(f"[AsyncFSM] Failed to get state instance for {state_name}")
            return state_json, None

        # Ensure API client is injected (in case state was created before set_api_client was called)
        if not state_instance._api_client:
            state_instance.set_api_client(self.api_client)
            self.debug(f"[AsyncFSM] API client injected into {state_name} state instance")

        try:
            # Call state's API method (transition_name will be determined by TransitionCoordinator)
            response = await state_instance.call_api(state_json, transition_name=None)

            # For generating API, collect actions from async iterator
            if transition_type == 'generating':
                actions = []
                async for action in response:
                    actions.append(action)

                self.info(f"[AsyncFSM] Received {len(actions)} actions, executing...")

                # Execute all actions (update stores)
                for action in actions:
                    step = self._convert_action_to_step(action)
                    self.script_store.exec_action(step)

                # Build new state from stores
                new_state_json = self._build_state_from_stores(state_json)

                # Apply transition (update FSM to BEHAVIOR_COMPLETED)
                from utils.state_updater import state_updater
                if self.script_store:
                    state_updater.set_script_store(self.script_store)
                import json
                response = {'actions': actions, 'count': len(actions)}
                new_state, actual_transition_name = state_updater.apply_transition(
                    state=new_state_json,
                    transition_response=json.dumps(response),
                    transition_type='generating'
                )

                # 更新 API 日志文件名为实际的 transition 名称
                if actual_transition_name and self.api_client and hasattr(self.api_client, 'api_logger'):
                    self.api_client.api_logger.update_last_log_transition_name(actual_transition_name)

                return new_state, actual_transition_name
            else:
                # For planning and reflecting APIs, apply transition directly
                from utils.state_updater import state_updater
                if self.script_store:
                    state_updater.set_script_store(self.script_store)
                new_state, actual_transition_name = state_updater.apply_transition(
                    state=state_json,
                    transition_response=response,
                    transition_type=transition_type
                )

                # 更新 API 日志文件名为实际的 transition 名称
                if actual_transition_name and self.api_client and hasattr(self.api_client, 'api_logger'):
                    self.api_client.api_logger.update_last_log_transition_name(actual_transition_name)

                return new_state, actual_transition_name

        except Exception as e:
            self.error(f"[AsyncFSM] Error calling API for {state_name}: {e}", exc_info=True)
            return state_json, None

    def _convert_action_to_step(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换 action 格式为 script_store 需要的格式

        Args:
            action: API 返回的 action

        Returns:
            script_store 可执行的 step

        Note: API 返回的 action 已经是正确的格式，直接返回即可
        """
        # API 返回的 action 格式应该已经包含所需的所有字段：
        # - action: action 类型
        # - data: action 数据（如 content, language 等）
        # - cell_id/cellId: cell ID
        # - metadata: 元数据
        return action

    def _build_state_from_stores(self, base_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        从 stores 构建新状态

        Args:
            base_state: 基础状态 JSON

        Returns:
            更新后的状态 JSON（包含 notebook 和 effects）
        """
        import copy
        new_state = copy.deepcopy(base_state)

        # 更新 notebook（从 notebook_store）
        if hasattr(self.script_store, 'notebook_store'):
            new_state['state']['notebook'] = self.script_store.notebook_store.to_dict()

        # 更新 effects（从 ai_context_store）
        if hasattr(self.script_store, 'ai_context_store'):
            context = self.script_store.ai_context_store.get_context()
            new_state['state']['effects'] = context.effect  # 注意：是 effect 而不是 effects

        return new_state

    # ==============================================
    # Public API
    # ==============================================

    def register_effect(self, state: WorkflowState, effect: Callable[..., Awaitable]):
        """
        注册自定义 state effect

        Args:
            state: 状态
            effect: 异步 effect 函数
        """
        self._async_state_effects[state] = effect
        self.info(f"[AsyncFSM] Registered effect for state: {state.value}")
