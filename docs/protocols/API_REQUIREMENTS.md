# Notebook-BCC API 需求规范

## 📋 概述

本文档总结 Notebook-BCC 系统所需的后端 API 端点、请求/响应格式及实现要求，供后端开发人员参考。

---

## 🎯 API 端点总览

| API 端点 | 方法 | 用途 | 调用时机 | 响应格式 |
|---------|------|------|---------|---------|
| `/planning` | POST | 目标检查与规划 | Step开始前、Behavior完成后 | JSON |
| `/generating` | POST | 生成Actions | Behavior开始时 | JSON / NDJSON (流式) |

---

## 📡 API 1: Planning API

### 端点信息

- **URL**: `POST /planning`
- **Content-Type**: `application/json`
- **用途**: 检查当前目标是否达成，并提供下一步指导

### 调用时机

1. **Step 开始前** (Planning First Protocol)
   - 检查Step目标是否已达成
   - 如未达成，决定是否需要生成Behavior

2. **Behavior 完成后** (Feedback)
   - 检查Behavior执行结果
   - 决定是否继续迭代或完成Step

### 请求格式

```json
{
  "observation": {
    "location": {
      "current": {
        "stage_id": "data_existence_establishment",
        "step_id": "data_collection_inventory",
        "behavior_id": "data_collection_inventory_b1",
        "behavior_iteration": 1
      },
      "progress": {
        "stages": {
          "completed": [ /* 已完成的stages */ ],
          "current": "data_existence_establishment",
          "remaining": [ /* 剩余stages */ ],
          "focus": "【Stage 详细分析文本】...",
          "current_outputs": {
            "expected": ["data_existence_report", "data_structure_document"],
            "produced": [],
            "in_progress": []
          }
        },
        "steps": {
          "completed": [ /* 已完成的steps */ ],
          "current": "data_collection_inventory",
          "remaining": [ /* 剩余steps */ ],
          "focus": "【Step 详细执行方案】...",
          "current_outputs": {
            "expected": ["data_existence_report"],
            "produced": [],
            "in_progress": []
          }
        },
        "behaviors": {
          "completed": [ /* 已完成的behaviors */ ],
          "current": "data_collection_inventory_b1",
          "iteration": 1,
          "focus": "【Behavior 详细指导】...",
          "current_outputs": {
            "expected": ["data_existence_report"],
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
      "variables": {
        "user_problem": "基于 Housing 数据集构建房价预测模型",
        "user_submit_files": ["./assets/housing.csv"]
      },
      "effects": {
        "current": ["Recent execution outputs..."],
        "history": []
      },
      "notebook": {
        "title": "Ames Housing Analysis",
        "cells": [ /* Notebook cells */ ],
        "execution_count": 1
      },
      "FSM": {
        "state": "BEHAVIOR_RUNNING",
        "last_transition": "START_BEHAVIOR",
        "timestamp": "2025-11-10T06:42:34Z"
      }
    }
  },
  "behavior_feedback": {
    "behavior_id": "behavior_001",
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

### 响应格式

```json
{
  "targetAchieved": false,

  "transition": {
    "continue_behaviors": true,
    "target_achieved": false
  },

  "context_update": {
    "variables": {
      "data_loaded": true,
      "schema_validated": true
    },

    "progress_update": {
      "level": "behaviors",
      "focus": "【Behavior 详细指导】\n\n## 执行目标\n...\n\n## 关键产出\n...\n\n## 建议方法\n..."
    },

    "workflow_update": {
      "workflowTemplate": { /* 更新的工作流模板 */ },
      "nextStageId": "stage_new"
    },

    "stage_steps_update": {
      "stage_id": "stage3",
      "steps": [ /* 更新的步骤列表 */ ]
    }
  },

  "context_filter": {
    "variables_to_include": ["df", "missing_groups", "missing_summary"],

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

    "focus_to_include": ["behaviors", "steps"],

    "outputs_tracking": {
      "expected_variables": ["df_working", "imputation_log"],
      "validation_required": ["high_missing_validated"]
    }
  }
}
```

### 字段说明

#### targetAchieved (必需)

**类型**: `boolean`

**说明**: 当前层级的目标是否已达成

**取值**:
- `true` - 目标已达成，可以完成当前Step/Stage
- `false` - 目标未达成，需要继续生成Behavior

#### transition (可选)

**说明**: 控制Behavior循环的转换指令

**字段**:
- `continue_behaviors` - 是否需要继续生成新的Behavior
- `target_achieved` - 目标是否达成（通常与`targetAchieved`一致）

#### context_update (可选)

**说明**: 更新Client端的上下文状态

**子字段**:

1. **variables** - 更新环境变量
   ```json
   "variables": {
     "data_loaded": true,
     "row_count": 1000
   }
   ```

2. **progress_update** - 更新层级化focus（详细分析文本）
   ```json
   "progress_update": {
     "level": "behaviors",  // "stages" | "steps" | "behaviors"
     "focus": "【详细分析文本】..."
   }
   ```

3. **workflow_update** - 更新工作流模板
4. **stage_steps_update** - 更新阶段步骤列表

#### context_filter (可选)

**说明**: 指导Client在调用Generating API时应传递哪些信息

**用途**: 减少token消耗，优化提示词质量

---

## 📡 API 2: Generating API

### 端点信息

- **URL**: `POST /generating`
- **Content-Type**: `application/json`
- **用途**: 生成执行行为所需的Actions列表
- **支持流式**: 是 (NDJSON格式)

### 调用时机

当Planning API返回`targetAchieved: false`时，Client会调用Generating API生成下一个Behavior的Actions。

### 请求格式

请求格式与Planning API基本相同，但可能经过`context_filter`筛选：

```json
{
  "observation": {
    "location": {
      "current": { /* 当前位置 */ },
      "progress": {
        "behaviors": {
          "focus": "【Behavior 详细指导】...",
          "current_outputs": {
            "expected": ["df_working", "imputation_log"]
          }
        },
        "steps": {
          "focus": "【Step 详细方案】...",
          "current_outputs": {
            "expected": ["df", "missing_fill_report"]
          }
        }
      }
    },
    "context": {
      "variables": {
        "df": "DataFrame(1460×79)",
        "missing_groups": { /* 筛选后的变量 */ }
      },
      "effects": {
        "current": [ /* 最近3条输出 */ ]
      }
    }
  },
  "options": {
    "stream": true
  }
}
```

### 响应格式

#### 非流式响应

```json
{
  "actions": [
    {
      "action": "new_chapter",
      "content": "数据收集与清单"
    },
    {
      "action": "add",
      "shot_type": "dialogue",
      "content": "We begin by establishing data existence..."
    },
    {
      "action": "add",
      "shot_type": "action",
      "content": "import pandas as pd\ndf_raw = pd.read_csv('./assets/housing.csv')"
    },
    {
      "action": "exec",
      "codecell_id": "lastAddedCellId",
      "need_output": true
    }
  ]
}
```

#### 流式响应 (NDJSON)

每行一个JSON对象，action包装在`"action"`键中：

```
{"action": {"action": "new_chapter", "content": "数据收集与清单"}}
{"action": {"action": "add", "shot_type": "dialogue", "content": "We begin..."}}
{"action": {"action": "add", "shot_type": "action", "content": "import pandas..."}}
{"action": {"action": "exec", "codecell_id": "lastAddedCellId", "need_output": true}}
```

**注意事项**:
- 每行必须是完整的JSON对象
- 行之间用`\n`分隔
- Client端使用buffer机制处理不完整的行

### Action 类型

| Action Type | 用途 | 必需字段 |
|------------|------|---------|
| `add` | 添加内容 | `content`, `shot_type` |
| `exec` | 执行代码 | `codecell_id` |
| `new_chapter` | 创建章节 | `content` |
| `new_section` | 创建小节 | `content` |
| `is_thinking` | 开始思考 | `thinking_text` (可选) |
| `finish_thinking` | 结束思考 | 无 |
| `update_title` | 更新标题 | `title` |

详细说明见 [ACTION_PROTOCOL.md](./ACTION.md)

---

## 📄 Reflection Mechanism (状态转换)

### 概述

Reflection是行为完成后的状态转换机制，通过XML格式文件描述状态转换信息。

### Reflection XML 格式

```xml
<reflection current_step_is_complete="true">
  <evaluation>
    <artifacts_produced>
      <artifact name="data_existence_report" status="complete">
        Description of artifact
      </artifact>
    </artifacts_produced>

    <acceptance_validation>
      <criterion status="passed">os.path.exists("./assets/housing.csv")==True</criterion>
    </acceptance_validation>

    <goal_achievement>
      <status>achieved</status>
      <reasoning>All criteria met...</reasoning>
    </goal_achievement>
  </evaluation>

  <decision>
    <next_state>STATE_Step_Running</next_state>
    <reasoning>Behavior complete, transition to next step</reasoning>
  </decision>

  <context_for_next>
    <variables_produced>
      <variable name="df_raw" value="DataFrame with 2930 rows">
        Loaded dataset
      </variable>
    </variables_produced>
  </context_for_next>

  <outputs_tracking_update>
    <produced><artifact>data_existence_report</artifact></produced>
    <in_progress></in_progress>
    <remaining></remaining>
  </outputs_tracking_update>
</reflection>
```

### Apply Transition 工具

**命令**:
```bash
python main.py apply-transition \
  --state-file <当前状态JSON> \
  --transition-file <转换XML> \
  --output <输出状态JSON>
```

**功能**:
1. 解析Reflection XML
2. 更新FSM状态
3. 添加新变量
4. 移动已完成的行为/步骤
5. 生成新状态JSON

---

## 🔄 完整工作流程

### 典型执行流程

```
1. Step 开始
   ↓
2. Client → Planning API: 检查目标
   ↓
3. Planning API 响应:
   - targetAchieved: false
   - context_filter: { variables_to_include: [...] }
   ↓
4. Client 应用 context_filter
   ↓
5. Client → Generating API: 生成Actions
   ↓
6. Generating API 流式返回:
   {"action": {"action": "add", ...}}
   {"action": {"action": "exec", ...}}
   ↓
7. Client 执行Actions
   ↓
8. Client → Planning API: 发送Feedback
   ↓
9. Planning API 响应:
   - transition.continue_behaviors: true/false
   - targetAchieved: true/false
   ↓
10a. continue_behaviors = true → 回到步骤5 (新Behavior)
10b. targetAchieved = true → 完成Step，进入下一Step
```

---

## ⚙️ 环境配置

### 默认端点

```python
DSLC_BASE_URL = "http://localhost:28600"
FEEDBACK_API_URL = "http://localhost:28600/planning"
BEHAVIOR_API_URL = "http://localhost:28600/generating"
```

### 环境变量

```bash
# .env 文件
DSLC_BASE_URL=http://your-server:28600
BACKEND_BASE_URL=http://your-backend:18600
NOTEBOOK_ID=optional-notebook-id
LOG_LEVEL=INFO
MAX_EXECUTION_STEPS=0  # 0 = 无限制
INTERACTIVE_MODE=false
USE_REMOTE_EXECUTION=true
```

---

## 🔍 Context Filter 协议

### 目的

减少token消耗，优化API性能，只传递相关信息。

### variables_to_include

指定完整传递的变量列表。

**错误处理**:
- 如果变量不存在，Client必须在`effects.current`中打`⚠️ WARN`
- 回退到`variables_to_summarize`策略
- 记录日志供调试

### variables_to_summarize

对大型变量进行摘要。

**摘要策略**:
- `shape_only` - 只传递shape
- `describe_only` - 只传递统计摘要
- `head_only` - 只传递前几行
- `last_N_only` - 只传递最后N个元素

### effects_config

配置effects的传递方式。

```json
"effects_config": {
  "include_current": true,
  "current_limit": 3,
  "include_history": false,
  "history_limit": 0
}
```

### focus_to_include

指定传递哪些层级的focus。

```json
"focus_to_include": ["behaviors", "steps"]
```

通常包含当前层级和上层指导，不包含`stages`（太宏观）。

---

## 📊 响应示例

### Planning API 完整响应示例

```json
{
  "targetAchieved": false,
  "transition": {
    "continue_behaviors": true,
    "target_achieved": false
  },
  "context_update": {
    "variables": {
      "analysis_checkpoint": "behavior_003_started"
    },
    "progress_update": {
      "level": "behaviors",
      "focus": "【Behavior 003: 执行缺失值填充操作】\n\n## 当前状态分析\n已完成behavior_001和behavior_002，生成了missing_summary和missing_groups。\n\n## 关键产出目标\n- df_working: 缺失值填充后的工作数据集\n- imputation_log: 填充操作记录\n\n## 建议执行方法\n1. 针对高缺失特征使用语义填充\n2. 针对车库相关特征使用连带填充\n3. 记录所有填充操作到imputation_log\n"
    }
  },
  "context_filter": {
    "variables_to_include": ["df", "missing_groups", "missing_summary"],
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

### Generating API 流式响应示例

```
{"action": {"action": "new_section", "content": "缺失值填充"}}
{"action": {"action": "add", "shot_type": "dialogue", "content": "针对高缺失率特征..."}}
{"action": {"action": "add", "shot_type": "action", "content": "# 语义填充\ndf_working = df.copy()"}}
{"action": {"action": "exec", "codecell_id": "lastAddedCellId", "need_output": true}}
{"action": {"action": "is_thinking", "thinking_text": "检查填充结果...", "agent_name": "DataAnalyst"}}
{"action": {"action": "finish_thinking"}}
{"action": {"action": "add", "shot_type": "dialogue", "content": "填充完成，共处理19个特征"}}
```

---

## ✅ 实现检查清单

### Planning API

- [ ] 支持POST请求
- [ ] 解析完整的observation结构
- [ ] 返回`targetAchieved`字段
- [ ] 返回`transition`对象
- [ ] 支持`context_update`（可选）
- [ ] 支持`context_filter`（可选）
- [ ] 处理`behavior_feedback`（Feedback场景）

### Generating API

- [ ] 支持POST请求
- [ ] 解析筛选后的observation
- [ ] 支持非流式响应（返回actions数组）
- [ ] 支持流式响应（NDJSON格式）
- [ ] Action包装在`{"action": {...}}`中
- [ ] 支持所有Action类型（见ACTION.md）

### Reflection Mechanism

- [ ] 生成Reflection XML文件
- [ ] 包含`current_step_is_complete`属性
- [ ] 包含`<decision><next_state>`节点
- [ ] 包含`<context_for_next><variables_produced>`
- [ ] 包含`<outputs_tracking_update>`

### 错误处理

- [ ] API超时处理
- [ ] 无效请求格式处理
- [ ] 变量不存在警告
- [ ] 流式响应中断处理

---

## 🔗 相关文档

- [STATE_MACHINE.md](./STATE_MACHINE.md) - 状态机协议和状态转移规则
- [API.md](./API.md) - 完整API交互协议
- [OBSERVATION.md](./OBSERVATION.md) - Observation结构和Context Filter
- [ACTION.md](./ACTION.md) - Action类型和格式详解

---

**Last Updated**: 2025-11-10
**Version**: 1.0
