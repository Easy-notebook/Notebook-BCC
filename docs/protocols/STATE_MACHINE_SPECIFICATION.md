# State Machine Specification

## Overview

This document describes the complete Finite State Machine (FSM) that drives the Notebook-BCC workflow execution. The FSM orchestrates the progression through Stages → Steps → Behaviors, ensuring proper sequencing, validation, and artifact production.

---

## State Definitions

### 1. IDLE
**Description**: Initial state before workflow starts
**Entry Condition**: System initialization
**Exit Transition**: `START_WORKFLOW`
**Characteristics**:
- No active stage/step/behavior
- Variables contain only user inputs: `user_problem`, `user_submit_files`
- Notebook is empty (cell_count = 0)

### 2. STAGE_RUNNING
**Description**: A stage has been planned and is active
**Entry Condition**: Workflow planning completed or previous stage completed
**Exit Transition**: `START_STEP`
**Characteristics**:
- Current stage is set with goals and expected artifacts
- Steps list is populated (completed, current, remaining)
- Stage-level focus and outputs tracking initialized

### 3. STEP_RUNNING
**Description**: A step within the current stage is active
**Entry Condition**: Stage initiated or previous step completed
**Exit Transition**: `START_BEHAVIOR`
**Characteristics**:
- Current step is set with specific goals and acceptance criteria
- Behaviors queue is prepared
- Step-level artifacts and PCS considerations defined

### 4. BEHAVIOR_RUNNING
**Description**: A behavior (atomic action) is executing
**Entry Condition**: Step initiated or previous behavior completed
**Exit Transition**: `COMPLETE_ACTION`
**Characteristics**:
- Specific agent assigned to execute task
- Input variables are bound
- Expected outputs clearly defined
- Notebook cells are being created/executed

### 5. BEHAVIOR_COMPLETED
**Description**: Behavior execution finished, awaiting reflection
**Entry Condition**: Actions completed successfully
**Exit Transition**: `TRANSITION_TO_COMPLETE_STEP` or `START_BEHAVIOR` (retry)
**Characteristics**:
- Artifacts produced and stored in variables
- Effects captured in `effects.current`
- Acceptance criteria validation pending

### 6. STEP_COMPLETED
**Description**: All behaviors in step finished, awaiting stage reflection
**Entry Condition**: Behavior reflection confirms step completion
**Exit Transition**: `COMPLETE_STAGE` or `START_STEP` (next step)
**Characteristics**:
- All step artifacts produced
- Variables updated with new artifacts
- Ready for stage-level decision

---

## State Transition Graph

```
IDLE
  └─[START_WORKFLOW]──> STAGE_RUNNING
                            └─[START_STEP]──> STEP_RUNNING
                                                 └─[START_BEHAVIOR]──> BEHAVIOR_RUNNING
                                                                          └─[COMPLETE_ACTION]──> BEHAVIOR_COMPLETED
                                                                                                    ├─[TRANSITION_TO_COMPLETE_STEP]──> STEP_COMPLETED
                                                                                                    │                                      ├─[START_STEP]──> STEP_RUNNING (next step)
                                                                                                    │                                      └─[COMPLETE_STAGE]──> STAGE_RUNNING (next stage)
                                                                                                    └─[START_BEHAVIOR]──> BEHAVIOR_RUNNING (retry/next)
```

---

## Transitions

### T1: START_WORKFLOW (IDLE → STAGE_RUNNING)
**Trigger**: User submits problem and files
**Agent**: Stage-Planner Agent
**Input**:
- `user_problem`: Problem description
- `user_submit_files`: Uploaded file paths
**Output**: XML with stages breakdown
**Process**:
1. Parse user requirements
2. Decompose into 6-8 stages following DSLC framework
3. Define stage goals, artifacts, acceptance criteria
4. Establish stage dependencies via `required_variables`
**Transition Payload**: `00_Transition_planning_START_WORKFLOW.xml`

**Key Elements**:
```xml
<stages>
  <remaining>
    <stage id="stage_id" title="Stage Title">
      <goal>Goal with Artifacts and Acceptance</goal>
      <verified_artifacts>...</verified_artifacts>
      <required_variables>...</required_variables>
    </stage>
  </remaining>
  <focus>Key thresholds (RMSE, R², PCS)</focus>
</stages>
```

---

### T2: START_STEP (STAGE_RUNNING → STEP_RUNNING)
**Trigger**: Stage becomes active or previous step completes
**Agent**: Step-Planner Agent
**Input**:
- Current stage context
- Stage goals and artifacts
**Output**: XML with steps breakdown for current stage
**Process**:
1. Decompose stage into 3-7 executable steps
2. Define step goals, artifacts, acceptance criteria
3. Specify required input variables from previous steps
4. Add PCS considerations for each step
**Transition Payload**: `01_Transition_planning_START_STEP.xml`

**Key Elements**:
```xml
<steps>
  <step id="step_id" title="Step Title">
    <goal>Goal with Artifacts and Acceptance</goal>
    <verified_artifacts>...</verified_artifacts>
    <required_variables>...</required_variables>
    <pcs_considerations>
      <predictability>...</predictability>
      <computability>...</computability>
      <stability>...</stability>
    </pcs_considerations>
  </step>
  <focus>Detailed execution guidance</focus>
  <goals>Updated stage goals if needed</goals>
</steps>
```

---

### T3: START_BEHAVIOR (STEP_RUNNING → BEHAVIOR_RUNNING)
**Trigger**: Step becomes active or previous behavior completes
**Agent**: Behavior Arrangement Agent
**Input**:
- Current step context
- Available variables in state
**Output**: XML specifying agent and task
**Process**:
1. Select appropriate agent (Explore, Define, Validate, etc.)
2. Assemble task description with specific instructions
3. Bind input variables with actual values
4. Define expected outputs matching step's verified_artifacts
5. Set programmatic acceptance criteria
**Transition Payload**: `02_Transition_planning_START_BEHAVIOUR.xml`

**Key Elements**:
```xml
<behavior id="step_id_b1" step_id="step_id">
  <agent>AgentName</agent>
  <task behavior_id="behavior_id">Specific instructions</task>
  <inputs>
    <variable name="name">actual_value</variable>
  </inputs>
  <effects>True/False</effects>
  <outputs>
    <artifact name="name">description</artifact>
  </outputs>
  <acceptance>
    <criterion>condition</criterion>
  </acceptance>
</behavior>
```

---

### T4: COMPLETE_ACTION (BEHAVIOR_RUNNING → BEHAVIOR_COMPLETED)
**Trigger**: Action-Generator produces actions and they execute
**Agent**: Action-Generator Agent
**Input**:
- Behavior context
- Current notebook state
- Execution results (effects.current)
**Output**: XML with executable actions
**Process**:
1. Generate markdown text for explanations
2. Generate Python code for execution
3. Create variables matching verified_artifacts
4. Update notebook titles/sections
5. Optionally communicate with other agents
**Prompt**: `03_START_ACTION.txt`

**Key Elements**:
```xml
<actions>
  <update-project-title>Title</update-project-title>
  <update-section-title>Section</update-section-title>
  <add-text>Markdown explanation</add-text>
  <add-code2run>Python code</add-code2run>
  <communication to="agent_name">Message</communication>
</actions>
```

---

### T5: TRANSITION_TO_COMPLETE_STEP (BEHAVIOR_COMPLETED → STEP_COMPLETED)
**Trigger**: Behavior reflection confirms step completion
**Agent**: Behavior Reflection Agent
**Input**:
- Behavior execution results
- Variables produced
- Acceptance criteria
**Output**: XML reflection
**Process**:
1. Evaluate artifacts produced (complete/incomplete/missing)
2. Validate acceptance criteria (passed/failed)
3. Assess execution quality (errors, warnings)
4. Determine goal achievement status
5. Decide next state (continue behavior or complete step)
6. Update outputs tracking
**Transition Payload**: `04_Transition_Complete_Step.xml`

**Key Elements**:
```xml
<reflection current_step_is_complete="true|false">
  <evaluation>
    <artifacts_produced>...</artifacts_produced>
    <acceptance_validation>...</acceptance_validation>
    <execution_quality>...</execution_quality>
    <goal_achievement>...</goal_achievement>
  </evaluation>
  <decision>
    <next_state>STEP_RUNNING|STEP_COMPLETED</next_state>
    <reasoning>...</reasoning>
  </decision>
  <context_for_next>...</context_for_next>
  <outputs_tracking_update>...</outputs_tracking_update>
</reflection>
```

---

### T6: COMPLETE_STAGE (STEP_COMPLETED → STAGE_RUNNING or WORKFLOW_COMPLETE)
**Trigger**: Step reflection confirms stage may be complete
**Agent**: Stage Reflection Agent
**Input**:
- Completed step results
- Stage progress (completed/remaining steps)
- Stage artifacts status
**Output**: XML stage reflection
**Process**:
1. Evaluate step completion
2. Assess stage progress (percentage, artifacts status)
3. Review stage goal (needs update?)
4. Manage variables (extract, retain, deprecate)
5. Decide: continue stage (START_STEP) or complete stage (move to next)
6. Summarize experience (only if stage complete)
**Transition Payload**: `05_Transition_Complete_Stage.xml`
**Prompt**: `05_COMPELETE_STAGE_OPTIMIZED.txt`

**Key Elements**:
```xml
<stage_reflection stage_is_complete="true|false">
  <step_evaluation>...</step_evaluation>
  <stage_assessment>
    <progress>...</progress>
    <stage_artifacts_status>...</stage_artifacts_status>
    <goal_status>achieved|partial|not_achieved</goal_status>
  </stage_assessment>
  <!-- Conditional: only if progress >50% OR issues -->
  <stage_goal_review needs_update="true|false">...</stage_goal_review>
  <!-- Conditional: only if stage_is_complete=true -->
  <stage_experience from="stage_id">...</stage_experience>
  <decision>
    <next_state>STAGE_COMPLETED|STEP_RUNNING</next_state>
    <next_focus>...</next_focus>
    <reasoning>...</reasoning>
  </decision>
  <variable_management>
    <extracted_from_notebook>...</extracted_from_notebook>
    <retain>...</retain>
    <deprecate>...</deprecate>
    <gaps>...</gaps>
  </variable_management>
  <outputs_update>...</outputs_update>
  <pcs_check>...</pcs_check>
</stage_reflection>
```

---

## State Variables Schema

### observation.location.current
- `stage_id`: Current stage identifier
- `step_id`: Current step identifier
- `behavior_id`: Current behavior identifier
- `behavior_iteration`: Retry count for current behavior

### observation.location.progress
**stages**:
- `completed`: Array of completed stages
- `current`: Current stage object
- `remaining`: Array of remaining stages
- `focus`: Key objectives and thresholds
- `current_outputs`: expected/produced/in_progress artifacts

**steps**:
- `completed`: Array of completed steps
- `current`: Current step object
- `remaining`: Array of remaining steps
- `focus`: Execution guidance
- `current_outputs`: expected/produced/in_progress artifacts

**behaviors**:
- `completed`: Array of completed behaviors
- `current`: Current behavior object
- `iteration`: Current iteration number
- `focus`: Task description
- `current_outputs`: expected/produced/in_progress artifacts

### state.variables
Key-value store for all artifacts and intermediate variables produced during workflow execution.

### state.effects
- `current`: Array of recent execution outputs
- `history`: Archive of all previous effects

### state.notebook
- `notebook_id`: Unique notebook identifier
- `title`: Notebook title
- `cell_count`: Number of cells
- `last_cell_type`: Type of last cell (code/markdown)
- `last_output`: Output from last executed cell

### state.FSM
- `state`: Current FSM state name
- `last_transition`: Name of last transition
- `timestamp`: ISO 8601 timestamp of last update

---

## Workflow Execution Example

### Initial State (IDLE)
```json
{
  "observation": {
    "location": {
      "current": {"stage_id": null, "step_id": null, "behavior_id": null}
    }
  },
  "state": {
    "variables": {
      "user_problem": "Build house price model, RMSE < 25000, R² > 0.85",
      "user_submit_files": ["./assets/housing.csv"]
    },
    "FSM": {"state": "IDLE"}
  }
}
```

### After START_WORKFLOW (STAGE_RUNNING)
```json
{
  "observation": {
    "location": {
      "current": {"stage_id": "data_existence_establishment", "step_id": null}
    },
    "progress": {
      "stages": {
        "completed": [],
        "current": {"stage_id": "data_existence_establishment", "title": "Data Existence Establishment", "goal": "..."},
        "remaining": [/* 5 more stages */]
      }
    }
  },
  "state": {
    "FSM": {"state": "STAGE_RUNNING", "last_transition": "START_WORKFLOW"}
  }
}
```

### After START_STEP (STEP_RUNNING)
```json
{
  "observation": {
    "location": {
      "current": {
        "stage_id": "data_existence_establishment",
        "step_id": "data_collection_inventory"
      }
    },
    "progress": {
      "steps": {
        "completed": [],
        "current": {"step_id": "data_collection_inventory", "title": "Data Collection and Initial Inventory", "goal": "..."},
        "remaining": [/* 4 more steps */]
      }
    }
  },
  "state": {
    "FSM": {"state": "STEP_RUNNING", "last_transition": "START_STEP"}
  }
}
```

### After START_BEHAVIOR (BEHAVIOR_RUNNING)
```json
{
  "observation": {
    "location": {
      "current": {
        "stage_id": "data_existence_establishment",
        "step_id": "data_collection_inventory",
        "behavior_id": "data_collection_inventory_b1",
        "behavior_iteration": 1
      }
    },
    "progress": {
      "behaviors": {
        "completed": [],
        "current": {
          "behavior_id": "data_collection_inventory_b1",
          "agent": "behavior_2_initial_inventory_and_access_check",
          "task": "Perform initial inventory..."
        }
      }
    }
  },
  "state": {
    "FSM": {"state": "BEHAVIOR_RUNNING", "last_transition": "START_BEHAVIOR"}
  }
}
```

### After COMPLETE_ACTION (BEHAVIOR_COMPLETED)
```json
{
  "state": {
    "variables": {
      "user_problem": "...",
      "user_submit_files": ["./assets/housing.csv"],
      "raw_dataset": "housing dataframe",
      "data_inventory_checklist": "Inventory report for ./assets/housing.csv"
    },
    "effects": {
      "current": ["数据集成功加载！数据形状：(2930, 82)\n"]
    },
    "notebook": {
      "cell_count": 2,
      "last_output": "数据集成功加载！数据形状：(2930, 82)\n"
    },
    "FSM": {"state": "BEHAVIOR_COMPLETED", "last_transition": "COMPLETE_ACTION"}
  }
}
```

### After TRANSITION_TO_COMPLETE_STEP (STEP_COMPLETED)
```json
{
  "observation": {
    "progress": {
      "behaviors": {
        "completed": [{
          "behavior_id": "data_collection_inventory_b1",
          "completion_status": "success",
          "artifacts_produced": ["data_inventory_checklist", "raw_dataset"]
        }]
      }
    }
  },
  "state": {
    "FSM": {"state": "STEP_COMPLETED", "last_transition": "TRANSITION_TO_COMPELETE_STEP"}
  }
}
```

---

## Design Principles

### 1. Artifact-First
Every state transition must produce concrete, verifiable artifacts with programmatic acceptance criteria.

### 2. Deterministic
State transitions follow a fixed sequence. No random or conditional branching beyond defined FSM rules.

### 3. PCS-Aligned
Every step and behavior must explicitly address:
- **Predictability**: Generalization capability
- **Computability**: Reproducibility with seeds/versioning
- **Stability**: Robustness to data perturbations

### 4. No Hallucination
Agents only use variables from `state.variables`. No fabricated data or undefined references.

### 5. Continuity-Aware
Each agent reads complete notebook context to avoid duplication and maintain consistency.

### 6. Conditional Complexity
Output structure adapts to progress level:
- **Early (0-50%)**: Focus on progress tracking
- **Mid (50-80%)**: Add goal review if needed
- **Late (80-100%)**: Full evaluation with experience summary

---

## Error Handling

### Behavior Retry
If `behavior_iteration` < max_retries and artifacts incomplete:
- Decision: `STEP_RUNNING` (same behavior, increment iteration)
- Provide feedback in context_for_next

### Step Failure
If acceptance criteria consistently fail:
- Escalate to stage reflection
- Consider stage goal revision

### Variable Dependency Missing
If required variables unavailable:
- Identify gaps in `variable_management.gaps`
- Suggest resolution strategy
- May require backtracking to previous step/stage

---

## Metrics and Monitoring

### Progress Tracking
- **Stage Progress**: `completed_steps / total_steps`
- **Overall Progress**: `completed_stages / total_stages`
- **Artifact Completion**: `produced_artifacts / expected_artifacts`

### Quality Indicators
- **Acceptance Pass Rate**: Ratio of passed criteria to total criteria
- **Retry Rate**: Average behavior iterations per step
- **Variable Coverage**: Ratio of produced to required variables

### PCS Compliance
- **Predictability**: Test set exists, no data leakage detected
- **Computability**: All code includes seeds, versions documented
- **Stability**: Variation coefficient < threshold

---

## Related Documents
- [API Requirements](./API_REQUIREMENTS.md) - API specification for FSM operations
- [Prompt Design Patterns](./PROMPT_DESIGN_PATTERNS.md) - Prompt engineering guidelines
- [Stage Catalog](./STAGE_CATALOG.md) - DSLC stage definitions
