# Notebook-BCC 文档中心

## 📚 核心协议文档

### [STATE_MACHINE_PROTOCOL.md](./STATE_MACHINE_PROTOCOL.md) 🆕
**状态机协议规范** - 工作流状态机的完整定义

**包含内容**：
- 完整状态定义（idle → stage → step → behavior → action）
- 事件定义和触发条件
- 完整状态转移表（40+ 种转移规则）
- 责任划分（Planning API vs Client vs Generating API）
- 状态转移流程图（Mermaid 图表）
- 错误处理和容错机制
- 典型场景示例
- 实现指南和最佳实践

**适用对象**：
- 前端开发者（实现状态机逻辑）
- 系统架构师（理解控制流）
- 后端开发者（理解 API 触发的转移）

---

### [OBSERVATION_PROTOCOL.md](./OBSERVATION_PROTOCOL.md)
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

### [CODE_VERIFICATION_REPORT.md](./CODE_VERIFICATION_REPORT.md) 🆕
**代码实现验证报告** - 详细验证代码是否符合协议规范

**包含内容**：
- 逐状态转移验证（15 个状态）
- API 调用时机和 Payload 验证
- Observation 结构 100% 对比
- 发现的问题和修复记录
- 协议符合度评分（4.9/5.0）

**适用对象**：
- 技术审查人员（验证实现正确性）
- QA 团队（测试清单）
- 系统架构师（设计决策验证）

---

### [API_CALLS_FIX_SUMMARY.md](./API_CALLS_FIX_SUMMARY.md) 🆕
**Planning API 调用修复总结** - 修复缺失的 Planning API 调用

**包含内容**：
- 修复前后问题对比（4 个缺失的 API 调用点）
- 完整的 Planning API 调用汇总（6 个状态）
- API 调用频率对比（修复前 vs 修复后）
- 潜在问题和注意事项（双重调用、降级策略）
- 完整验证清单

**适用对象**：
- 开发者（理解 API 调用修复）
- 技术审查人员（验证修复正确性）
- 系统架构师（理解调用频率影响）

---

### [CODE_UPDATE_SUMMARY.md](./CODE_UPDATE_SUMMARY.md)
**代码实现更新总结** - 代码更新以符合新协议规范

**包含内容**：
- Focus 结构变更（List → String）
- 输出追踪系统实现
- Context Update 增强
- 所有修改文件的详细说明
- 使用示例和测试清单

**适用对象**：
- 所有开发者（了解实现变更）
- Code Reviewers（审查更新）

---

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
├── STATE_MACHINE_PROTOCOL.md      # 🆕 状态机协议（控制流）
├── OBSERVATION_PROTOCOL.md        # 🆕 Observation 协议（数据结构）
├── API_PROTOCOL.md                # API 交互协议
├── ACTION_PROTOCOL.md             # Action 规范
├── CODE_VERIFICATION_REPORT.md    # 🆕 代码实现验证报告
├── API_CALLS_FIX_SUMMARY.md       # 🆕 Planning API 调用修复总结
├── CODE_UPDATE_SUMMARY.md         # 🆕 代码实现更新总结
├── REFACTORING_SUMMARY.md         # 重构总结
└── examples/                       # 🆕 示例和测试用例
    └── ames_housing/               # Ames Housing 房价预测示例
        ├── README.md               # 示例说明
        ├── workflow.json           # 工作流定义
        └── payloads/               # 所有状态的 payload 示例
            ├── INDEX.md            # Payload 索引
            └── *.json              # 各状态 payload（10+ 个）
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

1. **首先阅读**：[STATE_MACHINE_PROTOCOL.md](./STATE_MACHINE_PROTOCOL.md)
   - 理解状态机设计
   - 实现状态转移逻辑
   - 理解 Client 的导航职责

2. **然后阅读**：[OBSERVATION_PROTOCOL.md](./OBSERVATION_PROTOCOL.md)
   - 构建 observation payload
   - 实现产出追踪
   - 实现临时变量升格

3. **接着阅读**：[API_PROTOCOL.md](./API_PROTOCOL.md)
   - 调用 Planning/Generating API
   - 处理 context_filter
   - 应用筛选逻辑

4. **参考**：[ACTION_PROTOCOL.md](./ACTION_PROTOCOL.md)
   - 执行 Actions
   - 更新 effects

### 我是新加入的开发者

1. **快速了解**：[REFACTORING_SUMMARY.md](./REFACTORING_SUMMARY.md)
   - 理解系统架构
   - 理解设计决策
   - 理解重构原因

2. **查看示例**：[examples/ames_housing/](./examples/ames_housing/)
   - 完整的 workflow 示例
   - 所有状态的 payload 示例
   - API 调用实例

3. **深入学习**：按上述角色指南阅读相关文档

---

## 🔑 核心概念速查

### 状态机 (FSM)
工作流控制系统，定义状态和转移规则：
- **状态层级**: idle → stage → step → behavior → action
- **混合控制**: Planning API（目标判断）+ Client（导航）
- **事件驱动**: 通过事件触发状态转移
- 详见：[STATE_MACHINE_PROTOCOL.md](./STATE_MACHINE_PROTOCOL.md)

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

### Artifact ID 命名规范
当临时变量需要升格为正式产出时，使用标准命名格式：
```
格式：<base_name>@<version_identifier>

示例：
- df_imputed@iter3          # 迭代版本
- df_cleaned@step_final     # 步骤最终版本
- model_v1@stage_modeling   # 阶段版本
- report_summary@behavior_005  # Behavior 产出
```
- 详见：[OBSERVATION_PROTOCOL.md](./OBSERVATION_PROTOCOL.md#artifact-id-命名规范)

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

## 💡 示例和测试用例

### [Ames Housing 房价预测示例](./examples/ames_housing/) 🆕

**完整的端到端示例**，展示整个 workflow 的状态转移和 payload 结构。

**包含内容**：
- 完整的 workflow 定义（3 个 stages，7 个 steps，18 个 behaviors）
- 10 个关键状态的 payload 示例（JSON 格式）
- Planning API 和 Generating API 调用实例
- 数据演化轨迹（从 0 到 21 个变量）
- 产出追踪示例（expected → in_progress → produced）

**适用场景**：
- 理解协议的完整实现
- 验证 API 集成
- 生成测试用例
- 调试状态转移问题

**快速开始**：
```bash
# 查看 workflow 定义
cat examples/ames_housing/workflow.json | jq .

# 查看 Planning First 示例
cat examples/ames_housing/payloads/03_STEP_RUNNING_s1_step1.json | jq .

# 查看所有 payload 索引
cat examples/ames_housing/payloads/INDEX.md
```

**关键示例**：
- **Planning First**: [03_STEP_RUNNING_s1_step1.json](./examples/ames_housing/payloads/03_STEP_RUNNING_s1_step1.json)
- **Generating API**: [04_BEHAVIOR_RUNNING_s1_step1_b1.json](./examples/ames_housing/payloads/04_BEHAVIOR_RUNNING_s1_step1_b1.json)
- **Behavior Feedback**: [06_ACTION_COMPLETED_s1_step1_b1.json](./examples/ames_housing/payloads/06_ACTION_COMPLETED_s1_step1_b1.json)
- **产出追踪**: [08_STEP_COMPLETED_s1_step1.json](./examples/ames_housing/payloads/08_STEP_COMPLETED_s1_step1.json)

---

## 📝 更新日志

### 2025-10-30 (Phase 5: Examples)
- 🆕 创建 examples/ames_housing/ 示例目录
- 🆕 创建完整的 Ames Housing 房价预测 workflow 定义
- 🆕 创建 10 个关键状态的 payload 示例
- ✅ 覆盖所有 Planning API 和 Generating API 调用场景
- ✅ 展示 Planning First 协议
- ✅ 展示三状态产出追踪（expected/produced/in_progress）
- ✅ 展示 behavior_feedback 传递
- ✅ 展示 context_update 应用
- ✅ 提供完整的数据演化轨迹

### 2025-10-30 (Phase 4: API Calls Fix)
- 🆕 创建 API_CALLS_FIX_SUMMARY.md（Planning API 调用修复总结）
- ✅ 修复 STAGE_RUNNING：添加 Planning API 调用以决定启动哪个 step
- ✅ 修复 ACTION_COMPLETED：添加 Planning API 调用以确认 behavior 完成
- ✅ 修复 STEP_COMPLETED：添加 Planning API 调用以决定是否完成 stage
- ✅ 修复 STAGE_COMPLETED：添加 Planning API 调用以决定是否完成 workflow
- ✅ Planning API 调用从 2 个状态增加到 6 个状态
- ✅ 所有 Planning API 调用都使用 require_progress_info=True
- ✅ 完整的错误处理和降级策略

### 2025-10-30 (Phase 3: Verification)
- 🆕 创建 CODE_VERIFICATION_REPORT.md（代码验证报告）
- ✅ 验证所有状态转移（15 个状态，40+ 种转移）
- ✅ 验证 API 调用时机和 Payload 结构
- ✅ 验证 Observation 结构 100% 符合协议
- ✅ 修复 step_effects.py require_progress_info 问题
- ⚠️ 初始评分 4.9/5.0（后续发现更多问题）

### 2025-10-30 (Phase 2: Code Implementation)
- 🆕 创建 CODE_UPDATE_SUMMARY.md（代码实现更新总结）
- ✅ 更新 state_machine.py：Focus 从 List[str] 改为 str
- ✅ 更新 state_machine.py：添加 current_outputs 追踪
- ✅ 更新 behavior_effects.py：增强 context_update 处理
- ✅ 更新 step_effects.py：添加 Planning API 响应处理
- ✅ 更新 api_client.py：增强文档注释
- ✅ 所有代码与协议文档对齐

### 2025-10-30 (Phase 1: Documentation)
- 🆕 创建 STATE_MACHINE_PROTOCOL.md（完整状态机协议）
- 🆕 创建 OBSERVATION_PROTOCOL.md（POMDP 观测结构）
- ✅ 更新 API_PROTOCOL.md，添加 Context Filter 协议
- ✅ 更新 ACTION_PROTOCOL.md，明确 Generating vs Planning
- ✅ 修正文档日期一致性和交叉引用
- 🗑️ 清理旧设计文档

### 2025-10-28
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

**Last Updated**: 2025-10-30
**Version**: 2.0 (After Refactoring)
