"""
API Call Logger
记录每次 API 调用的详细信息到独立的日志文件
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import threading


class APICallLogger:
    """
    API 调用日志记录器
    为每次 API 调用创建独立的日志文件
    """

    # 类级别的调用计数器
    _call_counter = 0
    _lock = threading.Lock()

    def __init__(self, log_dir: str = "api_logs"):
        """
        初始化 API 日志记录器

        Args:
            log_dir: 日志文件保存目录
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

    @classmethod
    def _get_next_call_number(cls) -> int:
        """获取下一个调用编号（线程安全）"""
        with cls._lock:
            cls._call_counter += 1
            return cls._call_counter

    def log_api_call(
        self,
        api_url: str,
        method: str,
        payload: Dict[str, Any],
        context_state: Optional[Dict[str, Any]] = None,
        extra_info: Optional[Dict[str, Any]] = None,
        response: Optional[Any] = None,
        response_status: Optional[int] = None,
        response_error: Optional[str] = None,
        final_state: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        记录 API 调用信息到独立的日志文件

        Args:
            api_url: API 地址
            method: HTTP 方法 (GET, POST, etc.)
            payload: 请求负载
            context_state: 当前上下文状态（变量等）
            extra_info: 额外信息
            response: API 响应内容 (可选)
            response_status: HTTP 状态码 (可选)
            response_error: 错误信息 (可选)
            final_state: 处理完成后的最终状态 (可选)

        Returns:
            日志文件路径
        """
        # 获取调用编号
        call_number = self._get_next_call_number()

        # 生成时间戳
        timestamp = datetime.now()
        time_str = timestamp.strftime("%Y%m%d_%H%M%S_%f")[:-3]  # 精确到毫秒

        # 清理 API URL 用于文件名（移除特殊字符）
        api_name = api_url.replace('http://', '').replace('https://', '')
        api_name = api_name.replace(':', '_').replace('/', '_')

        # 生成文件名：编号_时间_API地址.log
        filename = f"{call_number:04d}_{time_str}_{api_name}.log"
        log_file = self.log_dir / filename

        # 准备日志内容
        log_content = self._format_log_content(
            call_number=call_number,
            timestamp=timestamp,
            api_url=api_url,
            method=method,
            payload=payload,
            context_state=context_state,
            extra_info=extra_info,
            response=response,
            response_status=response_status,
            response_error=response_error,
            final_state=final_state
        )

        # 写入日志文件
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(log_content)

            return str(log_file)
        except Exception as e:
            print(f"⚠️  写入 API 日志失败: {e}")
            return ""

    def _format_log_content(
        self,
        call_number: int,
        timestamp: datetime,
        api_url: str,
        method: str,
        payload: Dict[str, Any],
        context_state: Optional[Dict[str, Any]],
        extra_info: Optional[Dict[str, Any]],
        response: Optional[Any] = None,
        response_status: Optional[int] = None,
        response_error: Optional[str] = None,
        final_state: Optional[Dict[str, Any]] = None
    ) -> str:
        """格式化日志内容"""

        lines = []
        lines.append("=" * 80)
        lines.append(f"API 调用日志")
        lines.append("=" * 80)
        lines.append("")

        # 基本信息
        lines.append(" 基本信息")
        lines.append("-" * 80)
        lines.append(f"调用编号: #{call_number:04d}")
        lines.append(f"调用时间: {timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
        lines.append(f"API 地址: {api_url}")
        lines.append(f"HTTP 方法: {method}")
        lines.append("")

        # 请求负载
        lines.append(" 请求负载 (Payload)")
        lines.append("-" * 80)
        try:
            payload_json = json.dumps(payload, indent=2, ensure_ascii=False)
            lines.append(payload_json)
        except Exception as e:
            lines.append(f"⚠️  无法序列化 payload: {e}")
            lines.append(str(payload))
        lines.append("")

        # 当前上下文状态
        if context_state:
            lines.append("🎯 当前上下文状态")
            lines.append("-" * 80)

            # Variables
            if 'variables' in context_state:
                lines.append(f"📊 变量 (Variables): {len(context_state['variables'])} 个")
                if context_state['variables']:
                    for key, value in context_state['variables'].items():
                        value_str = str(value)
                        if len(value_str) > 100:
                            value_str = value_str[:100] + "..."
                        lines.append(f"  - {key}: {value_str}")
                else:
                    lines.append("  (无变量)")
                lines.append("")

            # To-Do List
            if 'toDoList' in context_state:
                lines.append(f"✅ 待办事项 (To-Do List): {len(context_state['toDoList'])} 项")
                for i, todo in enumerate(context_state['toDoList'], 1):
                    lines.append(f"  {i}. {todo}")
                if not context_state['toDoList']:
                    lines.append("  (无待办)")
                lines.append("")

            # Checklist
            if 'checklist' in context_state:
                checklist = context_state['checklist']
                current = checklist.get('current', [])
                completed = checklist.get('completed', [])
                lines.append(f"📝 检查清单 (Checklist):")
                lines.append(f"  当前: {len(current)} 项")
                for item in current:
                    lines.append(f"    - [ ] {item}")
                lines.append(f"  已完成: {len(completed)} 项")
                for item in completed:
                    lines.append(f"    - [x] {item}")
                lines.append("")

            # Thinking
            if 'thinking' in context_state:
                lines.append(f"💭 思考记录 (Thinking): {len(context_state['thinking'])} 条")
                for i, think in enumerate(context_state['thinking'][-5:], 1):  # 只显示最后5条
                    lines.append(f"  {i}. {think[:200]}...")
                lines.append("")

            # Effect
            if 'effect' in context_state:
                effect = context_state['effect']
                current_effects = effect.get('current', [])
                lines.append(f"⚡ 执行效果 (Effect): {len(current_effects)} 条")
                for effect_item in current_effects:
                    lines.append(f"  - {effect_item}")
                lines.append("")

            # Stage Status
            if 'stageStatus' in context_state:
                lines.append(f"🎬 阶段状态 (Stage Status):")
                for stage_id, completed in context_state['stageStatus'].items():
                    status = "✅ 完成" if completed else "⏳ 进行中"
                    lines.append(f"  - {stage_id}: {status}")
                lines.append("")

            # Notebook Content (完整 Markdown 格式)
            if 'notebook' in context_state:
                notebook = context_state['notebook']
                cells = notebook.get('cells', [])
                lines.append(f"📓 Notebook 内容 (Markdown 格式)")
                lines.append("-" * 80)
                lines.append(f"# {notebook.get('title', 'Untitled Notebook')}")
                lines.append("")
                lines.append(f"**Cells 总数**: {len(cells)} | **执行计数**: {notebook.get('execution_count', 0)}")
                lines.append("")
                lines.append("=" * 80)
                lines.append("")

                if cells:
                    for i, cell in enumerate(cells, 1):
                        cell_type = cell.get('type', 'unknown')
                        cell_id = cell.get('id', 'unknown')
                        content = cell.get('content', '')

                        lines.append(f"## Cell {i}: [{cell_type}] {cell_id}")
                        lines.append("")

                        # 根据cell类型显示内容
                        if cell_type == 'markdown':
                            lines.append(content)
                        elif cell_type == 'code':
                            language = cell.get('language', 'python')
                            lines.append(f"```{language}")
                            lines.append(content)
                            lines.append("```")

                            # 显示输出
                            outputs = cell.get('outputs', [])
                            if outputs:
                                lines.append("")
                                lines.append("**Output:**")
                                lines.append("```")
                                for output in outputs:
                                    if isinstance(output, dict):
                                        output_text = output.get('content') or output.get('text', str(output))
                                    else:
                                        output_text = str(output)
                                    lines.append(output_text)
                                lines.append("```")
                        elif cell_type == 'thinking':
                            agent_name = cell.get('agent_name', 'AI')
                            lines.append(f"> **{agent_name} is thinking...**")
                            lines.append(">")
                            for line in content.split('\n'):
                                lines.append(f"> {line}")
                        else:
                            # 其他类型
                            lines.append("```")
                            lines.append(content)
                            lines.append("```")

                        # Cell 元数据
                        metadata = cell.get('metadata', {})
                        if metadata:
                            lines.append("")
                            lines.append(f"*Metadata: {json.dumps(metadata, ensure_ascii=False)}*")

                        lines.append("")
                        lines.append("-" * 80)
                        lines.append("")
                else:
                    lines.append("*( Notebook 中暂无 cells )*")
                    lines.append("")

        # 额外信息
        if extra_info:
            lines.append("ℹ️  额外信息")
            lines.append("-" * 80)
            try:
                extra_json = json.dumps(extra_info, indent=2, ensure_ascii=False)
                lines.append(extra_json)
            except Exception as e:
                lines.append(f"⚠️  无法序列化额外信息: {e}")
                lines.append(str(extra_info))
            lines.append("")

        # 统计信息
        lines.append("📊 统计信息")
        lines.append("-" * 80)
        if context_state:
            var_count = len(context_state.get('variables', {}))
            todo_count = len(context_state.get('toDoList', []))
            thinking_count = len(context_state.get('thinking', []))

            lines.append(f"变量总数: {var_count}")
            lines.append(f"待办总数: {todo_count}")
            lines.append(f"思考记录数: {thinking_count}")

            # Notebook统计
            if 'notebook' in context_state:
                notebook = context_state['notebook']
                cells_count = len(notebook.get('cells', []))
                lines.append(f"Notebook Cells 数: {cells_count}")

        payload_size = len(json.dumps(payload))
        lines.append(f"Payload 大小: {payload_size} bytes ({payload_size/1024:.2f} KB)")
        lines.append("")

        # API 响应
        if response is not None or response_status is not None or response_error is not None:
            lines.append("=" * 80)
            lines.append(" API 响应 (Response)")
            lines.append("=" * 80)
            lines.append("")

            if response_status is not None:
                status_emoji = "✅" if 200 <= response_status < 300 else "❌"
                lines.append(f"{status_emoji} HTTP 状态码: {response_status}")
                lines.append("")

            if response_error:
                lines.append("❌ 错误信息:")
                lines.append("-" * 80)
                lines.append(response_error)
                lines.append("")

            if response is not None:
                lines.append("📦 响应内容:")
                lines.append("-" * 80)
                try:
                    if isinstance(response, str):
                        # 字符串响应（可能是XML或纯文本）
                        lines.append(response)
                    elif isinstance(response, dict):
                        # JSON响应
                        response_json = json.dumps(response, indent=2, ensure_ascii=False)
                        lines.append(response_json)
                    else:
                        # 其他类型
                        lines.append(str(response))
                except Exception as e:
                    lines.append(f"⚠️  无法序列化响应: {e}")
                    lines.append(str(response))
                lines.append("")

                # 响应大小统计
                if isinstance(response, str):
                    response_size = len(response.encode('utf-8'))
                elif isinstance(response, dict):
                    response_size = len(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                else:
                    response_size = len(str(response).encode('utf-8'))
                lines.append(f"响应大小: {response_size} bytes ({response_size/1024:.2f} KB)")
                lines.append("")

        # 最终状态（处理完成后）
        if final_state:
            lines.append("=" * 80)
            lines.append("🏁 最终状态 (Final State)")
            lines.append("=" * 80)
            lines.append("")

            # Variables
            if 'variables' in final_state:
                lines.append(f"📊 变量 (Variables): {len(final_state['variables'])} 个")
                if final_state['variables']:
                    for key, value in final_state['variables'].items():
                        value_str = str(value)
                        if len(value_str) > 100:
                            value_str = value_str[:100] + "..."
                        lines.append(f"  - {key}: {value_str}")
                else:
                    lines.append("  (无变量)")
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

            # Effects
            if 'effects' in final_state:
                effects = final_state['effects']
                current_effects = effects.get('current', [])
                lines.append(f"⚡ 执行效果 (Effects): {len(current_effects)} 条")
                for effect_item in current_effects:
                    lines.append(f"  - {effect_item}")
                lines.append("")

            # Notebook summary
            if 'notebook' in final_state:
                notebook = final_state['notebook']
                cells = notebook.get('cells', [])
                lines.append(f"📓 Notebook 状态:")
                lines.append(f"  Cells 总数: {len(cells)}")
                lines.append(f"  执行计数: {notebook.get('execution_count', 0)}")
                lines.append("")

        lines.append("=" * 80)
        lines.append(f"日志记录时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
        lines.append("=" * 80)

        return "\n".join(lines)

    def update_log_with_final_state(
        self,
        log_file_path: str,
        final_state: Dict[str, Any]
    ) -> bool:
        """
        更新已有日志文件，添加最终状态信息

        Args:
            log_file_path: 日志文件路径
            final_state: 最终状态数据

        Returns:
            是否更新成功
        """
        try:
            from pathlib import Path
            log_path = Path(log_file_path)

            if not log_path.exists():
                print(f"⚠️  日志文件不存在: {log_file_path}")
                return False

            # 读取现有内容
            with open(log_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()

            # 移除旧的结束标记
            lines = existing_content.split('\n')
            # 找到最后的 "=" * 80 行并移除
            while lines and lines[-1].strip() == '=' * 80:
                lines.pop()
            while lines and '日志记录时间:' in lines[-1]:
                lines.pop()
            while lines and lines[-1].strip() == '=' * 80:
                lines.pop()

            # 添加最终状态
            lines.append("")
            lines.append("=" * 80)
            lines.append("🏁 最终状态 (Final State)")
            lines.append("=" * 80)
            lines.append("")

            # Variables
            if 'variables' in final_state:
                lines.append(f"📊 变量 (Variables): {len(final_state['variables'])} 个")
                if final_state['variables']:
                    for key, value in final_state['variables'].items():
                        value_str = str(value)
                        if len(value_str) > 100:
                            value_str = value_str[:100] + "..."
                        lines.append(f"  - {key}: {value_str}")
                else:
                    lines.append("  (无变量)")
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

            # Effects
            if 'effects' in final_state:
                effects = final_state['effects']
                current_effects = effects.get('current', [])
                lines.append(f"⚡ 执行效果 (Effects): {len(current_effects)} 条")
                for effect_item in current_effects:
                    lines.append(f"  - {effect_item}")
                lines.append("")

            # Notebook summary
            if 'notebook' in final_state:
                notebook = final_state['notebook']
                cells = notebook.get('cells', [])
                lines.append(f"📓 Notebook 状态:")
                lines.append(f"  Cells 总数: {len(cells)}")
                lines.append(f"  执行计数: {notebook.get('execution_count', 0)}")
                lines.append("")

            # 添加更新时间标记
            lines.append("=" * 80)
            lines.append(f"最终状态更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
            lines.append("=" * 80)

            # 写回文件
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))

            return True

        except Exception as e:
            print(f"⚠️  更新日志文件失败: {e}")
            return False


# 全局单例
_api_logger = None


def get_api_logger(log_dir: str = "api_logs") -> APICallLogger:
    """获取全局 API 日志记录器单例"""
    global _api_logger
    if _api_logger is None:
        _api_logger = APICallLogger(log_dir)
    return _api_logger
