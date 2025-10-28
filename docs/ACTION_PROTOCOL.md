# Notebook-BCC Action 协议规范

## 📋 概述

Action 是 Notebook-BCC 工作流中的最小执行单元。每个 Action 代表一个具体的操作，如添加文本、执行代码、创建章节等。

---

## 🧠 POMDP 设计原理

### 什么是 POMDP

Notebook-BCC 采用 **POMDP (Partially Observable Markov Decision Process)** 设计：

```
POMDP = (S, A, O, T, R, Ω)

S - States:        Notebook 的状态（内容、结构、变量等）
A - Actions:       可执行的操作（11种 Action 类型）
O - Observations:  观测数据（location, context, progress）
T - Transitions:   状态转移函数（Action 如何改变状态）
R - Rewards:       奖励函数（目标达成度）
Ω - Observations:  观测函数（从状态生成观测）
```

### POMDP Payload 结构

每个 API 请求都包含完整的 POMDP 观测：

```json
{
  "observation": {
    "location": {
      // 当前位置（部分可观测）
      "current": {
        "stage_id": "data_analysis",
        "step_id": "load_data",
        "behavior_id": "behavior_003",
        "behavior_iteration": 3
      },
      "progress": {
        // 进度追踪（历史信息）
        "stages": {"completed": [...], "current": "...", "remaining": [...]},
        "steps": {"completed": [...], "current": "...", "remaining": [...]},
        "behaviors": {"completed": [...], "current": "...", "iteration": 3}
      },
      "goals": {
        // 目标定义
        "stage": "Complete data analysis",
        "step": "Load and preprocess data",
        "behavior": null  // 动态生成
      }
    },
    "context": {
      // 工作上下文（状态的可观测部分）
      "variables": {"row_count": 1000},        // 环境变量
      "toDoList": ["Check data quality"],       // 任务列表
      "effects": {"current": ["Loaded CSV"]},   // 效果历史
      "notebook": {                             // Notebook 状态
        "cells": [...],
        "metadata": {...}
      },
      "FSM": {                                  // 状态机追踪
        "state": "BEHAVIOR_RUNNING",
        "transition": [...]
      }
    }
  },
  "options": {"stream": true}
}
```

### Action 在 POMDP 中的作用

**Actions 是状态转移函数**：

```
S(t+1) = T(S(t), Action)

当前状态 + Action = 新状态
```

每个 Action 执行后会：
1. **改变 Notebook 状态** - 添加/修改 cells
2. **更新 Context** - 修改 variables、effects、toDoList
3. **影响观测** - 新的观测反映状态变化
4. **触发奖励计算** - 评估目标达成度

### 为什么需要不同的 Action 类型

| 状态维度 | 对应 Action | 作用 |
|---------|------------|------|
| **内容状态** | `add`, `new_chapter`, `new_section` | 构建 Notebook 结构和内容 |
| **计算状态** | `exec` | 执行代码，产生副作用（变量、输出） |
| **认知状态** | `is_thinking`, `finish_thinking` | 显示推理过程，增强可解释性 |
| **元数据状态** | `update_title`, `update_workflow` | 修改工作流结构 |
| **流程状态** | `end_phase`, `next_event` | 控制状态转移 |

---

## 🎯 Action 类型总览

| Action Type | 类型标识 | 用途 | Shot Type |
|------------|---------|------|-----------|
| **ADD_ACTION** | `add` | 添加内容到 Notebook | `dialogue` / `observation` |
| **EXEC_CODE** | `exec` | 执行代码单元格 | `action` |
| **IS_THINKING** | `is_thinking` | 开始思考过程 | `dialogue` |
| **FINISH_THINKING** | `finish_thinking` | 结束思考过程 | `dialogue` |
| **NEW_CHAPTER** | `new_chapter` | 创建新章节 (##) | `dialogue` |
| **NEW_SECTION** | `new_section` | 创建新小节 (###) | `dialogue` |
| **UPDATE_TITLE** | `update_title` | 更新 Notebook 标题 | `dialogue` |
| **UPDATE_WORKFLOW** | `update_workflow` | 更新工作流模板 | `action` |
| **UPDATE_STEP_LIST** | `update_stage_steps` | 更新阶段步骤列表 | `action` |
| **COMPLETE_STEP** | `end_phase` | 完成当前步骤 | `action` |
| **NEXT_EVENT** | `next_event` | 触发下一个事件 | `action` |

---

## 📝 详细 Action 规范

### 1. ADD_ACTION (添加内容)

**用途**: 向 Notebook 添加文本或代码内容

**POMDP 作用**:
- **状态维度**: 内容状态 (Notebook cells)
- **状态转移**: `S.notebook.cells → S.notebook.cells + [new_cell]`
- **观测影响**: 新 cell 在下次观测的 `context.notebook` 中可见
- **副作用**: 更新 `context.effects.current` 和 AI Context

**状态转移示例**:
```python
# 执行前状态
S(t) = {
  notebook: { cells: [cell_1, cell_2] },
  effects: { current: ["Previous action"] }
}

# 执行 add(content="Hello World", shot_type="dialogue")
Action = { action: "add", content: "Hello World", shot_type: "dialogue" }

# 执行后状态
S(t+1) = {
  notebook: { cells: [cell_1, cell_2, cell_3(markdown)] },
  effects: { current: ["Added content: Hello World"] }
}
```

**格式**:
```json
{
  "action": "add",
  "shot_type": "dialogue",  // "dialogue" 或 "observation"
  "content": "要添加的内容",
  "store_id": "optional-id",
  "metadata": {
    "is_step": false,
    "is_chapter": false,
    "is_section": false,
    "extra": {}
  }
}
```

**Shot Type 说明**:
- `dialogue` - 普通文本内容
- `observation` - 观察/输出内容
- `action` - 代码内容

**示例**:
```json
{
  "action": "add",
  "shot_type": "dialogue",
  "content": "## 数据分析报告\n\n本报告分析了..."
}
```

**处理流程**:
1. 清理内容（移除不必要的前缀）
2. 根据 `shot_type` 确定 cell 类型
3. 创建新的 cell 并添加到 Notebook
4. 更新 AI Context 的 effect

---

### 2. EXEC_CODE (执行代码)

**用途**: 执行指定的代码单元格

**POMDP 作用**:
- **状态维度**: 计算状态 (环境变量、输出)
- **状态转移**: `S.variables → S.variables'` (代码执行产生副作用)
- **观测影响**: 执行结果添加到 cell 的 outputs，并更新 `context.variables`
- **副作用**: 可能改变运行时环境（定义变量、导入库、生成文件等）

**状态转移示例**:
```python
# 执行前状态
S(t) = {
  notebook: { cells: [code_cell("x = 5")] },
  variables: {},
  effects: { current: [] }
}

# 执行 exec(codecell_id="code-1", need_output=true)
Action = { action: "exec", codecell_id: "code-1" }

# 执行后状态
S(t+1) = {
  notebook: { cells: [code_cell("x = 5", outputs=[{result: "x=5"}])] },
  variables: { x: 5 },  # 环境中新增变量
  effects: { current: ["Executed code: x = 5", "Output: x=5"] }
}
```

**格式**:
```json
{
  "action": "exec",
  "codecell_id": "code-cell-id",
  "need_output": true,
  "auto_debug": false,
  "keep_debug_button_visible": false
}
```

**字段说明**:
- `codecell_id` - 要执行的代码单元格 ID (必需)
- `need_output` - 是否需要输出结果 (默认: true)
- `auto_debug` - 是否自动调试 (默认: false)
- `keep_debug_button_visible` - 是否保持调试按钮可见 (默认: false)

**特殊值**:
- `codecell_id: "lastAddedCellId"` - 执行最后添加的代码单元格

**示例**:
```json
{
  "action": "exec",
  "codecell_id": "code-1",
  "need_output": true
}
```

**处理流程**:
1. 验证 `codecell_id` 存在
2. 清除该单元格之前的输出
3. 通过 `code_executor` 执行代码
4. 将输出添加到单元格
5. 更新 AI Context 的 effect（包含输出）
6. 标记单元格为已更新

**输出格式**:
```python
{
  "output_type": "execute_result",  # 或 "stream" / "error"
  "data": {
    "text/plain": "执行结果"
  }
}
```

---

### 3. IS_THINKING (开始思考)

**用途**: 开始一个思考过程，创建思考单元格

**POMDP 作用**:
- **状态维度**: 认知状态 (Agent 思考过程)
- **状态转移**: `S.thinking_active → true`
- **观测影响**: 在 Notebook 中显示思考过程，提升可解释性
- **副作用**: 创建特殊的 `thinking` 类型 cell，更新 AI Context

**状态转移示例**:
```python
# 执行前状态
S(t) = {
  notebook: { cells: [cell_1] },
  thinking_active: false
}

# 执行 is_thinking(thinking_text="正在分析数据...", agent_name="Analyst")
Action = { action: "is_thinking", thinking_text: "正在分析数据..." }

# 执行后状态
S(t+1) = {
  notebook: { cells: [cell_1, thinking_cell("正在分析数据...")] },
  thinking_active: true,
  effects: { current: ["Agent thinking started"] }
}
```

**实际用途**:
- 提供 AI 推理过程的可视化
- 增强用户对工作流的理解
- 支持调试和验证 Agent 决策

**格式**:
```json
{
  "action": "is_thinking",
  "thinking_text": "正在思考的内容...",
  "agent_name": "Analyst",
  "custom_text": "自定义显示文本",
  "text_array": ["思考片段1", "思考片段2"]
}
```

**字段说明**:
- `thinking_text` - 思考内容 (可选)
- `agent_name` - Agent 名称 (可选)
- `custom_text` - 自定义显示文本 (可选)
- `text_array` - 思考片段数组 (可选)

**示例**:
```json
{
  "action": "is_thinking",
  "thinking_text": "Let me analyze the data distribution...",
  "agent_name": "DataAnalyst"
}
```

**处理流程**:
1. 创建 `thinking` 类型的 cell
2. 设置 thinking 内容和元数据
3. 添加到 Notebook
4. 更新 AI Context effect

---

### 4. FINISH_THINKING (结束思考)

**用途**: 结束当前的思考过程

**POMDP 作用**:
- **状态维度**: 认知状态 (Agent 思考过程)
- **状态转移**: `S.thinking_active → false`
- **观测影响**: 标记思考单元格为完成状态
- **副作用**: 清理 AI Context 中的思考状态

**状态转移示例**:
```python
# 执行前状态
S(t) = {
  notebook: { cells: [thinking_cell(finished=false)] },
  thinking_active: true
}

# 执行 finish_thinking()
Action = { action: "finish_thinking" }

# 执行后状态
S(t+1) = {
  notebook: { cells: [thinking_cell(finished=true)] },
  thinking_active: false,
  effects: { current: ["Thinking completed"] }
}
```

**实际用途**:
- 标记推理过程结束
- 清理思考状态，准备下一个 action

**格式**:
```json
{
  "action": "finish_thinking"
}
```

**处理流程**:
1. 标记当前思考单元格为完成
2. 更新元数据 `finished_thinking: true`
3. 清理 AI Context 中的思考状态

---

### 5. NEW_CHAPTER (创建章节)

**用途**: 创建新的章节标题 (Markdown ## 标题)

**POMDP 作用**:
- **状态维度**: 内容状态 (Notebook 结构)
- **状态转移**: `S.notebook.structure → 新增章节层级`
- **观测影响**: 增加章节计数，更新 Notebook 结构
- **副作用**: 创建带有 `is_chapter` 元数据的 markdown cell

**状态转移示例**:
```python
# 执行前状态
S(t) = {
  notebook: {
    cells: [cell_1],
    chapter_count: 0
  }
}

# 执行 new_chapter(content="数据预处理")
Action = { action: "new_chapter", content: "数据预处理" }

# 执行后状态
S(t+1) = {
  notebook: {
    cells: [cell_1, markdown_cell("## 数据预处理", metadata={is_chapter: true})],
    chapter_count: 1
  },
  effects: { current: ["Created chapter: 数据预处理"] }
}
```

**实际用途**:
- 组织 Notebook 结构，创建主要章节
- 支持文档导航和目录生成
- 标记工作流的主要阶段

**格式**:
```json
{
  "action": "new_chapter",
  "content": "Chapter Title",
  "metadata": {
    "is_chapter": true,
    "chapter_number": 1
  }
}
```

**处理流程**:
1. 递增章节计数器
2. 生成章节 ID (`chapter-{number}`)
3. 添加 `## ` 前缀
4. 创建 markdown cell
5. 更新元数据

**示例**:
```json
{
  "action": "new_chapter",
  "content": "数据预处理"
}
```

**生成结果**:
```markdown
## 数据预处理
```

---

### 6. NEW_SECTION (创建小节)

**用途**: 创建新的小节标题 (Markdown ### 标题)

**POMDP 作用**:
- **状态维度**: 内容状态 (Notebook 结构)
- **状态转移**: `S.notebook.structure → 新增小节层级`
- **观测影响**: 增加小节计数，细化 Notebook 结构
- **副作用**: 创建带有 `is_section` 元数据的 markdown cell

**状态转移示例**:
```python
# 执行前状态
S(t) = {
  notebook: {
    cells: [chapter_cell("## 数据预处理")],
    section_count: 0
  }
}

# 执行 new_section(content="缺失值处理")
Action = { action: "new_section", content: "缺失值处理" }

# 执行后状态
S(t+1) = {
  notebook: {
    cells: [
      chapter_cell("## 数据预处理"),
      markdown_cell("### 缺失值处理", metadata={is_section: true})
    ],
    section_count: 1
  },
  effects: { current: ["Created section: 缺失值处理"] }
}
```

**实际用途**:
- 在章节内创建子主题
- 细化文档结构层次
- 支持更精细的内容组织

**格式**:
```json
{
  "action": "new_section",
  "content": "Section Title",
  "metadata": {
    "is_section": true,
    "section_number": 1
  }
}
```

**处理流程**:
1. 递增小节计数器
2. 生成小节 ID (`section-{number}`)
3. 添加 `### ` 前缀
4. 创建 markdown cell
5. 更新元数据

**示例**:
```json
{
  "action": "new_section",
  "content": "缺失值处理"
}
```

**生成结果**:
```markdown
### 缺失值处理
```

---

### 7. UPDATE_TITLE (更新标题)

**用途**: 更新 Notebook 的主标题

**POMDP 作用**:
- **状态维度**: 元数据状态 (Notebook metadata)
- **状态转移**: `S.notebook.metadata.title → new_title`
- **观测影响**: 更新 Notebook 元数据和首个标题 cell
- **副作用**: 可能修改第一个 cell 为 `# Title` 格式

**状态转移示例**:
```python
# 执行前状态
S(t) = {
  notebook: {
    metadata: { title: "Untitled" },
    cells: []
  }
}

# 执行 update_title(title="销售数据分析报告")
Action = { action: "update_title", title: "销售数据分析报告" }

# 执行后状态
S(t+1) = {
  notebook: {
    metadata: { title: "销售数据分析报告" },
    cells: [markdown_cell("# 销售数据分析报告")]
  },
  effects: { current: ["Updated title: 销售数据分析报告"] }
}
```

**实际用途**:
- 设置 Notebook 的主题和标识
- 生成文档标题页
- 更新工作流元数据

**格式**:
```json
{
  "action": "update_title",
  "title": "New Notebook Title"
}
```

**处理流程**:
1. 更新 Notebook 元数据中的 title
2. 可选：更新第一个 cell 的内容为 `# Title`

**示例**:
```json
{
  "action": "update_title",
  "title": "销售数据分析报告"
}
```

---

### 8. UPDATE_WORKFLOW (更新工作流)

**用途**: 更新整个工作流模板

**POMDP 作用**:
- **状态维度**: 元数据状态 (Workflow definition)
- **状态转移**: `S.workflow → new_workflow` + `S.FSM → WORKFLOW_UPDATE_PENDING`
- **观测影响**: 触发状态机进入 workflow 更新状态
- **副作用**: 返回特殊标志 `workflow_update_pending: true`

**状态转移示例**:
```python
# 执行前状态
S(t) = {
  workflow: {
    name: "Data Analysis",
    stages: [stage1, stage2]
  },
  FSM: { state: "BEHAVIOR_RUNNING" }
}

# 执行 update_workflow(updated_workflow={...})
Action = { action: "update_workflow", updated_workflow: {...} }

# 执行后状态
S(t+1) = {
  workflow: {
    name: "Updated Workflow",
    stages: [stage1, stage2, stage3]  # 更新后的结构
  },
  FSM: { state: "WORKFLOW_UPDATE_PENDING" },  # 状态机转换
  effects: { current: ["Workflow update pending"] }
}
```

**实际用途**:
- 动态调整工作流结构
- 基于运行时决策重新规划 Stages/Steps
- 支持工作流的自适应

**格式**:
```json
{
  "action": "update_workflow",
  "updated_workflow": {
    "name": "Updated Workflow",
    "stages": [
      {
        "id": "stage1",
        "name": "Stage 1",
        "steps": [...]
      }
    ]
  }
}
```

**处理流程**:
1. 验证新工作流格式
2. 标记为 pending update
3. 返回特殊标志通知状态机
4. 状态机转换到 WORKFLOW_UPDATE_PENDING

**特殊返回**:
```python
{
  'workflow_update_pending': True
}
```

---

### 9. UPDATE_STEP_LIST (更新步骤列表)

**用途**: 更新当前阶段的步骤列表

**POMDP 作用**:
- **状态维度**: 元数据状态 (Stage steps)
- **状态转移**: `S.workflow.stages[i].steps → updated_steps`
- **观测影响**: 修改 Stage 的 steps 列表，影响后续导航
- **副作用**: 更新 location.progress.steps 信息

**状态转移示例**:
```python
# 执行前状态
S(t) = {
  workflow: {
    stages: [
      { id: "stage1", steps: [step1, step2] }
    ]
  },
  location: {
    progress: { steps: { remaining: [step1, step2] } }
  }
}

# 执行 update_stage_steps(stage_id="stage1", updated_steps=[...])
Action = {
  action: "update_stage_steps",
  stage_id: "stage1",
  updated_steps: [step1, step2, step3]  # 新增 step3
}

# 执行后状态
S(t+1) = {
  workflow: {
    stages: [
      { id: "stage1", steps: [step1, step2, step3] }  # 步骤列表更新
    ]
  },
  location: {
    progress: { steps: { remaining: [step1, step2, step3] } }
  },
  effects: { current: ["Updated steps for stage1"] }
}
```

**实际用途**:
- 动态调整单个 Stage 的步骤
- 基于中间结果增减步骤
- 支持更细粒度的工作流调整

**格式**:
```json
{
  "action": "update_stage_steps",
  "stage_id": "stage-id",
  "updated_steps": [
    {
      "id": "step1",
      "name": "Step 1",
      "description": "..."
    }
  ]
}
```

**处理流程**:
1. 获取当前工作流
2. 找到指定阶段
3. 更新该阶段的 steps 列表
4. 保存更新后的工作流

---

### 10. COMPLETE_STEP (完成步骤)

**用途**: 标记当前步骤完成，触发状态机转移

**POMDP 作用**:
- **状态维度**: 流程状态 (FSM state)
- **状态转移**: `S.FSM → STEP_COMPLETED` + 更新进度信息
- **观测影响**: 将当前 step 移动到 completed 列表，更新 remaining
- **副作用**: 触发状态机的 COMPLETE_STEP 事件

**状态转移示例**:
```python
# 执行前状态
S(t) = {
  location: {
    current: { step_id: "load_data" },
    progress: {
      steps: {
        completed: [],
        current: "load_data",
        remaining: ["preprocess_data", "analyze_data"]
      }
    }
  },
  FSM: { state: "BEHAVIOR_RUNNING" }
}

# 执行 end_phase(step_id="load_data")
Action = { action: "end_phase", step_id: "load_data" }

# 执行后状态
S(t+1) = {
  location: {
    current: { step_id: "preprocess_data" },  # 移动到下一步
    progress: {
      steps: {
        completed: ["load_data"],  # 已完成
        current: "preprocess_data",
        remaining: ["analyze_data"]
      }
    }
  },
  FSM: { state: "STEP_COMPLETED" },  # 状态机转移
  effects: { current: ["Step completed: load_data"] }
}
```

**实际用途**:
- 标记步骤完成，推进工作流
- 触发状态机进入下一个状态
- 更新进度追踪信息

**格式**:
```json
{
  "action": "end_phase",
  "step_id": "optional-step-id"
}
```

**处理流程**:
1. 记录步骤完成
2. 更新进度信息
3. 触发状态机完成步骤事件

---

### 11. NEXT_EVENT (下一个事件)

**用途**: 触发自定义工作流事件（保留用于未来扩展）

**POMDP 作用**:
- **状态维度**: 流程状态 (FSM state)
- **状态转移**: `S.FSM → custom_state` (根据 event_type)
- **观测影响**: 触发特定的状态机事件
- **副作用**: 可扩展的事件系统，支持自定义状态转移

**状态转移示例**:
```python
# 执行前状态
S(t) = {
  FSM: { state: "BEHAVIOR_RUNNING" }
}

# 执行 next_event(event_type="custom_checkpoint")
Action = { action: "next_event", event_type: "custom_checkpoint" }

# 执行后状态
S(t+1) = {
  FSM: { state: "CUSTOM_CHECKPOINT" },  # 自定义状态
  effects: { current: ["Triggered event: custom_checkpoint"] }
}
```

**实际用途**:
- 支持自定义工作流事件
- 扩展状态机功能
- 预留接口用于未来功能

**格式**:
```json
{
  "action": "next_event",
  "event_type": "custom_event"
}
```

---

## 🔧 Action 元数据

### ActionMetadata 结构

```python
{
  "is_step": false,          # 是否是步骤标记
  "is_chapter": false,       # 是否是章节
  "is_section": false,       # 是否是小节
  "chapter_id": null,        # 章节 ID
  "section_id": null,        # 小节 ID
  "chapter_number": null,    # 章节编号
  "section_number": null,    # 小节编号
  "finished_thinking": false,# 思考是否完成
  "thinking_text": null,     # 思考内容
  "extra": {}                # 额外元数据
}
```

---

## 📊 Action 处理流程

### 通用处理流程

```
1. 接收 Action (ExecutionStep)
   ↓
2. 根据 action 类型查找 handler
   ↓
3. 执行 pre-hooks (如果有)
   ↓
4. 调用对应的 handler
   ↓
5. 执行 post-hooks (如果有)
   ↓
6. 返回结果
```

### 注册自定义 Action

```python
from stores.script_store import ScriptStore

# 方法1: 类级别注册
ScriptStore.register_custom_action('my_action', my_handler)

# 方法2: 实例级别注册
store = ScriptStore()
store._registry.register_handler('my_action', my_handler)

# 方法3: 使用装饰器
from stores.action_registry import ActionRegistry

registry = ActionRegistry()

@registry.register('my_action')
def my_handler(script_store, step):
    # 处理逻辑
    return result
```

---

## 🎨 Shot Type 说明

`shot_type` 用于指示 Action 的显示类型：

| Shot Type | 含义 | 对应 Cell Type |
|-----------|------|----------------|
| `dialogue` | 对话/文本内容 | `markdown` |
| `observation` | 观察/输出 | `markdown` |
| `action` | 代码执行 | `code` |

**示例**:
```json
// 添加普通文本
{"action": "add", "shot_type": "dialogue", "content": "Hello"}

// 添加代码
{"action": "add", "shot_type": "action", "content": "print('hi')"}

// 添加观察结果
{"action": "add", "shot_type": "observation", "content": "Output: 42"}
```

---

## 🛠️ 错误处理

### 常见错误

1. **缺少必需字段**
```python
# 缺少 codecell_id
{"action": "exec"}  # ❌ 错误

# 正确
{"action": "exec", "codecell_id": "code-1"}  # ✅
```

2. **无效的 Action 类型**
```python
{"action": "invalid_action"}  # ❌ 抛出异常
```

3. **Handler 不存在**
```python
# 未注册的 action 类型
{"action": "custom_action"}  # ❌ 警告并跳过
```

### 错误响应

```python
# 执行失败
{
  "success": false,
  "error": "Code execution failed: NameError",
  "action_id": "action-123"
}
```

---

## 📝 完整示例

### 典型工作流 Actions 序列

```json
[
  // 1. 创建章节
  {
    "action": "new_chapter",
    "content": "数据分析"
  },

  // 2. 添加说明文本
  {
    "action": "add",
    "shot_type": "dialogue",
    "content": "首先加载数据集"
  },

  // 3. 添加代码
  {
    "action": "add",
    "shot_type": "action",
    "content": "import pandas as pd\ndf = pd.read_csv('data.csv')"
  },

  // 4. 执行代码
  {
    "action": "exec",
    "codecell_id": "lastAddedCellId",
    "need_output": true
  },

  // 5. 开始思考
  {
    "action": "is_thinking",
    "thinking_text": "Analyzing data structure...",
    "agent_name": "Analyst"
  },

  // 6. 结束思考
  {
    "action": "finish_thinking"
  },

  // 7. 添加分析结果
  {
    "action": "add",
    "shot_type": "dialogue",
    "content": "数据集包含 1000 行，5 列"
  },

  // 8. 完成步骤
  {
    "action": "end_phase",
    "step_id": "load_data"
  }
]
```

---

## 🔗 相关文档

- [API 协议](./API_PROTOCOL.md) - API 交互协议
- [快速参考](../QUICK_REFERENCE.md) - 常用命令
- [高级用法](../ADVANCED_USAGE.md) - 扩展和定制
