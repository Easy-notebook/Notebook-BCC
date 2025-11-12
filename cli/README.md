# CLI 模块化重构文档

## 概述

原 `commands.py` 文件（1544行）已被重构为模块化的类继承结构，提高了代码的可维护性和可扩展性。

## 新的目录结构

```
cli/
├── __init__.py                  # 主入口，导出 WorkflowCLI 和 main
├── workflow_cli.py              # WorkflowCLI 主类（多重继承组合）
├── argument_parser.py           # 命令行参数解析器
├── commands.py                  # 向后兼容层（重新导出）
├── commands_old_backup.py       # 原始文件备份
├── commands_legacy.py           # 废弃标记文件
├── repl.py                      # REPL 交互式界面（未修改）
│
├── base/                        # 基础类
│   ├── __init__.py
│   ├── base_command.py          # BaseCommand - 核心初始化和stores
│   ├── cli_helpers.py           # CLIHelpers - 辅助工具方法
│   └── dummy_context.py         # DummyContext - 上下文管理器
│
└── commands/                    # 功能命令类
    ├── __init__.py
    ├── start_command.py         # StartCommand - start 命令和迭代循环
    ├── state_commands.py        # StateCommands - 状态管理命令
    ├── notebook_commands.py     # NotebookCommands - 笔记本命令
    ├── api_commands.py          # APICommands - API 相关命令
    └── basic_commands.py        # BasicCommands - 基础命令（status, repl）
```

## 类继承结构

```
WorkflowCLI
├── BaseCommand          (核心初始化、stores、logging)
├── CLIHelpers           (辅助方法：_load_state_file, _sync_state_to_stores 等)
├── StartCommand         (start 命令、迭代循环)
├── StateCommands        (resume, test-request, apply-transition)
├── NotebookCommands     (show, list, export, export-markdown)
├── APICommands          (send-api, test-actions)
└── BasicCommands        (status, repl)
```

## 各模块职责

### base/base_command.py - BaseCommand
- 初始化所有 stores（pipeline_store, script_store, notebook_store, ai_context_store）
- 初始化 managers（notebook_manager, cell_renderer）
- 初始化 state_machine
- 设置日志配置

### base/cli_helpers.py - CLIHelpers
提供统一的辅助方法：
- `_load_state_file()` - 加载并解析状态文件
- `_infer_api_type()` - 推断 API 类型
- `_convert_action_to_step()` - 转换 action 为 ExecutionStep
- `_execute_actions_internal()` - 执行 actions
- `_build_state_from_stores()` - 从 stores 构建状态
- `_sync_state_to_stores()` - 同步状态到 stores

### commands/start_command.py - StartCommand
- `cmd_start()` - start 命令主入口
- `_start_traditional()` - 传统模式启动（--problem, --context）
- `_start_from_config()` - 从配置文件启动
- `_start_from_state_file()` - 从状态文件启动
- `_build_idle_state()` - 构建 IDLE 状态
- `_run_iteration_loop()` - 自动迭代循环
- `_generate_output_path()` - 生成输出文件路径

### commands/state_commands.py - StateCommands
- `cmd_resume()` - resume 命令
- `cmd_test_request()` - test-request 命令
- `cmd_apply_transition()` - apply-transition 命令

### commands/notebook_commands.py - NotebookCommands
- `cmd_show()` - show 命令
- `cmd_list()` - list 命令
- `cmd_export()` - export 命令
- `cmd_export_markdown()` - export-markdown 命令

### commands/api_commands.py - APICommands
- `cmd_send_api()` - send-api 命令
- `cmd_test_actions()` - test-actions 命令
- `_build_output_state_for_test_actions()` - 构建输出状态

### commands/basic_commands.py - BasicCommands
- `cmd_status()` - status 命令
- `cmd_repl()` - repl 命令

### workflow_cli.py - WorkflowCLI
主 CLI 类，通过多重继承组合所有功能：
- `create_parser()` - 创建参数解析器
- `run()` - 运行 CLI，分发命令到各个 handler

### argument_parser.py - CLIArgumentParser
- `create_parser()` - 静态方法，创建完整的 argparse 参数解析器

## 向后兼容性

### cli/commands.py
新的 `commands.py` 作为向后兼容层，重新导出所有必要的类和函数：
```python
from cli.workflow_cli import WorkflowCLI, main
from cli.base.dummy_context import DummyContext
```

现有代码无需修改，可以继续使用：
```python
from cli.commands import WorkflowCLI, main
```

### cli/__init__.py
主入口点更新为：
```python
from .workflow_cli import WorkflowCLI, main
from .repl import WorkflowREPL
from .base.dummy_context import DummyContext
```

## 使用示例

### 直接使用（与之前完全相同）
```bash
python main.py start --problem "Analyze data"
python main.py send-api --state-file state.json
python main.py test-actions --actions-file actions.json --state-file state.json --output output.json
```

### Python 代码中使用
```python
# 方式1：从 cli 导入（推荐）
from cli import WorkflowCLI, main

# 方式2：从 cli.workflow_cli 导入（新模块）
from cli.workflow_cli import WorkflowCLI, main

# 方式3：从 cli.commands 导入（向后兼容）
from cli.commands import WorkflowCLI, main

# 使用
cli = WorkflowCLI(max_steps=10, interactive=True)
cli.run(['start', '--problem', 'Task'])
```

## 扩展新命令

要添加新命令，只需：

1. 在 `cli/commands/` 创建新的命令类
2. 在 `WorkflowCLI` 中添加继承
3. 在 `argument_parser.py` 添加参数
4. 在 `workflow_cli.run()` 添加命令映射

示例：
```python
# cli/commands/my_command.py
class MyCommand:
    def cmd_my_action(self, args):
        print("My action")

# cli/workflow_cli.py
class WorkflowCLI(..., MyCommand):
    def run(self, argv=None):
        command_handlers = {
            ...
            'my-action': self.cmd_my_action,
        }
```

## 优点

1. **模块化**：每个命令类独立管理，职责单一
2. **可维护性**：代码分散到多个小文件，易于理解和修改
3. **可扩展性**：添加新命令只需创建新类并继承
4. **复用性**：辅助方法在 CLIHelpers 中统一管理
5. **测试性**：各个命令类可独立测试
6. **向后兼容**：现有代码无需修改

## 迁移说明

对于现有项目：
- **不需要修改任何导入语句**
- `from cli.commands import WorkflowCLI` 仍然有效
- 所有命令行参数和用法保持不变
- 原始 `commands.py` 已备份为 `commands_old_backup.py`

## 文件大小对比

| 文件 | 行数 | 说明 |
|------|------|------|
| commands_old_backup.py | 1544 | 原始单体文件 |
| workflow_cli.py | ~120 | 主类（多重继承） |
| base/base_command.py | ~70 | 基础初始化 |
| base/cli_helpers.py | ~160 | 辅助工具 |
| commands/start_command.py | ~450 | start 命令和迭代 |
| commands/state_commands.py | ~180 | 状态管理 |
| commands/notebook_commands.py | ~70 | 笔记本命令 |
| commands/api_commands.py | ~200 | API 命令 |
| commands/basic_commands.py | ~50 | 基础命令 |
| argument_parser.py | ~150 | 参数解析器 |

**总计**：~1450 行（分散在 9 个文件中，更易维护）

## 注意事项

1. 多重继承的方法解析顺序（MRO）：Python 使用 C3 线性化算法
2. 所有命令类共享同一个 stores 实例（通过 BaseCommand）
3. Helper 方法使用 `self` 访问 stores（mixin 模式）
4. REPL 类独立，未做修改（repl.py）
