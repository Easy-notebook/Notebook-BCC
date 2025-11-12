# Notebook-BCC 协议文档索引

## 📚 文档总览

本目录包含 Notebook-BCC 系统的完整协议规范，涵盖状态机、API交互、数据观测和动作执行等核心机制。

---

## 🗂️ 协议文档列表

### 核心规范文档

| 文档 | 用途 | 适用角色 |
|-----|------|---------|
| [API_REQUIREMENTS.md](./API_REQUIREMENTS.md) | **API需求总结** - 后端开发必读 | 后端开发者 |
| [STATE_MACHINE.md](./STATE_MACHINE.md) | 状态机协议和状态转移规则 | 全栈开发者、架构师 |
| [API.md](./API.md) | 完整API交互协议 | 后端/前端开发者 |
| [OBSERVATION.md](./OBSERVATION.md) | Observation结构和Context Filter | 后端开发者、AI工程师 |
| [ACTION.md](./ACTION.md) | Action类型和格式详解 | 前端开发者、AI工程师 |

### 新增：系统设计与实现指南

| 文档 | 用途 | 适用角色 |
|-----|------|---------|
| [STATE_MACHINE_SPECIFICATION.md](./STATE_MACHINE_SPECIFICATION.md) | **状态机完整规范** - 包含所有状态定义、转换关系、示例payloads | 架构师、全栈开发者 |
| [PROMPT_DESIGN_PATTERNS.md](./PROMPT_DESIGN_PATTERNS.md) | **提示词设计模式** - Agent设计原则、优化经验、反模式总结 | AI工程师、提示词工程师 |
| [STATE_TRANSITION_QUICK_REFERENCE.md](./STATE_TRANSITION_QUICK_REFERENCE.md) | **快速参考指南** - 状态转换速查表、调试清单 | 所有开发者 |

---

## 🚀 快速开始

### 我是后端开发者

**最重要**: [API_REQUIREMENTS.md](./API_REQUIREMENTS.md)

**推荐阅读顺序**:
1. [API_REQUIREMENTS.md](./API_REQUIREMENTS.md) - 了解需要实现的API端点
2. [API.md](./API.md) - 深入理解API交互协议
3. [OBSERVATION.md](./OBSERVATION.md) - 理解请求/响应数据结构
4. [STATE_MACHINE.md](./STATE_MACHINE.md) - 理解系统状态流转

### 我是前端开发者

**推荐阅读顺序**:
1. [STATE_MACHINE.md](./STATE_MACHINE.md) - 理解系统状态流转
2. [ACTION.md](./ACTION.md) - 了解可执行的动作类型
3. [API.md](./API.md) - 了解如何调用后端API
4. [OBSERVATION.md](./OBSERVATION.md) - 理解状态数据结构

### 我是AI工程师

**推荐阅读顺序**:
1. [STATE_MACHINE_SPECIFICATION.md](./STATE_MACHINE_SPECIFICATION.md) - **必读** 完整状态机规范
2. [PROMPT_DESIGN_PATTERNS.md](./PROMPT_DESIGN_PATTERNS.md) - **必读** 提示词设计最佳实践
3. [OBSERVATION.md](./OBSERVATION.md) - 理解观测数据结构
4. [ACTION.md](./ACTION.md) - 了解POMDP动作空间
5. [STATE_TRANSITION_QUICK_REFERENCE.md](./STATE_TRANSITION_QUICK_REFERENCE.md) - 快速查询状态转换

### 我是架构师/系统设计者

**推荐阅读顺序**:
1. [STATE_MACHINE_SPECIFICATION.md](./STATE_MACHINE_SPECIFICATION.md) - **核心** 完整FSM规范和设计原则
2. [STATE_TRANSITION_QUICK_REFERENCE.md](./STATE_TRANSITION_QUICK_REFERENCE.md) - 状态转换可视化图谱
3. [PROMPT_DESIGN_PATTERNS.md](./PROMPT_DESIGN_PATTERNS.md) - Agent角色和职责分离
4. [API_REQUIREMENTS.md](./API_REQUIREMENTS.md) - API设计要求
5. [STATE_MACHINE.md](./STATE_MACHINE.md) - 历史状态机文档参考

---

## 📖 核心概念速查

### 系统架构

```
POMDP Framework
    ├─ Observation (观测) - 部分可观测的状态信息
    ├─ Action (动作) - 可执行的操作
    ├─ State Transition (状态转移) - 状态机控制流程
    └─ Reward (奖励) - 目标达成度评估
```

### API 端点

| 端点 | 用途 | 文档 |
|-----|------|------|
| `POST /planning` | 目标检查与规划 | [API_REQUIREMENTS.md](./API_REQUIREMENTS.md#-api-1-planning-api) |
| `POST /generating` | 生成Actions | [API_REQUIREMENTS.md](./API_REQUIREMENTS.md#-api-2-generating-api) |

### 状态机核心状态

| 状态 | 说明 | 文档 |
|------|------|------|
| `idle` | 初始状态 | [STATE_MACHINE.md](./STATE_MACHINE.md#-状态定义) |
| `stage_running` | Stage执行中 | [STATE_MACHINE.md](./STATE_MACHINE.md#-状态定义) |
| `step_running` | Step执行中 | [STATE_MACHINE.md](./STATE_MACHINE.md#-状态定义) |
| `behavior_running` | Behavior执行中 | [STATE_MACHINE.md](./STATE_MACHINE.md#-状态定义) |
| `action_running` | Action执行中 | [STATE_MACHINE.md](./STATE_MACHINE.md#-状态定义) |
| `action_completed` | Action完成 | [STATE_MACHINE.md](./STATE_MACHINE.md#-状态定义) |

### Action 类型

| Action | 用途 | 文档 |
|--------|------|------|
| `add` | 添加内容 | [ACTION.md](./ACTION.md#1-add_action-添加内容) |
| `exec` | 执行代码 | [ACTION.md](./ACTION.md#2-exec_code-执行代码) |
| `new_chapter` | 创建章节 | [ACTION.md](./ACTION.md#5-new_chapter-创建章节) |
| `new_section` | 创建小节 | [ACTION.md](./ACTION.md#6-new_section-创建小节) |
| `is_thinking` | 开始思考 | [ACTION.md](./ACTION.md#3-is_thinking-开始思考) |
| `finish_thinking` | 结束思考 | [ACTION.md](./ACTION.md#4-finish_thinking-结束思考) |
| `update_title` | 更新标题 | [ACTION.md](./ACTION.md#7-update_title-更新标题) |

---

## 🔄 典型工作流程

### Planning First Protocol

```
Step Start
    ↓
POST /planning (检查目标)
    ↓
targetAchieved?
    ├─ true → Complete Step
    └─ false → POST /generating
                    ↓
                Execute Actions
                    ↓
                POST /planning (Feedback)
                    ↓
                Continue or Complete
```

详见: [API.md - Planning First Protocol](./API.md#1-planning-first-protocol-规划优先协议)

### Behavior Loop (Server控制)

```
Planning API → targetAchieved: false
    ↓
Generating API → Actions
    ↓
Client 执行 Actions
    ↓
Planning API (Feedback)
    ↓
transition.continue_behaviors?
    ├─ true → 回到 Generating API
    └─ false → Complete Step
```

详见: [STATE_MACHINE.md - Behavior Loop](./STATE_MACHINE.md#场景-2-behavior-迭代)

### Reflection Mechanism

```
Behavior 完成
    ↓
生成 Reflection XML
    ↓
apply-transition 工具
    ↓
新状态 JSON
    ↓
继续执行
```

详见: [API.md - Reflection Mechanism](./API.md#-reflection-mechanism-反思机制)

---

## 📋 常见问题

### Q1: Planning API 和 Generating API 有什么区别?

**Planning API** (`/planning`):
- 负责目标检查和策略决策
- 判断目标是否达成
- 控制Behavior循环
- 返回`targetAchieved`和`context_update`

**Generating API** (`/generating`):
- 负责内容生成
- 生成具体的Actions列表
- 支持流式返回
- 不涉及目标判断

详见: [API.md - API工作流程](./API.md#-api-工作流程)

### Q2: 什么是 Context Filter?

Context Filter 是 Planning API 返回的筛选指令，告诉Client在调用Generating API时应该传递哪些信息，用于:
- 减少token消耗
- 优化提示词质量
- 提高API性能

详见: [OBSERVATION.md - Context Filter 协议](./OBSERVATION.md#-context-filter-协议)

### Q3: 如何处理变量不存在的情况?

当`context_filter.variables_to_include`中的变量不存在时:
1. ⚠️ 不要静默丢弃
2. 在`effects.current`中打WARN
3. 回退到`variables_to_summarize`策略
4. 记录日志供调试

详见: [OBSERVATION.md - Context Filter - variables_to_include](./OBSERVATION.md#1-variables_to_include)

### Q4: Reflection XML 的作用是什么?

Reflection XML 用于描述行为完成后的状态转换:
- 标记行为是否完成 (`current_step_is_complete`)
- 指定下一个FSM状态 (`<decision><next_state>`)
- 提供新产生的变量 (`<variables_produced>`)
- 更新产出追踪 (`<outputs_tracking_update>`)

详见: [API.md - Reflection Mechanism](./API.md#-reflection-mechanism-反思机制)

### Q5: Action 的 shot_type 有什么含义?

`shot_type` 指示Action的显示类型:
- `dialogue` - 对话/文本内容 (markdown cell)
- `observation` - 观察/输出内容 (markdown cell)
- `action` - 代码内容 (code cell)

详见: [ACTION.md - Shot Type 说明](./ACTION.md#-shot-type-说明)

---

## 🛠️ 命令行工具

### apply-transition

**用途**: 根据Reflection XML生成下一个状态JSON

```bash
python main.py apply-transition \
  --state-file <当前状态JSON> \
  --transition-file <转换XML> \
  --output <输出状态JSON>
```

**示例**:
```bash
python main.py apply-transition \
  --state-file docs/examples/ames_housing/payloads/04_STATE_Action_Completed.json \
  --transition-file docs/examples/ames_housing/payloads/04_Transition_Complete_behavior.xml \
  --output docs/examples/ames_housing/payloads/05_STATE_Step_Running.json
```

详见: [API.md - Apply Transition 工具](./API.md#apply-transition-工具)

---

## 📊 数据结构速查

### Observation 结构

```json
{
  "observation": {
    "location": {
      "current": { "stage_id", "step_id", "behavior_id", "behavior_iteration" },
      "progress": { "stages", "steps", "behaviors" },
      "goals": { "stage", "step", "behavior" }
    },
    "context": {
      "variables": { /* 环境变量 */ },
      "effects": { "current": [], "history": [] },
      "notebook": { /* Notebook状态 */ },
      "FSM": { "state", "last_transition" }
    }
  },
  "options": { "stream": true/false }
}
```

详见: [OBSERVATION.md - 完整 Observation 结构](./OBSERVATION.md#-完整-observation-结构)

### Planning API 响应

```json
{
  "targetAchieved": boolean,
  "transition": { "continue_behaviors", "target_achieved" },
  "context_update": { "variables", "progress_update", ... },
  "context_filter": { "variables_to_include", ... }
}
```

详见: [API_REQUIREMENTS.md - Planning API 响应格式](./API_REQUIREMENTS.md#响应格式)

### Action 格式

```json
{
  "action": "add|exec|new_chapter|...",
  "shot_type": "dialogue|observation|action",
  "content": "...",
  /* 其他特定字段 */
}
```

详见: [ACTION.md - 详细 Action 规范](./ACTION.md#-详细-action-规范)

---

## 🔐 重要原则

### 1. Planning First

每个Step开始前，**必须先调用Planning API**：

```python
# ✅ 正确
response = planning_api.check_step_goal(observation)
if response['targetAchieved']:
    complete_step()
else:
    start_behavior()

# ❌ 错误：直接调用Generating API
actions = generating_api.get_actions(observation)  # 跳过Planning
```

详见: [API.md - Planning First Protocol](./API.md#1-planning-first-protocol-规划优先协议)

### 2. Server控制Behavior Loop

**Server (Planning API)** 通过`transition.continue_behaviors`控制Behavior循环

**Client** 只负责导航和执行

详见: [API.md - 控制职责分离](./API.md#2-控制职责分离)

### 3. 变量不存在必须WARN

当`context_filter`请求的变量不存在时，Client必须:
- 在`effects.current`中打`⚠️ WARN`
- 记录日志
- 回退到`summarize`策略

详见: [OBSERVATION.md - 变量不存在处理](./OBSERVATION.md#1-variables_to_include)

---

## 📘 新文档亮点

### STATE_MACHINE_SPECIFICATION.md

本文档提供了完整的状态机规范，包括：

- **6个核心状态定义**: IDLE, STAGE_RUNNING, STEP_RUNNING, BEHAVIOR_RUNNING, BEHAVIOR_COMPLETED, STEP_COMPLETED
- **6个状态转换详解**: 每个转换的触发条件、输入输出、Agent职责
- **完整示例**: 基于Ames Housing案例的真实状态流转演示
- **设计原则**: Artifact-First, Deterministic, PCS-Aligned等核心理念
- **错误处理**: Behavior重试、Step失败、变量依赖缺失的处理策略

**适合**: 新加入团队的开发者快速理解整个系统架构

### PROMPT_DESIGN_PATTERNS.md

本文档总结了6个Agent的提示词设计经验：

- **Stage-Planner Agent**: 如何进行阶段级别分解
- **Step-Planner Agent**: 如何进行步骤级别细化
- **Behavior Arrangement Agent**: 如何选择合适的执行Agent
- **Action-Generator Agent**: 如何生成高质量的Notebook内容
- **Behavior Reflection Agent**: 如何评估行为完成度
- **Stage Reflection Agent**: 如何进行阶段反思和变量管理

**核心价值**:
- ✅ **设计模式库**: 可复用的XML模板
- ✅ **优化历史**: 基于实际迭代的改进经验
- ✅ **反模式总结**: 7个常见错误及解决方案
- ✅ **检查清单**: 每类Agent的质量保证清单

**适合**: AI工程师、提示词工程师，以及需要优化Agent性能的开发者

### STATE_TRANSITION_QUICK_REFERENCE.md

本文档是一个便捷的速查手册：

- **可视化状态图**: ASCII艺术风格的状态机流程图
- **转换总结表**: 一目了然的转换关系矩阵
- **状态特征速查**: 每个状态的JSON结构示例
- **决策逻辑流程**: Behavior/Stage reflection的决策算法
- **变量生命周期**: 变量在各状态间的演化过程
- **调试清单**: 常见问题的排查步骤和快速修复

**适合**: 所有开发者日常开发时的案头参考

---

## 🔗 外部资源

- [GitHub Repository](https://github.com/your-org/Notebook-BCC)
- [示例项目: Ames Housing](../examples/ames_housing/)
- [问题反馈](https://github.com/your-org/Notebook-BCC/issues)

---

## 📝 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| 1.0 | 2025-11-10 | 初始版本，整合所有协议文档 |
| 2.0 | 2025-11-10 | 添加Reflection Mechanism，更新API协议 |
| 3.0 | 2025-11-12 | **重大更新** - 新增三个核心文档：状态机完整规范、提示词设计模式、快速参考指南 |

---

**Last Updated**: 2025-11-12
**Maintainer**: Notebook-BCC Team
