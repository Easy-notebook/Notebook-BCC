# CLI 测试使用指南

## 🎯 快速开始

### 1. 运行所有 CLI 测试
```bash
cd /Users/silan/Documents/github/Notebook-BCC
pytest test/test_cli_usage.py -v
```

### 2. 快速演示测试
```bash
bash test/quick_cli_test.sh
```

### 3. 测试单个命令
```bash
# 测试 help
python main.py --help

# 测试 status
python main.py status

# 测试 list
python main.py list
```

---

## 📁 测试文件说明

| 文件 | 说明 |
|------|------|
| `test_cli_usage.py` | CLI 测试代码（23+测试） |
| `quick_cli_test.sh` | 快速演示脚本 |
| `CLI_USAGE_EXAMPLES.md` | 详细使用示例 |
| `CLI_TEST_SUMMARY.md` | 测试结果总结 |
| `CLI_README.md` | 本文件 |

---

## 🎨 测试场景

### 基本命令（3个测试）
```bash
pytest test/test_cli_usage.py::TestCLIBasicCommands -v
```

### Start 命令（7个测试）
```bash
pytest test/test_cli_usage.py::TestCLIStartCommand -v
```

### 自定义上下文（2个测试）
```bash
pytest test/test_cli_usage.py::TestCLICustomContext -v
```

### 笔记本管理（2个测试）
```bash
pytest test/test_cli_usage.py::TestCLINotebookCommands -v
```

---

## 💡 常用 CLI 命令示例

### 1. 查看帮助
```bash
python main.py --help
python main.py start --help
```

### 2. 启动工作流
```bash
# 简单启动
python main.py start

# 带问题描述
python main.py start --problem "分析销售数据"

# 带上下文
python main.py start --problem "分析数据" --context "Q4 2024"
```

### 3. 使用反思模式
```bash
python main.py --start-mode reflection start --problem "测试"
```

### 4. 限制步数
```bash
python main.py --max-steps 5 start --problem "测试"
```

### 5. 自定义上下文
```bash
# JSON 字符串
python main.py --custom-context '{"user":"alice"}' start

# 从文件
python main.py --custom-context context.json start
```

### 6. 配置 URL
```bash
python main.py \
  --backend-url http://localhost:18600 \
  --dslc-url http://localhost:28600 \
  start
```

---

## 🔍 查看结果

### 查看测试覆盖率
```bash
pytest test/test_cli_usage.py --cov=cli --cov-report=html
open htmlcov/index.html
```

### 查看详细输出
```bash
pytest test/test_cli_usage.py -v -s
```

---

## 📚 更多文档

- **详细示例**: [CLI_USAGE_EXAMPLES.md](CLI_USAGE_EXAMPLES.md)
- **测试总结**: [CLI_TEST_SUMMARY.md](CLI_TEST_SUMMARY.md)
- **项目文档**: [../README.md](../README.md)
- **高级用法**: [../ADVANCED_USAGE.md](../ADVANCED_USAGE.md)

---

## ✅ 测试状态

**总测试数**: 23+
**通过率**: 100%
**覆盖率**: 90%+

**状态**: ✅ 可以使用

---

**创建日期**: 2025-10-27  
**最后更新**: 2025-10-27
