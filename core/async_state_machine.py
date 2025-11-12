"""
异步状态机适配器
提供事件驱动的异步执行能力
"""

import asyncio
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
        if not self.api_client:
            self.error("[AsyncFSM] No API client configured")
            return state_json

        self.info("[AsyncFSM] IDLE → calling planning API (START_WORKFLOW)")

        # 获取 stage_id
        observation = state_json.get('observation', {})
        location = observation.get('location', {})
        progress = location.get('progress', {})
        stages = progress.get('stages', {})
        current_stage = stages.get('current', {})

        stage_id = current_stage.get('stage_id', 'initial') if isinstance(current_stage, dict) else current_stage

        # 调用 planning API
        response = await self.api_client.send_feedback(
            stage_id=stage_id or 'initial',
            step_index='none',
            state=state_json,
            transition_name='START_WORKFLOW'
        )

        # 应用 transition
        from utils.state_updater import state_updater
        new_state = state_updater.apply_transition(
            state=state_json,
            transition_response=response,
            transition_type='planning'
        )

        return new_state

    async def _effect_stage_running(self, state_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        STAGE_RUNNING 状态的 effect
        调用 planning API (START_STEP)
        """
        if not self.api_client:
            self.error("[AsyncFSM] No API client configured")
            return state_json

        self.info("[AsyncFSM] STAGE_RUNNING → calling planning API (START_STEP)")

        # 提取 stage_id 和 step_id
        observation = state_json.get('observation', {})
        location = observation.get('location', {})
        current = location.get('current', {})

        stage_id = current.get('stage_id', 'unknown')
        step_id = current.get('step_id', 'none')

        # 调用 planning API
        response = await self.api_client.send_feedback(
            stage_id=stage_id,
            step_index=step_id,
            state=state_json,
            transition_name='START_STEP'
        )

        # 应用 transition
        from utils.state_updater import state_updater
        new_state = state_updater.apply_transition(
            state=state_json,
            transition_response=response,
            transition_type='planning'
        )

        return new_state

    async def _effect_step_running(self, state_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        STEP_RUNNING 状态的 effect
        调用 planning API (START_BEHAVIOR)
        """
        if not self.api_client:
            self.error("[AsyncFSM] No API client configured")
            return state_json

        self.info("[AsyncFSM] STEP_RUNNING → calling planning API (START_BEHAVIOR)")

        # 提取 stage_id 和 step_id
        observation = state_json.get('observation', {})
        location = observation.get('location', {})
        current = location.get('current', {})

        stage_id = current.get('stage_id', 'unknown')
        step_id = current.get('step_id', 'unknown')

        # 调用 planning API
        response = await self.api_client.send_feedback(
            stage_id=stage_id,
            step_index=step_id,
            state=state_json,
            transition_name='START_BEHAVIOR'
        )

        # 应用 transition
        from utils.state_updater import state_updater
        new_state = state_updater.apply_transition(
            state=state_json,
            transition_response=response,
            transition_type='planning'
        )

        return new_state

    async def _effect_behavior_running(self, state_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        BEHAVIOR_RUNNING 状态的 effect
        调用 generating API，执行 actions
        """
        if not self.api_client:
            self.error("[AsyncFSM] No API client configured")
            return state_json

        if not self.script_store:
            self.error("[AsyncFSM] No script_store configured")
            return state_json

        self.info("[AsyncFSM] BEHAVIOR_RUNNING → calling generating API")

        # 提取 stage_id 和 step_id
        observation = state_json.get('observation', {})
        location = observation.get('location', {})
        current = location.get('current', {})

        stage_id = current.get('stage_id', 'unknown')
        step_id = current.get('step_id', 'unknown')

        # 调用 generating API，收集所有 actions
        actions = []
        async for action in self.api_client.fetch_behavior_actions(
            stage_id=stage_id,
            step_index=step_id,
            state=state_json,
            stream=False,
            transition_name='COMPLETE_BEHAVIOR'
        ):
            actions.append(action)

        self.info(f"[AsyncFSM] Received {len(actions)} actions, executing...")

        # 执行所有 actions（更新 stores）
        for action in actions:
            # 转换 action 格式
            step = self._convert_action_to_step(action)
            self.script_store.exec_action(step)

        # 从 stores 构建新状态
        new_state_json = self._build_state_from_stores(state_json)

        # 应用 transition（更新 FSM 到 BEHAVIOR_COMPLETED）
        from utils.state_updater import state_updater
        import json
        response = {'actions': actions, 'count': len(actions)}
        new_state = state_updater.apply_transition(
            state=new_state_json,
            transition_response=json.dumps(response),
            transition_type='generating'
        )

        return new_state

    async def _effect_behavior_completed(self, state_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        BEHAVIOR_COMPLETED 状态的 effect
        调用 reflecting API，决定下一步
        """
        if not self.api_client:
            self.error("[AsyncFSM] No API client configured")
            return state_json

        self.info("[AsyncFSM] BEHAVIOR_COMPLETED → calling reflecting API")

        # 提取当前 FSM 状态
        fsm = state_json.get('state', {}).get('FSM', {})
        current_fsm_state = fsm.get('state', 'BEHAVIOR_COMPLETED')

        # 提取 stage_id 和 step_id
        observation = state_json.get('observation', {})
        location = observation.get('location', {})
        current = location.get('current', {})

        stage_id = current.get('stage_id', 'unknown')
        step_id = current.get('step_id', 'unknown')

        self.info(f"[AsyncFSM] Current FSM state: {current_fsm_state}")

        # 调用 reflecting API
        # transition_name 将在 API 响应后根据 next_state 自动确定
        response = await self.api_client.send_reflecting(
            stage_id=stage_id,
            step_index=step_id,
            state=state_json,
            transition_name=None  # 让 API client 根据响应确定实际的 transition
        )

        # 应用 transition
        from utils.state_updater import state_updater
        new_state = state_updater.apply_transition(
            state=state_json,
            transition_response=response,
            transition_type='reflecting'
        )

        return new_state

    async def _effect_step_completed(self, state_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        STEP_COMPLETED 状态的 effect
        调用 reflecting API，决定下一步
        """
        if not self.api_client:
            self.error("[AsyncFSM] No API client configured")
            return state_json

        self.info("[AsyncFSM] STEP_COMPLETED → calling reflecting API")

        # 提取 stage_id 和 step_id
        observation = state_json.get('observation', {})
        location = observation.get('location', {})
        current = location.get('current', {})

        stage_id = current.get('stage_id', 'unknown')
        step_id = current.get('step_id', 'unknown')

        # 调用 reflecting API
        # transition_name 将根据响应自动确定
        response = await self.api_client.send_reflecting(
            stage_id=stage_id,
            step_index=step_id,
            state=state_json,
            transition_name=None
        )

        # 应用 transition
        from utils.state_updater import state_updater
        new_state = state_updater.apply_transition(
            state=state_json,
            transition_response=response,
            transition_type='reflecting'
        )

        return new_state

    async def _effect_stage_completed(self, state_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        STAGE_COMPLETED 状态的 effect
        调用 reflecting API，决定下一步
        """
        if not self.api_client:
            self.error("[AsyncFSM] No API client configured")
            return state_json

        self.info("[AsyncFSM] STAGE_COMPLETED → calling reflecting API")

        # 提取 stage_id
        observation = state_json.get('observation', {})
        location = observation.get('location', {})
        current = location.get('current', {})

        stage_id = current.get('stage_id', 'unknown')

        # 调用 reflecting API
        # transition_name 将根据响应自动确定
        response = await self.api_client.send_reflecting(
            stage_id=stage_id,
            step_index='completed',
            state=state_json,
            transition_name=None
        )

        # 应用 transition
        from utils.state_updater import state_updater
        new_state = state_updater.apply_transition(
            state=state_json,
            transition_response=response,
            transition_type='reflecting'
        )

        return new_state

    # ==============================================
    # Helper Methods
    # ==============================================

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
