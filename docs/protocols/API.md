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

##  API 请求格式

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
          "completed": [
            {
              "stage_id": "stage1",
              "goal": "...",
              "outputs_produced": {...}
            }
          ],
          "current": "stage3",
          "remaining": ["stage4"],
          "focus": "【Stage 详细分析文本】\n\n## 阶段目标\n...",  // Planner 生成的详细分析文本
          "current_outputs": {
            "expected": ["df_cleaned", "cleaning_report"],
            "produced": [],
            "in_progress": []
          }
        },
        "steps": {
          "completed": [
            {
              "step_id": "step1",
              "goal": "...",
              "outputs_produced": {...}
            }
          ],
          "current": "step2",
          "remaining": ["step3", "step4"],
          "focus": "【Step 详细执行方案】\n\n...",  // Planner 生成的详细分析文本
          "current_outputs": {
            "expected": ["df", "missing_fill_report"],
            "produced": [],
            "in_progress": []
          }
        },
        "behaviors": {
          "completed": [
            {
              "behavior_id": "behavior_001",
              "goal": "...",
              "outputs_produced": {...}
            }
          ],
          "current": "behavior_003",
          "iteration": 3,
          "focus": "【Behavior 详细指导】\n\n...",  // Planner 生成的详细分析文本
          "current_outputs": {
            "expected": ["df_working", "imputation_log"],
            "produced": [],
            "in_progress": []
          }
        }
      },
      "goals": {
        "stage": "Complete data analysis",
        "step": "Load and preprocess data",
        "behavior": null
      }
    },
    "context": {
      // 工作上下文 (简化后的结构)
      "variables": {
        "data_loaded": true,
        "schema_validated": false,
        // ... 其他变量
      },
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
      }
      // Note: focus 现在位于 observation.location.progress.*.focus
      // 不再包含 toDoList, section_progress, workflow_progress
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
    "variables": {
      "data_loaded": true,
      "schema_validated": true
    },
    "progress_update": {
      "level": "steps",  // "stages" | "steps" | "behaviors"
      "focus": "【Step 详细执行方案】\n\n当前状态分析：...\n\n关键产出目标：...\n\n建议方法：..."  // 更新 focus（详细分析文本）
    },
    "workflow_update": {
      "workflowTemplate": { /* 更新的工作流模板 */ }
    },
    "stage_steps_update": {
      "stage_id": "stage3",
      "steps": [ /* 更新的步骤列表 */ ]
    }
  },

  "context_filter": {      // 可选：筛选指令（用于下次 Generating API 调用）
    "variables_to_include": ["df", "missing_groups"],
    "variables_to_summarize": {
      "correlation_matrix": "shape_only"
    },
    "effects_config": {
      "include_current": true,
      "current_limit": 3
    },
    "focus_to_include": ["behaviors", "steps"]
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
    "variables": {
      "intermediate_result": "some_value"
    },
    "progress_update": {
      "level": "behaviors",
      "focus": "【Behavior 详细指导】\n\n执行目标：...\n关键产出：...\n建议方法：..."
    }
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

服务器可以在 Planning API 响应中返回 `context_update` 来更新客户端状态。

### 更新类型

| 更新类型 | 说明 | API |
|---------|------|-----|
| `variables` | 更新上下文变量 | Planning |
| `progress_update` | 更新层级化 focus | Planning |
| `effects_update` | 更新执行效果 | Planning |
| `workflow_update` | 更新工作流模板 | Planning |
| `stage_steps_update` | 更新阶段步骤 | Planning |

### 变量更新
更新上下文变量，用于存储工作流执行过程中的数据：

```json
{
  "context_update": {
    "variables": {
      "data_loaded": true,
      "row_count": 1000,
      "schema_validated": true
    }
  }
}
```

### 层级化 Focus 更新 (NEW)
更新 Planner 生成的详细分析文本，用于指导 Generating API：

```json
{
  "context_update": {
    "progress_update": {
      "level": "steps",  // "stages" | "steps" | "behaviors"
      "focus": "【Step: 缺失值处理 - 详细执行方案】\n\n## 当前状态分析\n已完成 behavior_001 和 behavior_002，生成了 missing_summary 和 missing_groups。\n\n## 关键产出目标\n- df: 更新后的主数据集\n- missing_fill_report: 填充报告\n- imputation_log: 操作日志\n\n## 建议执行方法\n1. 针对高缺失特征使用语义填充\n2. 针对车库相关特征使用连带填充\n..."
    }
  }
}
```

**Focus 语义**:
- Focus 是 Planner 生成的**详细分析文本**（字符串）
- 不是变量名列表，不是任务描述列表
- 用途：为 Generating API 提供上下文提示和执行指导
- 格式：详细的分析、目标、建议等信息

### 工作流更新
更新工作流模板结构：

```json
{
  "context_update": {
    "workflow_update": {
      "workflowTemplate": {
        "name": "Updated Workflow",
        "stages": [ /* 新的阶段列表 */ ]
      },
      "nextStageId": "stage_new"  // 可选：切换到新阶段
    }
  }
}
```

### 阶段步骤更新
更新特定阶段的步骤列表：

```json
{
  "context_update": {
    "stage_steps_update": {
      "stage_id": "data_analysis",
      "steps": [
        { "id": "step1", "description": "Load data" },
        { "id": "step2", "description": "Preprocess" }
      ]
    }
  }
}
```

### 效果更新
更新执行效果记录：

```json
{
  "context_update": {
    "effects_update": {
      "current": ["New effect text"],
      "history": ["Previous effect 1", "Previous effect 2"]
    }
  }
}
```

---

## 🔍 Context Filter 协议（NEW）

Planning API 可以在响应中返回 `context_filter`，指导 Client 在下次调用 Generating API 时应该传递哪些信息。这样可以：
- 减少 token 消耗
- 提高提示词质量（只包含相关信息）
- 优化 API 性能

### Context Filter 结构

```json
{
  "context_filter": {
    "variables_to_include": [
      "df",
      "missing_groups",
      "missing_summary"
    ],

    "variables_to_summarize": {
      "correlation_matrix": "shape_only",
      "df_train": "describe_only"
    },

    "effects_config": {
      "include_current": true,
      "current_limit": 3,
      "include_history": false,
      "history_limit": 0
    },

    "focus_to_include": [
      "behaviors",
      "steps"
    ],

    "outputs_tracking": {
      "expected_variables": ["df_working", "imputation_log"],
      "validation_required": ["high_missing_validated"]
    }
  }
}
```

### 字段说明

#### 1. variables_to_include

指定完整传递给 Generating API 的变量列表。

**错误处理规则**：
- ⚠️ **如果变量不存在，Client 不要静默丢弃**
- 必须在 effects 中打 WARN：`"⚠️ WARN: Variable 'xxx' not found"`
- 回退到 `variables_to_summarize` 策略（如果定义）
- 记录日志供调试

```python
# Client 实现示例
for var in variables_to_include:
    if var not in context.variables:
        warning = f"⚠️ WARN: Variable '{var}' requested but not found"
        context.effects.current.append(warning)
        logger.warning(warning)
```

#### 2. variables_to_summarize

对大型变量进行摘要而非完整传递。

**摘要策略**：
- `shape_only`: 只传递 shape（适用于 DataFrame/矩阵）
- `describe_only`: 只传递统计摘要
- `head_only`: 只传递前几行
- `last_N_only`: 只传递最后 N 个元素

示例：
```json
"variables_to_summarize": {
  "correlation_matrix": "shape_only",     // (79, 79)
  "df_train": "describe_only",            // df.describe()
  "model_history": "last_5_only"          // 最后5条记录
}
```

#### 3. effects_config

配置 effects 的传递方式。

```json
"effects_config": {
  "include_current": true,        // 是否包含 current
  "current_limit": 3,             // current 最多保留几条
  "include_history": false,       // 是否包含 history
  "history_limit": 0              // history 最多保留几条
}
```

#### 4. focus_to_include

指定传递哪些层级的 focus。通常包含当前层级和上层指导。

```json
"focus_to_include": [
  "behaviors",  // 当前层级（必须）
  "steps"       // 上层指导
]
// 不包含 "stages"（通常太宏观）
```

#### 5. outputs_tracking

指定 Generating API 应该关注的期望产出。

```json
"outputs_tracking": {
  "expected_variables": ["df_working", "imputation_log"],
  "validation_required": ["high_missing_validated"]
}
```

### Client 处理流程

```python
def apply_context_filter(observation, context_filter):
    """应用 Planning API 返回的 context_filter"""

    # 1. 筛选 variables
    filtered_vars = {}
    for var_name in context_filter.get('variables_to_include', []):
        if var_name in observation.context.variables:
            filtered_vars[var_name] = observation.context.variables[var_name]
        else:
            # 错误处理：打 WARN
            warning = f"⚠️ WARN: Variable '{var_name}' not found"
            observation.context.effects.current.append(warning)

            # 尝试 summarize 回退
            if var_name in context_filter.get('variables_to_summarize', {}):
                strategy = context_filter['variables_to_summarize'][var_name]
                filtered_vars[var_name] = f"<{strategy}: not available>"

    # 2. 处理 summarize 变量
    for var_name, strategy in context_filter.get('variables_to_summarize', {}).items():
        if var_name in observation.context.variables:
            var_value = observation.context.variables[var_name]
            filtered_vars[var_name] = apply_summarize_strategy(var_value, strategy)

    # 3. 筛选 effects
    effects_cfg = context_filter.get('effects_config', {})
    filtered_effects = {}

    if effects_cfg.get('include_current', True):
        limit = effects_cfg.get('current_limit', float('inf'))
        filtered_effects['current'] = observation.context.effects.current[:limit]

    if effects_cfg.get('include_history', False):
        limit = effects_cfg.get('history_limit', 0)
        filtered_effects['history'] = observation.context.effects.history[:limit]

    # 4. 筛选 focus
    filtered_progress = {}
    for level in context_filter.get('focus_to_include', ['behaviors']):
        filtered_progress[level] = {
            'focus': observation.location.progress[level].focus,
            'current_outputs': observation.location.progress[level].current_outputs
        }

    # 5. 构建精简 payload
    return {
        'observation': {
            'location': {
                'current': observation.location.current,
                'progress': filtered_progress
            },
            'context': {
                'variables': filtered_vars,
                'effects': filtered_effects
            }
        },
        'options': {'stream': True}
    }
```

### 使用示例

**场景**：Behavior 003 需要填充高缺失特征

```json
// Planning API 响应
{
  "targetAchieved": false,
  "context_filter": {
    "variables_to_include": [
      "df",              // 需要主数据集
      "missing_groups"   // 需要分组策略
    ],
    "variables_to_summarize": {
      "correlation_matrix": "shape_only"  // 相关性矩阵太大，只传递形状
    },
    "effects_config": {
      "current_limit": 3  // 只保留最近3条输出
    },
    "focus_to_include": ["behaviors", "steps"]
  }
}

// Client 应用筛选后的 Generating API payload
{
  "observation": {
    "location": {
      "progress": {
        "behaviors": {
          "focus": "【Behavior 003 详细指导】...",
          "current_outputs": {"expected": ["df_working", "imputation_log"]}
        },
        "steps": {
          "focus": "【Step 详细方案】...",
          "current_outputs": {"expected": ["df", "missing_fill_report"]}
        }
      }
    },
    "context": {
      "variables": {
        "df": "DataFrame(1460×79)",
        "missing_groups": {...},
        "correlation_matrix": "(79, 79)"  // 只传递形状
      },
      "effects": {
        "current": [
          "车库特征缺失连带性分析：...",
          "{'high_missing': [...], ...}",
          "LotFrontage 与 Neighborhood 相关性分析：..."
        ]
      }
    }
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
2. **context.FSM** - 状态机追踪信息
3. **context_update** - 上下文更新 (Planning API 响应)

### 错误处理

如果缺少必需字段，API 会返回错误：

```python
ValueError: "Missing required 'progress_info' in state.
            New POMDP protocol requires hierarchical progress information."
```

---

## 🎯 最佳实践

1. **始终提供完整的 progress_info**
   - 包含 current, progress (含 focus), goals 三部分
   - 确保 behavior_id 和 iteration 正确
   - 每个层级的 focus 是 Planner 生成的详细分析文本

2. **使用 Planning First**
   - 每个 Step 开始前调用 Planning API
   - 避免不必要的 Generating 调用

3. **正确处理 context_update**
   - 立即应用服务器返回的上下文更新
   - 特别注意 progress_update 更新层级化 focus（详细文本）
   - 保持客户端和服务器状态同步

4. **Focus 文本设计**
   - Focus 是 Planner 生成的详细分析文本，不是变量名列表
   - 应包含：当前状态分析、关键产出目标、建议执行方法
   - 用于为 Generating API 提供丰富的上下文和指导
   - 示例格式：`"【Behavior: ...】\n\n## 状态分析\n...\n\n## 关键目标\n...\n\n## 建议方法\n..."`

5. **流式响应处理**
   - Generating API 建议使用流式模式
   - 可以实时显示生成进度

6. **错误重试**
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

- [STATE_MACHINE_PROTOCOL.md](./STATE_MACHINE_PROTOCOL.md) - 状态机协议和状态转移规则
- [OBSERVATION_PROTOCOL.md](./OBSERVATION_PROTOCOL.md) - 完整 Observation 结构和 Context Filter 协议
- [ACTION_PROTOCOL.md](./ACTION_PROTOCOL.md) - 详细的 Action 类型和格式
- [REFACTORING_SUMMARY.md](./REFACTORING_SUMMARY.md) - 系统重构总结
- [README.md](./README.md) - 文档导航和核心概念速查
