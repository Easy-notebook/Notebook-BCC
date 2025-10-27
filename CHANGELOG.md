# Changelog

## [1.1.0] - 2024-10-27

### ✨ New Features

#### 1. Custom Context Injection (自定义上下文注入)

允许用户在 API 调用时注入自定义数据：

**实现文件：**
- `stores/ai_context_store.py` - 添加 `custom_context` 字段和相关方法

**新增方法：**
- `set_custom_context(context)` - 设置完整自定义上下文
- `update_custom_context(key, value)` - 更新单个键值
- `get_custom_context()` - 获取自定义上下文
- `clear_custom_context()` - 清空自定义上下文

**命令行参数：**
```bash
--custom-context <json>  # JSON 字符串或文件路径
```

**使用示例：**
```bash
python main.py --custom-context '{"user":"alice"}' start
python main.py --custom-context context.json start
```

---

#### 2. Step Limits & Breakpoint Debugging (步骤限制和断点调试)

允许限制执行步骤数，支持暂停/恢复：

**实现文件：**
- `core/state_machine.py` - 添加步骤计数和控制逻辑
- `config.py` - 添加 `MAX_EXECUTION_STEPS` 和 `INTERACTIVE_MODE`

**新增属性：**
- `step_counter` - 当前步骤计数
- `max_steps` - 最大步骤限制（0 = 无限制）
- `interactive` - 交互模式开关
- `paused` - 暂停状态

**新增方法：**
- `check_step_limit()` - 检查是否达到步骤限制
- `increment_step()` - 增加步骤计数
- `reset_step_counter()` - 重置计数器
- `pause()` - 暂停执行
- `resume()` - 恢复执行
- `set_max_steps(n)` - 设置最大步骤
- `get_execution_status()` - 获取执行状态

**命令行参数：**
```bash
--max-steps <n>     # 最大步骤数（0 = 无限制）
--interactive       # 启用交互模式
```

**使用示例：**
```bash
# 限制 10 步
python main.py --max-steps 10 start

# 交互模式（到达限制时暂停）
python main.py --max-steps 5 --interactive start
```

**环境变量：**
```bash
MAX_EXECUTION_STEPS=10
INTERACTIVE_MODE=true
```

---

#### 3. Start Mode Selection (启动模式选择)

允许选择工作流启动策略（reflection vs generation）：

**实现文件：**
- `core/state_machine.py` - 添加 `start_mode` 和相关逻辑
- `config.py` - 添加 `WORKFLOW_START_MODE`

**模式说明：**

| 模式 | 行为 | 适用场景 |
|------|------|---------|
| `generation` | 直接调用 `/actions` API 生成动作 | 主动执行任务 |
| `reflection` | 先调用 `/reflection` API 判断目标是否达成 | 验证、检查 |

**新增方法：**
- `_start_with_reflection()` - 以 reflection 模式启动步骤

**命令行参数：**
```bash
--start-mode <mode>  # reflection 或 generation
```

**使用示例：**
```bash
# Generation 模式（默认）
python main.py --start-mode generation start

# Reflection 模式
python main.py --start-mode reflection start
```

**环境变量：**
```bash
WORKFLOW_START_MODE=reflection
```

**执行流程对比：**

**Generation 模式：**
```
STEP_RUNNING → START_BEHAVIOR → BEHAVIOR_RUNNING → fetch /actions
```

**Reflection 模式：**
```
STEP_RUNNING → call /reflection
  ↓
  ├─ targetAchieved=true  → COMPLETE_STEP
  └─ targetAchieved=false → START_BEHAVIOR → fetch /actions
```

---

### 📝 Configuration Updates

#### `.env.example`

新增配置项：
```bash
# Workflow Control
MAX_EXECUTION_STEPS=0
WORKFLOW_START_MODE=generation
INTERACTIVE_MODE=false
```

#### `requirements.txt`

新增依赖：
```
python-dotenv>=1.0.0
```

---

### 📚 Documentation

新增文档：
- `ADVANCED_USAGE.md` - 高级功能详细使用指南
- `CHANGELOG.md` - 本文件

更新文档：
- `README.md` - 添加高级功能说明
- `.env.example` - 添加新配置项和示例

---

### 🔧 CLI Enhancements

#### 新增全局参数

```bash
--backend-url <url>         # Backend Jupyter kernel URL
--dslc-url <url>            # DSLC workflow API URL
--notebook-id <id>          # Initial notebook ID
--max-steps <n>             # Maximum steps to execute
--start-mode <mode>         # Start mode (reflection/generation)
--interactive               # Enable interactive mode
--custom-context <json>     # Custom context JSON or file
```

#### 增强的 status 命令

现在显示：
- 执行控制状态（步骤计数、限制、模式、暂停状态）
- 自定义上下文信息

---

### 🎯 API Changes

#### `AIContext` (stores/ai_context_store.py)

新增字段：
```python
custom_context: Dict[str, Any] = field(default_factory=dict)
```

修改方法：
```python
def to_dict(self) -> Dict[str, Any]:
    # 现在会合并 custom_context
```

#### `WorkflowStateMachine` (core/state_machine.py)

新增初始化参数：
```python
def __init__(
    self,
    pipeline_store=None,
    script_store=None,
    ai_context_store=None,
    max_steps: int = 0,              # 新增
    start_mode: str = 'generation',  # 新增
    interactive: bool = False        # 新增
)
```

修改方法：
```python
def _execute_state_effects(self, state, payload):
    # 现在会检查暂停状态和步骤限制
```

#### `WorkflowCLI` (cli/commands.py)

新增初始化参数：
```python
def __init__(
    self,
    max_steps=0,
    start_mode='generation',
    interactive=False
)
```

---

### 🚀 Usage Examples

#### 完整示例 1: 调试模式

```bash
python main.py \
  --backend-url http://localhost:9000 \
  --max-steps 10 \
  --interactive \
  --start-mode generation \
  --custom-context '{"debug":true,"user":"tester"}' \
  start --problem "测试新功能"
```

#### 完整示例 2: 验证模式

```bash
python main.py \
  --start-mode reflection \
  --custom-context validation_context.json \
  start --problem "验证数据质量"
```

#### 代码示例

```python
from cli.commands import WorkflowCLI

cli = WorkflowCLI(
    max_steps=50,
    start_mode='reflection',
    interactive=True
)

# 设置自定义上下文
cli.ai_context_store.set_custom_context({
    "user_id": "alice",
    "priority": "high"
})

# 初始化并启动工作流
workflow = cli.pipeline_store.initialize_workflow({...})
cli.pipeline_store.start_workflow_execution(cli.state_machine)

# 执行控制
cli.state_machine.pause()
status = cli.state_machine.get_execution_status()
cli.state_machine.resume()
```

---

### 🐛 Bug Fixes

无

---

### ⚡ Performance Improvements

无

---

### 💥 Breaking Changes

无。所有新功能都是可选的，向后兼容现有代码。

---

### 🔄 Migration Guide

现有项目无需修改即可升级。新功能通过命令行参数或环境变量启用：

```bash
# 旧方式（仍然有效）
python main.py start --problem "数据分析"

# 新方式（启用新功能）
python main.py --max-steps 10 --start-mode reflection start --problem "数据分析"
```

---

### 📦 Full File List

#### 新增文件
- `ADVANCED_USAGE.md` - 高级功能使用指南
- `CHANGELOG.md` - 变更日志

#### 修改文件
- `stores/ai_context_store.py` - 添加自定义上下文功能
- `core/state_machine.py` - 添加步骤控制和启动模式
- `config.py` - 添加新配置项
- `cli/commands.py` - 添加新命令行参数
- `.env.example` - 添加新配置示例
- `requirements.txt` - 添加 python-dotenv
- `README.md` - 更新文档

---

## [1.0.0] - 2024-10-26

### 初始版本

- 完整的状态机实现
- API 集成（workflow 和 code execution）
- 配置管理系统
- CLI 和 REPL 接口
- Notebook 管理
- 完整文档
