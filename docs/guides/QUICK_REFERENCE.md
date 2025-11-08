# Quick Reference Card

## 🚀 常用命令

### 基础使用
```bash
# 启动工作流
python main.py start --problem "分析数据"

# 查看状态
python main.py status

# 列出 notebook
python main.py list

# 交互模式
python main.py repl
```

### 配置选项
```bash
# 后端服务配置
--backend-url http://localhost:18600  # Jupyter kernel URL
--dslc-url http://localhost:28600     # Workflow API URL
--notebook-id abc123                 # 已存在的 notebook ID

# 执行控制
--max-steps 10        # 限制步骤数（0 = 无限制）
--start-mode MODE     # reflection 或 generation
--interactive         # 启用交互模式（到达限制时暂停）

# 自定义上下文
--custom-context '{"key":"value"}'   # JSON 字符串
--custom-context context.json        # JSON 文件
```

---

## 🎮 执行控制

### 步骤限制
```bash
# 只执行 5 步
python main.py --max-steps 5 start

# 交互模式（暂停以检查）
python main.py --max-steps 10 --interactive start
```

### 代码控制
```python
cli.state_machine.pause()              # 暂停
cli.state_machine.resume()             # 恢复
cli.state_machine.set_max_steps(20)    # 设置限制
cli.state_machine.reset_step_counter() # 重置计数
```

---

## 🔄 执行流程 (统一协议 v2.0+)

### 新的统一流程
```bash
python main.py start --problem "任务描述"
```

**所有执行都遵循相同流程:**
```
STEP → /planning (检查目标)
     ↓
   已完成? → 是 → 跳过执行，进入下一步
     ↓
    否
     ↓
BEHAVIOR → /generating (获取actions)
     ↓
   执行 actions
     ↓
BEHAVIOR_COMPLETED → /planning (再次检查)
```

**优势:**
- 🎯 智能跳过已完成的任务
- 🚀 避免重复执行
- ✅ 每步都验证目标达成状态

---

## 📦 自定义上下文

### 通过命令行
```bash
# JSON 字符串
python main.py --custom-context '{"user":"alice","priority":"high"}' start

# JSON 文件
python main.py --custom-context context.json start
```

### 通过代码
```python
# 完整设置
cli.ai_context_store.set_custom_context({
    "user_id": "alice",
    "session": "test123"
})

# 单个更新
cli.ai_context_store.update_custom_context("priority", "high")

# 获取
ctx = cli.ai_context_store.get_custom_context()

# 清空
cli.ai_context_store.clear_custom_context()
```

---

## 🔧 环境变量

### .env 文件
```bash
# API 端点
BACKEND_BASE_URL=http://localhost:18600
DSLC_BASE_URL=http://localhost:28600
NOTEBOOK_ID=

# 执行控制
MAX_EXECUTION_STEPS=0
WORKFLOW_START_MODE=generation
INTERACTIVE_MODE=false

# 执行设置
EXECUTION_TIMEOUT=300
STATUS_CHECK_INTERVAL=1.0

# 日志
LOG_LEVEL=INFO
```

---

## 📊 状态查看

### CLI 状态
```bash
python main.py status
```

输出：
```
📊 Workflow Status
==================
Current State: ACTION_RUNNING
Stage ID: stage_1
Step ID: step_1
Actions: 3 / 5

🎮 Execution Control
Steps: 8/10
Start Mode: generation
Interactive: Yes
Paused: No

📝 Notebook Status
...

🎯 AI Context
Variables: 5
TODO List: 2
Custom Context: 3 keys
```

### 代码状态
```python
# 执行状态
status = cli.state_machine.get_execution_status()
# {
#   'current_step': 8,
#   'max_steps': 10,
#   'paused': False,
#   'start_mode': 'generation',
#   'interactive': True,
#   'state': 'ACTION_RUNNING'
# }

# 工作流状态
info = cli.state_machine.get_state_info()

# AI 上下文
context = cli.ai_context_store.get_context()
```

---

## 🎯 典型场景

### 场景 1: 开发调试
```bash
python main.py \
  --max-steps 5 \
  --interactive \
  --custom-context '{"debug":true}' \
  start --problem "测试功能"
```

### 场景 2: 验证模式
```bash
python main.py \
  --start-mode reflection \
  --custom-context validation.json \
  start --problem "验证数据"
```

### 场景 3: 生产执行
```bash
python main.py \
  --backend-url http://prod:18600 \
  --notebook-id prod-123 \
  --custom-context prod_context.json \
  start --problem "数据处理"
```

### 场景 4: 长时间运行
```bash
python main.py \
  --max-steps 0 \
  start --problem "完整分析" > output.log 2>&1 &
```

---

## 🔍 故障排除

### 执行卡住
```bash
# 检查状态
python main.py status

# 看是否暂停
# Paused: Yes → 需要代码中 resume()
```

### API 连接失败
```bash
# 测试 backend
curl http://localhost:18600/initialize

# 测试 DSLC
curl http://localhost:28600/planning -X POST

# 更改 URL
python main.py --backend-url http://other:18600 start
```

### 步骤不增加
- 步骤只在 ACTION_RUNNING/COMPLETED 增加
- 检查是否真的执行了 action

### 自定义上下文未生效
```bash
# 验证 JSON 格式
python -c "import json; print(json.loads('{\"key\":\"value\"}'))"

# 检查文件
cat context.json | python -m json.tool
```

---

## 📝 REPL 命令

```
start <task>           启动工作流
status                 查看状态
pause                  暂停执行
resume                 恢复执行
set_max_steps <n>      设置最大步骤
set_custom_context <k> <v>  设置自定义上下文
var set <key> <value>  设置变量
todo add <item>        添加 TODO
exec <code>            执行代码
save <file>            保存 notebook
quit                   退出
```

---

## 🔗 相关文档

- **README.md** - 完整项目说明
- **ADVANCED_USAGE.md** - 高级功能详细指南
- **CHANGELOG.md** - 版本变更历史
- **.env.example** - 配置文件模板

---

## 💡 提示

1. **开发**: 使用 `--max-steps 5 --interactive` 快速迭代
2. **测试**: 使用 `--start-mode reflection` 验证逻辑
3. **生产**: 移除步骤限制，使用 `.env` 管理配置
4. **调试**: 定期 `status` 检查执行状态
5. **自定义**: 通过 custom context 注入业务数据

---

## 📞 快速帮助

```bash
# 显示帮助
python main.py --help

# 显示命令帮助
python main.py start --help

# 查看配置
cat .env

# 查看日志
tail -f workflow.log

# 检查 API
curl http://localhost:18600/initialize
curl http://localhost:28600/planning -X POST -d '{}'
```
