"""
Transition Logger
记录每次状态转换的详细信息到独立的日志文件

设计理念：
1. 日志在 TransitionHandler 执行完成后创建
2. 使用实际的 transition 名称（而非预测的）
3. 记录完整的转换上下文：API 请求、响应、状态变化
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import threading


class TransitionLogger:
    """
    状态转换日志记录器
    为每次状态转换创建独立的日志文件
    """

    # 类级别的调用计数器
    _call_counter = 0
    _lock = threading.Lock()

    def __init__(self, log_dir: str = "logs"):
        """
        初始化转换日志记录器

        Args:
            log_dir: 日志文件保存目录
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.last_log_file: Optional[Path] = None

    def set_log_dir(self, log_dir: str) -> None:
        """
        更新日志目录

        Args:
            log_dir: 新的日志文件保存目录
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

    @classmethod
    def _get_next_call_number(cls) -> int:
        """获取下一个调用编号（线程安全）"""
        with cls._lock:
            cls._call_counter += 1
            return cls._call_counter

    def log_transition(
        self,
        transition_name: str,
        from_state: str,
        to_state: str,
        api_type: Optional[str] = None,
        api_request: Optional[Dict[str, Any]] = None,
        api_response: Optional[Dict[str, Any]] = None,
        state_before: Optional[Dict[str, Any]] = None,
        state_after: Optional[Dict[str, Any]] = None,
        extra_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        记录状态转换信息到日志文件

        Args:
            transition_name: 转换名称（如 START_WORKFLOW, COMPLETE_BEHAVIOR, NEXT_BEHAVIOR）
            from_state: 源状态
            to_state: 目标状态
            api_type: API 类型（planning, generating, reflecting）
            api_request: API 请求内容
            api_response: API 响应内容
            state_before: 转换前的状态
            state_after: 转换后的状态
            extra_info: 额外信息

        Returns:
            日志文件路径
        """
        # 获取调用编号
        call_number = self._get_next_call_number()

        # 生成文件名: 序号_转换名称.log
        # 例如: 0001_START_WORKFLOW.log, 0002_START_STEP.log, 0003_NEXT_BEHAVIOR.log
        filename = f"{call_number:04d}_{transition_name}.log"
        log_file = self.log_dir / filename

        # 准备日志内容
        log_content = self._format_log_content(
            call_number=call_number,
            transition_name=transition_name,
            from_state=from_state,
            to_state=to_state,
            api_type=api_type,
            api_request=api_request,
            api_response=api_response,
            state_before=state_before,
            state_after=state_after,
            extra_info=extra_info
        )

        # 写入日志文件
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(log_content)

            self.last_log_file = log_file
            return str(log_file)
        except Exception as e:
            print(f"⚠️  写入转换日志失败: {e}")
            return ""

    def _format_log_content(
        self,
        call_number: int,
        transition_name: str,
        from_state: str,
        to_state: str,
        api_type: Optional[str],
        api_request: Optional[Dict[str, Any]],
        api_response: Optional[Dict[str, Any]],
        state_before: Optional[Dict[str, Any]],
        state_after: Optional[Dict[str, Any]],
        extra_info: Optional[Dict[str, Any]]
    ) -> str:
        """格式化日志内容"""

        lines = []
        timestamp = datetime.now()

        # 标题
        lines.append("=" * 80)
        lines.append(f"状态转换日志 - {transition_name}")
        lines.append("=" * 80)
        lines.append("")

        # 基本信息
        lines.append("📋 基本信息")
        lines.append("-" * 80)
        lines.append(f"转换编号: #{call_number:04d}")
        lines.append(f"转换名称: {transition_name}")
        lines.append(f"转换时间: {timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
        lines.append(f"状态变化: {from_state} → {to_state}")
        if api_type:
            lines.append(f"API 类型: {api_type}")
        lines.append("")

        # API 请求
        if api_request:
            lines.append("📤 API 请求")
            lines.append("-" * 80)
            lines.append(json.dumps(api_request, indent=2, ensure_ascii=False))
            lines.append("")

        # API 响应
        if api_response:
            lines.append("📥 API 响应")
            lines.append("-" * 80)

            # 如果响应包含 actions，特别标注
            if isinstance(api_response, dict) and 'actions' in api_response:
                actions = api_response.get('actions', [])
                lines.append(f"Actions 数量: {len(actions)}")
                lines.append("")

                # 列出所有 action types
                action_types = [a.get('type', 'unknown') for a in actions if isinstance(a, dict)]
                lines.append(f"Action 类型列表: {', '.join(action_types)}")
                lines.append("")

                # 检查控制信号
                control_signals = []
                for action in actions:
                    if isinstance(action, dict):
                        action_type = action.get('type', '')
                        if action_type in ('mark_step_complete', 'mark_stage_complete', 'complete_reflection'):
                            control_signals.append(action_type)

                if control_signals:
                    lines.append(f"🎯 控制信号: {', '.join(control_signals)}")
                    lines.append("")

            lines.append(json.dumps(api_response, indent=2, ensure_ascii=False))
            lines.append("")

        # 状态变化对比
        if state_before and state_after:
            lines.append("🔄 状态变化")
            lines.append("-" * 80)

            # FSM 状态
            fsm_before = state_before.get('FSM', {})
            fsm_after = state_after.get('FSM', {})

            lines.append("FSM 状态:")
            lines.append(f"  state: {fsm_before.get('state')} → {fsm_after.get('state')}")

            # 位置信息
            loc_before = state_before.get('observation', {}).get('location', {}).get('current', {})
            loc_after = state_after.get('observation', {}).get('location', {}).get('current', {})

            if loc_before != loc_after:
                lines.append("")
                lines.append("位置变化:")
                if loc_before.get('stage_id') != loc_after.get('stage_id'):
                    lines.append(f"  stage_id: {loc_before.get('stage_id')} → {loc_after.get('stage_id')}")
                if loc_before.get('step_id') != loc_after.get('step_id'):
                    lines.append(f"  step_id: {loc_before.get('step_id')} → {loc_after.get('step_id')}")
                if loc_before.get('behavior_id') != loc_after.get('behavior_id'):
                    lines.append(f"  behavior_id: {loc_before.get('behavior_id')} → {loc_after.get('behavior_id')}")

            # 变量变化
            vars_before = set(state_before.get('variables', {}).keys())
            vars_after = set(state_after.get('variables', {}).keys())

            new_vars = vars_after - vars_before
            if new_vars:
                lines.append("")
                lines.append(f"新增变量: {', '.join(new_vars)}")

            lines.append("")

        # 转换后状态摘要
        if state_after:
            lines.append("📊 转换后状态摘要")
            lines.append("-" * 80)

            # 变量
            variables = state_after.get('variables', {})
            lines.append(f"变量数量: {len(variables)}")
            if variables:
                for key, value in list(variables.items())[:5]:  # 只显示前5个
                    value_str = str(value)
                    if len(value_str) > 100:
                        value_str = value_str[:100] + "..."
                    lines.append(f"  - {key}: {value_str}")
                if len(variables) > 5:
                    lines.append(f"  ... 还有 {len(variables) - 5} 个变量")
            lines.append("")

            # Effects
            effects = state_after.get('effects', {})
            current_effects = effects.get('current', [])
            lines.append(f"当前 Effects: {len(current_effects)}")
            for effect in current_effects[:3]:  # 只显示前3个
                lines.append(f"  - {effect}")
            if len(current_effects) > 3:
                lines.append(f"  ... 还有 {len(current_effects) - 3} 个 effects")
            lines.append("")

            # Notebook
            notebook = state_after.get('notebook', {})
            cells = notebook.get('cells', [])
            lines.append(f"Notebook Cells: {len(cells)}")
            lines.append(f"执行计数: {notebook.get('execution_count', 0)}")
            lines.append("")

        # 额外信息
        if extra_info:
            lines.append("ℹ️  额外信息")
            lines.append("-" * 80)
            lines.append(json.dumps(extra_info, indent=2, ensure_ascii=False))
            lines.append("")

        # 结束标记
        lines.append("=" * 80)
        lines.append(f"日志记录时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
        lines.append("=" * 80)

        return "\n".join(lines)


# 全局单例
_transition_logger = None


def get_transition_logger(log_dir: str = "logs") -> TransitionLogger:
    """获取全局转换日志记录器单例"""
    global _transition_logger
    if _transition_logger is None:
        _transition_logger = TransitionLogger(log_dir)
    return _transition_logger
