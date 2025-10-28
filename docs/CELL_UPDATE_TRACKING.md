# Cell 更新追踪功能

## 概述

Notebook-BCC 现在支持在 `context_notebook` 字段中自动标注哪些 cell 发生了更新。每个 cell 会包含一个 `isUpdate` 字段，用于追踪自上次发送 API 以来该 cell 是否被修改。

## 功能特性

### ✅ 自动追踪

以下操作会自动将 cell 标记为 `isUpdate: true`:

1. **添加新 cell** - 新创建的 cell 自动标记为已更新
2. **更新 cell 内容** - 修改 cell 的 content 字段
3. **添加 cell output** - 向代码 cell 添加执行结果
4. **更新 cell metadata** - 修改 cell 的 metadata
5. **清除 cell outputs** - 清除代码 cell 的输出（如果之前有输出）

### ✅ 智能检测

- **内容比较**: 更新相同内容不会标记为已更新
- **增量追踪**: 只追踪自上次清除追踪以来的变化
- **空操作检测**: 清除本来就空的 outputs 不会标记

## 使用方法

### 1. 基本使用

```python
from stores.notebook_store import NotebookStore

# 创建 notebook store
notebook_store = NotebookStore()

# 添加 cells (自动标记为 updated)
notebook_store.add_cell({
    'id': 'cell-1',
    'type': 'markdown',
    'content': '# Introduction'
})

# 获取 notebook 数据（包含 isUpdate 标记）
notebook_data = notebook_store.to_dict(include_update_status=True)

# 检查哪些 cells 被更新了
for cell in notebook_data['cells']:
    if cell['isUpdate']:
        print(f"Cell {cell['id']} was updated")
```

### 2. 在 State Machine 中使用

在 `core/state_machine.py` 中，notebook 数据会自动包含 `isUpdate` 标记：

```python
# 发送 feedback 到 API
current_state = self.ai_context_store.get_context().to_dict()

# 添加 notebook 数据（自动包含 isUpdate）
if self.script_store and hasattr(self.script_store, 'notebook_store'):
    current_state['notebook'] = self.script_store.notebook_store.to_dict()

# 发送到 API
response = workflow_api_client.send_feedback_sync(
    stage_id=self.context.current_stage_id,
    step_index=self.context.current_step_id,
    state=current_state
)
```

### 3. 清除更新追踪

在发送完 API 请求后，应该清除更新追踪以准备下一轮：

```python
# 发送 API 后清除追踪
notebook_store.clear_update_tracking()

# 现在所有 cells 的 isUpdate 都为 False
# 直到下次有 cell 被修改
```

### 4. 获取已更新的 Cell IDs

```python
# 获取所有被更新的 cell IDs
updated_ids = notebook_store.get_updated_cell_ids()
print(f"Updated cells: {updated_ids}")
# Output: ['cell-1', 'cell-3', 'cell-5']
```

## API 返回格式

### context_notebook 结构

```json
{
  "notebook": {
    "title": "My Notebook",
    "cells": [
      {
        "id": "cell-1",
        "type": "markdown",
        "content": "# Introduction",
        "isUpdate": true  // ← 这个 cell 被更新了
      },
      {
        "id": "cell-2",
        "type": "code",
        "content": "x = 1 + 1",
        "outputs": [
          {
            "output_type": "execute_result",
            "content": "2"
          }
        ],
        "isUpdate": true  // ← 这个 cell 也被更新了（添加了 output）
      },
      {
        "id": "cell-3",
        "type": "markdown",
        "content": "## Summary",
        "isUpdate": false  // ← 这个 cell 没有变化
      }
    ],
    "execution_count": 1
  }
}
```

## 工作流示例

### 典型的工作流循环

```python
# 1. 初始化
notebook_store = NotebookStore()

# 2. 第一轮：添加初始 cells
notebook_store.add_cell({'id': 'cell-1', 'type': 'markdown', 'content': '# Title'})
notebook_store.add_cell({'id': 'cell-2', 'type': 'code', 'content': 'x = 1'})

# 3. 发送到 API（所有 cells 都标记为 isUpdate: true）
state = {'notebook': notebook_store.to_dict()}
send_to_api(state)

# 4. 清除追踪
notebook_store.clear_update_tracking()

# 5. 第二轮：只更新部分 cells
notebook_store.update_cell('cell-2', 'x = 2')  # 只更新 cell-2
notebook_store.add_cell({'id': 'cell-3', 'type': 'markdown', 'content': '## New Section'})

# 6. 发送到 API（只有 cell-2 和 cell-3 标记为 isUpdate: true）
state = {'notebook': notebook_store.to_dict()}
send_to_api(state)
# cell-1: isUpdate = false (没有变化)
# cell-2: isUpdate = true  (内容被更新)
# cell-3: isUpdate = true  (新添加的)

# 7. 重复循环...
```

## 实现细节

### 内部机制

1. **快照机制** (`_cell_snapshots`)
   - 为每个 cell 创建快照保存初始状态
   - 快照包含: content, outputs_count, metadata

2. **更新集合** (`_updated_cells`)
   - 使用 set 存储已更新的 cell IDs
   - 高效的查找性能 O(1)

3. **自动标记**
   - 所有修改操作都会调用 `_mark_as_updated()`
   - 新添加的 cell 自动标记

4. **清除机制**
   - `clear_update_tracking()` 更新所有快照
   - 清空 `_updated_cells` 集合

### 性能考虑

- **内存**: 每个 cell 的快照只包含关键字段，内存开销小
- **时间**: O(1) 查找和标记，O(n) 清除追踪（n = cells 数量）
- **扩展性**: 可处理数千个 cells 而不影响性能

## 测试覆盖

完整的测试套件位于 `test/test_cell_update_tracking.py`:

✅ 12 个测试用例，100% 通过率

- `test_01`: 新 cell 标记为 updated
- `test_02`: 更新内容标记为 updated
- `test_03`: 相同内容不标记
- `test_04`: 添加 output 标记为 updated
- `test_05`: 更新 metadata 标记为 updated
- `test_06`: 清除追踪重置标记
- `test_07`: 多 cells 选择性更新
- `test_08`: 清除 outputs 标记为 updated
- `test_09`: 清除空 outputs 不标记
- `test_10`: 获取已更新的 cell IDs
- `test_11`: 不包含 update status
- `test_12`: 完整工作流模拟

运行测试:
```bash
python test/test_cell_update_tracking.py
```

## 配置选项

### to_dict() 参数

```python
# 包含 isUpdate 标记（默认）
notebook_data = notebook_store.to_dict(include_update_status=True)

# 不包含 isUpdate 标记（向后兼容）
notebook_data = notebook_store.to_dict(include_update_status=False)
```

## 最佳实践

### ✅ 推荐做法

1. **在每次 API 调用后清除追踪**
   ```python
   # 发送到 API
   send_feedback(state)

   # 清除追踪
   notebook_store.clear_update_tracking()
   ```

2. **使用 get_updated_cell_ids() 进行调试**
   ```python
   updated = notebook_store.get_updated_cell_ids()
   if updated:
       logger.info(f"Updated cells: {updated}")
   ```

3. **在 state machine effect 中清除追踪**
   ```python
   def _effect_step_running(self, payload=None):
       # ... 执行 actions ...

       # 发送 feedback
       self._send_feedback()

       # 清除追踪
       if self.script_store and hasattr(self.script_store, 'notebook_store'):
           self.script_store.notebook_store.clear_update_tracking()
   ```

### ❌ 避免的做法

1. **不要忘记清除追踪**
   - 会导致所有 cells 持续标记为 updated

2. **不要在单个请求中多次清除**
   - 会丢失更新信息

3. **不要手动修改 `_updated_cells`**
   - 使用公共 API 方法

## 故障排除

### 问题: 所有 cells 都标记为 isUpdate

**原因**: 忘记调用 `clear_update_tracking()`

**解决**:
```python
# 在每次 API 调用后清除
notebook_store.clear_update_tracking()
```

### 问题: Cells 没有被标记为 isUpdate

**原因**:
1. 更新的内容与原内容相同
2. 在清除追踪前就获取了 to_dict()

**解决**:
```python
# 确保内容确实改变
notebook_store.update_cell('cell-1', 'New content')

# 在清除追踪后再更新
notebook_store.clear_update_tracking()
notebook_store.update_cell('cell-1', 'Updated')
```

## 相关文件

- `stores/notebook_store.py` - NotebookStore 实现
- `test/test_cell_update_tracking.py` - 完整测试套件
- `core/state_machine.py` - State machine 集成
- `models/cell.py` - Cell 数据模型

## 版本历史

- **v1.0** (2025-10-28) - 初始实现
  - 添加 isUpdate 标记
  - 实现自动追踪
  - 添加清除追踪功能
  - 完整测试覆盖

---

**维护者**: Notebook-BCC Team
**最后更新**: 2025-10-28
