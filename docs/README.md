# Notebook-BCC 文档索引

欢迎查阅 Notebook-BCC 的技术文档。

---

## 📚 文档列表

### 1. [API 交互协议](./API_PROTOCOL.md)

**内容**：
- ⚙️ API 配置和环境变量
- 🔄 API 工作流程（Planning First Protocol）
- 📤 请求格式（POMDP Observation）
- 📥 响应格式和上下文更新
- 🌊 **流式响应处理详解**
- 🔒 协议要求和错误处理
- 🎯 最佳实践和完整示例

**适用对象**：
- 后端开发者（了解需要实现的 API 格式）
- 前端开发者（了解如何调用 API）
- 集成开发者（了解协议规范）

---

### 2. [Action 协议规范](./ACTION_PROTOCOL.md)

**内容**：
- 📋 11 种 Action 类型总览
- 📝 每种 Action 的详细规范
  - `add` - 添加内容
  - `exec` - 执行代码
  - `is_thinking` / `finish_thinking` - 思考过程
  - `new_chapter` / `new_section` - 章节管理
  - `update_title` / `update_workflow` - 元数据更新
  - `end_phase` / `next_event` - 流程控制
- 🔧 Action 元数据结构
- 📊 处理流程和错误处理
- 🎨 Shot Type 说明
- 📝 完整使用示例

**适用对象**：
- 后端开发者（生成正确格式的 Actions）
- 扩展开发者（注册自定义 Actions）
- 测试人员（验证 Action 格式）

---

## 🚀 快速开始

### 查看 API 配置

```python
from config import Config

# 获取 API 配置
api_config = Config.get_api_config()
print(f"Planning API: {api_config['feedback_api_url']}")
print(f"Generating API: {api_config['behavior_api_url']}")
```

### 调用 Planning API

```python
from utils.api_client import workflow_api_client

response = workflow_api_client.send_feedback_sync(
    stage_id="data_analysis",
    step_id="load_data",
    state={
        "observation": {
            "location": { /* 进度信息 */ },
            "context": { /* 工作上下文 */ }
        }
    }
)

if response['targetAchieved']:
    print("目标已达成！")
```

### 调用 Generating API（流式）

```python
from utils.api_client import workflow_api_client

# 流式获取 Actions
actions = workflow_api_client.fetch_behavior_actions_sync(
    stage_id="data_analysis",
    step_id="load_data",
    state=current_state,
    stream=True  # 启用流式响应
)

# 逐个执行 Actions
for action in actions:
    print(f"执行 Action: {action['action']}")
    script_store.exec_action(action)
```

### 执行 Actions

```python
from stores.script_store import ScriptStore

store = ScriptStore(
    notebook_store=notebook_store,
    ai_context_store=ai_context_store,
    code_executor=code_executor
)

# 执行单个 Action
action = {
    "action": "add",
    "shot_type": "dialogue",
    "content": "Hello World"
}

result = store.exec_action(action)
```

---

## 🔗 相关文档

- [README](../README.md) - 项目概述和安装指南
- [快速参考](../QUICK_REFERENCE.md) - 常用命令和 API
- [高级用法](../ADVANCED_USAGE.md) - 扩展和定制

---

## 📊 协议版本

- **当前版本**: POMDP v2.0
- **主要特性**:
  - 层级化进度信息（location/progress/goals）
  - Planning First Protocol（规划优先）
  - Behavior Feedback（行为反馈）
  - 流式响应支持（NDJSON）

---

## 🆘 常见问题

### Q: 流式响应格式是什么？

**A**: 服务器返回 NDJSON 格式，每行一个 JSON 对象：

```json
{"action": {"action": "add", "content": "Hello"}}
{"action": {"action": "exec", "codecell_id": "code-1"}}
```

注意：action 包装在 `"action"` 键中。

### Q: 如何配置 API 端点？

**A**: 三种方式：
1. 环境变量：`.env` 文件设置 `DSLC_BASE_URL`
2. 运行时配置：`Config.set_dslc_url("http://...")`
3. 代码中直接修改：`config.py`

### Q: Planning API 和 Generating API 的区别？

**A**:
- **Planning API** - 检查目标是否达成，返回 `targetAchieved`
- **Generating API** - 生成具体的 Actions，返回 action 列表

每个 Step 开始时**必须先调用 Planning API**。

### Q: 如何注册自定义 Action？

**A**:
```python
from stores.script_store import ScriptStore

def my_handler(script_store, step):
    # 处理逻辑
    return result

# 注册
ScriptStore.register_custom_action('my_action', my_handler)
```

详见：[Action 协议规范 - 注册自定义 Action](./ACTION_PROTOCOL.md#注册自定义-action)

---

## 📝 更新日志

### 2025-10-28
- ✅ 添加流式响应处理详解
- ✅ 更新 Action 协议规范（11 种 Actions）
- ✅ 添加 API 配置说明
- ✅ 完善错误处理指南

---

**文档维护**: 如有问题或建议，请提交 Issue 或 PR。
