"""
Action Execution Logger
记录每个 action 执行的详细状态到日志文件
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List


class ActionExecutionLogger:
    """
    Action 执行日志记录器
    记录每个 action 的执行状态
    """

    def __init__(self, log_dir: str = "api_logs"):
        """
        初始化 Action 执行日志记录器

        Args:
            log_dir: 日志文件保存目录
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.current_log_file: Optional[str] = None
        self.action_logs: List[Dict[str, Any]] = []

    def start_behavior_log(self, behavior_id: str, stage_id: str, step_id: str) -> str:
        """
        开始一个新的 behavior 日志

        Args:
            behavior_id: Behavior ID
            stage_id: Stage ID
            step_id: Step ID

        Returns:
            日志文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"actions_{behavior_id}_{timestamp}.log"
        self.current_log_file = str(self.log_dir / filename)
        self.action_logs = []

        # 写入日志头部
        lines = []
        lines.append("=" * 80)
        lines.append("Action 执行日志")
        lines.append("=" * 80)
        lines.append("")
        lines.append(f"Behavior ID: {behavior_id}")
        lines.append(f"Stage ID: {stage_id}")
        lines.append(f"Step ID: {step_id}")
        lines.append(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
        lines.append("")
        lines.append("=" * 80)
        lines.append("")

        with open(self.current_log_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        return self.current_log_file

    def log_action_start(self, action_index: int, action: Dict[str, Any]) -> None:
        """
        记录 action 开始执行

        Args:
            action_index: Action 索引
            action: Action 数据
        """
        if not self.current_log_file:
            return

        timestamp = datetime.now()
        action_log = {
            'index': action_index,
            'action_type': action.get('action') or action.get('type', 'unknown'),
            'start_time': timestamp.isoformat(),
            'status': 'started',  # 标记为已开始
            'executed': False  # 默认未执行完成
        }
        self.action_logs.append(action_log)

        # 追加到日志文件
        lines = []
        lines.append(f"{'─' * 80}")
        lines.append(f"Action #{action_index + 1} - 开始执行")
        lines.append(f"{'─' * 80}")
        lines.append(f"⏰ 开始时间: {timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
        lines.append(f"🎬 Action 类型: {action_log['action_type']}")
        lines.append("")
        lines.append("📦 Action 内容:")
        try:
            action_json = json.dumps(action, indent=2, ensure_ascii=False)
            lines.append(action_json)
        except Exception as e:
            lines.append(f"⚠️  无法序列化 action: {e}")
            lines.append(str(action))
        lines.append("")

        with open(self.current_log_file, 'a', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')

    def log_action_complete(
        self,
        action_index: int,
        result: Any = None,
        error: Optional[str] = None,
        executed: bool = True
    ) -> None:
        """
        记录 action 执行完成

        Args:
            action_index: Action 索引
            result: 执行结果
            error: 错误信息（如果有）
            executed: 是否真正执行了（有些action可能被跳过）
        """
        if not self.current_log_file or action_index >= len(self.action_logs):
            return

        timestamp = datetime.now()
        action_log = self.action_logs[action_index]
        action_log['end_time'] = timestamp.isoformat()
        action_log['executed'] = executed

        if not executed:
            action_log['status'] = 'skipped'
        elif error:
            action_log['status'] = 'failed'
            action_log['error'] = error
        else:
            action_log['status'] = 'completed'

        # 计算执行时间
        start_time = datetime.fromisoformat(action_log['start_time'])
        duration = (timestamp - start_time).total_seconds()

        # 追加到日志文件
        lines = []
        lines.append(f"✅ 完成时间: {timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
        lines.append(f"⏱️  执行耗时: {duration:.3f} 秒")

        if not executed:
            lines.append(f"⏭️  状态: 跳过（未执行）")
        elif error:
            lines.append(f"❌ 状态: 失败")
            lines.append(f"错误信息: {error}")
        else:
            lines.append(f"✅ 状态: 成功执行")

        if result:
            lines.append("")
            lines.append("📊 执行结果:")
            try:
                if isinstance(result, (dict, list)):
                    result_json = json.dumps(result, indent=2, ensure_ascii=False)
                    lines.append(result_json)
                else:
                    lines.append(str(result))
            except Exception as e:
                lines.append(f"⚠️  无法序列化结果: {e}")
                lines.append(str(result))

        lines.append("")
        lines.append("")

        with open(self.current_log_file, 'a', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')

    def finalize_behavior_log(self, final_state: Optional[Dict[str, Any]] = None) -> None:
        """
        完成 behavior 日志，添加汇总信息

        Args:
            final_state: 最终状态（可选）
        """
        if not self.current_log_file:
            return

        lines = []
        lines.append("=" * 80)
        lines.append("执行汇总")
        lines.append("=" * 80)
        lines.append("")

        # 统计信息
        total_actions = len(self.action_logs)
        completed_actions = sum(1 for log in self.action_logs if log['status'] == 'completed')
        failed_actions = sum(1 for log in self.action_logs if log['status'] == 'failed')
        skipped_actions = sum(1 for log in self.action_logs if log['status'] == 'skipped')
        executed_actions = sum(1 for log in self.action_logs if log.get('executed', False))

        lines.append(f"总 Actions 数: {total_actions}")
        lines.append(f"✅ 成功执行: {completed_actions}")
        lines.append(f"❌ 执行失败: {failed_actions}")
        lines.append(f"⏭️  跳过未执行: {skipped_actions}")
        lines.append(f"📊 实际执行率: {executed_actions}/{total_actions} ({executed_actions/total_actions*100:.1f}%)")
        lines.append("")

        # 执行时间统计
        if self.action_logs:
            total_duration = 0
            for log in self.action_logs:
                if 'end_time' in log and 'start_time' in log:
                    start = datetime.fromisoformat(log['start_time'])
                    end = datetime.fromisoformat(log['end_time'])
                    total_duration += (end - start).total_seconds()

            lines.append(f"总执行时间: {total_duration:.3f} 秒")
            lines.append(f"平均每个 Action: {total_duration/total_actions:.3f} 秒")
            lines.append("")

        # Action 执行详情表格
        lines.append("=" * 80)
        lines.append("📋 Action 执行详情")
        lines.append("=" * 80)
        lines.append("")
        lines.append(f"{'#':<4} {'类型':<15} {'状态':<12} {'耗时(秒)':<12} {'是否执行':<10}")
        lines.append("-" * 80)

        for log in self.action_logs:
            index = log['index'] + 1
            action_type = log['action_type'][:14]
            status = log['status']
            executed_mark = "✅ 是" if log.get('executed', False) else "❌ 否"

            # 计算耗时
            if 'end_time' in log and 'start_time' in log:
                start = datetime.fromisoformat(log['start_time'])
                end = datetime.fromisoformat(log['end_time'])
                duration = (end - start).total_seconds()
                duration_str = f"{duration:.3f}"
            else:
                duration_str = "N/A"

            # 状态符号
            if status == 'completed':
                status_str = "✅ 成功"
            elif status == 'failed':
                status_str = "❌ 失败"
            elif status == 'skipped':
                status_str = "⏭️  跳过"
            else:
                status_str = status

            lines.append(f"{index:<4} {action_type:<15} {status_str:<12} {duration_str:<12} {executed_mark:<10}")

        lines.append("")

        # 最终状态
        if final_state:
            lines.append("=" * 80)
            lines.append("🏁 最终状态")
            lines.append("=" * 80)
            lines.append("")

            # FSM State
            if 'FSM' in final_state:
                fsm = final_state['FSM']
                lines.append(f"🎯 状态机 (FSM):")
                lines.append(f"  当前状态: {fsm.get('currentState', 'N/A')}")
                lines.append(f"  阶段: {fsm.get('currentStageId', 'N/A')}")
                lines.append(f"  步骤: {fsm.get('currentStepId', 'N/A')}")
                lines.append(f"  Behavior: {fsm.get('currentBehaviorId', 'N/A')}")
                lines.append("")

            # Variables
            if 'variables' in final_state:
                lines.append(f"📊 变量: {len(final_state['variables'])} 个")
                if final_state['variables']:
                    for key, value in list(final_state['variables'].items())[:10]:  # 只显示前10个
                        value_str = str(value)
                        if len(value_str) > 100:
                            value_str = value_str[:100] + "..."
                        lines.append(f"  - {key}: {value_str}")
                    if len(final_state['variables']) > 10:
                        lines.append(f"  ... 还有 {len(final_state['variables']) - 10} 个变量")
                lines.append("")

        lines.append("=" * 80)
        lines.append(f"日志完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
        lines.append("=" * 80)

        with open(self.current_log_file, 'a', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')

        # 重置
        self.current_log_file = None
        self.action_logs = []


# 全局单例
_action_logger = None


def get_action_logger(log_dir: str = "api_logs") -> ActionExecutionLogger:
    """获取全局 Action 执行日志记录器单例"""
    global _action_logger
    if _action_logger is None:
        _action_logger = ActionExecutionLogger(log_dir)
    return _action_logger
