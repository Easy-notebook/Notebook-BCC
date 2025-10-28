# Notebook-BCC 测试文档

本目录包含 Notebook-BCC 项目的完整测试套件。

## 测试文件

### test_stores.py
**完整的 Stores 模块测试套件**

涵盖以下模块的全面测试：
- `ScriptStore` - Action 执行引擎
- `ActionRegistry` - Handler 注册系统
- `NotebookStore` - Notebook cell 管理
- `AIPlanningContextStore` - AI 上下文管理
- `PipelineStore` - 工作流模板管理

#### 测试类别

1. **ScriptStore 核心功能** (8 个测试)
   - 实例创建
   - Action 注册和管理
   - 内容清理
   - Handler 执行

2. **可扩展性功能** (5 个测试)
   - 自定义 action 注册
   - Pre/Post 钩子机制
   - 钩子容错性

3. **错误处理** (6 个测试)
   - 参数验证
   - 异常处理
   - 边界条件

4. **其他 Stores** (15 个测试)
   - NotebookStore
   - AIPlanningContextStore
   - PipelineStore
   - ActionRegistry

## 运行测试

### 方式 1: 运行所有测试

```bash
python test/test_stores.py
```

输出示例:
```
======================================================================
Stores 模块完整测试套件
======================================================================

test_01_instance_creation ... ok
test_02_registered_actions ... ok
...
----------------------------------------------------------------------
Ran 34 tests in 0.011s

OK

======================================================================
测试总结
======================================================================
运行测试: 34
成功: 34
失败: 0
错误: 0
======================================================================
```

### 方式 2: 使用 unittest 运行

```bash
# 运行所有测试
python -m unittest discover test

# 运行特定测试类
python -m unittest test.test_stores.TestScriptStore

# 运行单个测试方法
python -m unittest test.test_stores.TestScriptStore.test_01_instance_creation

# 详细输出
python -m unittest test.test_stores -v
```

### 方式 3: 使用 pytest（如果已安装）

```bash
# 安装 pytest
pip install pytest

# 运行测试
pytest test/test_stores.py

# 详细输出
pytest test/test_stores.py -v

# 显示覆盖率
pytest test/test_stores.py --cov=stores
```

## 测试结果

最新测试结果请查看 [TEST_REPORT.md](./TEST_REPORT.md)

**当前状态**: ✅ 34/34 测试通过 (100%)

## 添加新测试

### 示例: 为新的 action handler 添加测试

```python
def test_09_handle_my_new_action(self):
    """测试 MY_NEW_ACTION handler"""
    step = ExecutionStep(
        action='my_new_action',
        content='Test content',
        metadata=ActionMetadata()
    )

    result = self.store._handle_my_new_action(step)

    # 验证结果
    self.assertIsNotNone(result)
    self.assertEqual(len(self.store.actions), 1)
```

### 示例: 测试自定义扩展

```python
def test_custom_extension(self):
    """测试自定义扩展功能"""
    # 注册自定义 handler
    def my_handler(step: ExecutionStep) -> str:
        return f"Processed: {step.content}"

    ScriptStore.register_custom_action('custom', my_handler)

    # 执行
    step = ExecutionStep(action='custom', content='test')
    result = self.store.exec_action(step)

    # 验证
    self.assertEqual(result, "Processed: test")
```

## 测试覆盖范围

### ScriptStore (优化后的核心模块)

✅ **核心功能**
- [x] ActionRegistry 注册机制
- [x] 12 个默认 action handlers
- [x] 内容清理和格式化
- [x] Action 执行流程

✅ **可扩展性**
- [x] 自定义 action 注册
- [x] Pre/Post 钩子系统
- [x] 外部扩展 API
- [x] 钩子失败容错

✅ **错误处理**
- [x] 参数验证（ValueError）
- [x] 必需字段检查
- [x] 边界条件处理
- [x] 异常日志记录

### 其他 Stores

✅ **NotebookStore**
- [x] Cell CRUD 操作
- [x] 按类型查询
- [x] Metadata 管理

✅ **AIPlanningContextStore**
- [x] 变量管理
- [x] TODO 列表
- [x] Effect 管理
- [x] 自定义上下文

✅ **PipelineStore**
- [x] 工作流激活状态
- [x] 模板初始化
- [x] 重置功能

## 持续集成

### GitHub Actions 配置示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11

    - name: Install dependencies
      run: |
        pip install -r requirements.txt

    - name: Run tests
      run: |
        python test/test_stores.py
```

## 性能基准

当前性能指标:
- **总测试时间**: ~0.011s
- **平均每个测试**: ~0.32ms
- **最慢的测试**: < 1ms

## 调试失败的测试

### 详细输出

```bash
python test/test_stores.py -v
```

### 只运行失败的测试

```bash
# 使用 pytest
pytest test/test_stores.py --lf  # last-failed
```

### 调试单个测试

```python
# 在测试方法中添加
import pdb; pdb.set_trace()
```

## 贡献指南

添加新测试时请遵循:

1. **命名规范**: `test_XX_description` (XX 为序号)
2. **文档字符串**: 每个测试添加清晰的描述
3. **断言**: 使用明确的断言消息
4. **清理**: setUp 和 tearDown 确保测试隔离
5. **覆盖**: 测试正常路径和边界情况

## 问题报告

如果测试失败，请提供:
- 完整的错误输出
- 运行环境（Python 版本、OS）
- 重现步骤

## 相关文档

- [架构文档](../docs/ARCHITECTURE_OPTIMIZATION.md)
- [最终设计](../docs/FINAL_DESIGN.md)
- [测试报告](./TEST_REPORT.md)

---

**最后更新**: 2025-10-28
**测试覆盖率**: 100% (34/34 通过)
**维护者**: Notebook-BCC Team
