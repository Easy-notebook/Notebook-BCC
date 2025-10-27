# 最终架构设计

## 1. 执行层级结构

```
Workflow (工作流)
  └─ Stage (阶段) - e.g., chapter_0_planning
      └─ Step (步骤) - e.g., section_1_design_workflow
          └─ Behavior (行为) - 一次API交互
              └─ Action (动作) - add/execute/update等
                  └─ Section (章节) - 内容组织标记
```

**关键点**：
- 一个Step = 多个Behaviors（不是一个！）
- 每个Behavior = 从API获取的一组Actions
- 循环执行Behaviors直到`targetAchieved = true`

## 2. Behavior循环机制

```
Step开始
  │
  ├─→ [API调用] GET /v1/actions
  │   传入: stage_id, step_id, context, behavior_iteration
  │   返回: {behavior: {...}, actions: [...], transition: {...}}
  │
  ├─→ [本地执行] 执行所有actions
  │   - add_section: 添加章节标题
  │   - add_content: 添加内容
  │   - execute_code: 执行代码
  │
  ├─→ [API调用] POST /v1/reflection
  │   传入: 执行结果 + 更新后的context
  │   返回: {targetAchieved: bool, ...}
  │
  ├─→ [判断] targetAchieved?
  │   false → 回到第一步（下一个behavior）
  │   true  → Step完成
  │
  └─ Step结束
```

## 3. Request Payload 结构

```json
{
  "observation": {
    "location": {
      "current_stage_id": "chapter_3_data_insight",
      "current_step_id": "section_1_workflow_initialization",
      "behavior_id": "behavior_003",
      "behavior_iteration": 3
    },
    "context": {
      "variables": {
        "csv_file_path": "data.csv",
        "problem_description": "训练房价预测模型"
      },
      "toDoList": [
        "Section 2: 数据状态评估",
        "Section 3: 变量定义"
      ],
      "effects": {
        "current": [],
        "history": [{"action": "load_data", "result": "success"}]
      },
      "section_progress": {
        "current_section_id": "data_loading",
        "current_section_number": 2,
        "completed_sections": ["introduction"]
      },
      "notebook": {
        "title": "数据分析",
        "cells": [...]
      }
    }
  },
  "behavior_feedback": {
    "actions_executed": 5,
    "sections_added": 1,
    "last_action_result": "success"
  },
  "options": {
    "stream": true
  }
}
```

## 4. Response Payload 结构

```json
{
  "behavior": {
    "id": "behavior_004",
    "iteration": 4,
    "target": "完成Section 2: 数据状态评估"
  },
  "actions": [
    {
      "type": "add_content",
      "content_type": "text",
      "content": "## Section 2: 数据状态评估",
      "metadata": {
        "is_section": true,
        "section_id": "data_assessment",
        "section_number": 2
      }
    },
    {
      "type": "add_content",
      "content_type": "code",
      "content": "data.info()"
    }
  ],
  "transition": {
    "strategy": "server_controlled",
    "next_stage_id": null,
    "next_step_id": null,
    "continue_behaviors": true,
    "target_achieved": false,
    "workflow_update": null
  },
  "context_update": {
    "variables": {
      "data_shape": "(2930, 82)"
    },
    "todo_list_update": {
      "operation": "remove",
      "items": ["Section 2: 数据状态评估"]
    },
    "section_progress": {
      "current_section_id": "variable_definition",
      "current_section_number": 3
    }
  },
  "metadata": {
    "target_achieved": false,
    "estimated_remaining_behaviors": 2
  }
}
```

## 5. 核心数据结构

### WorkflowContext
```python
@dataclass
class WorkflowContext:
    current_stage_id: str
    current_step_id: str
    current_behavior_id: str          # 新增
    current_behavior_actions: List    # 已有，需暴露
    current_action_index: int         # 已有
```

### SectionProgress (新增)
```python
@dataclass
class SectionProgress:
    current_section_id: Optional[str]
    current_section_number: Optional[int]
    completed_sections: List[str]
    all: List[str]  # 所有计划的sections (由workflow_update设置)
```

### ActionMetadata
```python
@dataclass
class ActionMetadata:
    is_step: bool
    is_chapter: bool
    is_section: bool              # 新增
    section_id: Optional[str]     # 新增
    section_number: Optional[int] # 新增
```

## 6. 关键字段说明

### 新增字段

| 字段 | 类型 | 位置 | 作用 |
|------|------|------|------|
| `behavior_id` | string | location | 标识当前behavior实例 |
| `behavior_iteration` | int | location | 记录这是第几个behavior |
| `behavior_feedback` | object | request | 上一个behavior的执行结果 |
| `section_progress` | object | context | 追踪章节完成情况 |
| `section_progress.all` | list | section_progress | 所有计划的sections列表（由workflow_update设置）|
| `is_section` | bool | action.metadata | 标记这个action是章节标题 |
| `section_id` | string | action.metadata | 章节唯一标识 |
| `section_number` | int | action.metadata | 章节编号 |
| `continue_behaviors` | bool | transition | 服务端告知是否需要更多behaviors |
| `todo_list_update` | object | context_update | 服务端更新待办列表 |

### 重命名字段

| 旧名称 | 新名称 | 原因 |
|-------|--------|------|
| `step_index` | `current_step_id` | 实际是ID不是index |
| `stage_id` | `current_stage_id` | 明确是当前位置 |
| `state` | `context` | 区分POMDP的state概念 |
| `toDoList` | `todo_list` | Python命名规范 |
| `stageStatus` | ~~删除~~ | 从不更新 |
| `shotType` | `content_type` | 更明确 |
| `targetAchieved` | `target_achieved` | Python命名规范 |

### 删除字段

| 字段 | 原因 |
|------|------|
| `stageStatus` | 从不更新，始终为 `{}` |
| `checklist` | 从不使用，始终为空 |
| `thinking` | 仅内部使用，不在payload中 |
| `updated_steps` | 定义了但从未使用 |

## 7. 核心原则

### POMDP对齐

**服务端（隐藏状态）**：
- 完整的workflow结构
- 所有stage/step定义
- Behavior生成策略（决定需要几个behaviors）
- Section模板和顺序

**客户端（观察状态）**：
- 当前位置（stage/step/behavior）
- 执行上下文（variables/todo_list/effects/sections）
- 局部action队列

**通信协议**：
- 请求：观察（位置 + 上下文 + 反馈）
- 响应：决策（actions + transition + context_update）

### 服务端控制

- ✅ 服务端决定所有stage/step转换
- ✅ 服务端决定需要多少个behaviors
- ✅ 服务端通过todo_list引导内容生成
- ✅ 客户端执行actions并反馈结果

### TodoList驱动

```python
# 服务端逻辑示例
if "Section 2: 数据评估" in request.todo_list:
    # 生成Section 2相关的actions
    return {
        "actions": generate_section_2_actions(),
        "context_update": {
            "todo_list_update": {
                "operation": "remove",
                "items": ["Section 2: 数据评估"]
            }
        }
    }
```

## 8. 优化效果

### Payload大小
- 旧：~4.5KB
- 新：~3.8KB
- 优化：15%减少 + 更清晰的结构

### 功能提升
- ✅ Behavior级别的执行追踪
- ✅ Section组织的结构化内容
- ✅ TodoList驱动的智能生成
- ✅ 服务端完全控制流程
- ✅ 零客户端/服务端同步问题

### 代码质量
- ✅ 清晰的命名（snake_case）
- ✅ 明确的层级关系
- ✅ 易于测试和维护
- ✅ POMDP理论对齐
