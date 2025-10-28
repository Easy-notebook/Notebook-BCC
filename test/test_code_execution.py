"""
测试代码执行 action 是否正确更新上下文
验证代码执行的完整流程：cell outputs 和 AI context effect
"""

import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import unittest
from models.action import ExecutionStep, ActionMetadata, ScriptAction
from models.cell import CellOutput
from stores.script_store import ScriptStore
from stores.notebook_store import NotebookStore
from stores.ai_context_store import AIPlanningContextStore


class MockCodeExecutor:
    """模拟代码执行器"""

    def __init__(self, mock_result=None):
        self.executed_cells = []
        self.mock_result = mock_result or {
            'success': True,
            'outputs': [
                CellOutput(
                    output_type='stream',
                    content='Hello from code execution!\n',
                    text='Hello from code execution!\n'
                )
            ]
        }

    def execute(self, code: str, cell_id: str = None):
        """模拟代码执行"""
        self.executed_cells.append({
            'code': code,
            'cell_id': cell_id
        })
        return self.mock_result


class TestCodeExecutionContext(unittest.TestCase):
    """测试代码执行对上下文的更新"""

    def setUp(self):
        """每个测试前的设置"""
        self.notebook_store = NotebookStore()
        self.ai_context_store = AIPlanningContextStore()
        self.code_executor = MockCodeExecutor()

        self.script_store = ScriptStore(
            notebook_store=self.notebook_store,
            ai_context_store=self.ai_context_store,
            code_executor=self.code_executor
        )

    def test_01_exec_code_updates_cell_outputs(self):
        """测试代码执行是否更新 cell outputs"""
        # 1. 创建一个代码 cell
        action = ScriptAction(
            id='code-cell-1',
            type='code',
            content='print("Hello World")',
            metadata=ActionMetadata()
        )
        self.script_store.add_action(action, add_to_notebook=True)

        # 2. 执行代码
        step = ExecutionStep(
            action='exec',
            codecell_id='code-cell-1',
            need_output=True,
            auto_debug=False
        )

        result = self.script_store.exec_action(step)

        # 3. 验证代码执行器被调用
        self.assertEqual(len(self.code_executor.executed_cells), 1)
        self.assertEqual(
            self.code_executor.executed_cells[0]['cell_id'],
            'code-cell-1'
        )

        # 4. 验证 cell 的 outputs 被更新
        cell = self.notebook_store.get_cell('code-cell-1')
        self.assertIsNotNone(cell)
        self.assertEqual(len(cell.outputs), 1)
        self.assertIn('Hello from code execution', cell.outputs[0].content)

    def test_02_exec_code_updates_ai_context_effect(self):
        """测试代码执行是否更新 AI context 的 effect"""
        # 1. 创建代码 cell
        action = ScriptAction(
            id='code-cell-2',
            type='code',
            content='x = 1 + 1\nprint(x)',
            metadata=ActionMetadata()
        )
        self.script_store.add_action(action, add_to_notebook=True)

        # 2. 检查初始 effect
        context_before = self.ai_context_store.get_context()
        effect_count_before = len(context_before.effect['current'])

        # 3. 执行代码
        step = ExecutionStep(
            action='exec',
            codecell_id='code-cell-2'
        )
        self.script_store.exec_action(step)

        # 4. 验证 effect 被更新
        context_after = self.ai_context_store.get_context()
        effect_count_after = len(context_after.effect['current'])

        self.assertGreater(effect_count_after, effect_count_before)
        self.assertIn(
            'Hello from code execution',
            context_after.effect['current'][-1]
        )

    def test_03_exec_code_with_multiple_outputs(self):
        """测试代码执行产生多个输出"""
        # 1. 设置多个输出的模拟结果
        multi_output_result = {
            'success': True,
            'outputs': [
                CellOutput(
                    output_type='stream',
                    content='Output 1\n',
                    text='Output 1\n'
                ),
                CellOutput(
                    output_type='stream',
                    content='Output 2\n',
                    text='Output 2\n'
                ),
                CellOutput(
                    output_type='execute_result',
                    content='42',
                    text='42'
                )
            ]
        }

        self.code_executor.mock_result = multi_output_result

        # 2. 创建并执行代码
        action = ScriptAction(
            id='code-cell-3',
            type='code',
            content='print("Output 1")\nprint("Output 2")\n42',
            metadata=ActionMetadata()
        )
        self.script_store.add_action(action, add_to_notebook=True)

        step = ExecutionStep(
            action='exec',
            codecell_id='code-cell-3'
        )
        result = self.script_store.exec_action(step)

        # 3. 验证所有 outputs 都被添加到 cell
        cell = self.notebook_store.get_cell('code-cell-3')
        self.assertEqual(len(cell.outputs), 3)

        # 4. 验证所有 outputs 都被添加到 effect
        context = self.ai_context_store.get_context()
        effects = context.effect['current']

        # 应该有 3 个新的 effects
        self.assertGreaterEqual(len(effects), 3)

    def test_04_exec_code_with_error(self):
        """测试代码执行失败的情况"""
        # 1. 设置错误结果
        error_result = {
            'success': False,
            'error': 'NameError: name "undefined_var" is not defined',
            'outputs': []
        }

        self.code_executor.mock_result = error_result

        # 2. 创建并执行代码
        action = ScriptAction(
            id='code-cell-4',
            type='code',
            content='print(undefined_var)',
            metadata=ActionMetadata()
        )
        self.script_store.add_action(action, add_to_notebook=True)

        step = ExecutionStep(
            action='exec',
            codecell_id='code-cell-4',
            auto_debug=False
        )
        result = self.script_store.exec_action(step)

        # 3. 验证返回错误信息
        self.assertIsNotNone(result)
        self.assertIn('NameError', result)

    def test_05_exec_code_with_last_added_cell_id(self):
        """测试使用 lastAddedCellId 执行代码"""
        # 1. 创建一个代码 cell（会设置 last_added_action_id）
        action = ScriptAction(
            id='code-cell-5',
            type='code',
            content='print("Last added cell")',
            metadata=ActionMetadata()
        )
        self.script_store.add_action(action, add_to_notebook=True)

        # 2. 使用 lastAddedCellId 执行
        step = ExecutionStep(
            action='exec',
            codecell_id='lastAddedCellId'
        )
        result = self.script_store.exec_action(step)

        # 3. 验证正确的 cell 被执行
        self.assertEqual(len(self.code_executor.executed_cells), 1)
        self.assertEqual(
            self.code_executor.executed_cells[0]['cell_id'],
            'code-cell-5'
        )

    def test_06_exec_action_full_workflow(self):
        """测试完整的代码执行工作流"""
        # 1. 添加一个文本 cell
        text_action = ScriptAction(
            id='text-1',
            type='text',
            content='# Code Execution Test',
            metadata=ActionMetadata()
        )
        self.script_store.add_action(text_action, add_to_notebook=True)

        # 2. 添加一个代码 cell
        code_action = ScriptAction(
            id='code-1',
            type='code',
            content='result = 2 + 2\nprint(f"Result: {result}")',
            metadata=ActionMetadata()
        )
        self.script_store.add_action(code_action, add_to_notebook=True)

        # 3. 通过 exec_action 执行（测试完整流程）
        step = ExecutionStep(
            action='exec',
            codecell_id='code-1',
            need_output=True,
            auto_debug=False
        )

        result = self.script_store.exec_action(step)

        # 4. 验证 notebook 状态
        self.assertEqual(self.notebook_store.get_cell_count(), 2)

        # 5. 验证代码 cell 的 outputs
        code_cell = self.notebook_store.get_cell('code-1')
        self.assertGreater(len(code_cell.outputs), 0)

        # 6. 验证 AI context effect
        context = self.ai_context_store.get_context()
        self.assertGreater(len(context.effect['current']), 0)

    def test_07_exec_code_clears_previous_outputs(self):
        """测试代码执行会清除之前的 outputs"""
        # 1. 创建代码 cell 并第一次执行
        action = ScriptAction(
            id='code-cell-6',
            type='code',
            content='print("First execution")',
            metadata=ActionMetadata()
        )
        self.script_store.add_action(action, add_to_notebook=True)

        step = ExecutionStep(action='exec', codecell_id='code-cell-6')
        self.script_store.exec_action(step)

        # 验证第一次执行的输出
        cell = self.notebook_store.get_cell('code-cell-6')
        first_output_count = len(cell.outputs)
        self.assertGreater(first_output_count, 0)

        # 2. 第二次执行
        self.code_executor.mock_result = {
            'success': True,
            'outputs': [
                CellOutput(
                    output_type='stream',
                    content='Second execution\n',
                    text='Second execution\n'
                )
            ]
        }

        self.script_store.exec_action(step)

        # 3. 验证旧的 outputs 被清除，只有新的 output
        cell = self.notebook_store.get_cell('code-cell-6')
        self.assertEqual(len(cell.outputs), 1)
        self.assertIn('Second execution', cell.outputs[0].content)

    def test_08_exec_code_without_executor(self):
        """测试没有代码执行器的情况"""
        # 1. 创建没有 executor 的 ScriptStore
        store_no_executor = ScriptStore(
            notebook_store=self.notebook_store,
            ai_context_store=self.ai_context_store,
            code_executor=None
        )

        # 2. 添加代码 cell
        action = ScriptAction(
            id='code-cell-7',
            type='code',
            content='print("Should not execute")',
            metadata=ActionMetadata()
        )
        store_no_executor.add_action(action, add_to_notebook=True)

        # 3. 尝试执行
        step = ExecutionStep(action='exec', codecell_id='code-cell-7')
        result = store_no_executor.exec_action(step)

        # 4. 验证返回 None（无法执行）
        self.assertIsNone(result)


class TestCodeExecutionIntegration(unittest.TestCase):
    """集成测试：测试代码执行与其他 actions 的配合"""

    def setUp(self):
        """设置"""
        self.notebook_store = NotebookStore()
        self.ai_context_store = AIPlanningContextStore()
        self.code_executor = MockCodeExecutor()

        self.script_store = ScriptStore(
            notebook_store=self.notebook_store,
            ai_context_store=self.ai_context_store,
            code_executor=self.code_executor
        )

    def test_01_add_and_exec_workflow(self):
        """测试添加代码 + 执行代码的工作流"""
        # 1. 通过 ADD_ACTION 添加代码
        add_step = ExecutionStep(
            action='add',
            shot_type='action',  # 'action' 表示代码
            content='x = 10\nprint(x)',
            store_id='test-code-1',
            metadata=ActionMetadata()
        )

        self.script_store.exec_action(add_step)

        # 2. 执行刚添加的代码
        exec_step = ExecutionStep(
            action='exec',
            codecell_id='test-code-1'
        )

        result = self.script_store.exec_action(exec_step)

        # 3. 验证整个流程
        cell = self.notebook_store.get_cell('test-code-1')
        self.assertIsNotNone(cell)
        self.assertEqual(cell.type.value, 'code')
        self.assertGreater(len(cell.outputs), 0)

        # 4. 验证 context
        context = self.ai_context_store.get_context()
        self.assertGreater(len(context.effect['current']), 0)

    def test_02_multiple_cells_execution(self):
        """测试多个 cell 的顺序执行"""
        # 1. 添加多个代码 cells
        for i in range(3):
            action = ScriptAction(
                id=f'code-{i}',
                type='code',
                content=f'print("Cell {i}")',
                metadata=ActionMetadata()
            )
            self.script_store.add_action(action, add_to_notebook=True)

        # 2. 按顺序执行
        for i in range(3):
            step = ExecutionStep(action='exec', codecell_id=f'code-{i}')
            self.script_store.exec_action(step)

        # 3. 验证所有 cells 都被执行
        self.assertEqual(len(self.code_executor.executed_cells), 3)

        # 4. 验证所有 cells 都有 outputs
        for i in range(3):
            cell = self.notebook_store.get_cell(f'code-{i}')
            self.assertGreater(len(cell.outputs), 0)


def run_test_suite():
    """运行测试套件"""
    print("=" * 70)
    print("代码执行上下文更新测试套件")
    print("=" * 70)
    print()

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestCodeExecutionContext))
    suite.addTests(loader.loadTestsFromTestCase(TestCodeExecutionIntegration))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 打印总结
    print()
    print("=" * 70)
    print("测试总结")
    print("=" * 70)
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")

    if result.wasSuccessful():
        print()
        print("✅ 代码执行正确更新了上下文！")
        print("   - Cell outputs 正确添加")
        print("   - AI context effect 正确更新")
        print("   - 多输出处理正常")
        print("   - 错误处理正确")
    else:
        print()
        print("❌ 发现问题，请检查失败的测试")

    print("=" * 70)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_test_suite()
    sys.exit(0 if success else 1)
