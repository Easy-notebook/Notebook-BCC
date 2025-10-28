"""
完整的 Stores 模块测试
测试所有 stores 的核心功能、可扩展性和错误处理
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import unittest
from typing import Any
from models.action import ExecutionStep, ActionMetadata, ScriptAction
from models.cell import CellType
from stores.script_store import ScriptStore, ActionRegistry
from stores.ai_context_store import AIPlanningContextStore
from stores.notebook_store import NotebookStore
from stores.pipeline_store import PipelineStore


class TestScriptStore(unittest.TestCase):
    """测试 ScriptStore 核心功能"""

    def setUp(self):
        """每个测试前的设置"""
        self.store = ScriptStore()
        self.notebook_store = NotebookStore()
        self.ai_context_store = AIPlanningContextStore()

    def test_01_instance_creation(self):
        """测试实例创建"""
        self.assertIsNotNone(self.store)
        self.assertIsInstance(self.store, ScriptStore)
        self.assertEqual(len(self.store.actions), 0)

    def test_02_registered_actions(self):
        """测试默认注册的 actions"""
        actions = ScriptStore.list_registered_actions()
        self.assertGreaterEqual(len(actions), 12, "应该至少注册 12 个 actions")

        # 验证关键 actions 存在
        required_actions = ['add', 'exec', 'new_chapter', 'new_section',
                           'is_thinking', 'finish_thinking', 'update_title']
        for action in required_actions:
            self.assertTrue(
                ScriptStore.has_handler(action),
                f"缺少必需的 action handler: {action}"
            )

    def test_03_action_creation(self):
        """测试 action 创建"""
        action = self.store.create_new_action(
            action_type='text',
            content='Test content',
            action_id='test-action-1'
        )
        self.assertEqual(action.id, 'test-action-1')
        self.assertEqual(action.type, 'text')
        self.assertEqual(action.content, 'Test content')

    def test_04_add_action(self):
        """测试添加 action"""
        action = ScriptAction(
            id='test-action-2',
            type='code',
            content='print("Hello")',
            metadata=ActionMetadata()
        )

        action_id = self.store.add_action(action, add_to_notebook=False)
        self.assertEqual(action_id, 'test-action-2')
        self.assertEqual(len(self.store.actions), 1)
        self.assertEqual(self.store.last_added_action_id, 'test-action-2')

    def test_05_content_cleaning(self):
        """测试内容清理功能"""
        # 导入新的 clean_content 函数
        from stores.handlers.content_handlers import clean_content

        # 测试移除前缀
        content = "Add text to the notebook: Hello World"
        cleaned = clean_content(content, 'text')
        self.assertEqual(cleaned, "Hello World")

        # 测试代码块清理
        code_content = "```python\nprint('test')\n```"
        cleaned_code = clean_content(code_content, 'code')
        self.assertEqual(cleaned_code, "print('test')")

    def test_06_handle_add_action(self):
        """测试 ADD_ACTION handler"""
        from stores.handlers.content_handlers import handle_add_action

        step = ExecutionStep(
            action='add',
            shot_type='observation',
            content='Test observation',
            store_id='obs-1',
            metadata=ActionMetadata()
        )

        result = handle_add_action(self.store, step)
        self.assertIsNotNone(result)
        self.assertEqual(len(self.store.actions), 1)

    def test_07_handle_new_chapter(self):
        """测试 NEW_CHAPTER handler"""
        from stores.handlers.content_handlers import handle_new_chapter

        step = ExecutionStep(
            action='new_chapter',
            content='Chapter 1: Introduction',
            metadata=ActionMetadata()
        )

        result = handle_new_chapter(self.store, step)
        self.assertIsNotNone(result)
        self.assertEqual(len(self.store.actions), 1)
        self.assertTrue(self.store.actions[0].content.startswith('##'))

    def test_08_handle_new_section(self):
        """测试 NEW_SECTION handler"""
        from stores.handlers.content_handlers import handle_new_section

        step = ExecutionStep(
            action='new_section',
            content='Section 1.1',
            metadata=ActionMetadata()
        )

        result = handle_new_section(self.store, step)
        self.assertIsNotNone(result)
        self.assertEqual(len(self.store.actions), 1)
        self.assertTrue(self.store.actions[0].content.startswith('###'))


class TestScriptStoreExtensibility(unittest.TestCase):
    """测试 ScriptStore 可扩展性功能"""

    def setUp(self):
        """每个测试前的设置"""
        self.store = ScriptStore()

    def test_01_register_custom_action(self):
        """测试注册自定义 action"""
        def custom_handler(step: ExecutionStep) -> str:
            return f"Custom: {step.content}"

        # 注册前不存在
        self.assertFalse(ScriptStore.has_handler('custom_test'))

        # 注册
        ScriptStore.register_custom_action('custom_test', custom_handler)

        # 注册后存在
        self.assertTrue(ScriptStore.has_handler('custom_test'))

    def test_02_custom_action_execution(self):
        """测试执行自定义 action"""
        call_count = []

        def counting_handler(step: ExecutionStep) -> int:
            call_count.append(1)
            return len(call_count)

        ScriptStore.register_custom_action('counting_action', counting_handler)

        step = ExecutionStep(
            action='counting_action',
            content='test'
        )

        result = self.store.exec_action(step)
        self.assertEqual(result, 1)
        self.assertEqual(len(call_count), 1)

    def test_03_pre_hook_execution(self):
        """测试前置钩子执行"""
        hook_calls = []

        def pre_hook(step: ExecutionStep):
            hook_calls.append(('pre', step.action))

        ScriptStore.add_execution_hook('pre', pre_hook)

        step = ExecutionStep(
            action='add',
            shot_type='observation',
            content='Test',
            metadata=ActionMetadata()
        )

        self.store.exec_action(step)
        self.assertEqual(len(hook_calls), 1)
        self.assertEqual(hook_calls[0], ('pre', 'add'))

    def test_04_post_hook_execution(self):
        """测试后置钩子执行"""
        hook_calls = []

        def post_hook(step: ExecutionStep, result: Any):
            hook_calls.append(('post', step.action, result))

        ScriptStore.add_execution_hook('post', post_hook)

        step = ExecutionStep(
            action='add',
            shot_type='observation',
            content='Test',
            metadata=ActionMetadata()
        )

        self.store.exec_action(step)
        self.assertEqual(len(hook_calls), 1)
        self.assertEqual(hook_calls[0][0], 'post')
        self.assertEqual(hook_calls[0][1], 'add')

    def test_05_hook_failure_resilience(self):
        """测试钩子失败时的容错性"""
        def failing_pre_hook(step: ExecutionStep):
            raise RuntimeError("Hook failed!")

        ScriptStore.add_execution_hook('pre', failing_pre_hook)

        step = ExecutionStep(
            action='add',
            shot_type='observation',
            content='Test',
            metadata=ActionMetadata()
        )

        # 钩子失败不应该影响主流程
        result = self.store.exec_action(step)
        self.assertIsNotNone(result)


class TestScriptStoreErrorHandling(unittest.TestCase):
    """测试 ScriptStore 错误处理"""

    def setUp(self):
        """每个测试前的设置"""
        self.store = ScriptStore()

    def test_01_invalid_hook_type(self):
        """测试无效的钩子类型"""
        with self.assertRaises(ValueError) as ctx:
            ScriptStore.add_execution_hook('invalid', lambda x: None)

        self.assertIn("Must be 'pre' or 'post'", str(ctx.exception))

    def test_02_non_callable_hook(self):
        """测试非可调用的钩子"""
        with self.assertRaises(ValueError) as ctx:
            ScriptStore.add_execution_hook('pre', "not callable")

        self.assertIn("must be callable", str(ctx.exception))

    def test_03_empty_action_type(self):
        """测试空的 action 类型"""
        with self.assertRaises(ValueError):
            ScriptStore.register_custom_action('', lambda x: None)

    def test_04_non_callable_handler(self):
        """测试非可调用的 handler"""
        with self.assertRaises(ValueError):
            ScriptStore.register_custom_action('test', "not callable")

    def test_05_missing_required_fields(self):
        """测试缺少必需字段"""
        from stores.handlers.content_handlers import handle_new_chapter

        # NEW_CHAPTER 缺少 content
        step = ExecutionStep(
            action='new_chapter',
            content=None
        )
        result = handle_new_chapter(self.store, step)
        self.assertIsNone(result, "缺少必需字段应该返回 None")

    def test_06_exec_code_without_cell_id(self):
        """测试执行代码但没有 cell_id"""
        from stores.handlers.code_handlers import handle_exec_code

        step = ExecutionStep(
            action='exec',
            codecell_id=None
        )
        result = handle_exec_code(self.store, step)
        self.assertIsNone(result, "没有 cell_id 应该返回 None")


class TestNotebookStore(unittest.TestCase):
    """测试 NotebookStore"""

    def setUp(self):
        """每个测试前的设置"""
        self.store = NotebookStore()

    def test_01_add_cell(self):
        """测试添加 cell"""
        cell_data = {
            'id': 'cell-1',
            'type': 'markdown',
            'content': 'Test cell'
        }
        cell = self.store.add_cell(cell_data)
        self.assertEqual(cell.id, 'cell-1')
        self.assertEqual(len(self.store.cells), 1)

    def test_02_get_cell(self):
        """测试获取 cell"""
        cell_data = {'id': 'cell-2', 'type': 'code', 'content': 'print(1)'}
        self.store.add_cell(cell_data)

        cell = self.store.get_cell('cell-2')
        self.assertIsNotNone(cell)
        self.assertEqual(cell.content, 'print(1)')

    def test_03_update_cell(self):
        """测试更新 cell"""
        cell_data = {'id': 'cell-3', 'type': 'markdown', 'content': 'Old'}
        self.store.add_cell(cell_data)

        success = self.store.update_cell('cell-3', 'New content')
        self.assertTrue(success)

        cell = self.store.get_cell('cell-3')
        self.assertEqual(cell.content, 'New content')

    def test_04_delete_cell(self):
        """测试删除 cell"""
        cell_data = {'id': 'cell-4', 'type': 'markdown', 'content': 'Delete me'}
        self.store.add_cell(cell_data)

        success = self.store.delete_cell('cell-4')
        self.assertTrue(success)
        self.assertIsNone(self.store.get_cell('cell-4'))

    def test_05_get_cells_by_type(self):
        """测试按类型获取 cells"""
        self.store.add_cell({'id': 'c1', 'type': 'markdown', 'content': 'M1'})
        self.store.add_cell({'id': 'c2', 'type': 'code', 'content': 'C1'})
        self.store.add_cell({'id': 'c3', 'type': 'markdown', 'content': 'M2'})

        markdown_cells = self.store.get_cells_by_type(CellType.MARKDOWN)
        self.assertEqual(len(markdown_cells), 2)


class TestAIContext(unittest.TestCase):
    """测试 AIPlanningContextStore"""

    def setUp(self):
        """每个测试前的设置"""
        self.store = AIPlanningContextStore()

    def test_01_variables(self):
        """测试变量管理"""
        self.store.add_variable('test', 'value')
        self.assertEqual(self.store.get_variable('test'), 'value')

    def test_02_todo_list(self):
        """测试 TODO 列表"""
        self.store.add_to_do_list("Task 1")
        self.store.add_to_do_list("Task 2")
        context = self.store.get_context()
        self.assertEqual(len(context.to_do_list), 2)

    def test_03_effect_management(self):
        """测试 effect 管理"""
        self.store.add_effect("Effect 1")
        context = self.store.get_context()
        self.assertEqual(len(context.effect['current']), 1)

        self.store.reset_effect()
        context = self.store.get_context()
        self.assertEqual(len(context.effect['current']), 0)

    def test_04_custom_context(self):
        """测试自定义上下文"""
        custom = {'key1': 'value1', 'key2': 'value2'}
        self.store.set_custom_context(custom)
        retrieved = self.store.get_custom_context()
        self.assertEqual(retrieved['key1'], 'value1')


class TestPipelineStore(unittest.TestCase):
    """测试 PipelineStore"""

    def setUp(self):
        """每个测试前的设置"""
        self.store = PipelineStore()

    def test_01_workflow_active_state(self):
        """测试工作流激活状态"""
        self.assertFalse(self.store.is_active())

        self.store.set_workflow_active(True)
        self.assertTrue(self.store.is_active())

        self.store.set_workflow_active(False)
        self.assertFalse(self.store.is_active())

    def test_02_initialize_workflow(self):
        """测试初始化工作流"""
        planning_request = {
            'problem': 'Test problem',
            'context': 'Test context'
        }

        template = self.store.initialize_workflow(planning_request)
        self.assertIsNotNone(template)
        self.assertIsNotNone(self.store.workflow_template)
        self.assertEqual(template.name, "Data Science Lifecycle (DCLS) Analysis")

    def test_03_reset(self):
        """测试重置"""
        planning_request = {'problem': 'Test'}
        self.store.initialize_workflow(planning_request)
        self.store.set_workflow_active(True)

        self.store.reset()
        self.assertIsNone(self.store.workflow_template)
        self.assertFalse(self.store.is_active())


class TestActionRegistry(unittest.TestCase):
    """测试 ActionRegistry"""

    def setUp(self):
        """每个测试前的设置"""
        self.registry = ActionRegistry()

    def test_01_register_decorator(self):
        """测试装饰器注册"""
        @self.registry.register('test_action')
        def test_handler(step: ExecutionStep) -> str:
            return "test"

        self.assertIn('test_action', self.registry.registered_actions)
        handler = self.registry.get_handler('test_action')
        self.assertIsNotNone(handler)

    def test_02_register_handler_programmatically(self):
        """测试程序化注册"""
        def my_handler(step: ExecutionStep) -> int:
            return 42

        self.registry.register_handler('my_action', my_handler)
        self.assertIn('my_action', self.registry.registered_actions)

    def test_03_hook_management(self):
        """测试钩子管理"""
        def pre_hook(step):
            pass

        def post_hook(step, result):
            pass

        self.registry.add_pre_hook(pre_hook)
        self.registry.add_post_hook(post_hook)

        self.assertEqual(len(self.registry._pre_hooks), 1)
        self.assertEqual(len(self.registry._post_hooks), 1)


def run_test_suite():
    """运行完整测试套件"""
    print("=" * 70)
    print("Stores 模块完整测试套件")
    print("=" * 70)
    print()

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestScriptStore))
    suite.addTests(loader.loadTestsFromTestCase(TestScriptStoreExtensibility))
    suite.addTests(loader.loadTestsFromTestCase(TestScriptStoreErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestNotebookStore))
    suite.addTests(loader.loadTestsFromTestCase(TestAIContext))
    suite.addTests(loader.loadTestsFromTestCase(TestPipelineStore))
    suite.addTests(loader.loadTestsFromTestCase(TestActionRegistry))

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
    print("=" * 70)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_test_suite()
    sys.exit(0 if success else 1)
