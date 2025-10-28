# Advanced Usage Guide

## 自定义上下文注入 (Custom Context Injection)

### 1. 通过命令行注入 JSON

```bash
python main.py \
  --custom-context '{"user_id":"alice","dataset":"sales_2024","priority":"high"}' \
  start --problem "分析销售数据"
```

### 2. 通过文件注入

创建 `context.json`:
```json
{
  "user_id": "alice",
  "dataset": "sales_2024",
  "priority": "high",
  "filters": {
    "region": "north",
    "quarter": "Q4"
  }
}
```

运行：
```bash
python main.py --custom-context context.json start
```

### 3. 在代码中使用

```python
from cli.commands import WorkflowCLI

cli = WorkflowCLI()

# 设置自定义上下文
custom_context = {
    "user_id": "alice",
    "dataset": "sales_2024",
    "priority": "high"
}
cli.ai_context_store.set_custom_context(custom_context)

# 或者更新单个键
cli.ai_context_store.update_custom_context("timestamp", "2024-01-15")

# 获取自定义上下文
context = cli.ai_context_store.get_custom_context()
print(context)
```

### 自定义上下文的作用

- 自定义上下文会随每次 API 调用一起发送
- 可以覆盖默认的上下文字段
- 允许向 LLM 提供额外的业务信息

---

## 步骤限制和断点调试 (Step Limits & Breakpoints)

### 1. 限制执行步骤数

```bash
# 只执行 5 个步骤
python main.py --max-steps 5 start --problem "测试工作流"
```

### 2. 交互模式 (Interactive Mode)

在交互模式下，达到步骤限制时会自动暂停：

```bash
python main.py --max-steps 5 --interactive start --problem "调试工作流"
```

执行到第 5 步时会暂停，可以：
- 检查状态：`python main.py status`
- 继续执行（需要在代码中调用）

### 3. 手动暂停和恢复

```python
from cli.commands import WorkflowCLI

cli = WorkflowCLI(max_steps=10, interactive=True)

# 手动暂停
cli.state_machine.pause()

# 检查状态
status = cli.state_machine.get_execution_status()
print(f"当前步骤: {status['current_step']}")
print(f"是否暂停: {status['paused']}")

# 恢复执行
cli.state_machine.resume()

# 动态调整最大步骤
cli.state_machine.set_max_steps(20)

# 重置计数器
cli.state_machine.reset_step_counter()
```

### 使用场景

- **调试**: 限制步骤数，避免长时间运行
- **测试**: 验证前几个步骤的正确性
- **演示**: 分步展示工作流执行
- **监控**: 在关键点暂停检查状态

---

## 执行流程协议 (Unified Execution Protocol v2.0+)

### ⚠️ 重要更新

**从 v2.0 开始，所有工作流都采用统一的"Planning First"协议。**

### 统一执行流程

所有步骤现在都遵循相同的智能执行流程：

```bash
python main.py start --problem "分析数据"
```

**执行流程：**
```
STEP_RUNNING
  ↓
  ├─→ [1] 调用 /planning API (检查目标是否已达成)
  │
  ├─→ targetAchieved = true?
  │   ├─ YES → STEP_COMPLETED (跳过执行)
  │   └─ NO  → 继续执行
  │
  ├─→ [2] BEHAVIOR_RUNNING → 调用 /generating API
  │   获取 actions 列表
  │
  ├─→ [3] 执行所有 actions
  │
  ├─→ [4] BEHAVIOR_COMPLETED → 再次调用 /planning API
  │   检查本次 behavior 是否达成目标
  │
  └─→ continue_behaviors?
      ├─ YES → 回到步骤 2 (新的 behavior)
      └─ NO  → STEP_COMPLETED
```

### 新协议优势

| 特性 | 说明 |
|------|------|
| 🎯 **智能跳过** | 自动检测已完成的任务，避免重复执行 |
| 🔄 **双重验证** | Step开始和Behavior完成时都进行目标检查 |
| 📊 **精确控制** | 服务端完全控制是否需要更多behaviors |
| ⚡ **高效执行** | 按需生成actions，避免不必要的API调用 |

### 环境变量配置

`.env` 文件中的相关配置：

```bash
# 执行控制
MAX_EXECUTION_STEPS=0  # 0 = unlimited
INTERACTIVE_MODE=false
```

---

## 综合示例

### 示例 1: 调试模式 - 限制步骤数

```bash
python main.py \
  --max-steps 10 \
  --interactive \
  start --problem "测试新功能"
```

执行 10 步后自动暂停，可以检查状态后决定是否继续。

### 示例 2: 验证模式 - 带自定义上下文

```bash
python main.py \
  --custom-context '{"validation_mode":true}' \
  start --problem "验证数据质量"
```

每个 step 自动先检查目标是否达成（新协议默认行为），已达成则跳过行为生成。

### 示例 3: 生产模式 - 完整执行

```bash
python main.py \
  --backend-url http://prod-kernel:18600 \
  --dslc-url http://prod-dslc:28600 \
  --notebook-id prod-session-123 \
  --custom-context production_context.json \
  start --problem "生产环境数据处理"
```

### 示例 4: 代码中的高级控制

```python
from cli.commands import WorkflowCLI
from config import Config

# 初始化配置
Config.set_backend_url("http://localhost:9000")
Config.set_dslc_url("http://localhost:9001")

# 创建 CLI
cli = WorkflowCLI(
    max_steps=50,
    start_mode='reflection',
    interactive=True
)

# 设置自定义上下文
cli.ai_context_store.set_custom_context({
    "user_id": "alice",
    "session_id": "abc123",
    "debug_mode": True
})

# 初始化工作流
workflow = cli.pipeline_store.initialize_workflow({
    'problem_name': 'Data Analysis',
    'user_goal': '分析用户行为数据',
    'problem_description': '分析过去30天的用户活动',
    'context_description': '电商平台用户行为分析'
})

# 开始执行
cli.pipeline_store.start_workflow_execution(cli.state_machine)

# 执行期间可以：
# 1. 暂停执行
cli.state_machine.pause()

# 2. 检查状态
status = cli.state_machine.get_execution_status()
print(f"步骤: {status['current_step']}/{status['max_steps']}")
print(f"模式: {status['start_mode']}")
print(f"暂停: {status['paused']}")

# 3. 检查上下文
context = cli.ai_context_store.get_context()
print(f"变量: {context.variables}")
print(f"TODO: {context.to_do_list}")
print(f"自定义: {context.custom_context}")

# 4. 动态调整
cli.state_machine.set_max_steps(100)  # 增加限制
cli.state_machine.start_mode = 'generation'  # 切换模式

# 5. 恢复执行
cli.state_machine.resume()
```

---

## REPL 中的使用

```bash
python main.py repl
```

在 REPL 中：

```
(workflow) > start Data Analysis Task

(workflow) > status
📊 Workflow Status
==================
...
🎮 Execution Control
Steps: 3/10
Start Mode: generation
Interactive: Yes
Paused: No

(workflow) > pause

(workflow) > status
...
Paused: Yes

(workflow) > resume

(workflow) > set_max_steps 20

(workflow) > set_custom_context user_id alice

(workflow) > quit
```

---

## 最佳实践

### 1. 开发阶段
- 使用 `--max-steps 5 --interactive` 进行快速迭代
- 使用 `--start-mode reflection` 验证逻辑
- 使用自定义上下文注入测试数据

### 2. 测试阶段
- 使用 `--max-steps 50` 限制执行范围
- 使用 `--custom-context` 注入测试场景
- 定期检查 status 确保状态正确

### 3. 生产阶段
- 移除 `--max-steps` 限制（或设为 0）
- 使用 `--start-mode generation` 提高效率
- 通过 `.env` 文件管理配置
- 使用日志监控执行进度

---

## 故障排除

### 问题 1: 执行卡住不动
```bash
# 检查是否被暂停
python main.py status

# 如果 Paused: Yes，需要在代码中调用 resume()
```

### 问题 2: 步骤数不增加
```bash
# 步骤计数器只在 ACTION_RUNNING 和 ACTION_COMPLETED 状态增加
# 检查是否真的执行了 action
```

### 问题 3: 自定义上下文未生效
```bash
# 确认 JSON 格式正确
python -c "import json; print(json.loads('{\"key\":\"value\"}'))"

# 或使用文件
cat context.json | python -m json.tool
```

### 问题 4: Reflection 模式不工作
```bash
# 确认 DSLC API 可访问
curl http://localhost:28600/planning -X POST -H "Content-Type: application/json" -d '{}'

# 检查日志
tail -f workflow.log | grep "reflection"
```
