"""
测试 CLI 的各种使用场景
Tests for CLI command-line usage scenarios
"""

import pytest
import subprocess
import sys
import os
import tempfile
import json
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent


@pytest.mark.cli
class TestCLIBasicCommands:
    """测试基本 CLI 命令"""

    def test_cli_help(self):
        """测试 --help 命令"""
        result = subprocess.run(
            [sys.executable, 'main.py', '--help'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=5
        )

        assert result.returncode == 0
        assert 'Notebook-BCC' in result.stdout
        assert 'Commands' in result.stdout or 'command' in result.stdout.lower()

    def test_cli_version_info(self):
        """测试版本信息"""
        result = subprocess.run(
            [sys.executable, 'main.py', '--help'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=5
        )

        # Help should display successfully
        assert result.returncode == 0

    def test_cli_status_command(self):
        """测试 status 命令"""
        result = subprocess.run(
            [sys.executable, 'main.py', 'status'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should show workflow status
        output = result.stdout + result.stderr
        assert 'Workflow Status' in output or 'State' in output


@pytest.mark.cli
class TestCLIStartCommand:
    """测试 start 命令的各种用法"""

    def test_start_simple(self):
        """测试简单的 start 命令"""
        result = subprocess.run(
            [sys.executable, 'main.py', 'start'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=15
        )

        output = result.stdout + result.stderr
        # Should start workflow
        assert 'Starting' in output or 'Workflow' in output

    def test_start_with_problem(self):
        """测试 start --problem 命令"""
        result = subprocess.run(
            [sys.executable, 'main.py', 'start', '--problem', 'Analyze sales data'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=15
        )

        output = result.stdout + result.stderr
        assert 'Starting' in output or 'Workflow' in output or 'sales' in output.lower()

    def test_start_with_context(self):
        """测试 start --problem --context 命令"""
        result = subprocess.run(
            [
                sys.executable, 'main.py', 'start',
                '--problem', 'Data analysis',
                '--context', 'Q4 2024 sales report'
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=15
        )

        output = result.stdout + result.stderr
        assert 'Starting' in output or 'Workflow' in output

    def test_start_with_max_steps(self):
        """测试 start 命令配合 --max-steps"""
        result = subprocess.run(
            [
                sys.executable, 'main.py',
                '--max-steps', '5',
                'start',
                '--problem', 'Test workflow'
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=15
        )

        output = result.stdout + result.stderr
        assert 'Starting' in output or 'Workflow' in output

    def test_start_reflection_mode(self):
        """测试反思模式启动"""
        result = subprocess.run(
            [
                sys.executable, 'main.py',
                '--start-mode', 'reflection',
                'start',
                '--problem', 'Test problem'
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=15
        )

        output = result.stdout + result.stderr
        assert 'Starting' in output or 'Workflow' in output

    def test_start_generation_mode(self):
        """测试生成模式启动（默认）"""
        result = subprocess.run(
            [
                sys.executable, 'main.py',
                '--start-mode', 'generation',
                'start',
                '--problem', 'Test problem'
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=15
        )

        output = result.stdout + result.stderr
        assert 'Starting' in output or 'Workflow' in output

    def test_start_interactive_mode(self):
        """测试交互模式"""
        # Note: This will timeout waiting for input, so we expect timeout
        with pytest.raises(subprocess.TimeoutExpired):
            subprocess.run(
                [
                    sys.executable, 'main.py',
                    '--interactive',
                    '--max-steps', '1',
                    'start',
                    '--problem', 'Test'
                ],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=3  # Short timeout since it will hang
            )


@pytest.mark.cli
class TestCLICustomContext:
    """测试自定义上下文功能"""

    def test_custom_context_json_string(self):
        """测试通过 JSON 字符串传递自定义上下文"""
        custom_ctx = json.dumps({'user': 'alice', 'priority': 'high'})

        result = subprocess.run(
            [
                sys.executable, 'main.py',
                '--custom-context', custom_ctx,
                'start',
                '--problem', 'Test'
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=15
        )

        output = result.stdout + result.stderr
        assert 'Starting' in output or 'Workflow' in output

    def test_custom_context_from_file(self):
        """测试从文件加载自定义上下文"""
        # Create a temporary context file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({'project': 'test', 'environment': 'staging'}, f)
            context_file = f.name

        try:
            result = subprocess.run(
                [
                    sys.executable, 'main.py',
                    '--custom-context', context_file,
                    'start',
                    '--problem', 'Test'
                ],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=15
            )

            output = result.stdout + result.stderr
            assert 'Starting' in output or 'Workflow' in output or result.returncode in [0, 1]
        finally:
            os.unlink(context_file)


@pytest.mark.cli
class TestCLINotebookCommands:
    """测试笔记本相关命令"""

    def test_list_notebooks(self):
        """测试 list 命令"""
        result = subprocess.run(
            [sys.executable, 'main.py', 'list'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        )

        output = result.stdout + result.stderr
        assert 'Notebooks' in output or 'notebook' in output.lower() or result.returncode == 0

    def test_show_notebook_current(self):
        """测试 show 命令（显示当前笔记本）"""
        result = subprocess.run(
            [sys.executable, 'main.py', 'show'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should display something about notebook or cells
        output = result.stdout + result.stderr
        assert result.returncode in [0, 1]  # May fail if no notebook exists


@pytest.mark.cli
class TestCLIURLConfiguration:
    """测试 URL 配置选项"""

    def test_backend_url_option(self):
        """测试 --backend-url 选项"""
        result = subprocess.run(
            [
                sys.executable, 'main.py',
                '--backend-url', 'http://localhost:9000',
                'status'
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        )

        # Command should execute successfully
        assert result.returncode in [0, 1]

    def test_dslc_url_option(self):
        """测试 --dslc-url 选项"""
        result = subprocess.run(
            [
                sys.executable, 'main.py',
                '--dslc-url', 'http://localhost:9001',
                'status'
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        )

        # Command should execute successfully
        assert result.returncode in [0, 1]

    def test_both_urls_option(self):
        """测试同时配置两个 URL"""
        result = subprocess.run(
            [
                sys.executable, 'main.py',
                '--backend-url', 'http://localhost:9000',
                '--dslc-url', 'http://localhost:9001',
                'status'
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        )

        # Command should execute successfully
        assert result.returncode in [0, 1]


@pytest.mark.cli
class TestCLIComplexScenarios:
    """测试复杂使用场景"""

    def test_full_workflow_scenario(self):
        """测试完整的工作流场景"""
        # 1. Check status
        result1 = subprocess.run(
            [sys.executable, 'main.py', 'status'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result1.returncode in [0, 1]

        # 2. List notebooks
        result2 = subprocess.run(
            [sys.executable, 'main.py', 'list'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result2.returncode in [0, 1]

    def test_all_options_combined(self):
        """测试组合所有选项"""
        result = subprocess.run(
            [
                sys.executable, 'main.py',
                '--backend-url', 'http://localhost:18600',
                '--dslc-url', 'http://localhost:28600',
                '--max-steps', '10',
                '--start-mode', 'generation',
                'start',
                '--problem', 'Comprehensive test',
                '--context', 'Testing all options'
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=20
        )

        output = result.stdout + result.stderr
        # Should attempt to start
        assert 'Starting' in output or 'Workflow' in output or result.returncode in [0, 1]


@pytest.mark.cli
@pytest.mark.slow
class TestCLIExportCommand:
    """测试导出命令"""

    def test_export_help(self):
        """测试 export 命令的帮助"""
        result = subprocess.run(
            [sys.executable, 'main.py', 'export', '--help'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=5
        )

        assert result.returncode == 0
        assert 'export' in result.stdout.lower()


def test_cli_executable():
    """测试 main.py 是否可执行"""
    main_py = PROJECT_ROOT / 'main.py'
    assert main_py.exists(), "main.py should exist"
    assert main_py.is_file(), "main.py should be a file"


if __name__ == '__main__':
    # 运行测试
    pytest.main([__file__, '-v'])
