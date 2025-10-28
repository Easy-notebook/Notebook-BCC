# Notebook-BCC API 交互协议

## 📡 概述

Notebook-BCC 采用基于 POMDP (Partially Observable Markov Decision Process) 的交互协议，通过两个主要 API 端点与后端服务通信：

- **Planning API** (`/planning`) - 目标检查，判断当前步骤是否已达成
- **Generating API** (`/generating`) - 行为生成，获取下一步要执行的 actions

---

## ⚙️ API 配置

### 默认端点

```python
# DSLC (Data Science Lifecycle) 服务
DSLC_BASE_URL = "http://localhost:28600"

# API 端点
FEEDBACK_API_URL = "http://localhost:28600/planning"    # Planning/Feedback API
BEHAVIOR_API_URL = "http://localhost:28600/generating"  # Generating API
GENERATE_API_URL = "http://localhost:28600/generate"    # Generate API (备用)
```

### 环境变量配置

可以通过 `.env` 文件或环境变量覆盖默认配置：

```bash
# .env 文件
DSLC_BASE_URL=http://your-server:28600
BACKEND_BASE_URL=http://your-backend:18600
NOTEBOOK_ID=optional-notebook-id

# 日志级别
LOG_LEVEL=INFO

# 执行控制
MAX_EXECUTION_STEPS=0        # 0 = 无限制
INTERACTIVE_MODE=false       # 交互模式

# 功能开关
USE_REMOTE_EXECUTION=true    # 远程代码执行
```

### 运行时配置

```python
from config import Config

# 更新 DSLC URL
Config.set_dslc_url("http://new-server:28600")

# 更新 Backend URL
Config.set_backend_url("http://new-backend:18600")

# 设置 Notebook ID
Config.set_notebook_id("notebook-123")

# 获取当前配置
api_config = Config.get_api_config()
print(api_config)
# {
#   'dslc_base_url': 'http://localhost:28600',
#   'feedback_api_url': 'http://localhost:28600/planning',
#   'behavior_api_url': 'http://localhost:28600/generating',
#   ...
# }
```

---

## 🔄 API 工作流程

### 1. Planning First Protocol (规划优先协议)

每个 Step 开始时，**必须先调用 Planning API**，然后根据结果决定下一步：

```
Step Start
    ↓
Planning API (/planning)
    ↓
targetAchieved?
    ├─ Yes → Complete Step (跳过 Generating)
    └─ No → Generating API (/generating)
             ↓
        Execute Actions
             ↓
        Feedback API (/planning)
             ↓
        Continue or Complete
```

### 2. 控制职责分离

- **Server (后端)** - 控制 Behavior Loop (单个 Step 内的行为循环)
- **Client (前端)** - 控制 Stage/Step Navigation (阶段和步骤的导航)

---

## 📤 API 请求格式

### 通用请求结构 (POMDP Observation)

所有 API 请求都遵循 POMDP 观测结构：

```json
{
  "observation": {
    "location": {
      // 层级化进度信息
      "current": {
        "stage_id": "string",
        "step_id": "string",
        "behavior_id": "string",
        "behavior_iteration": 1
      },
      "progress": {
        "stages": {
          "completed": ["stage1", "stage2"],
          "current": "stage3",
          "remaining": ["stage4"]
        },
        "steps": {
          "completed": ["step1"],
          "current": "step2",
          "remaining": ["step3", "step4"]
        },
        "behaviors": {
          "completed": ["behavior_001", "behavior_002"],
          "current": "behavior_003",
          "iteration": 3
        }
      },
      "goals": {
        "stage": "Complete data analysis",
        "step": "Load and preprocess data",
        "behavior": null
      }
    },
    "context": {
      // 工作上下文
      "variables": {
        "key": "value"
      },
      "toDoList": ["task1", "task2"],
      "effects": {
        "current": ["effect text..."],
        "history": []
      },
      "notebook": {
        // Notebook 数据结构
      },
      "FSM": {
        "state": "BEHAVIOR_RUNNING",
        "transition": [
          // 状态转换历史
        ]
      },
      "section_progress": "optional",
      "workflow_progress": "optional"
    }
  },
  "options": {
    "stream": false
  }
}
```

### Planning API 请求

**端点**: `POST /planning`

**用途**: 检查当前步骤目标是否已达成

**请求**:
```json
{
  "observation": {
    "location": { /* 层级进度 */ },
    "context": { /* 工作上下文 */ }
  },
  "options": {
    "stream": false
  }
}
```

**响应**:
```json
{
  "targetAchieved": true,  // 目标是否达成
  "context_update": {      // 可选：上下文更新
    "variables": { "key": "new_value" },
    "todo_list_update": {
      "operation": "remove",  // "add" | "remove" | "replace"
      "items": ["completed_task"]
    },
    "section_progress": "updated_value"
  }
}
```

### Generating API 请求

**端点**: `POST /generating`

**用途**: 获取下一个 Behavior 要执行的 Actions

**请求**:
```json
{
  "observation": {
    "location": { /* 层级进度 */ },
    "context": { /* 工作上下文 */ }
  },
  "options": {
    "stream": true  // 支持流式返回
  }
}
```

**响应** (流式):
```json
// 流式返回，每行一个 JSON 对象，action 包装在 "action" 键中
{"action": {"action": "add", "content": "Hello", "shot_type": "dialogue"}}
{"action": {"action": "exec", "codecell_id": "code-1", "shot_type": "action"}}
{"action": {"action": "is_thinking", "thinking_text": "Analyzing...", "shot_type": "dialogue"}}
```

**客户端处理**:
```python
# 流式处理逻辑 (api_client.py)
async for chunk in response.content.iter_any():
    buffer += chunk.decode('utf-8')
    lines = buffer.split('\n')
    buffer = lines.pop()  # 保留不完整行

    for line in lines:
        if line.strip():
            message = json.loads(line)
            if 'action' in message:
                yield message['action']  # 提取内部的 action 对象
```

**响应** (非流式):
```json
{
  "actions": [
    {"action": "add", "content": "Hello", "shot_type": "dialogue"},
    {"action": "exec", "codecell_id": "code-1", "shot_type": "action"}
  ]
}
```

### Feedback API 请求

**端点**: `POST /planning` (与 Planning API 相同)

**用途**: Behavior 完成后发送反馈，获取下一步指令

**请求**:
```json
{
  "observation": {
    "location": { /* 层级进度 */ },
    "context": { /* 工作上下文 */ }
  },
  "behavior_feedback": {
    "behavior_id": "behavior_003",
    "actions_executed": 5,
    "actions_succeeded": 5,
    "sections_added": 2,
    "last_action_result": "success"
  },
  "options": {
    "stream": false
  }
}
```

**响应**:
```json
{
  "targetAchieved": false,
  "transition": {
    "continue_behaviors": true,  // Server 控制：是否继续 Behavior Loop
    "target_achieved": false     // 目标是否达成
  },
  "context_update": {
    "variables": { /* ... */ },
    "todo_list_update": { /* ... */ }
  }
}
```

---

## 🌊 流式响应处理

### 流式 vs 非流式

Generating API 支持两种响应模式：

| 模式 | 触发条件 | 响应格式 | 适用场景 |
|------|---------|---------|---------|
| **流式** | `options.stream: true` | 逐行 JSON (NDJSON) | 实时显示、长时间生成 |
| **非流式** | `options.stream: false` | 单个 JSON 对象 | 快速获取、批量处理 |

### 流式响应格式 (NDJSON)

每一行是一个独立的 JSON 对象，action 包装在 `"action"` 键中：

```
{"action": {"action": "add", "content": "Step 1", "shot_type": "dialogue"}}
{"action": {"action": "add", "content": "print('hello')", "shot_type": "action"}}
{"action": {"action": "exec", "codecell_id": "lastAddedCellId"}}
```

**注意**：
- 每行必须是完整的 JSON 对象
- 行之间用换行符 `\n` 分隔
- 客户端需要处理不完整的行（buffer 机制）

### 流式处理流程

```python
# 1. 初始化 buffer
buffer = ""

# 2. 逐块读取响应
async for chunk in response.content.iter_any():
    # 3. 解码并追加到 buffer
    buffer += chunk.decode('utf-8')

    # 4. 按行分割
    lines = buffer.split('\n')

    # 5. 保留最后一行（可能不完整）
    buffer = lines.pop()

    # 6. 处理完整的行
    for line in lines:
        if line.strip():
            try:
                # 7. 解析 JSON
                message = json.loads(line)

                # 8. 提取 action
                if 'action' in message:
                    action = message['action']

                    # 9. yield 或处理 action
                    yield action
            except json.JSONDecodeError:
                # 处理解析错误
                pass
```

### 流式 vs 非流式对比

**流式优势**：
- ✅ 实时反馈 - 用户可以立即看到生成进度
- ✅ 内存效率 - 逐个处理，不需要等待全部生成完成
- ✅ 更好的用户体验 - 避免长时间等待

**非流式优势**：
- ✅ 简单实现 - 一次性获取所有 actions
- ✅ 批量处理 - 可以预先检查所有 actions
- ✅ 原子性 - 要么全部成功，要么全部失败

### 服务器端响应格式

**服务器应该返回的流式响应示例**：

```http
HTTP/1.1 200 OK
Content-Type: application/json
Transfer-Encoding: chunked

{"action": {"action": "new_chapter", "content": "数据分析"}}
{"action": {"action": "add", "shot_type": "dialogue", "content": "开始分析数据..."}}
{"action": {"action": "add", "shot_type": "action", "content": "import pandas as pd\ndf = pd.read_csv('data.csv')"}}
{"action": {"action": "exec", "codecell_id": "lastAddedCellId", "need_output": true}}
{"action": {"action": "is_thinking", "thinking_text": "正在分析数据结构...", "agent_name": "Analyst"}}
{"action": {"action": "finish_thinking"}}
{"action": {"action": "add", "shot_type": "dialogue", "content": "数据加载完成，共 1000 行"}}
```

**每行格式**：
- 外层包装：`{"action": {...}}`
- 内层 action：完整的 action 对象

### 错误处理

**流式错误**：
```python
try:
    async for action in fetch_behavior_actions(stream=True):
        # 处理单个 action
        process_action(action)
except json.JSONDecodeError as e:
    # 处理 JSON 解析错误
    logger.error(f"Failed to parse action: {e}")
except Exception as e:
    # 处理其他错误
    logger.error(f"Stream error: {e}")
```

**非流式错误**：
```python
try:
    response = fetch_behavior_actions(stream=False)
    actions = response['actions']
    # 批量处理
    for action in actions:
        process_action(action)
except Exception as e:
    logger.error(f"Failed to fetch actions: {e}")
```

---

## 📥 上下文更新协议

服务器可以在响应中返回 `context_update` 来更新客户端状态：

### 变量更新
```json
{
  "context_update": {
    "variables": {
      "data_loaded": true,
      "row_count": 1000
    }
  }
}
```

### TODO 列表更新
```json
{
  "context_update": {
    "todo_list_update": {
      "operation": "remove",  // "add" | "remove" | "replace"
      "items": ["Load data", "Preprocess"]
    }
  }
}
```

### 进度更新
```json
{
  "context_update": {
    "section_progress": "Data preprocessing: 75%",
    "workflow_progress": "Analysis phase: 2/5"
  }
}
```

---

## 🔒 协议要求

### 必需字段

1. **progress_info** - 层级化进度信息 (新协议必需)
2. **location.current** - 当前位置信息
3. **location.progress** - 进度追踪信息

### 可选字段

1. **behavior_feedback** - Behavior 执行反馈 (仅在 Feedback 时提供)
2. **context.section_progress** - 章节进度
3. **context.workflow_progress** - 工作流进度
4. **context.FSM** - 状态机追踪信息

### 错误处理

如果缺少必需字段，API 会返回错误：

```python
ValueError: "Missing required 'progress_info' in state.
            New POMDP protocol requires hierarchical progress information."
```

---

## 🎯 最佳实践

1. **始终提供完整的 progress_info**
   - 包含 current, progress, goals 三部分
   - 确保 behavior_id 和 iteration 正确

2. **使用 Planning First**
   - 每个 Step 开始前调用 Planning API
   - 避免不必要的 Generating 调用

3. **正确处理 context_update**
   - 立即应用服务器返回的上下文更新
   - 保持客户端和服务器状态同步

4. **流式响应处理**
   - Generating API 建议使用流式模式
   - 可以实时显示生成进度

5. **错误重试**
   - Planning API 失败时，可以降级到 Generating API
   - Generating API 失败时，应该传播错误并停止

---

## 📊 示例交互流程

```python
# Step 开始 - Planning First
response = api_client.send_feedback_sync(
    stage_id="data_analysis",
    step_id="load_data",
    state=current_state
)

if response['targetAchieved']:
    # 目标已达成，直接完成 Step
    transition(WorkflowEvent.COMPLETE_STEP)
else:
    # 目标未达成，生成 Behavior
    transition(WorkflowEvent.START_BEHAVIOR)

    # 获取 Actions
    actions = api_client.fetch_behavior_actions_sync(
        stage_id="data_analysis",
        step_id="load_data",
        state=current_state,
        stream=True
    )

    # 执行 Actions
    for action in actions:
        script_store.exec_action(action)

    # 发送反馈
    feedback_response = api_client.send_feedback_sync(
        stage_id="data_analysis",
        step_id="load_data",
        state=current_state,
        behavior_feedback={
            'behavior_id': 'behavior_001',
            'actions_executed': len(actions),
            'actions_succeeded': len(actions),
            'sections_added': 2,
            'last_action_result': 'success'
        }
    )

    # 根据服务器指令决定下一步
    if feedback_response['transition']['continue_behaviors']:
        # 继续下一个 Behavior
        transition(WorkflowEvent.NEXT_BEHAVIOR)
    elif feedback_response['transition']['target_achieved']:
        # 完成 Step
        transition(WorkflowEvent.COMPLETE_STEP)
```

---

## 🔗 相关文档

- [Action 协议](./ACTION_PROTOCOL.md) - 详细的 Action 类型和格式
- [README](../README.md) - 项目概述和快速开始
- [快速参考](../QUICK_REFERENCE.md) - 常用命令和 API
