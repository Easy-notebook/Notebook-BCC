# Transition Actions 功能说明

## 概述

本次更新为关键的 FSM transition 添加了自动执行 notebook actions 的功能。当状态机在关键的 transition 点执行时，会自动向 notebook 添加相应的标题和分节标记。

## 功能列表

### 1. START_WORKFLOW (IDLE → STAGE_RUNNING)
当 workflow 开始时，自动执行以下 actions：
- **update_title**: 使用 workflow 的 `focus` 字段更新 notebook 标题
- **new_section**: 使用第一个 stage 的 `title` 字段创建 Level 2 标题 (##)

**示例**：
```
# Workflow Focus Title

## Stage 1: Data Preparation
```

### 2. START_STEP (STAGE_RUNNING → STEP_RUNNING)
当 step 开始时，自动执行：
- **new_step**: 使用 step 的 `title` 字段创建 Level 3 标题 (###)

**示例**：
```
### Step 1: Load Dataset
```

### 3. NEXT_STEP (STEP_COMPLETED → STEP_RUNNING)
当进入下一个 step 时，自动执行：
- **new_step**: 使用下一个 step 的 `title` 字段创建 Level 3 标题 (###)

**示例**：
```
### Step 2: Data Cleaning
```

### 4. NEXT_STAGE (STAGE_COMPLETED → STAGE_RUNNING)
当进入下一个 stage 时，自动执行：
- **new_section**: 使用下一个 stage 的 `title` 字段创建 Level 2 标题 (##)

**示例**：
```
## Stage 2: Model Training
```

## 架构设计

### 核心组件

1. **BaseTransitionHandler**
   - 添加了 `script_store` 属性
   - 添加了 `_execute_action()` 辅助方法用于执行 notebook actions
   - 所有 transition handlers 继承此功能

2. **TransitionCoordinator**
   - 添加了 `set_script_store()` 方法用于注入 ScriptStore 实例
   - 在初始化时自动将 script_store 注入到所有 handlers
   - 添加了新的 NextStageHandler

3. **StateUpdater**
   - 添加了 `set_script_store()` 方法
   - 支持在初始化时或运行时注入 script_store

4. **AsyncStateMachineAdapter**
   - 在所有 `apply_transition()` 调用前自动注入 script_store
   - 确保 transition handlers 可以访问 ScriptStore 实例

### 新增文件

- **core/transition_handlers/NEXT_STAGE_handler.py**: 处理 STAGE_COMPLETED → STAGE_RUNNING 的 transition

### 修改文件

- **core/transition_handlers/base_transition_handler.py**: 添加 action 执行支持
- **core/transition_handlers/START_WORKFLOW_handler.py**: 添加 update_title 和 new_section
- **core/transition_handlers/START_STEP_handler.py**: 添加 new_step
- **core/transition_handlers/NEXT_STEP_handler.py**: 添加 new_step
- **core/transition_handlers/transition_coordinator.py**: 添加 script_store 注入和 NextStageHandler 注册
- **utils/state_updater.py**: 添加 script_store 支持
- **core/async_state_machine.py**: 在所有 transition 前注入 script_store

## 使用方法

### 基本使用

系统会自动执行 actions，无需额外配置。只要确保 AsyncStateMachineAdapter 在初始化时传入了 script_store：

```python
from core.async_state_machine import AsyncStateMachineAdapter
from stores.script_store import ScriptStore
from stores.notebook_store import NotebookStore

# 创建 stores
notebook_store = NotebookStore()
script_store = ScriptStore(notebook_store=notebook_store)

# 创建 AsyncStateMachineAdapter 并传入 script_store
adapter = AsyncStateMachineAdapter(
    state_machine=state_machine,
    api_client=api_client,
    script_store=script_store  # 关键：传入 script_store
)
```

### 手动注入 ScriptStore（可选）

如果需要在运行时更新 script_store：

```python
from utils.state_updater import state_updater

# 设置 script_store
state_updater.set_script_store(script_store)

# 后续的所有 transitions 都会使用这个 script_store
```

## Action 类型说明

### update_title
- **触发时机**: START_WORKFLOW
- **效果**: 更新 notebook 标题
- **内容来源**: workflow 的 `focus` 字段

### new_section
- **触发时机**: START_WORKFLOW, NEXT_STAGE
- **效果**: 创建 Level 2 标题 (##)
- **内容来源**: stage 的 `title` 字段

### new_step
- **触发时机**: START_STEP, NEXT_STEP
- **效果**: 创建 Level 3 标题 (###)
- **内容来源**: step 的 `title` 字段

## 示例输出

完整的 workflow 执行后，notebook 的结构会是：

```markdown
# Machine Learning Project

## Stage 1: Data Preparation

### Step 1: Load Dataset
[code cells and outputs]

### Step 2: Data Cleaning
[code cells and outputs]

### Step 3: Feature Engineering
[code cells and outputs]

## Stage 2: Model Training

### Step 1: Train Model
[code cells and outputs]

### Step 2: Evaluate Model
[code cells and outputs]

## Stage 3: Model Deployment

### Step 1: Export Model
[code cells and outputs]

### Step 2: Create API
[code cells and outputs]
```

## 扩展性

要为其他 transitions 添加 actions：

1. 在相应的 handler 的 `apply()` 方法末尾调用 `self._execute_action()`
2. 提供 action 类型和内容

**示例**：
```python
def apply(self, state: Dict[str, Any], api_response: Any) -> Dict[str, Any]:
    new_state = self._deep_copy_state(state)

    # ... 现有的状态更新逻辑 ...

    # 执行 action
    self._execute_action('new_chapter', content=chapter_title)

    return new_state
```

## 测试

要测试此功能：

1. 确保 AsyncStateMachineAdapter 初始化时传入了 script_store
2. 运行一个完整的 workflow
3. 检查 notebook 中是否正确添加了标题和分节标记
4. 验证标题内容与 stage/step 的 title 字段一致

## 故障排查

### Actions 没有执行

**可能原因**：
- script_store 未正确注入到 handlers
- stage/step 的 title 字段为空

**解决方案**：
- 检查 AsyncStateMachineAdapter 初始化时是否传入了 script_store
- 检查 API 响应中是否包含 title 字段

### 重复的标题

**可能原因**：
- 同一个 transition 被执行了多次

**解决方案**：
- 检查状态机的 transition 逻辑
- 确认没有重复调用 apply_transition()

## 注意事项

1. **幂等性**: Actions 的执行不是幂等的，每次 transition 都会创建新的标题
2. **顺序**: Actions 在状态更新之后执行，但在返回 new_state 之前
3. **错误处理**: Action 执行失败不会影响状态转换，只会记录错误日志
4. **性能**: Action 执行是同步的，但通常非常快速（主要是 notebook cell 的添加）
