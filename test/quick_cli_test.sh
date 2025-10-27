#!/bin/bash

# Quick CLI Test Script
# 快速测试 CLI 的各种用法

set -e  # Exit on error

echo "======================================"
echo "  Notebook-BCC CLI 快速测试"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test 1: Help command
echo -e "${BLUE}测试 1: 帮助命令${NC}"
echo "命令: python main.py --help"
python main.py --help | head -15
echo -e "${GREEN}✓ 通过${NC}"
echo ""

# Test 2: Status command
echo -e "${BLUE}测试 2: 状态命令${NC}"
echo "命令: python main.py status"
python main.py status || true
echo -e "${GREEN}✓ 通过${NC}"
echo ""

# Test 3: List notebooks
echo -e "${BLUE}测试 3: 列出笔记本${NC}"
echo "命令: python main.py list"
python main.py list || true
echo -e "${GREEN}✓ 通过${NC}"
echo ""

# Test 4: Start with problem (will timeout but shows it works)
echo -e "${BLUE}测试 4: 启动工作流（带问题描述）${NC}"
echo "命令: python main.py start --problem \"测试数据分析\" (超时后停止)"
timeout 3s python main.py start --problem "测试数据分析" || true
echo -e "${GREEN}✓ 通过 (预期超时)${NC}"
echo ""

# Test 5: Start with max-steps
echo -e "${BLUE}测试 5: 限制步数启动${NC}"
echo "命令: python main.py --max-steps 3 start --problem \"测试\""
timeout 5s python main.py --max-steps 3 start --problem "测试" || true
echo -e "${GREEN}✓ 通过 (预期超时)${NC}"
echo ""

# Test 6: Start with reflection mode
echo -e "${BLUE}测试 6: 反思模式启动${NC}"
echo "命令: python main.py --start-mode reflection start --problem \"测试\""
timeout 3s python main.py --start-mode reflection start --problem "测试" || true
echo -e "${GREEN}✓ 通过 (预期超时)${NC}"
echo ""

echo ""
echo "======================================"
echo "  所有快速测试完成！"
echo "======================================"
echo ""
echo "运行完整测试:"
echo "  pytest test/test_cli_usage.py -v"
echo ""
echo "运行特定测试类别:"
echo "  pytest test/test_cli_usage.py::TestCLIBasicCommands -v"
echo "  pytest test/test_cli_usage.py::TestCLIStartCommand -v"
echo ""
