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

        # 异步 state effects
        self._async_state_effects: Dict[WorkflowState, Callable[..., Awaitable]] = {}

        # Inject API client into StateFactory for all states
        if api_client:
            from .state_classes.state_factory import StateFactory
            StateFactory.set_api_client(api_client)
            self.info("API client injected into StateFactory")

        # 注册默认的 state effects
        self._register_default_effects()

    def _register_default_effects(self):
        """注册默认的 state effects"""
        # IDLE → 调用 planning API (START_WORKFLOW)
        self._async_state_effects[WorkflowState.IDLE] = self._effect_idle

        # STAGE_RUNNING → 调用 planning API (START_STEP)
        self._async_state_effects[WorkflowState.STAGE_RUNNING] = self._effect_stage_running

        # STEP_RUNNING → 调用 planning API (START_BEHAVIOR)
        self._async_state_effects[WorkflowState.STEP_RUNNING] = self._effect_step_running

        # BEHAVIOR_RUNNING → 调用 generating API
        self._async_state_effects[WorkflowState.BEHAVIOR_RUNNING] = self._effect_behavior_running

        # BEHAVIOR_COMPLETED → 调用 reflecting API
        self._async_state_effects[WorkflowState.BEHAVIOR_COMPLETED] = self._effect_behavior_completed

        # STEP_COMPLETED → 调用 reflecting API
        self._async_state_effects[WorkflowState.STEP_COMPLETED] = self._effect_step_completed

        # STAGE_COMPLETED → 调用 reflecting API
        self._async_state_effects[WorkflowState.STAGE_COMPLETED] = self._effect_stage_completed

    async def step(self, state_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行一步状态转换

        Args:
            state_json: 当前状态 JSON

        Returns:
            新的状态 JSON
        """
        self.current_state_json = state_json

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
                return state_json

        # 执行 state effect（异步）
        effect = self._async_state_effects.get(current_state)
        if effect:
            try:
                self.info(f"[AsyncFSM] Executing effect for state: {current_state.value}")
                new_state_json = await effect(state_json)
                return new_state_json
            except Exception as e:
                self.error(f"[AsyncFSM] Effect error for {current_state}: {e}", exc_info=True)
                # 触发 FAIL 事件
                self.state_machine.transition(WorkflowEvent.FAIL, {'error': str(e)})
                return state_json
        else:
            self.warning(f"[AsyncFSM] No effect registered for state: {current_state}")
            return state_json

    # ==============================================
    # State Effects Implementation
    # ==============================================

    async def _effect_idle(self, state_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        IDLE 状态的 effect
        调用 planning API (START_WORKFLOW)
        """
        return await self._call_state_api_and_apply_transition(
            state_json=state_json,
            state_name='IDLE',
            transition_name='START_WORKFLOW',
            transition_type='planning'
        )

    async def _effect_stage_running(self, state_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        STAGE_RUNNING 状态的 effect
        调用 planning API (START_STEP)
        """
        return await self._call_state_api_and_apply_transition(
            state_json=state_json,
            state_name='STAGE_RUNNING',
            transition_name='START_STEP',
            transition_type='planning'
        )

    async def _effect_step_running(self, state_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        STEP_RUNNING 状态的 effect
        调用 planning API (START_BEHAVIOR)
        """
        return await self._call_state_api_and_apply_transition(
            state_json=state_json,
            state_name='STEP_RUNNING',
            transition_name='START_BEHAVIOR',
            transition_type='planning'
        )

    async def _effect_behavior_running(self, state_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        BEHAVIOR_RUNNING 状态的 effect
        调用 generating API，执行 actions
        """
        if not self.script_store:
            self.error("[AsyncFSM] No script_store configured")
            return state_json

        return await self._call_state_api_and_apply_transition(
            state_json=state_json,
            state_name='BEHAVIOR_RUNNING',
            transition_name='COMPLETE_BEHAVIOR',
            transition_type='generating'
        )

    async def _effect_behavior_completed(self, state_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        BEHAVIOR_COMPLETED 状态的 effect
        调用 reflecting API，决定下一步
        """
        return await self._call_state_api_and_apply_transition(
            state_json=state_json,
            state_name='BEHAVIOR_COMPLETED',
            transition_name=None,  # Let API determine the transition
            transition_type='reflecting'
        )

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
        调用 reflecting API，决定下一步
        """
        return await self._call_state_api_and_apply_transition(
            state_json=state_json,
            state_name='STAGE_COMPLETED',
            transition_name=None,  # Let API determine the transition
            transition_type='reflecting'
        )

    # ==============================================
    # Helper Methods
    # ==============================================

    async def _call_state_api_and_apply_transition(
        self,
        state_json: Dict[str, Any],
        state_name: str,
        transition_name: Optional[str],
        transition_type: str
    ) -> Dict[str, Any]:
        """
        通用方法：调用 state 的 API 并应用 transition

        Args:
            state_json: 当前状态 JSON
            state_name: 状态名称
            transition_name: transition 名称
            transition_type: transition 类型 ('planning', 'generating', 'reflecting')

        Returns:
            更新后的状态 JSON
        """
        if not self.api_client:
            self.error("[AsyncFSM] No API client configured")
            return state_json

        self.info(f"[AsyncFSM] {state_name} → calling {transition_type} API (transition={transition_name})")

        # Get state instance
        from .state_classes.state_factory import StateFactory
        state_instance = StateFactory.get_state(state_name)

        if not state_instance:
            self.error(f"[AsyncFSM] Failed to get state instance for {state_name}")
            return state_json

        # Ensure API client is injected (in case state was created before set_api_client was called)
        if not state_instance._api_client:
            state_instance.set_api_client(self.api_client)
            self.debug(f"[AsyncFSM] API client injected into {state_name} state instance")

        try:
            # Call state's API method
            response = await state_instance.call_api(state_json, transition_name)

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
                new_state = state_updater.apply_transition(
                    state=new_state_json,
                    transition_response=json.dumps(response),
                    transition_type='generating'
                )

                return new_state
            else:
                # For planning and reflecting APIs, apply transition directly
                from utils.state_updater import state_updater
                if self.script_store:
                    state_updater.set_script_store(self.script_store)
                new_state = state_updater.apply_transition(
                    state=state_json,
                    transition_response=response,
                    transition_type=transition_type
                )

                return new_state

        except Exception as e:
            self.error(f"[AsyncFSM] Error calling API for {state_name}: {e}", exc_info=True)
            return state_json

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
