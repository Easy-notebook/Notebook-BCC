# Section Progress "all" 字段问题说明

## 问题现象

在 API 请求的 payload 中，`section_progress.all` 字段始终为空：

```json
{
  "observation": {
    "context": {
      "section_progress": {
        "current_section_id": null,
        "current_section_number": null,
        "completed_sections": [],
        "all": []  // ❌ 问题：始终为空
      }
    }
  }
}
```

## 问题根源

### 当前实现（客户端）

**已实现的部分**：

1. ✅ **数据结构已定义**（`core/context.py`）：
   ```python
   @dataclass
   class SectionProgress:
       current_section_id: Optional[str] = None
       current_section_number: Optional[int] = None
       completed_sections: List[str] = field(default_factory=list)
       all: List[str] = field(default_factory=list)  # 已添加
   ```

2. ✅ **字段已包含在 payload 中**（`utils/api_client.py`）：
   ```python
   'section_progress': compressed_state.get('section_progress', {
       'current_section_id': None,
       'current_section_number': None,
       'completed_sections': [],
       'all': []  # 默认空数组
   })
   ```

3. ✅ **AI Context Store 支持**（`stores/ai_context_store.py`）：
   - `set_section_progress()` 可以设置 `all` 字段
   - `to_dict()` 会输出 `all` 字段

**未实现的部分**：

❌ **在 workflow_update 时设置 `all` 字段**
- `_handle_workflow_update_confirmed()` 只更新了 workflow 模板
- **没有**提取 sections 列表并更新到 `section_progress.all`

## 设计意图

根据 `docs/FINAL_DESIGN.md`：

### `section_progress.all` 的作用

| 字段 | 类型 | 作用 |
|------|------|------|
| `section_progress.all` | list | 所有计划的sections列表（**由workflow_update设置**）|

### 工作流程

```
1. 服务端发送 UPDATE_WORKFLOW action
   - 包含新的 workflow 模板
   - workflow 模板中定义了所有 sections

2. 客户端接收并处理 workflow_update
   - 更新 workflow 模板 ✅
   - 从 workflow 中提取所有 section IDs ❌ (缺失)
   - 设置到 section_progress.all ❌ (缺失)

3. 后续的 API 请求中
   - section_progress.all 包含完整的 sections 列表
   - 用于计算进度、展示章节导航等
```

## 应该由谁负责设置 `all` 字段？

### 方案 A：客户端从 workflow 提取（之前尝试的方案）

**优点**：
- 客户端有完整的 workflow 结构
- 可以立即在 `_handle_workflow_update_confirmed()` 中设置

**缺点**：
- 需要解析 workflow 结构（可能复杂）
- workflow 模板格式可能变化

### 方案 B：服务端在 workflow_update 响应中直接提供 ⭐ **推荐**

**服务端在 workflow_update response 中应该包含**：

```json
{
  "action": "update_workflow",
  "updated_workflow": {
    "name": "房价预测模型训练",
    "stages": [...]
  },
  "context_update": {
    "section_progress": {
      "all": [
        "introduction",
        "data_loading",
        "data_assessment",
        "variable_definition",
        "feature_engineering",
        "model_training",
        "evaluation",
        "conclusion"
      ]
    }
  }
}
```

**优点**：
- 服务端完全控制 sections 定义
- 客户端只需接收和应用
- 符合"服务端控制内容，客户端控制流程"的架构

**缺点**：
- 需要服务端修改

## 建议的解决方案

### 如果服务端可以修改（推荐）

**服务端修改**：
在 `UPDATE_WORKFLOW` action 的响应中，添加 `context_update.section_progress.all` 字段。

**客户端修改**：
无需修改，现有的 `_apply_context_update()` 已经支持更新 `section_progress`。

### 如果服务端不能修改（临时方案）

**客户端修改**：
在 `_handle_workflow_update_confirmed()` 中：
1. 解析 `workflow_template`
2. 提取所有 section IDs
3. 更新 `ai_context_store.section_progress.all`

但这需要知道：
- workflow 模板中 sections 的具体结构
- sections 信息存储在哪个字段（`stage.sections`? `step.section_id`? 其他？）

## 需要确认的问题

1. **服务端是否可以在 `workflow_update` 响应中提供 `section_progress.all`？**
2. **如果不能，workflow 模板中 sections 信息的具体结构是什么？**
   - 是在 `stage.sections` 字段？
   - 还是在 `step.metadata.section_id`？
   - 还是其他位置？

## 当前状态总结

### 已完成 ✅
- `SectionProgress` 数据结构定义（包含 `all` 字段）
- Payload 中包含 `section_progress.all`
- AI Context Store 支持设置和读取
- 文档更新（FINAL_DESIGN.md, CHANGE_GUIDE.md）

### 缺失 ❌
- `section_progress.all` 的实际值始终为空
- 没有机制在 workflow_update 时填充该字段

### 需要决策
- 由**服务端**提供（推荐），还是**客户端**从 workflow 提取？
