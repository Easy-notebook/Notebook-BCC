# Observation 协议规范

##  概述

Observation 是 POMDP 框架中的核心数据结构，包含 Planner 维护的完整状态信息。本文档详细定义 observation 的结构、产出追踪机制、筛选协议和错误处理规则。

---

## 🏗️ 完整 Observation 结构

### 顶层结构

```json
{
  "observation": {
    "location": {
      "current": {...},      // 当前位置
      "progress": {...},     // 层级化进度（含 focus 和 outputs 追踪）
      "goals": {...}         // 各层级目标
    },
    "context": {
      "variables": {...},    // 环境变量
      "effects": {...},      // 代码执行输出
      "notebook": {...},     // Notebook 状态
      "FSM": {...}          // 状态机信息
    }
  },
  "options": {...}
}
```

---

## 📍 Location 详细结构

### 1. Current（当前位置）

```json
"current": {
  "stage_id": "data_cleaning",
  "step_id": "handle_missing_values",
  "behavior_id": "behavior_003",
  "behavior_iteration": 3
}
```

### 2. Progress（层级化进度）

每个层级（stages/steps/behaviors）包含：
- **completed**: 已完成项目列表（含产出追踪）
- **current**: 当前项目 ID
- **remaining**: 剩余项目列表
- **focus**: Planner 生成的详细分析文本
- **current_outputs**: 当前项目的产出追踪

#### Stage 级别示例

```json
"stages": {
  "completed": [
    {
      "stage_id": "data_loading",
      "goal": "加载  Housing 数据集并完成基本验证",
      "actions_taken": [
        "读取 train.csv 和 test.csv",
        "合并数据集",
        "基本数据探索"
      ],
      "outputs_produced": {
        "variables": ["df_train", "df_test", "df_full", "data_info"],
        "artifacts": [
          {
            "artifact_id": "df_full@loading",
            "variable_name": "df_full",
            "description": "合并的完整数据集",
            "created_at": "2025-01-15T10:00:00Z"
          }
        ],
        "key_findings": [
          "训练集1460行×81列",
          "测试集1459行×80列（无SalePrice）"
        ]
      }
    }
  ],

  "current": "data_cleaning",
  "remaining": ["feature_engineering", "modeling", "evaluation"],

  "focus": "【Data Cleaning Stage - 全局指导】\n\n## 阶段目标\n...",

  "current_outputs": {
    "expected": [
      "df_cleaned",
      "cleaning_report",
      "feature_quality_scores"
    ],
    "produced": [],
    "in_progress": []
  }
}
```

#### Step 级别示例

```json
"steps": {
  "completed": [
    {
      "step_id": "convert_data_types",
      "goal": "转换数据类型",
      "actions_taken": ["识别类别特征", "执行类型转换"],
      "outputs_produced": {
        "variables": ["df", "type_conversion_log"],
        "modified_features": ["MSSubClass", "OverallCond"],
        "validation": "4个特征类型转换成功"
      }
    }
  ],

  "current": "handle_missing_values",
  "remaining": ["handle_outliers", "validate_consistency"],

  "focus": "【Step: 缺失值处理 - 详细执行方案】\n\n...",

  "current_outputs": {
    "expected": [
      "df",                    // 更新后的主数据集
      "missing_fill_report",   // 填充报告
      "imputation_log"         // 操作日志
    ],
    "produced": [
      "missing_summary",       // Behavior 001 产出
      "missing_groups"         // Behavior 002 产出
    ],
    "in_progress": []          // 进入新 behavior 前已清空
  }
}
```

#### Behavior 级别示例

```json
"behaviors": {
  "completed": [
    {
      "behavior_id": "behavior_001",
      "goal": "统计所有特征的缺失值情况",
      "actions_taken": [
        "计算每列缺失值数量和比例",
        "生成缺失值可视化"
      ],
      "outputs_produced": {
        "variables": ["missing_summary", "missing_patterns"],
        "artifacts": [
          {
            "artifact_id": "missing_summary@behavior_001",
            "variable_name": "missing_summary",
            "description": "缺失值统计字典",
            "created_at": "2025-01-15T10:10:00Z"
          }
        ],
        "findings": "19个特征存在缺失，总缺失率6.0%"
      }
    }
  ],

  "current": "behavior_003",
  "iteration": 3,

  "focus": "【Behavior 003: 执行缺失值填充操作】\n\n...",

  "current_outputs": {
    "expected": [
      "df_working",
      "imputation_log",
      "high_missing_report"
    ],
    "produced": [],
    "in_progress": [
      "df_working",           // 正在创建
      "imputation_log"        // 正在构建
    ]
  }
}
```

### 3. Goals（目标声明）

```json
"goals": {
  "stage": "完成  Housing 数据集的全面清洗...",
  "step": "系统化处理数据集中的所有缺失值...",
  "behavior": "执行高缺失率特征的语义填充..."
}
```

---

## 📦 产出追踪机制

### 1. Outputs 字段说明

每个层级的 `current_outputs` 包含三个字段：

```python
"current_outputs": {
    "expected": List[str],      # 期望产生的变量名
    "produced": List[str],      # 已经产生的变量名
    "in_progress": List[str]    # 正在生成中的变量名
}
```

**字段语义**：
- **expected**: Planner 定义的该层级应该产出的变量
- **produced**: 已完成并验证的产出
- **in_progress**: 正在构建中的临时变量

### 2. 产出状态转移规则

#### ⚠️ 关键规则：produced 与 in_progress 严格区分

```python
# ❌ 错误：混淆两者
"current_outputs": {
    "produced": ["df_working", "report"],  # df_working 是临时的！
    "in_progress": []
}

# ✅ 正确：严格区分
"current_outputs": {
    "produced": ["missing_summary", "missing_groups"],  # 已完成的产出
    "in_progress": ["df_working", "imputation_log"]     # 正在构建的临时变量
}
```

#### 状态转移时机

**Behavior 完成时**：
```python
# Before: Behavior N 结束
"behaviors": {
    "current": "behavior_002",
    "current_outputs": {
        "expected": ["missing_groups"],
        "produced": ["missing_groups"],  # ✓ 已完成
        "in_progress": []                # ✓ 清空
    }
}

# After: Behavior N+1 开始
"behaviors": {
    "current": "behavior_003",
    "current_outputs": {
        "expected": ["df_working", "imputation_log"],
        "produced": [],      # ✓ 重置
        "in_progress": []    # ✓ 等待填充
    }
}
```

**Step 完成时**：
```python
# 将 behaviors 的所有 produced 搬运到 step.produced
"steps": {
    "current": "handle_missing_values",
    "current_outputs": {
        "expected": ["df", "missing_fill_report"],
        "produced": [
            "missing_summary",    # 来自 behavior_001
            "missing_groups",     # 来自 behavior_002
            "df_imputed@iter3"    # 来自 behavior_003（已升格）
        ],
        "in_progress": []
    }
}
```

### 3. 临时变量升格规则

#### 升格场景

当临时变量（如 `df_working`）需要成为阶段性产物时：

**规则**：
1. **重命名**：使用语义化名称 + 版本标识
2. **登记 artifact_id**：记录在 `artifacts` 列表
3. **从 in_progress 移除**：清理临时状态
4. **加入 produced**：标记为正式产出

#### 示例：df_working 升格

```python
# Before: df_working 在 in_progress
"current_outputs": {
    "in_progress": ["df_working", "imputation_log"]
}

# 升格操作
# 1. 在代码中重命名
df_imputed_iter3 = df_working.copy()
df_imputed_iter3.name = "df_imputed@iter3"

# 2. 登记 artifact
artifact = {
    "artifact_id": "df_imputed@iter3",
    "variable_name": "df_imputed_iter3",
    "description": "缺失值填充后的数据集（iteration 3）",
    "source": "behavior_003",
    "parent": "df_working",
    "created_at": "2025-01-15T10:25:00Z"
}

# After: 更新 outputs
"outputs_produced": {
    "variables": ["df_imputed_iter3", "imputation_log", "high_missing_report"],
    "artifacts": [artifact]
}

# 清理临时变量
del df_working  # 避免误用
```

#### Artifact ID 命名规范

```
格式：<base_name>@<version_identifier>

示例：
- df_imputed@iter3          # 迭代版本
- df_cleaned@step_final     # 步骤最终版本
- model_v1@stage_modeling   # 阶段版本
- report_summary@behavior_005  # Behavior 产出
```

---

## 🌊 Context 详细结构

### 1. Variables（环境变量）

```json
"variables": {
  "df": "DataFrame(1460×79)",
  "df_train": "DataFrame(1460×81)",
  "missing_summary": {
    "PoolQC": {"count": 1453, "rate": 0.995},
    "LotFrontage": {"count": 259, "rate": 0.177}
  },
  "missing_groups": {
    "high_missing": ["PoolQC", "MiscFeature", "Alley"],
    "garage_related": ["GarageType", "GarageYrBlt"]
  },
  "type_conversion_log": ["MSSubClass: int64 -> object"]
}
```

**说明**：
- 包含所有当前存在的 Python 变量
- 复杂对象用字符串表示类型（如 DataFrame）
- 字典/列表类型可以包含完整数据（如果不太大）

### 2. Effects（代码执行输出）

**⚠️ 关键理解**：Effects 是 Python 代码运行的**实际输出**，不是操作日志！

```json
"effects": {
  "current": [
    // 最近的代码输出（print、显示、返回值）
    "PoolQC         1453\nMiscFeature    1406\nAlley          1369\ndtype: int64",

    "车库特征缺失连带性分析：\nGarageType      81 (100.0%)\nGarageYrBlt     81 (100.0%)\n结论：这7个特征在同样的81条记录上都缺失",

    "{'high_missing': ['PoolQC', 'MiscFeature', 'Alley', 'Fence', 'FireplaceQu'], 'garage_related': [...]}"
  ],

  "history": [
    // 历史代码输出
    "数据类型转换：\nMSSubClass: int64 -> object\nOverallCond: int64 -> object\n转换完成",

    "检查重复记录...\ndf.duplicated().sum() = 0\n结果：未发现重复记录"
  ]
}
```

**Effects 的作用**：
1. **给 Planner 提供证据**：判断目标是否达成
2. **给 Generator 提供上下文**：了解最近发生了什么
3. **追踪执行历史**：记录数据演变过程

### 3. Notebook 状态

```json
"notebook": {
  "title": " Housing Price Prediction - Data Cleaning",
  "cell_count": 45,
  "last_cell_type": "code",
  "last_output": "{'high_missing': [...], ...}"
}
```

### 4. FSM 状态

```json
"FSM": {
  "state": "BEHAVIOR_RUNNING",
  "last_transition": "NEXT_BEHAVIOR -> BEHAVIOR_RUNNING",
  "timestamp": "2025-01-15T10:23:45Z"
}
```

---

## 🔍 Context Filter 协议

### Planning API 响应中的筛选指令

Planning API 可以在响应中指定 `context_filter`，告诉 Client 下次调用 Generating API 时应该传递什么信息。

### 完整 Planning 响应示例

```json
{
  "targetAchieved": false,

  "transition": {
    "continue_behaviors": true,
    "target_achieved": false
  },

  "context_update": {
    "variables": {
      "analysis_checkpoint": "behavior_003_started"
    },
    "progress_update": {
      "level": "behaviors",
      "focus": "【Behavior 003: 执行缺失值填充操作】\n\n..."
    }
  },

  "context_filter": {
    "variables_to_include": [
      "df",
      "missing_groups",
      "missing_summary"
    ],

    "variables_to_summarize": {
      "correlation_matrix": "shape_only",
      "df_train": "describe_only"
    },

    "effects_config": {
      "include_current": true,
      "current_limit": 3,
      "include_history": false,
      "history_limit": 0
    },

    "focus_to_include": [
      "behaviors",
      "steps"
    ],

    "outputs_tracking": {
      "expected_variables": ["df_working", "imputation_log"],
      "validation_required": ["high_missing_validated"]
    }
  }
}
```

### Context Filter 字段说明

#### 1. variables_to_include

指定传递给 Generating API 的变量列表。

```json
"variables_to_include": [
  "df",              // 完整传递
  "missing_groups"   // 完整传递
]
```

**⚠️ 错误处理规则**：
- 如果列表中的变量不存在于 `context.variables`
- Client **不要静默丢弃**
- 必须在 effects 中打 WARN
- 回退到 summarize 策略

```python
# Client 实现
for var_name in variables_to_include:
    if var_name not in context.variables:
        # 打 WARN 到 effects
        warning_msg = f"⚠️ WARN: Variable '{var_name}' requested but not found in context"
        effects.current.append(warning_msg)

        # 回退到 summarize
        if var_name in variables_to_summarize:
            # 使用 summarize 策略
            pass
        else:
            # 完全跳过
            continue
```

#### 2. variables_to_summarize

对大型变量进行摘要而非完整传递。

```json
"variables_to_summarize": {
  "correlation_matrix": "shape_only",    // 只传递形状
  "df_train": "describe_only",           // 只传递统计摘要
  "model_history": "last_5_only"         // 只传递最后5条
}
```

**摘要策略**：
- `shape_only`: 对于矩阵/DataFrame，只传递 shape
- `describe_only`: 只传递 `.describe()` 结果
- `head_only`: 只传递前几行
- `last_N_only`: 只传递最后 N 个元素

#### 3. effects_config

配置 effects 的传递方式。

```json
"effects_config": {
  "include_current": true,     // 是否包含 current
  "current_limit": 3,          // current 最多保留几条
  "include_history": false,    // 是否包含 history
  "history_limit": 0,          // history 最多保留几条
  "patterns": {
    "include": ["^✓", "^Error"],  // 正则匹配：只包含成功和错误
    "exclude": ["^DEBUG"]          // 排除 DEBUG 信息
  }
}
```

#### 4. focus_to_include

指定传递哪些层级的 focus。

```json
"focus_to_include": [
  "behaviors",  // 必须包含当前层级
  "steps"       // 包含上层指导
]
// 不包含 "stages"（太宏观）
```

#### 5. outputs_tracking

指定 Generating API 应该关注的期望产出。

```json
"outputs_tracking": {
  "expected_variables": ["df_working", "imputation_log"],
  "validation_required": ["high_missing_validated"]
}
```

---

## 🔄 完整工作流程

### 1. Behavior 完成 → Planning API

```json
// Client 发送完整 observation
POST /planning
{
  "observation": {
    "location": {
      "progress": {
        "behaviors": {
          "current_outputs": {
            "expected": ["missing_groups"],
            "produced": ["missing_groups"],
            "in_progress": []  // ✓ 已清空
          }
        }
      }
    },
    "context": {
      "variables": { /* 所有变量 */ },
      "effects": { /* 所有 effects */ }
    }
  }
}
```

### 2. Planning API 分析并返回筛选指令

```json
// Planning API 响应
{
  "targetAchieved": false,
  "context_update": {
    "progress_update": {
      "level": "behaviors",
      "focus": "【新的 behavior focus】..."
    }
  },
  "context_filter": {
    "variables_to_include": ["df", "missing_groups"],
    "effects_config": {"current_limit": 3},
    "focus_to_include": ["behaviors", "steps"]
  }
}
```

### 3. Client 应用筛选 → Generating API

```python
# Client 处理
def prepare_generating_payload(observation, context_filter):
    # 筛选 variables
    filtered_vars = {}
    for var_name in context_filter['variables_to_include']:
        if var_name in observation.context.variables:
            filtered_vars[var_name] = observation.context.variables[var_name]
        else:
            # ⚠️ 错误处理：变量不存在
            warning = f"⚠️ WARN: Variable '{var_name}' not found, skipping"
            observation.context.effects.current.append(warning)

    # 筛选 effects
    effects_cfg = context_filter['effects_config']
    filtered_effects = observation.context.effects.current[:effects_cfg['current_limit']]

    # 筛选 focus
    filtered_progress = {}
    for level in context_filter['focus_to_include']:
        filtered_progress[level] = {
            'focus': observation.location.progress[level].focus,
            'current_outputs': observation.location.progress[level].current_outputs
        }

    # 构建精简 payload
    return {
        'observation': {
            'location': {
                'current': observation.location.current,
                'progress': filtered_progress
            },
            'context': {
                'variables': filtered_vars,
                'effects': {'current': filtered_effects}
            }
        },
        'options': {'stream': True}
    }
```

### 4. Generating API 收到精简 Payload

```json
// 精简后的 observation
{
  "observation": {
    "location": {
      "current": {
        "stage_id": "data_cleaning",
        "step_id": "handle_missing_values",
        "behavior_id": "behavior_003"
      },
      "progress": {
        "behaviors": {
          "focus": "【Behavior 003 详细指导】...",
          "current_outputs": {
            "expected": ["df_working", "imputation_log"]
          }
        },
        "steps": {
          "focus": "【Step 详细方案】...",
          "current_outputs": {
            "expected": ["df", "missing_fill_report"]
          }
        }
      }
    },
    "context": {
      "variables": {
        "df": "DataFrame(1460×79)",
        "missing_groups": {...}
      },
      "effects": {
        "current": [
          "车库特征缺失连带性分析：...",
          "{'high_missing': [...], ...}"
        ]
      }
    }
  }
}
```

---

## ✅ 最佳实践

### 1. 产出管理

```python
# ✅ 正确：严格管理产出状态
def complete_behavior(behavior_id, outputs):
    # 1. 验证所有 expected 都已产出
    expected = current_outputs['expected']
    produced = outputs['produced']
    assert set(expected).issubset(set(produced)), "未完成所有期望产出"

    # 2. 清空 in_progress
    current_outputs['in_progress'] = []

    # 3. 搬运 produced 到上层
    step_outputs['produced'].extend(produced)

    # 4. 升格临时变量
    if 'df_working' in produced:
        rename_and_register_artifact('df_working', f'df_imputed@{behavior_id}')
```

### 2. 临时变量管理

```python
# ✅ 正确：升格规则
def promote_temp_variable(temp_name, artifact_id):
    # 1. 重命名
    new_name = artifact_id.replace('@', '_')
    globals()[new_name] = globals()[temp_name].copy()

    # 2. 登记 artifact
    artifact = {
        'artifact_id': artifact_id,
        'variable_name': new_name,
        'description': f'Promoted from {temp_name}',
        'created_at': datetime.now().isoformat()
    }
    register_artifact(artifact)

    # 3. 清理临时变量
    del globals()[temp_name]

    # 4. 从 in_progress 移除，加入 produced
    current_outputs['in_progress'].remove(temp_name)
    current_outputs['produced'].append(new_name)
```

### 3. 错误处理

```python
# ✅ 正确：变量不存在时的处理
def filter_variables(var_list, context_vars, effects):
    filtered = {}
    for var_name in var_list:
        if var_name in context_vars:
            filtered[var_name] = context_vars[var_name]
        else:
            # 打 WARN 到 effects
            warning = f"⚠️ WARN: Variable '{var_name}' requested but not found"
            effects['current'].append(warning)

            # 记录日志
            logger.warning(f"Missing variable: {var_name}")

    return filtered
```

---

## 🔗 相关文档

- [STATE_MACHINE_PROTOCOL.md](./STATE_MACHINE_PROTOCOL.md) - 状态机协议和状态转移规则
- [API_PROTOCOL.md](./API_PROTOCOL.md) - API 交互协议
- [ACTION_PROTOCOL.md](./ACTION_PROTOCOL.md) - Action 类型和格式
- [REFACTORING_SUMMARY.md](./REFACTORING_SUMMARY.md) - 系统重构总结
