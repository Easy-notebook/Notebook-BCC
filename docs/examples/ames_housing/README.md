# Housing Example - Complete Workflow Guide

## 📖 Overview

This example demonstrates a complete workflow for building a house price prediction model using the Housing dataset. It shows the full lifecycle from IDLE state through all workflow stages, illustrating:

- **FSM State Transitions** - How states change through the workflow
- **Prompt Engineering** - What prompts are sent to Planning/Generating APIs
- **API Requests & Responses** - Complete request/response examples
- **State Evolution** - How variables and artifacts accumulate

---

## 🗂️ File Organization

```
ames_housing/
├── README.md                    # This file
├── prompt/                      # Prompts sent to APIs
│   ├── 00_START_WORKFLOW.txt   # Planning API: Generate workflow stages
│   ├── 01_START_SECTION.txt    # Planning API: Generate stage steps
│   └── 02_START_BEHAVIOUR.txt  # Planning API: Generate behavior context
│
└── payloads/                    # State files and transitions
    ├── 00_STATE_IDLE.json                           # Initial state
    ├── 00_Transition_planning_START_WORKFLOW.xml    # Planning response: stages
    ├── 01_STATE_Stage_Running.json                  # After START_WORKFLOW
    ├── 01_Transition_planning_START_STEP.xml        # Planning response: steps
    ├── 02_STATE_Step_Running.json                   # After START_STEP
    └── 02_Transition_planning_START_BEHAVIOUR.xml   # Planning response: behavior
```

---

## 🔄 Workflow State Machine

### State Flow Diagram

```
IDLE
  │
  │ Planning API (START_WORKFLOW)
  │ Prompt: 00_START_WORKFLOW.txt
  │ Response: 00_Transition_planning_START_WORKFLOW.xml
  ↓
STAGE_RUNNING (data_existence_establishment)
  │
  │ Planning API (START_STEP)
  │ Prompt: 01_START_SECTION.txt
  │ Response: 01_Transition_planning_START_STEP.xml
  ↓
STEP_RUNNING (data_collection_inventory)
  │
  │ Planning API (START_BEHAVIOUR)
  │ Prompt: 02_START_BEHAVIOUR.txt
  │ Response: 02_Transition_planning_START_BEHAVIOUR.xml
  ↓
BEHAVIOR_RUNNING
  │
  │ Generating API
  │ Response: actions (ADD_ACTION, EXEC_CODE, etc.)
  ↓
... (continues)
```

---

## 📝 State Details

### State 0: IDLE

**File:** `payloads/00_STATE_IDLE.json`

**FSM State:** `IDLE`

**Description:** Initial state before workflow starts. Contains only user inputs.

**Variables:**
```json
{
  "user_problem": "基于 Housing 数据集构建房价预测模型，RMSE < 25000，R² > 0.85，符合 PCS 标准",
  "user_submit_files": ["./assets/housing.csv"]
}
```

**What Happens Next:**
1. Client calls **Planning API** to start workflow
2. Sends prompt from `prompt/00_START_WORKFLOW.txt`
3. Planning API returns workflow stages

---

### Transition 0: START_WORKFLOW

**Prompt:** `prompt/00_START_WORKFLOW.txt`

**API Called:** Planning API (`/planning`)

**Prompt Type:** Stage Planning Request

**Prompt Content:**
- **System Prompt**: You are Stage-Planner Agent
- **User Context**:
  - user_problem: "Build house price prediction model..."
  - user_submit_files: ["./assets/housing.csv"]
  - Current variables: ["user_problem", "user_submit_files"]
- **Request**: Generate 8 DSLC stages with goals, artifacts, acceptance criteria
- **Output Format**: XML with `<stages>` containing `<stage>` elements

**Expected Response:** `payloads/00_Transition_planning_START_WORKFLOW.xml`

**Response Structure:**
```xml
<stages>
  <remaining>
    <stage id="data_existence_establishment" title="Data Existence Establishment">
      <goal>Establish and verify the existence, structure, and relevance...</goal>
      <verified_artifacts>
        <variable name="data_existence_report">...</variable>
        <variable name="data_structure_document">...</variable>
        <variable name="variable_analysis_report">...</variable>
        <variable name="pcs_hypothesis_framework">...</variable>
      </verified_artifacts>
      <required_variables>
        <variable name="user_submit_files">...</variable>
        <variable name="user_problem">...</variable>
      </required_variables>
    </stage>
    <!-- More stages: data_integrity_assurance, exploratory_data_analysis, etc. -->
  </remaining>
  <focus>Key thresholds: RMSE < 25000, R² > 0.85, CV folds ≥ 5...</focus>
  <goals>Develop robust house price prediction model following 8-stage PCS lifecycle...</goals>
</stages>
```

**State Transition:** IDLE → STAGE_RUNNING

---

### State 1: STAGE_RUNNING

**File:** `payloads/01_STATE_Stage_Running.json`

**FSM State:** `STAGE_RUNNING`

**Current Position:**
- **stage_id**: `data_existence_establishment`
- **step_id**: `null`
- **behavior_id**: `null`

**Description:** Workflow has stages defined. Ready to start first step.

**Progress:**
```json
{
  "stages": {
    "completed": [],
    "current": {
      "stage_id": "data_existence_establishment",
      "title": "Data Existence Establishment",
      "goal": "Establish and verify the existence, structure, and relevance...",
      "verified_artifacts": {...}
    },
    "remaining": [
      "data_integrity_assurance",
      "exploratory_data_analysis",
      "methodology_strategy_formulation",
      "model_implementation_execution",
      "predictability_validation",
      "stability_assessment",
      "results_communication"
    ]
  }
}
```

**What Happens Next:**
1. Client calls **Planning API** to start first step
2. Sends prompt from `prompt/01_START_SECTION.txt`
3. Planning API returns step breakdown

---

### Transition 1: START_STEP

**Prompt:** `prompt/01_START_SECTION.txt`

**API Called:** Planning API (`/planning`)

**Prompt Type:** Step Planning Request

**Prompt Content:**
- **System Prompt**: You are Step-Planner Agent
- **Current Stage Context**:
  - stage_id: data_existence_establishment
  - Goal: Establish and verify data existence
  - Expected artifacts: data_existence_report, data_structure_document, etc.
  - Required variables: user_submit_files, user_problem
- **Global Context**: user_problem, workflow goals, PCS requirements
- **Step Catalog**: Reference examples for this stage type
- **Request**: Generate 3-7 executable steps with artifacts and acceptance

**Expected Response:** `payloads/01_Transition_planning_START_STEP.xml`

**Response Structure:**
```xml
<steps>
  <step id="data_collection_inventory" title="Data Collection and Inventory">
    <goal>
      Collect and validate the housing dataset to confirm accessibility, completeness, and version traceability.
      Artifacts: data_existence_report;
      Acceptance: `os.path.exists("./assets/housing.csv")==True` and `os.path.getsize("./assets/housing.csv")>0`.
    </goal>
    <verified_artifacts>
      <variable name="data_existence_report">Comprehensive record confirming dataset presence...</variable>
    </verified_artifacts>
    <required_variables>
      <variable name="user_submit_files">Raw dataset file paths, source: user submission.</variable>
      <variable name="user_problem">Defines project scope, source: global context.</variable>
    </required_variables>
    <pcs_considerations>
      <predictability>Ensures the dataset is consistently sourced and representative...</predictability>
      <computability>Standardizes file loading path and encoding for reproducibility...</computability>
      <stability>Validates dataset integrity to prevent downstream errors...</stability>
    </pcs_considerations>
  </step>
  <!-- More steps: data_structure_discovery, variable_semantic_analysis, etc. -->
  <focus>
    Execute this stage by verifying data existence through systematic validation.
    Begin with data collection inventory to confirm file accessibility...
  </focus>
  <goals>
    Refine stage goal: To systematically verify the housing dataset's existence,
    structure, and semantic readiness for predictive modeling...
  </goals>
</steps>
```

**State Transition:** STAGE_RUNNING → STEP_RUNNING

---

### State 2: STEP_RUNNING

**File:** `payloads/02_STATE_Step_Running.json`

**FSM State:** `STEP_RUNNING`

**Current Position:**
- **stage_id**: `data_existence_establishment`
- **step_id**: `data_collection_inventory`
- **behavior_id**: `null`

**Description:** Stage has steps defined. Ready to start first behavior.

**Progress:**
```json
{
  "steps": {
    "completed": [],
    "current": {
      "step_id": "data_collection_inventory",
      "title": "Data Collection and Inventory",
      "goal": "Collect and validate the housing dataset...",
      "verified_artifacts": {
        "data_existence_report": "Comprehensive record confirming dataset presence..."
      },
      "required_variables": {
        "user_submit_files": "Raw dataset file paths...",
        "user_problem": "Defines project scope..."
      },
      "pcs_considerations": {...}
    },
    "remaining": [
      "data_structure_discovery",
      "variable_semantic_analysis",
      "variable_relevance_assessment",
      "pcs_hypothesis_generation"
    ]
  }
}
```

**What Happens Next:**
1. Client calls **Planning API** to arrange behavior
2. Sends prompt from `prompt/02_START_BEHAVIOUR.txt`
3. Planning API returns behavior context for Generating API

---

### Transition 2: START_BEHAVIOUR

**Prompt:** `prompt/02_START_BEHAVIOUR.txt`

**API Called:** Planning API (`/planning`)

**Prompt Type:** Behavior Arrangement Request

**Prompt Content:**
- **System Prompt**: You are Behavior Arrangement Agent
- **Current Stage Context**:
  - stage_id: data_existence_establishment
  - Goal and artifacts
- **Current Step Context**:
  - step_id: data_collection_inventory
  - Goal: Collect and validate dataset
  - Verified artifacts: data_existence_report
  - Required variables: user_submit_files, user_problem
  - PCS considerations
- **Current State**:
  - Variables: {user_problem, user_submit_files}
  - Effects: []
- **Available Behaviors**: List of 3 behavior options
- **Agent Selection Strategy**: Which agent to use for each task type

**Expected Response:** `payloads/02_Transition_planning_START_BEHAVIOUR.xml`

**Response Structure:**
```xml
<behavior id="data_collection_inventory_b1" step_id="data_collection_inventory">
  <agent>ExploreAgent</agent>
  <task behavior_id="data_collection_inventory_b1">
    Load the housing dataset from ./assets/housing.csv and verify its existence,
    accessibility, and basic properties. Create a data_existence_report documenting
    file metadata (size, timestamp, row count, column count).
  </task>
  <inputs>
    <variable name="user_submit_files">["./assets/housing.csv"]</variable>
    <variable name="user_problem">基于 Housing 数据集构建房价预测模型...</variable>
  </inputs>
  <effects>True</effects>
  <outputs>
    <artifact name="data_existence_report">JSON/Markdown report confirming dataset presence</artifact>
  </outputs>
  <acceptance>
    <criterion>os.path.exists("./assets/housing.csv")==True</criterion>
    <criterion>os.path.getsize("./assets/housing.csv")>0</criterion>
  </acceptance>
</behavior>
```

**State Transition:** STEP_RUNNING → BEHAVIOR_RUNNING

---

## 🎯 Prompt Analysis

### Prompt 1: Stage Planning (00_START_WORKFLOW.txt)

**Purpose:** Generate workflow stages

**Agent Role:** Stage-Planner Agent

**Key Components:**
1. **Who You Are**: Stage-Planner Agent generating stage-level plans
2. **Inputs**: user_problem, user_submit_files, dataset_hint
3. **Output Format**: XML with `<stages>` structure
4. **Key Principles**:
   - Artifact-First (concrete outputs)
   - Deterministic (stable IDs)
   - PCS-Aligned (RMSE/R²/cv_std verifiable)
   - No Hallucination (follow inputs only)

**User Context:**
- Problem: "Build house price prediction model, RMSE < 25000, R² > 0.85"
- Files: ["./assets/housing.csv"]
- Current variables: ["user_problem", "user_submit_files"]

**DSLC Stage Reference:** 8 stages provided as reference
1. Data Existence Establishment
2. Data Integrity Assurance
3. Exploratory Data Analysis
4. Methodology Strategy Formulation
5. Model Implementation Execution
6. Predictability Validation
7. Stability Assessment
8. Results Communication

**Expected Output:** XML with 8 stages, each having:
- `id`, `title`, `goal`
- `<verified_artifacts>` - outputs to produce
- `<required_variables>` - inputs needed
- `<focus>` - guidance with thresholds
- `<goals>` - overall workflow objectives

---

### Prompt 2: Step Planning (01_START_SECTION.txt)

**Purpose:** Generate step breakdown for current stage

**Agent Role:** Step-Planner Agent

**Key Components:**
1. **Who You Are**: Step-Planner generating step-level execution plans
2. **Inputs**: Current stage context, global workflow context, step catalog
3. **Output Format**: XML with `<steps>` structure
4. **Key Principles**: Same as stage planning + PCS considerations required

**Current Stage Context:**
- stage_id: data_existence_establishment
- Goal: Establish and verify data existence
- Expected artifacts: 4 artifacts
- Required variables: user_submit_files, user_problem

**Step Catalog Reference:** Detailed breakdown for this stage type:
- Data Collection and Inventory
- Data Structure Discovery
- Variable Semantic Analysis
- Observation Unit Identification
- Variable Relevance Assessment
- PCS Hypothesis Generation

**Expected Output:** XML with 3-7 steps, each having:
- `id`, `title`, `goal` (with acceptance)
- `<verified_artifacts>` - outputs to produce
- `<required_variables>` - inputs needed (with source)
- `<pcs_considerations>` - predictability/computability/stability
- `<focus>` - detailed execution guidance
- `<goals>` - refined stage goals

---

### Prompt 3: Behavior Arrangement (02_START_BEHAVIOUR.txt)

**Purpose:** Select agent and assemble execution context

**Agent Role:** Behavior Arrangement Agent

**Key Components:**
1. **Who You Are**: Behavior Arrangement Agent selecting appropriate agent
2. **Inputs**: Stage context, step context, current state, behavior options
3. **Output Format**: XML with `<behavior>` structure
4. **Key Rules**: Use actual values from state.variables

**Current Step Context:**
- step_id: data_collection_inventory
- Goal: Collect and validate housing dataset
- Verified artifacts: data_existence_report
- Required variables: user_submit_files, user_problem
- PCS considerations provided

**Current State:**
```json
{
  "variables": {
    "user_problem": "基于 Housing 数据集构建房价预测模型...",
    "user_submit_files": ["./assets/housing.csv"]
  },
  "effects": []
}
```

**Behavior Options:** 3 behaviors to choose from:
1. behavior_1_data_collection_strategy → Define Agent
2. behavior_2_initial_inventory_and_access_check → Explore Agent
3. behavior_3_validation_and_acceptance → Define Agent

**Agent Selection Strategy:** Examples of which agent for which task

**Expected Output:** XML with one `<behavior>`:
- `id`, `step_id`
- `<agent>` - which agent to use
- `<task>` - specific instructions with file paths/variables
- `<inputs>` - actual values from state
- `<effects>` - whether to track execution effects
- `<outputs>` - artifacts to produce
- `<acceptance>` - verifiable criteria
- `<whathappened>` - optional context if needed

---

## 🔬 API Request Flow

### Request 1: Planning API (IDLE → STAGE_RUNNING)

**Endpoint:** `POST /planning`

**Request Body:**
```json
{
  "observation": {
    "location": {
      "current": {
        "stage_id": null,
        "step_id": null,
        "behavior_id": null,
        "behavior_iteration": null
      },
      "progress": {
        "stages": {"completed": [], "current": null, "remaining": []},
        "steps": {"completed": [], "current": null, "remaining": []},
        "behaviors": {"completed": [], "current": null, "iteration": null}
      },
      "goals": "用户提出了问题%user_problem%，上传了文件%user_submit_files%。\n请你立即开始规划工作流..."
    },
    "context": {
      "variables": {
        "user_problem": "基于 Housing 数据集构建房价预测模型...",
        "user_submit_files": ["./assets/housing.csv"]
      },
      "effects": {"current": [], "history": []},
      "notebook": {...},
      "FSM": {"state": "IDLE", "last_transition": null}
    }
  },
  "options": {"stream": false}
}
```

**System Prompt Injected:** Content from `prompt/00_START_WORKFLOW.txt`

**Response:**
```xml
<stages>
  <remaining>
    <stage id="data_existence_establishment" title="...">...</stage>
    <stage id="data_integrity_assurance" title="...">...</stage>
    <!-- 6 more stages -->
  </remaining>
  <focus>RMSE < 25000; R² > 0.85; CV folds ≥ 5...</focus>
  <goals>Develop robust house price prediction model...</goals>
</stages>
```

**Client Action:** Parse XML, update state, transition to STAGE_RUNNING

---

### Request 2: Planning API (STAGE_RUNNING → STEP_RUNNING)

**Endpoint:** `POST /planning`

**Request Body:**
```json
{
  "observation": {
    "location": {
      "current": {
        "stage_id": "data_existence_establishment",
        "step_id": null,
        "behavior_id": null
      },
      "progress": {
        "stages": {
          "completed": [],
          "current": {
            "stage_id": "data_existence_establishment",
            "title": "Data Existence Establishment",
            "goal": "Establish and verify...",
            "verified_artifacts": {...}
          },
          "remaining": [...]
        }
      },
      "goals": "Refine stage goal: To systematically verify..."
    },
    "context": {
      "variables": {
        "user_problem": "...",
        "user_submit_files": ["./assets/housing.csv"]
      },
      "FSM": {"state": "STAGE_RUNNING", "last_transition": "START_WORKFLOW"}
    }
  }
}
```

**System Prompt Injected:** Content from `prompt/01_START_SECTION.txt`

**Response:**
```xml
<steps>
  <step id="data_collection_inventory" title="...">
    <goal>...</goal>
    <verified_artifacts>...</verified_artifacts>
    <required_variables>...</required_variables>
    <pcs_considerations>...</pcs_considerations>
  </step>
  <!-- More steps -->
  <focus>Execute this stage by verifying data existence...</focus>
  <goals>Refined stage goal...</goals>
</steps>
```

**Client Action:** Parse XML, update state, transition to STEP_RUNNING

---

### Request 3: Planning API (STEP_RUNNING → BEHAVIOR_RUNNING)

**Endpoint:** `POST /planning`

**Request Body:**
```json
{
  "observation": {
    "location": {
      "current": {
        "stage_id": "data_existence_establishment",
        "step_id": "data_collection_inventory",
        "behavior_id": null
      },
      "progress": {
        "steps": {
          "current": {
            "step_id": "data_collection_inventory",
            "goal": "...",
            "verified_artifacts": {...},
            "required_variables": {...}
          }
        }
      }
    },
    "context": {
      "variables": {...},
      "effects": {"current": [], "history": []},
      "FSM": {"state": "STEP_RUNNING", "last_transition": "START_STEP"}
    }
  }
}
```

**System Prompt Injected:** Content from `prompt/02_START_BEHAVIOUR.txt`

**Response:**
```xml
<behavior id="data_collection_inventory_b1" step_id="data_collection_inventory">
  <agent>ExploreAgent</agent>
  <task behavior_id="...">Load the housing dataset from ./assets/housing.csv...</task>
  <inputs>...</inputs>
  <effects>True</effects>
  <outputs>...</outputs>
  <acceptance>...</acceptance>
</behavior>
```

**Client Action:** Parse XML, prepare for Generating API call

---

### Request 4: Generating API (BEHAVIOR_RUNNING → ACTION_RUNNING)

**Endpoint:** `POST /generating`

**Request Body:**
```json
{
  "observation": {
    "location": {
      "current": {
        "stage_id": "data_existence_establishment",
        "step_id": "data_collection_inventory",
        "behavior_id": "data_collection_inventory_b1",
        "behavior_iteration": 1
      },
      "progress": {...},
      "goals": "Load the housing dataset from ./assets/housing.csv and verify..."
    },
    "context": {
      "variables": {
        "user_problem": "...",
        "user_submit_files": ["./assets/housing.csv"]
      },
      "effects": {"current": [], "history": []},
      "FSM": {"state": "BEHAVIOR_RUNNING"}
    }
  },
  "options": {"stream": true}
}
```

**Response (streaming):**
```json
[
  {
    "action": "add",
    "shot_type": "one-shot",
    "shot_sequence": 1,
    "type": "markdown",
    "content": "# Data Collection and Inventory\n\nLoading housing dataset..."
  },
  {
    "action": "exec",
    "shot_type": "one-shot",
    "shot_sequence": 2,
    "language": "python",
    "code": "import pandas as pd\nimport os\n\nfile_path = './assets/housing.csv'\ndf_raw = pd.read_csv(file_path)"
  },
  {
    "action": "exec",
    "shot_type": "one-shot",
    "shot_sequence": 3,
    "language": "python",
    "code": "# Create data existence report\ndata_existence_report = {\n  'file_path': file_path,\n  'exists': os.path.exists(file_path),\n  'size_bytes': os.path.getsize(file_path),\n  'row_count': len(df_raw),\n  'column_count': len(df_raw.columns)\n}\nprint(data_existence_report)"
  }
]
```

**Client Action:** Execute actions, update notebook, track effects

---

## 📊 State Evolution

### Variables Accumulation

| State | Variables Count | New Variables |
|-------|----------------|---------------|
| **IDLE** | 2 | user_problem, user_submit_files |
| **STAGE_RUNNING** | 2 | (no new variables) |
| **STEP_RUNNING** | 2 | (no new variables) |
| **BEHAVIOR_RUNNING** | 2 | (no new variables) |
| **After EXEC actions** | 4+ | df_raw, data_existence_report, ... |

### Artifacts Production

| Stage | Step | Expected Artifact | Status |
|-------|------|-------------------|--------|
| data_existence_establishment | data_collection_inventory | data_existence_report | in_progress |
| data_existence_establishment | data_structure_discovery | data_structure_document | expected |
| data_existence_establishment | variable_semantic_analysis | variable_analysis_report | expected |
| data_existence_establishment | pcs_hypothesis_generation | pcs_hypothesis_framework | expected |

---

## 🧪 Testing the Workflow

### Test 1: Preview Requests

```bash
# Preview IDLE → STAGE_RUNNING
python main.py test-request \
  --state-file ./docs/examples/ames_housing/payloads/00_STATE_IDLE.json

# Preview STAGE_RUNNING → STEP_RUNNING
python main.py test-request \
  --state-file ./docs/examples/ames_housing/payloads/01_STATE_Stage_Running.json

# Preview STEP_RUNNING → BEHAVIOR_RUNNING
python main.py test-request \
  --state-file ./docs/examples/ames_housing/payloads/02_STATE_Step_Running.json
```

### Test 2: Apply Transitions Offline

```bash
# Apply START_WORKFLOW transition
python main.py apply-transition \
  --state-file ./docs/examples/ames_housing/payloads/00_STATE_IDLE.json \
  --transition-file ./docs/examples/ames_housing/payloads/00_Transition_planning_START_WORKFLOW.xml \
  --output ./test/01_STATE_Stage_Running.json

# Apply START_STEP transition
python main.py apply-transition \
  --state-file ./docs/examples/ames_housing/payloads/01_STATE_Stage_Running.json \
  --transition-file ./docs/examples/ames_housing/payloads/01_Transition_planning_START_STEP.xml \
  --output ./test/02_STATE_Step_Running.json

# Apply START_BEHAVIOUR transition
python main.py apply-transition \
  --state-file ./docs/examples/ames_housing/payloads/02_STATE_Step_Running.json \
  --transition-file ./docs/examples/ames_housing/payloads/02_Transition_planning_START_BEHAVIOUR.xml \
  --output ./test/03_STATE_Behavior_Running.json
```

### Test 3: Send Actual Requests (requires server)

```bash
# Send from IDLE (will call Planning API)
python main.py send-api \
  --state-file ./docs/examples/ames_housing/payloads/00_STATE_IDLE.json

# Send from STAGE_RUNNING
python main.py send-api \
  --state-file ./docs/examples/ames_housing/payloads/01_STATE_Stage_Running.json

# Send from STEP_RUNNING
python main.py send-api \
  --state-file ./docs/examples/ames_housing/payloads/02_STATE_Step_Running.json
```

---

## 📚 Key Learnings

### 1. Prompt Structure

Each prompt has consistent structure:
- **[SYSTEM PROMPT]** - Define agent role and output format
- **[USER PROMPT]** - Provide current context and requirements
- **Output Format** - Strict XML schema
- **Key Principles** - Artifact-First, Deterministic, PCS-Aligned, No Hallucination

### 2. State Transitions

State transitions follow Planning First protocol:
- **IDLE** → Planning API generates workflow stages
- **STAGE_RUNNING** → Planning API generates step breakdown
- **STEP_RUNNING** → Planning API arranges behavior context
- **BEHAVIOR_RUNNING** → Generating API produces actions

### 3. Context Accumulation

Each transition adds more context:
- **Stages** added in IDLE → STAGE_RUNNING
- **Steps** added in STAGE_RUNNING → STEP_RUNNING
- **Behavior** added in STEP_RUNNING → BEHAVIOR_RUNNING
- **Variables** added after action execution

### 4. PCS Framework Integration

Every level considers:
- **Predictability** - Generalization capability
- **Computability** - Reproducibility measures
- **Stability** - Robustness checks

---

## 🔗 Related Documentation

- [State Machine Protocol](../../protocols/STATE_MACHINE.md) - FSM states and transitions
- [Observation Protocol](../../protocols/OBSERVATION.md) - State file structure
- [API Protocol](../../protocols/API.md) - Planning/Generating API specs
- [CLI Usage Guide](../../guides/CLI_USAGE.md) - Commands for testing

---

**Last Updated:** 2025-11-08
