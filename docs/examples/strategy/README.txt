================================================================================
DATA SCIENCE WORKFLOW STRATEGY
================================================================================

本目录包含完整的数据科学工作流策略文件，组织为层次化的结构：

HIERARCHY STRUCTURE:
====================

strategy (工作流)
    ├─ Stage Name (阶段) - 目录
    │   ├─ Step Name (步骤) - 文件
    │   │   ├─ Behavior Name (行为) - 文件内章节
    │   │   │   ├─ Action 1 - 具体操作
    │   │   │   ├─ Action 2
    │   │   │   └─ Action N
    │   │   ├─ Behavior 2
    │   │   └─ Behavior N
    │   └─ Step N
    └─ Stage N

DIRECTORY OVERVIEW:
===================

STAGE 1: Data Existence Establishment (数据存在性建立)
    - 6 steps: 数据收集与盘点、数据结构发现、变量语义分析、观测单元识别、
               变量相关性评估、PCS假设生成

STAGE 2: Data Integrity Assurance (数据完整性保证)
    - 5 steps: 完整性检查策略与备份建立、维度完整性验证、值有效性保证、
               完整性恢复、综合完整性验证

STAGE 3: Exploratory Data Analysis (探索性数据分析)
    - 5 steps: 分析策略与工具准备、当前数据状态评估、定向探索生成、
               分析性洞察提取、综合洞察整合

STAGE 4: Methodology Strategy Formulation (方法策略制定)
    - 4 steps: 策略框架与资源评估、特征和模型方法提案、
               训练评估策略开发、方法策略整合

STAGE 5: Model Implementation Execution (模型实施执行)
    - 4 steps: 实施环境与基础架构建立、特征工程集成、
               建模方法集成、模型训练执行

STAGE 6: Predictability Validation (可预测性验证)
    - 6 steps: 验证策略与环境准备、交叉验证性能评估、留出测试集评估、
               时间验证、领域泛化测试、业务影响验证

STAGE 7: Stability Assessment (稳定性评估)
    - 4 steps: 稳定性评估策略与测试准备、数据扰动分析、
               模型参数敏感性、稳定性分析整合

STAGE 8: Results Communication (结果传达)
    - 6 steps: 受众分析与传达策略制定、技术文档编制、执行摘要、
               可视化传达、利益相关者参与、实施支持

TOTAL: 8 Stages, 40 Step Files

FILE FORMAT:
============

每个 step 文件包含：

1. STEP HEADER
   - Step 编号、名称（中英文）
   - 所属 Stage
   - Step 目标 (GOAL)
   - PCS 考量 (PCS CONSIDERATIONS)
     * Predictability (可预测性)
     * Computability (可计算性)
     * Stability (稳定性)

2. BEHAVIORS
   - 每个 Behavior 有独立的章节
   - Behavior 目标 (GOAL)
   - 详细的 Actions 列表

3. OUTPUT ARTIFACTS
   - 该 Step 的输出交付物清单

USAGE:
======

1. 作为提示词模板：
   - 将相应的 step 文件内容作为状态级别的提示词
   - 在 WORKFLOW 级别使用 Stage 概览
   - 在 SECTION (STEP) 级别使用具体的 step 文件
   - 在 BEHAVIOUR 级别引用对应的 Behavior 章节

2. 工作流规划：
   - 根据项目需求选择适用的 Stages
   - 在每个 Stage 内按 Steps 顺序执行
   - 每个 Step 内按 Behaviors 和 Actions 组织工作

3. 质量保证：
   - 使用 PCS CONSIDERATIONS 确保每个步骤符合框架要求
   - 通过 OUTPUT ARTIFACTS 验证每个步骤的完成度
   - 确保所有 Actions 都被执行

NOTES:
======

- Planning (规划) 不再作为独立的 Stage，已集成到 planning API 中
- "Workflow Initialization" 步骤已重命名为反映实际工作内容的名称
  因为规划工作已由 Planner 在 START_SECTION 阶段完成
- 所有文件使用纯文本格式，便于直接嵌入提示词
- 保持中英文双语，便于不同场景使用
- 完全符合 PCS (Predictability-Computability-Stability) 框架

REFERENCES:
===========

详细的章节说明参考：
- /docs/examples/docs/chapter_*.md

对应的 prompt 示例参考：
- /docs/examples/ames_housing/prompt/

================================================================================
Generated: 2025-11-03
Version: 1.1 (Step 1 titles updated to reflect actual work content)
================================================================================
