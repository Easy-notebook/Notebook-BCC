# CLI 使用示例测试文档

本文档展示 Notebook-BCC CLI 的各种使用方式及其测试。

## 📋 目录

1. [基本命令](#基本命令)
2. [启动工作流](#启动工作流)
3. [自定义上下文](#自定义上下文)
4. [笔记本管理](#笔记本管理)
5. [执行控制](#执行控制)
6. [高级用法](#高级用法)

---

## 基本命令

### 1. 显示帮助信息

```bash
python main.py --help
```

**测试:**
```bash
pytest test/test_cli_usage.py::TestCLIBasicCommands::test_cli_help -v
```

### 2. 查看工作流状态

```bash
python main.py status
```

**预期输出:**
- 当前状态
- 阶段和步骤信息
- 笔记本状态
- AI 上下文信息

**测试:**
```bash
pytest test/test_cli_usage.py::TestCLIBasicCommands::test_cli_status_command -v
```

---

## 启动工作流

### 1. 最简单的启动

```bash
python main.py start
```

**测试:**
```bash
pytest test/test_cli_usage.py::TestCLIStartCommand::test_start_simple -v
```

### 2. 指定问题描述

```bash
python main.py start --problem "分析销售数据"
```

**测试:**
```bash
pytest test/test_cli_usage.py::TestCLIStartCommand::test_start_with_problem -v
```

### 3. 同时指定问题和上下文

```bash
python main.py start --problem "数据分析" --context "2024年第四季度销售报告"
```

**测试:**
```bash
pytest test/test_cli_usage.py::TestCLIStartCommand::test_start_with_context -v
```

### 4. 使用反思模式（Reflection Mode）

```bash
python main.py --start-mode reflection start --problem "测试问题"
```

**说明:** 反思模式会先调用 `/reflection` API 检查目标是否已达成

**测试:**
```bash
pytest test/test_cli_usage.py::TestCLIStartCommand::test_start_reflection_mode -v
```

### 5. 使用生成模式（Generation Mode，默认）

```bash
python main.py --start-mode generation start --problem "测试问题"
```

**说明:** 生成模式直接调用 `/actions` API 执行动作

**测试:**
```bash
pytest test/test_cli_usage.py::TestCLIStartCommand::test_start_generation_mode -v
```

---

## 自定义上下文

### 1. 通过 JSON 字符串传递

```bash
python main.py --custom-context '{"user":"alice","priority":"high"}' start --problem "测试"
```

**测试:**
```bash
pytest test/test_cli_usage.py::TestCLICustomContext::test_custom_context_json_string -v
```

### 2. 从文件加载自定义上下文

创建文件 `context.json`:
```json
{
  "project": "sales-analysis",
  "environment": "production",
  "user": "alice",
  "priority": "high"
}
```

使用文件:
```bash
python main.py --custom-context context.json start --problem "分析数据"
```

**测试:**
```bash
pytest test/test_cli_usage.py::TestCLICustomContext::test_custom_context_from_file -v
```

---

## 笔记本管理

### 1. 列出所有笔记本

```bash
python main.py list
```

**测试:**
```bash
pytest test/test_cli_usage.py::TestCLINotebookCommands::test_list_notebooks -v
```

### 2. 显示当前笔记本

```bash
python main.py show
```

### 3. 显示特定笔记本

```bash
python main.py show --notebook notebook_20240101_120000.json
```

### 4. 导出笔记本为 Markdown

```bash
python main.py export notebook_20240101_120000.json --output analysis.md
```

**测试:**
```bash
pytest test/test_cli_usage.py::TestCLIExportCommand::test_export_help -v
```

---

## 执行控制

### 1. 限制最大步数

```bash
python main.py --max-steps 10 start --problem "测试工作流"
```

**说明:** 执行最多 10 个动作后停止

**测试:**
```bash
pytest test/test_cli_usage.py::TestCLIStartCommand::test_start_with_max_steps -v
```

### 2. 启用交互模式

```bash
python main.py --interactive --max-steps 5 start --problem "调试工作流"
```

**说明:** 达到步数限制时暂停，等待用户输入

**测试:**
```bash
pytest test/test_cli_usage.py::TestCLIStartCommand::test_start_interactive_mode -v
```

---

## 高级用法

### 1. 配置后端服务 URL

```bash
python main.py --backend-url http://localhost:9000 --dslc-url http://localhost:9001 start
```

**测试:**
```bash
pytest test/test_cli_usage.py::TestCLIURLConfiguration::test_both_urls_option -v
```

### 2. 组合所有选项

```bash
python main.py \
  --backend-url http://localhost:18600 \
  --dslc-url http://localhost:28600 \
  --max-steps 10 \
  --start-mode generation \
  --custom-context '{"user":"alice"}' \
  start \
  --problem "综合测试" \
  --context "测试所有选项"
```

**测试:**
```bash
pytest test/test_cli_usage.py::TestCLIComplexScenarios::test_all_options_combined -v
```

### 3. 使用环境变量配置

创建 `.env` 文件:
```
BACKEND_BASE_URL=http://localhost:18600
DSLC_BASE_URL=http://localhost:28600
NOTEBOOK_ID=my-notebook-123
```

然后运行:
```bash
python main.py start --problem "使用环境变量配置"
```

---

## 🚀 运行所有 CLI 测试

### 运行所有 CLI 测试

```bash
pytest test/test_cli_usage.py -v
```

### 运行特定测试类

```bash
# 测试基本命令
pytest test/test_cli_usage.py::TestCLIBasicCommands -v

# 测试 start 命令
pytest test/test_cli_usage.py::TestCLIStartCommand -v

# 测试自定义上下文
pytest test/test_cli_usage.py::TestCLICustomContext -v

# 测试笔记本命令
pytest test/test_cli_usage.py::TestCLINotebookCommands -v
```

### 运行特定测试方法

```bash
pytest test/test_cli_usage.py::TestCLIStartCommand::test_start_with_problem -v
```

### 显示详细输出

```bash
pytest test/test_cli_usage.py -v -s
```

### 使用标记运行

```bash
# 运行所有 CLI 测试
pytest -m cli -v

# 排除慢速测试
pytest -m "cli and not slow" -v
```

---

## 📊 测试覆盖的场景

### ✅ 已测试的命令

- [x] `--help` - 帮助信息
- [x] `status` - 状态查看
- [x] `start` - 启动工作流（多种变体）
- [x] `list` - 列出笔记本
- [x] `show` - 显示笔记本
- [x] `export` - 导出笔记本

### ✅ 已测试的选项

- [x] `--problem` - 问题描述
- [x] `--context` - 上下文描述
- [x] `--max-steps` - 最大步数限制
- [x] `--start-mode` - 启动模式（reflection/generation）
- [x] `--interactive` - 交互模式
- [x] `--custom-context` - 自定义上下文（JSON字符串和文件）
- [x] `--backend-url` - 后端服务 URL
- [x] `--dslc-url` - DSLC API URL

### ✅ 已测试的场景

- [x] 简单启动
- [x] 带参数启动
- [x] 反思模式 vs 生成模式
- [x] 自定义上下文注入
- [x] 步数限制和交互模式
- [x] URL 配置
- [x] 组合多个选项

---

## 🔍 测试结果解释

### 成功的测试

```
test_cli_usage.py::TestCLIBasicCommands::test_cli_help PASSED
```
表示命令执行成功，输出符合预期。

### 预期失败的测试

某些测试可能会"失败"但这是预期的，例如：
- 交互模式测试（会等待用户输入）
- 需要实际 API 连接的测试

### 调试失败的测试

```bash
# 查看详细输出
pytest test/test_cli_usage.py::TestName::test_name -v -s

# 保留测试环境
pytest test/test_cli_usage.py::TestName::test_name --pdb
```

---

## 💡 实用技巧

### 1. 快速测试单个命令

```bash
# 测试 help 命令
python main.py --help

# 测试 status 命令
python main.py status

# 测试 list 命令
python main.py list
```

### 2. 使用 Make 命令

如果有 Makefile，可以使用:

```bash
make test-cli
```

### 3. 持续测试

在开发时使用 watch 模式:

```bash
pytest-watch test/test_cli_usage.py
```

---

## 📚 相关文档

- [README.md](../README.md) - 项目主文档
- [ADVANCED_USAGE.md](../ADVANCED_USAGE.md) - 高级用法
- [test/README.md](README.md) - 测试文档

---

## ⚠️ 注意事项

1. **API 依赖**: 某些命令需要后端 API 运行，测试会尝试连接但可能失败
2. **超时设置**: CLI 测试有超时限制，长时间运行的命令可能超时
3. **文件系统**: 某些测试会创建临时文件，测试后会自动清理
4. **环境隔离**: 测试在独立的子进程中运行，不影响当前环境

---

## 🎯 下一步

1. 运行所有 CLI 测试: `pytest test/test_cli_usage.py -v`
2. 尝试手动执行示例命令
3. 根据项目需求扩展测试场景
4. 在 CI/CD 中集成 CLI 测试

**祝测试愉快！** 🚀
