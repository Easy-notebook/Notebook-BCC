"""
测试 Notebook Cell 更新追踪功能
验证 isUpdate 标记是否正确标注在 context_notebook 中
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import unittest
from stores.notebook_store import NotebookStore
from models.cell import CellOutput


class TestCellUpdateTracking(unittest.TestCase):
    """测试 Cell 更新追踪功能"""

    def setUp(self):
        """每个测试前的设置"""
        self.store = NotebookStore()

    def test_01_new_cell_marked_as_updated(self):
        """测试新添加的 cell 被标记为 updated"""
        # 添加一个新 cell
        cell_data = {
            'id': 'cell-1',
            'type': 'markdown',
            'content': 'Test cell'
        }
        self.store.add_cell(cell_data)

        # 验证 isUpdate 标记
        notebook_dict = self.store.to_dict(include_update_status=True)
        self.assertEqual(len(notebook_dict['cells']), 1)
        self.assertTrue(notebook_dict['cells'][0]['isUpdate'])

    def test_02_update_cell_content_marks_as_updated(self):
        """测试更新 cell 内容会标记为 updated"""
        # 添加 cell
        cell_data = {'id': 'cell-2', 'type': 'markdown', 'content': 'Original'}
        self.store.add_cell(cell_data)

        # 清除更新追踪
        self.store.clear_update_tracking()

        # 更新内容
        self.store.update_cell('cell-2', 'Updated content')

        # 验证标记
        notebook_dict = self.store.to_dict(include_update_status=True)
        self.assertTrue(notebook_dict['cells'][0]['isUpdate'])

    def test_03_no_change_no_update_mark(self):
        """测试内容不变时不标记为 updated"""
        # 添加 cell
        cell_data = {'id': 'cell-3', 'type': 'markdown', 'content': 'Same content'}
        self.store.add_cell(cell_data)

        # 清除更新追踪
        self.store.clear_update_tracking()

        # "更新"为相同内容
        self.store.update_cell('cell-3', 'Same content')

        # 验证没有被标记
        notebook_dict = self.store.to_dict(include_update_status=True)
        self.assertFalse(notebook_dict['cells'][0]['isUpdate'])

    def test_04_add_output_marks_as_updated(self):
        """测试添加 output 会标记为 updated"""
        # 添加代码 cell
        cell_data = {'id': 'cell-4', 'type': 'code', 'content': 'print(1)'}
        self.store.add_cell(cell_data)

        # 清除更新追踪
        self.store.clear_update_tracking()

        # 添加 output
        output = CellOutput(output_type='stream', content='1\n')
        self.store.add_cell_output('cell-4', output)

        # 验证标记
        notebook_dict = self.store.to_dict(include_update_status=True)
        self.assertTrue(notebook_dict['cells'][0]['isUpdate'])

    def test_05_update_metadata_marks_as_updated(self):
        """测试更新 metadata 会标记为 updated"""
        # 添加 cell
        cell_data = {'id': 'cell-5', 'type': 'code', 'content': 'x = 1'}
        self.store.add_cell(cell_data)

        # 清除更新追踪
        self.store.clear_update_tracking()

        # 更新 metadata
        self.store.update_cell_metadata('cell-5', {'custom_key': 'value'})

        # 验证标记
        notebook_dict = self.store.to_dict(include_update_status=True)
        self.assertTrue(notebook_dict['cells'][0]['isUpdate'])

    def test_06_clear_tracking_resets_flags(self):
        """测试清除追踪会重置所有标记"""
        # 添加多个 cells
        for i in range(3):
            cell_data = {
                'id': f'cell-{i}',
                'type': 'markdown',
                'content': f'Cell {i}'
            }
            self.store.add_cell(cell_data)

        # 所有 cells 都应该被标记为 updated
        notebook_dict = self.store.to_dict(include_update_status=True)
        for cell in notebook_dict['cells']:
            self.assertTrue(cell['isUpdate'])

        # 清除追踪
        self.store.clear_update_tracking()

        # 所有 cells 都不应该被标记
        notebook_dict = self.store.to_dict(include_update_status=True)
        for cell in notebook_dict['cells']:
            self.assertFalse(cell['isUpdate'])

    def test_07_multiple_cells_selective_update(self):
        """测试多个 cells 中只有部分被更新"""
        # 添加 3 个 cells
        for i in range(3):
            cell_data = {
                'id': f'cell-{i}',
                'type': 'markdown',
                'content': f'Cell {i}'
            }
            self.store.add_cell(cell_data)

        # 清除追踪
        self.store.clear_update_tracking()

        # 只更新中间的 cell
        self.store.update_cell('cell-1', 'Updated cell 1')

        # 验证
        notebook_dict = self.store.to_dict(include_update_status=True)
        self.assertFalse(notebook_dict['cells'][0]['isUpdate'])  # cell-0
        self.assertTrue(notebook_dict['cells'][1]['isUpdate'])   # cell-1 (updated)
        self.assertFalse(notebook_dict['cells'][2]['isUpdate'])  # cell-2

    def test_08_clear_outputs_marks_as_updated(self):
        """测试清除 outputs 会标记为 updated（如果有 outputs）"""
        # 添加代码 cell 并添加 output
        cell_data = {'id': 'cell-8', 'type': 'code', 'content': 'print(1)'}
        self.store.add_cell(cell_data)

        output = CellOutput(output_type='stream', content='1\n')
        self.store.add_cell_output('cell-8', output)

        # 清除追踪
        self.store.clear_update_tracking()

        # 清除 outputs
        self.store.clear_cell_outputs('cell-8')

        # 验证标记（因为之前有 outputs，清除后应该标记为 updated）
        notebook_dict = self.store.to_dict(include_update_status=True)
        self.assertTrue(notebook_dict['cells'][0]['isUpdate'])

    def test_09_clear_empty_outputs_no_update(self):
        """测试清除空 outputs 不标记为 updated"""
        # 添加代码 cell（没有 output）
        cell_data = {'id': 'cell-9', 'type': 'code', 'content': 'x = 1'}
        self.store.add_cell(cell_data)

        # 清除追踪
        self.store.clear_update_tracking()

        # 清除 outputs（本来就没有）
        self.store.clear_cell_outputs('cell-9')

        # 验证没有被标记
        notebook_dict = self.store.to_dict(include_update_status=True)
        self.assertFalse(notebook_dict['cells'][0]['isUpdate'])

    def test_10_get_updated_cell_ids(self):
        """测试获取已更新的 cell IDs 列表"""
        # 添加 3 个 cells
        for i in range(3):
            cell_data = {'id': f'cell-{i}', 'type': 'markdown', 'content': f'Cell {i}'}
            self.store.add_cell(cell_data)

        # 清除追踪
        self.store.clear_update_tracking()

        # 更新两个 cells
        self.store.update_cell('cell-0', 'Updated 0')
        self.store.update_cell('cell-2', 'Updated 2')

        # 获取更新的 cell IDs
        updated_ids = self.store.get_updated_cell_ids()

        # 验证
        self.assertEqual(len(updated_ids), 2)
        self.assertIn('cell-0', updated_ids)
        self.assertIn('cell-2', updated_ids)
        self.assertNotIn('cell-1', updated_ids)

    def test_11_to_dict_without_update_status(self):
        """测试不包含 update status 的 to_dict"""
        # 添加并更新 cell
        cell_data = {'id': 'cell-11', 'type': 'markdown', 'content': 'Test'}
        self.store.add_cell(cell_data)

        # 不包含 update status
        notebook_dict = self.store.to_dict(include_update_status=False)

        # 验证 isUpdate 字段不存在
        self.assertNotIn('isUpdate', notebook_dict['cells'][0])

    def test_12_workflow_simulation(self):
        """模拟完整的工作流：添加、更新、发送 API、清除追踪"""
        # 步骤 1: 添加初始 cells
        for i in range(3):
            cell_data = {'id': f'cell-{i}', 'type': 'markdown', 'content': f'Cell {i}'}
            self.store.add_cell(cell_data)

        # 步骤 2: 获取 context（应该所有 cells 都标记为 updated）
        context1 = self.store.to_dict(include_update_status=True)
        self.assertTrue(all(cell['isUpdate'] for cell in context1['cells']))

        # 步骤 3: 模拟发送到 API 后清除追踪
        self.store.clear_update_tracking()

        # 步骤 4: 下一轮，只更新一个 cell
        self.store.update_cell('cell-1', 'Modified cell 1')

        # 步骤 5: 获取新的 context（只有 cell-1 应该标记为 updated）
        context2 = self.store.to_dict(include_update_status=True)
        self.assertFalse(context2['cells'][0]['isUpdate'])  # cell-0
        self.assertTrue(context2['cells'][1]['isUpdate'])   # cell-1 (updated)
        self.assertFalse(context2['cells'][2]['isUpdate'])  # cell-2


def run_test_suite():
    """运行测试套件"""
    print("=" * 70)
    print("Cell 更新追踪测试套件")
    print("=" * 70)
    print()

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestCellUpdateTracking))

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
        print("✅ Cell 更新追踪功能正常！")
        print("   - isUpdate 标记正确添加")
        print("   - 更新检测准确")
        print("   - 清除追踪功能正常")
        print("   - 工作流集成正确")
    else:
        print()
        print("❌ 发现问题，请检查失败的测试")

    print("=" * 70)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_test_suite()
    sys.exit(0 if success else 1)
