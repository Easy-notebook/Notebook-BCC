# State Transition Quick Reference

## Visual State Machine

```
┌─────────────────────────────────────────────────────────────────┐
│                     Notebook-BCC State Machine                   │
└─────────────────────────────────────────────────────────────────┘

    IDLE                          User submits problem + files
     │
     │ [T1: START_WORKFLOW]       Agent: Stage-Planner
     │                            Output: stages.xml
     ↓
    STAGE_RUNNING                 Current stage activated
     │
     │ [T2: START_STEP]           Agent: Step-Planner
     │                            Output: steps.xml
     ↓
    STEP_RUNNING                  Current step activated
     │
     │ [T3: START_BEHAVIOR]       Agent: Behavior Arrangement
     │                            Output: behavior.xml
     ↓
    BEHAVIOR_RUNNING              Agent executes task
     │
     │ [T4: COMPLETE_ACTION]      Agent: Action-Generator
     │                            Output: actions.xml
     ↓
    BEHAVIOR_COMPLETED             Artifacts created, results captured
     │
     │ [T5: COMPLETE_STEP]        Agent: Behavior Reflection
     │ (reflection decision)       Output: reflection.xml
     │
     ├──[if incomplete]──┐
     │                   ↓
     │              BEHAVIOR_RUNNING (retry)
     │
     └──[if complete]───→ STEP_COMPLETED
                           │
                           │ [T6: COMPLETE_STAGE]   Agent: Stage Reflection
                           │ (reflection decision)    Output: stage_reflection.xml
                           │
                           ├──[if stage incomplete]──→ STEP_RUNNING (next step)
                           │
                           └──[if stage complete]────→ STAGE_RUNNING (next stage)
                                                         │
                                                         └──[if all stages done]──→ WORKFLOW_COMPLETE
```

---

## Transition Summary Table

| Transition | From State | To State | Agent | Prompt File | Key Output |
|------------|-----------|----------|-------|-------------|------------|
| T1: START_WORKFLOW | IDLE | STAGE_RUNNING | Stage-Planner | `00_START_WORKFLOW.txt` | stages.xml |
| T2: START_STEP | STAGE_RUNNING | STEP_RUNNING | Step-Planner | `01_START_SECTION.txt` | steps.xml |
| T3: START_BEHAVIOR | STEP_RUNNING | BEHAVIOR_RUNNING | Behavior Arrangement | `02_START_BEHAVIOUR.txt` | behavior.xml |
| T4: COMPLETE_ACTION | BEHAVIOR_RUNNING | BEHAVIOR_COMPLETED | Action-Generator | `03_START_ACTION.txt` | actions.xml |
| T5: COMPLETE_STEP | BEHAVIOR_COMPLETED | STEP_COMPLETED | Behavior Reflection | `04_COMPLETE_STEP.txt` | reflection.xml |
| T6: COMPLETE_STAGE | STEP_COMPLETED | STAGE_RUNNING or WORKFLOW_COMPLETE | Stage Reflection | `05_COMPELETE_STAGE_OPTIMIZED.txt` | stage_reflection.xml |

---

## State Characteristics Cheat Sheet

### IDLE
```json
{
  "FSM.state": "IDLE",
  "location.current": {"stage_id": null, "step_id": null, "behavior_id": null},
  "variables": {"user_problem": "...", "user_submit_files": [...]},
  "notebook.cell_count": 0
}
```
**Next Action**: Call START_WORKFLOW transition

---

### STAGE_RUNNING
```json
{
  "FSM.state": "STAGE_RUNNING",
  "location.current": {"stage_id": "data_existence_establishment", "step_id": null},
  "progress.stages.current": {
    "stage_id": "...",
    "title": "...",
    "goal": "...",
    "verified_artifacts": {...}
  },
  "progress.stages.remaining": [...]
}
```
**Next Action**: Call START_STEP transition

---

### STEP_RUNNING
```json
{
  "FSM.state": "STEP_RUNNING",
  "location.current": {"stage_id": "...", "step_id": "data_collection_inventory"},
  "progress.steps.current": {
    "step_id": "...",
    "title": "...",
    "goal": "...",
    "verified_artifacts": {...},
    "pcs_considerations": {...}
  },
  "progress.steps.remaining": [...]
}
```
**Next Action**: Call START_BEHAVIOR transition

---

### BEHAVIOR_RUNNING
```json
{
  "FSM.state": "BEHAVIOR_RUNNING",
  "location.current": {
    "stage_id": "...",
    "step_id": "...",
    "behavior_id": "data_collection_inventory_b1",
    "behavior_iteration": 1
  },
  "progress.behaviors.current": {
    "behavior_id": "...",
    "agent": "Explore-Agent",
    "task": "...",
    "inputs": {...},
    "outputs": {...}
  }
}
```
**Next Action**: Execute actions from Action-Generator

---

### BEHAVIOR_COMPLETED
```json
{
  "FSM.state": "BEHAVIOR_COMPLETED",
  "variables": {
    "user_problem": "...",
    "raw_dataset": "housing dataframe",  // ← New artifact
    "data_inventory_checklist": "..."    // ← New artifact
  },
  "effects.current": ["数据集成功加载！数据形状：(2930, 82)\n"],
  "notebook.cell_count": 2
}
```
**Next Action**: Call COMPLETE_STEP transition (reflection)

---

### STEP_COMPLETED
```json
{
  "FSM.state": "STEP_COMPLETED",
  "progress.behaviors.completed": [{
    "behavior_id": "data_collection_inventory_b1",
    "completion_status": "success",
    "artifacts_produced": ["data_inventory_checklist", "raw_dataset"]
  }],
  "progress.steps.current": null
}
```
**Next Action**: Call COMPLETE_STAGE transition (reflection)

---

## Transition Inputs/Outputs Quick Reference

### T1: START_WORKFLOW
**Inputs**:
- `user_problem`: String
- `user_submit_files`: Array of file paths

**Outputs**:
- `stages.remaining`: Array of stage objects
- `stages.focus`: Key objectives and thresholds
- `stages.current`: First stage activated

**Example Payload**: `00_Transition_planning_START_WORKFLOW.xml`
```xml
<stages>
  <remaining>
    <stage id="data_existence_establishment" title="...">
      <goal>Objective. Artifacts: X, Y; Acceptance: condition.</goal>
      <verified_artifacts>...</verified_artifacts>
      <required_variables>...</required_variables>
    </stage>
    <!-- More stages -->
  </remaining>
  <focus>RMSE < 25000, R² > 0.85, PCS compliance</focus>
</stages>
```

---

### T2: START_STEP
**Inputs**:
- `current_stage`: Stage object with goal, artifacts
- `global_context`: User problem, completed/remaining stages

**Outputs**:
- `steps.remaining`: Array of step objects for current stage
- `steps.focus`: Execution guidance
- `steps.current`: First step activated

**Example Payload**: `01_Transition_planning_START_STEP.xml`
```xml
<steps>
  <step id="data_collection_inventory" title="...">
    <goal>Objective. Artifacts: X; Acceptance: condition.</goal>
    <verified_artifacts>...</verified_artifacts>
    <required_variables>...</required_variables>
    <pcs_considerations>...</pcs_considerations>
  </step>
  <!-- More steps -->
  <focus>Execution guidance</focus>
  <goals>Updated stage goals</goals>
</steps>
```

---

### T3: START_BEHAVIOR
**Inputs**:
- `current_step`: Step object with goal, artifacts
- `state.variables`: All available variables

**Outputs**:
- `behaviors.current`: Behavior object with agent, task, inputs, outputs

**Example Payload**: `02_Transition_planning_START_BEHAVIOUR.xml`
```xml
<behavior id="data_collection_inventory_b1" step_id="data_collection_inventory">
  <agent>Explore-Agent</agent>
  <task behavior_id="data_collection_inventory_b1">
    Load './assets/housing.csv', verify existence, create data_existence_report.
  </task>
  <inputs>
    <variable name="user_submit_files">["./assets/housing.csv"]</variable>
  </inputs>
  <effects>False</effects>
  <outputs>
    <artifact name="data_existence_report">dict with file metadata</artifact>
  </outputs>
  <acceptance>
    <criterion>os.path.exists('./assets/housing.csv')==True</criterion>
  </acceptance>
</behavior>
```

---

### T4: COMPLETE_ACTION
**Inputs**:
- `behavior.task`: Task description
- `behavior.inputs`: Input variables
- `effects.current`: Recent execution outputs (may be empty first call)
- `notebook`: Current notebook state

**Outputs**:
- `actions`: Array of action objects (update-title, add-text, add-code2run, etc.)

**Example Actions**:
```xml
<actions>
  <update-project-title>Ames Housing Price Prediction</update-project-title>
  <add-text>We establish data existence...</add-text>
  <add-code2run>
import pandas as pd
df = pd.read_csv('./assets/housing.csv')
data_existence_report = {'row_count': len(df), ...}
print(f"Loaded {len(df)} rows")
  </add-code2run>
</actions>
```

---

### T5: COMPLETE_STEP (Behavior Reflection)
**Inputs**:
- `behavior.outputs`: Expected artifacts
- `state.variables`: Current variables (check if artifacts exist)
- `effects.current`: Execution results
- `acceptance_criteria`: Conditions to validate

**Outputs**:
- `reflection.evaluation`: Artifacts status, acceptance validation, goal achievement
- `reflection.decision.next_state`: STEP_RUNNING (retry) or STEP_COMPLETED (done)
- `reflection.context_for_next`: Guidance for next iteration/step

**Example Reflection**: `04_Transition_Complete_Step.xml`
```xml
<reflection current_step_is_complete="true">
  <evaluation>
    <artifacts_produced>
      <artifact name="data_existence_report" status="complete">
        Variable exists with 2930 rows
      </artifact>
    </artifacts_produced>
    <acceptance_validation>
      <criterion status="passed">os.path.exists(...)==True ✓</criterion>
    </acceptance_validation>
    <goal_achievement>
      <status>achieved</status>
      <reasoning>All artifacts produced, criteria met</reasoning>
    </goal_achievement>
  </evaluation>

  <decision>
    <next_state>STEP_COMPLETED</next_state>
    <reasoning>Step goal fully achieved</reasoning>
  </decision>

  <context_for_next>
    <variables_produced>
      <variable name="raw_dataset" value="housing dataframe">2930 rows, 82 cols</variable>
    </variables_produced>
    <recommendations_for_next>
      <if_moving_forward>Next step: analyze data structure</if_moving_forward>
    </recommendations_for_next>
  </context_for_next>

  <outputs_tracking_update>
    <produced><artifact>data_existence_report</artifact></produced>
  </outputs_tracking_update>
</reflection>
```

---

### T6: COMPLETE_STAGE (Stage Reflection)
**Inputs**:
- `completed_step`: Step just finished
- `stage.progress`: Completed/remaining steps
- `stage.artifacts`: Expected stage-level artifacts

**Outputs**:
- `stage_reflection.step_evaluation`: Assessment of completed step
- `stage_reflection.stage_assessment`: Progress percentage, artifacts status
- `stage_reflection.decision.next_state`: STEP_RUNNING (continue) or STAGE_COMPLETED (done)
- `stage_reflection.variable_management`: Extract/retain/deprecate variables
- `stage_reflection.stage_experience`: Lessons learned (only if stage complete)

**Example Reflection**: `05_Transition_Complete_Stage.xml`
```xml
<stage_reflection stage_is_complete="false">
  <step_evaluation>
    <step_id>data_collection_inventory</step_id>
    <completion_status>complete</completion_status>
    <artifacts_produced>
      <artifact name="raw_dataset" status="complete">2930 rows loaded</artifact>
    </artifacts_produced>
    <key_findings>
      <finding priority="high">Dataset exists and accessible</finding>
    </key_findings>
  </step_evaluation>

  <stage_assessment>
    <progress>
      <completed_steps>1</completed_steps>
      <remaining_steps>4</remaining_steps>
      <percentage>20%</percentage>
    </progress>
    <stage_artifacts_status>
      <artifact name="data_existence_report" status="in_progress">Partially done</artifact>
      <artifact name="data_structure_document" status="missing">Next step</artifact>
    </stage_artifacts_status>
    <goal_status>partial</goal_status>
  </stage_assessment>

  <decision>
    <next_state>STEP_RUNNING</next_state>
    <next_focus>data_structure_discovery</next_focus>
    <reasoning>Stage 20% complete, continue next step</reasoning>
  </decision>

  <variable_management>
    <extracted_from_notebook>
      <variable name="raw_dataset" type="DataFrame" source="cell_2">
        <summary>2930 rows × 82 columns</summary>
        <quality>complete</quality>
      </variable>
    </extracted_from_notebook>

    <retain>
      <variable name="raw_dataset" next_use="data_structure_discovery">
        Needed for next step
      </variable>
    </retain>

    <deprecate>
      <variable name="user_submit_files" replacement="raw_dataset" safe="true">
        File list no longer needed
      </variable>
    </deprecate>
  </variable_management>

  <outputs_update>
    <produced><artifact>raw_dataset</artifact></produced>
    <in_progress><artifact>data_existence_report</artifact></in_progress>
    <remaining>
      <artifact>data_structure_document</artifact>
      <artifact>variable_analysis_report</artifact>
    </remaining>
  </outputs_update>

  <pcs_check>
    <predictability>Dataset verified and representative</predictability>
    <computability>Reproducible loading with fixed path</computability>
    <stability>Integrity checks passed</stability>
  </pcs_check>
</stage_reflection>
```

---

## Decision Logic Flow

### Behavior Reflection Decision
```
IF all artifacts in variables AND
   all acceptance criteria passed AND
   no errors in execution
THEN
   decision.next_state = STEP_COMPLETED
ELSE
   IF behavior_iteration < max_retries
   THEN
      decision.next_state = STEP_RUNNING (retry same behavior)
   ELSE
      decision.next_state = STEP_FAILED (escalate)
```

### Stage Reflection Decision
```
IF all steps completed AND
   all stage artifacts produced
THEN
   decision.next_state = STAGE_COMPLETED
   Include: stage_experience summary
ELSE
   decision.next_state = STEP_RUNNING (next step)
   Skip: stage_experience (too early)

IF progress > 50% OR major_issues_found
THEN
   Include: stage_goal_review
ELSE
   Skip: stage_goal_review
```

---

## Variable Lifecycle

### Variables at Each State

**IDLE**:
- `user_problem`
- `user_submit_files`

**STAGE_RUNNING**:
- (same as IDLE)

**STEP_RUNNING**:
- (same as STAGE_RUNNING)
- + required_variables from step definition

**BEHAVIOR_COMPLETED**:
- (previous variables)
- + newly created artifacts

**STEP_COMPLETED**:
- (previous variables)
- + all step artifacts
- - deprecated variables (marked by reflection)

**Example Variable Evolution**:
```
IDLE:
  - user_problem
  - user_submit_files

BEHAVIOR_COMPLETED (after step 1):
  - user_problem
  - user_submit_files
  - raw_dataset ← NEW
  - data_inventory_checklist ← NEW

STEP_COMPLETED (after reflection):
  - user_problem
  - raw_dataset
  - data_inventory_checklist
  [user_submit_files DEPRECATED - replaced by raw_dataset]

BEHAVIOR_COMPLETED (after step 2):
  - user_problem
  - raw_dataset
  - data_inventory_checklist
  - data_structure_report ← NEW
```

---

## Agent Responsibilities Summary

| Agent | Role | Input | Output | Prompt File |
|-------|------|-------|--------|-------------|
| **Stage-Planner** | Decompose problem into stages | user_problem, user_submit_files | stages.xml | 00_START_WORKFLOW.txt |
| **Step-Planner** | Decompose stage into steps | stage context | steps.xml | 01_START_SECTION.txt |
| **Behavior Arrangement** | Select agent and assemble task | step context, state.variables | behavior.xml | 02_START_BEHAVIOUR.txt |
| **Action-Generator** | Generate executable actions | behavior context, notebook state | actions.xml | 03_START_ACTION.txt |
| **Behavior Reflection** | Evaluate behavior completion | execution results, artifacts | reflection.xml | 04_COMPLETE_STEP.txt |
| **Stage Reflection** | Evaluate stage progress | step results, stage progress | stage_reflection.xml | 05_COMPELETE_STAGE_OPTIMIZED.txt |

---

## Common Patterns

### Pattern 1: Linear Progression (Happy Path)
```
IDLE → STAGE_RUNNING → STEP_RUNNING → BEHAVIOR_RUNNING → BEHAVIOR_COMPLETED → STEP_COMPLETED → STEP_RUNNING (next) → ...
```

### Pattern 2: Behavior Retry
```
BEHAVIOR_RUNNING → BEHAVIOR_COMPLETED → [reflection: incomplete] → BEHAVIOR_RUNNING (iteration=2) → BEHAVIOR_COMPLETED → [reflection: complete] → STEP_COMPLETED
```

### Pattern 3: Stage Completion
```
STEP_COMPLETED (last step) → [stage reflection: stage complete] → STAGE_RUNNING (next stage) → STEP_RUNNING (first step of new stage)
```

### Pattern 4: Workflow Completion
```
STEP_COMPLETED (last step of last stage) → [stage reflection: all stages done] → WORKFLOW_COMPLETE
```

---

## Debugging Checklist

### If Stuck in BEHAVIOR_RUNNING:
- [ ] Check if actions.xml was generated
- [ ] Check if code executed successfully (effects.current)
- [ ] Verify notebook.cell_count increased
- [ ] Check for errors in execution

### If Stuck in BEHAVIOR_COMPLETED:
- [ ] Verify artifacts exist in state.variables
- [ ] Check acceptance criteria validation
- [ ] Review behavior_iteration count (max retries?)
- [ ] Check reflection.decision.next_state

### If Artifacts Missing:
- [ ] Verify Action-Generator created variables with exact names
- [ ] Check if code executed (effects.current not empty)
- [ ] Review verified_artifacts from step definition
- [ ] Ensure variables not deprecated prematurely

### If Stage Not Progressing:
- [ ] Check steps.completed vs steps.remaining
- [ ] Verify stage_artifacts_status
- [ ] Review stage_reflection.decision reasoning
- [ ] Check if goal_review needed (major issues?)

---

## Quick Fixes

### Fix: Artifact Name Mismatch
**Problem**: Step expects `data_report`, code creates `report`
**Solution**: Update code to create `data_report` exactly

### Fix: Premature Variable Deprecation
**Problem**: Variable deprecated but still needed by future step
**Solution**: Update variable_management.retain section

### Fix: Missing Acceptance Criteria
**Problem**: Reflection can't validate completion
**Solution**: Add programmatic criteria to step definition

### Fix: Execution Loop
**Problem**: Behavior retries infinitely
**Solution**: Check max_retries, add better error handling in code

---

## Related Documents
- [State Machine Specification](./STATE_MACHINE_SPECIFICATION.md) - Detailed FSM documentation
- [Prompt Design Patterns](./PROMPT_DESIGN_PATTERNS.md) - Prompt engineering guidelines
- [API Requirements](./API_REQUIREMENTS.md) - API specification
