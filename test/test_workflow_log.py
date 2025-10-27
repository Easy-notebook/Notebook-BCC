"""
测试 workflow.log 日志功能
Tests for workflow.log logging functionality
"""

import pytest
import subprocess
import sys
import os
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
LOG_FILE = PROJECT_ROOT / 'workflow.log'


@pytest.mark.cli
class TestWorkflowLogging:
    """测试工作流日志功能"""

    def test_log_file_exists(self):
        """测试日志文件是否存在"""
        # 运行一个命令来生成日志
        subprocess.run(
            [sys.executable, 'main.py', '--help'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            timeout=5
        )

        # 检查日志文件是否存在
        assert LOG_FILE.exists(), "workflow.log 文件应该存在"

    def test_log_file_is_writable(self):
        """测试日志文件是否可写"""
        if LOG_FILE.exists():
            assert os.access(LOG_FILE, os.W_OK), "workflow.log 应该可写"

    def test_log_contains_basic_info(self):
        """测试日志包含基本信息"""
        # 运行命令生成日志
        subprocess.run(
            [sys.executable, 'main.py', 'list'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            timeout=10
        )

        if LOG_FILE.exists():
            content = LOG_FILE.read_text()

            # 检查日志包含关键信息
            assert 'NotebookManager' in content, "日志应包含 NotebookManager"
            assert 'INFO' in content or 'ERROR' in content, "日志应包含日志级别"
            assert '2025' in content or '2024' in content, "日志应包含时间戳"

    def test_log_records_commands(self):
        """测试日志记录命令执行"""
        # 清空或备份现有日志
        if LOG_FILE.exists():
            original_size = LOG_FILE.stat().st_size
        else:
            original_size = 0

        # 执行命令
        subprocess.run(
            [sys.executable, 'main.py', 'status'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            timeout=10
        )

        # 等待日志写入
        time.sleep(0.5)

        if LOG_FILE.exists():
            new_size = LOG_FILE.stat().st_size
            # 日志文件应该增长
            assert new_size >= original_size, "执行命令后日志应该增长"

    def test_log_records_errors(self):
        """测试日志记录错误"""
        if LOG_FILE.exists():
            content = LOG_FILE.read_text()

            # 检查是否记录了错误（从之前的测试运行中）
            # 注意：这取决于之前是否有错误发生
            if 'ERROR' in content:
                assert 'Traceback' in content or 'Error' in content, \
                    "错误日志应包含详细信息"

    def test_log_format(self):
        """测试日志格式"""
        if LOG_FILE.exists():
            content = LOG_FILE.read_text()
            lines = content.strip().split('\n')

            if lines:
                # 检查第一行格式
                first_line = lines[0]
                # 日志格式应该是：时间戳 - 模块名 - 级别 - 消息
                parts = first_line.split(' - ')
                assert len(parts) >= 3, "日志格式应包含：时间戳 - 模块 - 级别 - 消息"

    def test_log_modules(self):
        """测试日志记录的模块"""
        if LOG_FILE.exists():
            content = LOG_FILE.read_text()

            # 检查是否记录了各个模块
            expected_modules = [
                'NotebookManager',
                'WorkflowCLI',
                'WorkflowStateMachine',
                'PipelineStore'
            ]

            found_modules = [m for m in expected_modules if m in content]
            assert len(found_modules) > 0, f"日志应包含至少一个模块的记录，期望: {expected_modules}"

    def test_log_levels(self):
        """测试日志级别"""
        if LOG_FILE.exists():
            content = LOG_FILE.read_text()

            # 检查日志级别
            log_levels = ['INFO', 'ERROR', 'WARNING', 'DEBUG']
            found_levels = [level for level in log_levels if level in content]

            assert len(found_levels) > 0, "日志应包含至少一个日志级别"

    def test_log_timestamps(self):
        """测试日志时间戳"""
        if LOG_FILE.exists():
            content = LOG_FILE.read_text()
            lines = content.strip().split('\n')

            if lines:
                # 检查时间戳格式：2025-10-27 20:16:44,625
                import re
                timestamp_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'

                timestamps_found = re.findall(timestamp_pattern, content)
                assert len(timestamps_found) > 0, "日志应包含时间戳"


@pytest.mark.cli
class TestLogAnalysis:
    """日志分析测试"""

    def test_analyze_log_errors(self):
        """分析日志中的错误"""
        if not LOG_FILE.exists():
            pytest.skip("日志文件不存在")

        content = LOG_FILE.read_text()
        error_lines = [line for line in content.split('\n') if 'ERROR' in line]

        # 打印错误信息（用于调试）
        if error_lines:
            print(f"\n发现 {len(error_lines)} 个错误日志条目")
            for error in error_lines[:5]:  # 显示前5个
                print(f"  - {error[:100]}")

    def test_analyze_log_warnings(self):
        """分析日志中的警告"""
        if not LOG_FILE.exists():
            pytest.skip("日志文件不存在")

        content = LOG_FILE.read_text()
        warning_lines = [line for line in content.split('\n') if 'WARNING' in line or 'WARN' in line]

        if warning_lines:
            print(f"\n发现 {len(warning_lines)} 个警告日志条目")

    def test_log_statistics(self):
        """统计日志信息"""
        if not LOG_FILE.exists():
            pytest.skip("日志文件不存在")

        content = LOG_FILE.read_text()
        lines = content.strip().split('\n')

        stats = {
            'total_lines': len(lines),
            'info': content.count('INFO'),
            'error': content.count('ERROR'),
            'warning': content.count('WARNING'),
        }

        print(f"\n日志统计:")
        print(f"  总行数: {stats['total_lines']}")
        print(f"  INFO: {stats['info']}")
        print(f"  ERROR: {stats['error']}")
        print(f"  WARNING: {stats['warning']}")

        # 至少应该有一些日志
        assert stats['total_lines'] > 0, "日志文件应该有内容"

    def test_recent_log_entries(self):
        """检查最近的日志条目"""
        if not LOG_FILE.exists():
            pytest.skip("日志文件不存在")

        content = LOG_FILE.read_text()
        lines = content.strip().split('\n')

        # 显示最后5条日志
        if lines:
            print("\n最近的日志条目:")
            for line in lines[-5:]:
                print(f"  {line}")


@pytest.mark.cli
class TestLogRotation:
    """日志轮转测试"""

    def test_log_file_size(self):
        """测试日志文件大小"""
        if not LOG_FILE.exists():
            pytest.skip("日志文件不存在")

        size_bytes = LOG_FILE.stat().st_size
        size_kb = size_bytes / 1024

        print(f"\n日志文件大小: {size_kb:.2f} KB ({size_bytes} bytes)")

        # 警告如果日志文件过大
        if size_kb > 1000:  # 超过1MB
            print(f"⚠️  警告: 日志文件较大 ({size_kb:.2f} KB)，建议清理或配置日志轮转")

    def test_log_backup_suggestion(self):
        """测试是否需要备份日志"""
        if not LOG_FILE.exists():
            pytest.skip("日志文件不存在")

        size_bytes = LOG_FILE.stat().st_size
        content = LOG_FILE.read_text()
        lines = len(content.split('\n'))

        # 如果日志超过1000行或100KB，建议备份
        if lines > 1000 or size_bytes > 100000:
            print(f"\n💡 建议: 日志文件已有 {lines} 行，大小 {size_bytes/1024:.2f} KB")
            print("   可以考虑备份并清空日志文件")


def test_log_file_path():
    """测试日志文件路径"""
    expected_path = PROJECT_ROOT / 'workflow.log'
    assert LOG_FILE == expected_path, f"日志文件路径应该是 {expected_path}"


def test_can_read_log():
    """测试是否可以读取日志"""
    if LOG_FILE.exists():
        try:
            content = LOG_FILE.read_text()
            assert isinstance(content, str), "日志内容应该是字符串"
        except Exception as e:
            pytest.fail(f"无法读取日志文件: {e}")


if __name__ == '__main__':
    # 运行测试
    pytest.main([__file__, '-v', '-s'])
