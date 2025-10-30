# Notebook-BCC 文档中心

## 📚 核心协议文档

### [OBSERVATION_PROTOCOL.md](./OBSERVATION_PROTOCOL.md) 🆕
**Observation 协议规范** - 完整的 POMDP observation 结构定义

**包含内容**：
- 完整 observation 结构（location, progress, goals, context）
- 层级化进度追踪机制（stages/steps/behaviors）
- 产出追踪系统（expected/produced/in_progress）
- 临时变量升格规则（df_working → df_imputed@iter3）
- Context Filter 协议详解
- 错误处理规则（变量不存在时的 WARN 机制）

**适用对象**：
- 后端开发者（实现 Planning/Generating API）
- 前端开发者（构建 observation payload）
- 系统架构师（理解数据流）

---

### [API_PROTOCOL.md](./API_PROTOCOL.md)
**API 交互协议** - Planning 和 Generating API 的完整规范

**包含内容**：
- API 端点配置
- Planning First 协议
- 请求/响应格式
- 流式响应处理
- **Context Filter 协议**（NEW）
- 上下文更新机制
- 最佳实践

**适用对象**：
- API 集成开发者
- 后端服务实现者

**关键更新**：
- ✅ 添加 Context Filter 协议
- ✅ 更新 focus 为文本格式（非变量名列表）
- ✅ 明确 effects 是代码执行输出

---

### [ACTION_PROTOCOL.md](./ACTION_PROTOCOL.md)
**Action 协议规范** - 7 种 Generating Actions 的详细定义

**包含内容**：
- POMDP 设计原理
- 7 种 Generating Actions：
  1. ADD_ACTION - 添加内容
  2. EXEC_CODE - 执行代码
  3. IS_THINKING / FINISH_THINKING - 思考过程
  4. NEW_CHAPTER / NEW_SECTION - 结构标记
  5. UPDATE_TITLE - 更新标题
- 已弃用的 Actions（UPDATE_WORKFLOW, COMPLETE_STEP 等）
- Shot Type 说明
- 错误处理

**适用对象**：
- Action 执行器实现者
- Generating API 开发者

**关键更新**：
- ✅ 明确 Generating Actions（7个）vs Planning Updates（6个）
- ✅ 添加已弃用 Actions 章节
- ✅ 更新 POMDP observation 示例

---

## 📖 总结文档

### [REFACTORING_SUMMARY.md](./REFACTORING_SUMMARY.md)
**系统重构总结** - Action 系统重构的完整记录

**包含内容**：
- 重构前后对比
- Actions 分组（Generating vs Planning）
- Context 简化
- 层级化 Focus 系统设计
- 迁移指南
- 测试清单

**适用对象**：
- 项目维护者
- 新加入的开发者
- 系统审计

---

## 🗂️ 目录结构

```
docs/
├── README.md                      # 本文档（导航）
├── OBSERVATION_PROTOCOL.md        # 🆕 Observation 协议（核心）
├── API_PROTOCOL.md                # API 交互协议
├── ACTION_PROTOCOL.md             # Action 规范
└── REFACTORING_SUMMARY.md         # 重构总结
```

---

## 🚀 快速开始

### 我是后端开发者

1. **首先阅读**：[OBSERVATION_PROTOCOL.md](./OBSERVATION_PROTOCOL.md)
   - 理解完整的 observation 结构
   - 理解产出追踪机制
   - 理解 Context Filter 协议

2. **然后阅读**：[API_PROTOCOL.md](./API_PROTOCOL.md)
   - 实现 Planning API
   - 实现 Generating API
   - 实现 context_filter 逻辑

3. **最后阅读**：[ACTION_PROTOCOL.md](./ACTION_PROTOCOL.md)
   - 生成 7 种 Generating Actions

### 我是前端开发者

1. **首先阅读**：[OBSERVATION_PROTOCOL.md](./OBSERVATION_PROTOCOL.md)
   - 构建 observation payload
   - 实现产出追踪
   - 实现临时变量升格

2. **然后阅读**：[API_PROTOCOL.md](./API_PROTOCOL.md)
   - 调用 Planning/Generating API
   - 处理 context_filter
   - 应用筛选逻辑

3. **参考**：[ACTION_PROTOCOL.md](./ACTION_PROTOCOL.md)
   - 执行 Actions
   - 更新 effects

### 我是新加入的开发者

1. **快速了解**：[REFACTORING_SUMMARY.md](./REFACTORING_SUMMARY.md)
   - 理解系统架构
   - 理解设计决策
   - 理解重构原因

2. **深入学习**：按上述角色指南阅读相关文档

---

## 🔑 核心概念速查

### Observation
完整的 POMDP 观测数据，包含：
- **Location**: 当前位置、进度、目标
- **Context**: 变量、effects、notebook 状态
- 详见：[OBSERVATION_PROTOCOL.md](./OBSERVATION_PROTOCOL.md)

### Focus
Planner 生成的**详细分析文本**，用于指导 Generating API：
- 不是变量名列表
- 不是任务描述列表
- 是完整的分析和建议文本
- 详见：[OBSERVATION_PROTOCOL.md](./OBSERVATION_PROTOCOL.md#2-progress层级化进度)

### Effects
Python 代码执行的**实际输出**：
- 不是操作日志
- 是 print() 输出、显示结果、返回值
- 用于提供执行证据
- 详见：[OBSERVATION_PROTOCOL.md](./OBSERVATION_PROTOCOL.md#2-effectseffects)

### 产出追踪
三状态追踪系统：
- **expected**: 期望产出
- **produced**: 已完成产出
- **in_progress**: 正在构建
- 详见：[OBSERVATION_PROTOCOL.md](./OBSERVATION_PROTOCOL.md#产出追踪机制)

### Context Filter
Planning API 的筛选指令：
- 控制传递给 Generating API 的信息
- 减少 token 消耗
- 提高提示词质量
- 详见：[API_PROTOCOL.md](./API_PROTOCOL.md#-context-filter-协议new)

### Actions 分组
- **Generating Actions**（7个）：由 Generating API 返回
- **Planning Updates**（6个）：由 Planning API 通过 context_update 返回
- 详见：[ACTION_PROTOCOL.md](./ACTION_PROTOCOL.md#-action-类型总览)

---

## 📝 更新日志

### 2025-01-15
- 🆕 创建 OBSERVATION_PROTOCOL.md
- ✅ 更新 API_PROTOCOL.md，添加 Context Filter 协议
- ✅ 更新 ACTION_PROTOCOL.md，明确 Generating vs Planning
- 🗑️ 清理旧设计文档

### 2025-01-14
- ✅ 完成系统重构
- ✅ 创建 REFACTORING_SUMMARY.md

---

## 🤝 贡献指南

更新文档时请遵循：
1. **保持一致性**：使用相同的术语和格式
2. **添加示例**：每个概念都要有代码示例
3. **注明版本**：重大更新要标记日期
4. **交叉引用**：相关概念要链接到其他文档

---

## 📧 联系方式

如有疑问或建议，请：
- 提交 Issue
- 查看 [GitHub Repository](https://github.com/anthropics/notebook-bcc)

---

**Last Updated**: 2025-01-15
**Version**: 2.0 (After Refactoring)
