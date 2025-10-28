# Notebook-BCC 新架构快速上手

**重构日期**: 2025-10-28

---

## 📂 新的项目结构

```
stores/
├── action_registry.py (202行) - Action注册机制
├── script_store.py (495行) - 核心调度 
└── handlers/ - 模块化handlers
    ├── content_handlers.py (174行)
    ├── code_handlers.py (190行) 
    ├── thinking_handlers.py (76行)
    ├── workflow_handlers.py (141行)
    └── text_handlers.py (54行)

core/
├── state_machine.py (903行) - FSM核心
├── state_transitions.py (153行) - 转换规则
├── states.py
├── events.py
└── context.py
```

---

## 🎯 核心改进

| 指标 | 结果 |
|------|------|
| script_store.py | 1030行 → 495行 (-52%) |
| 最大文件 | <500行 |
| 模块数量 | 13+ 个独立模块 |
| 平均文件大小 | ~200行 |

---

## 🚀 使用新架构

### 1. 导入模块

```python
from stores.script_store import ScriptStore
from stores.action_registry import ActionRegistry
from core.state_transitions import get_next_state
```

### 2. 添加自定义Handler

```python
# 1. 创建 stores/handlers/my_handler.py
def handle_custom(script_store, step):
    # 实现
    pass

# 2. 在 handlers/__init__.py 导出
from .my_handler import handle_custom

# 3. 在 script_store.py 注册
registry.register_handler('custom',
    lambda step: handle_custom(self, step))
```

### 3. 使用状态转换

```python
from core.state_transitions import (
    get_next_state,
    is_valid_transition,
    get_valid_events
)

# 获取下一状态
next_state = get_next_state(current_state, event)

# 验证转换
if is_valid_transition(current_state, event):
    # 执行转换
    pass
```

---

## 💡 设计原则

1. **单一职责** - 每个模块一个功能
2. **文件大小** - 保持 <200 行
3. **策略模式** - 可插拔的handler机制
4. **委托模式** - 核心类委托给专门模块

---

## 📝 最佳实践

- ✅ 新功能创建新文件
- ✅ 使用辅助函数而非直接访问
- ✅ Handler 保持独立可测试
- ✅ 通过 ActionRegistry 注册

---

## 📖 更多信息

- `OPTIMIZATION_REPORT.md` - 详细优化报告
- `REFACTORING_SUMMARY.md` - 重构总结
- 各模块文档字符串 - 具体API说明

---

**开始使用新架构！** 🎉
