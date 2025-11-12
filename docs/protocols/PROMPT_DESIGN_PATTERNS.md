# Prompt Design Patterns and Best Practices

## Overview

This document captures the design patterns, optimization strategies, and lessons learned from developing prompts for the Notebook-BCC state machine agents.

---

## Agent Roles and Responsibilities

### 1. Stage-Planner Agent
**Prompt**: `00_START_WORKFLOW.txt`
**Role**: Blueprint generator for stage-level decomposition
**Input**: User problem, submitted files, dataset hints
**Output**: XML with stages breakdown

**Design Principles**:
- **Artifact-First**: Every stage must define concrete artifacts with quality standards
- **Deterministic**: Stable IDs following snake_case convention
- **PCS-Aligned**: Each stage must address Predictability, Computability, Stability
- **Executable Acceptance**: Criteria must be programmatically checkable (e.g., `df_cleaned.isnull().sum().sum()==0`)

**Key Pattern**: Template-Based Decomposition
```xml
<stage id="unique_id" title="Human Title">
  <goal>
    Single paragraph with:
    - Main objective
    - Artifacts: concrete_var1, concrete_var2
    - Acceptance: executable_check1 AND executable_check2
  </goal>
  <verified_artifacts>
    <variable name="var_name">description, type, quality standards</variable>
  </verified_artifacts>
  <required_variables>
    <variable name="dep_var">source description</variable>
  </required_variables>
</stage>
```

**Lessons Learned**:
1. ✅ Always include 6 core DSLC stages (data existence → results communication)
2. ✅ Use `insert_after` attribute to maintain stage sequence
3. ⚠️ Avoid vague acceptance criteria like "data looks clean" → use `df.isnull().sum().sum() == 0`
4. ⚠️ Each stage should have 3-7 steps maximum (not too granular, not too coarse)

---

### 2. Step-Planner Agent
**Prompt**: `01_START_SECTION.txt`
**Role**: Decompose stage into executable steps
**Input**: Current stage context, global workflow context, step catalog
**Output**: XML with steps breakdown

**Design Principles**:
- **Granularity Control**: 3-7 steps per stage
- **Variable Dependency Chain**: Each step's outputs feed into next step's inputs
- **PCS Integration**: Every step has explicit PCS considerations
- **Context Sensitivity**: Can update stage goals based on learned information

**Key Pattern**: Progressive Refinement
```xml
<step id="step_id" title="Title">
  <goal>Objective with Artifacts: X, Y; Acceptance: condition</goal>
  <verified_artifacts>
    <variable name="X">type, quality standard</variable>
  </verified_artifacts>
  <required_variables>
    <variable name="prev_output">from previous step</variable>
  </required_variables>
  <pcs_considerations>
    <predictability>1-2 sentences on generalization</predictability>
    <computability>1-2 sentences on reproducibility</computability>
    <stability>1-2 sentences on robustness</stability>
  </pcs_considerations>
</step>
```

**Optimization Experience**:
1. ✅ Step IDs should reflect semantic meaning (e.g., `data_collection_inventory`, not `step1`)
2. ✅ Goals should explicitly mention both artifacts AND acceptance
3. ⚠️ Avoid cross-stage variable dependencies (breaks modularity)
4. ⚠️ PCS considerations should be specific to step, not generic boilerplate

---

### 3. Behavior Arrangement Agent
**Prompt**: `02_START_BEHAVIOUR.txt`
**Role**: Select appropriate agent and assemble execution context
**Input**: Step context, current state variables, available agents catalog
**Output**: XML with agent selection and task definition

**Design Principles**:
- **Agent Capability Matching**: Choose agent based on task type (Explore for data analysis, Define for planning, etc.)
- **Value Binding**: Use actual values from `state.variables`, not placeholders
- **Specificity**: Task instructions include file paths, variable names, methods
- **Effects Awareness**: If `effects.current` is not empty, communicate recent results to agent

**Key Pattern**: Context Assembly
```xml
<behavior id="step_id_b1" step_id="step_id">
  <agent>AgentName</agent>
  <task behavior_id="behavior_id">
    Specific instructions with:
    - File paths: ./assets/housing.csv
    - Variable names: df_raw
    - Methods: pd.read_csv(), df.shape
  </task>
  <inputs>
    <variable name="user_submit_files">["./assets/housing.csv"]</variable>
  </inputs>
  <effects>True/False</effects>
  <outputs>
    <artifact name="data_existence_report">description</artifact>
  </outputs>
  <acceptance>
    <criterion>os.path.exists("./assets/housing.csv")==True</criterion>
  </acceptance>
  <whathappened> <!-- Optional -->
    <overview>Context summary</overview>
    <background>Previous results</background>
  </whathappened>
</behavior>
```

**Agent Selection Strategy**:
| Task Type | Appropriate Agent |
|-----------|------------------|
| Data loading, schema discovery | Explore-Agent |
| Correlation analysis, EDA | Explore-Agent |
| Problem definition, planning | PlanningAnalyst |
| Artifact validation | QualityValidator |
| Documentation generation | DocumentationWriter |
| Model training | ModelingAgent |
| Evaluation | EvaluationAgent |

**Lessons Learned**:
1. ✅ Always provide actual values from state.variables, not abstract references
2. ✅ Include `<whathappened>` when effects.current contains useful context
3. ⚠️ Don't assign tasks beyond agent's capability (e.g., Explore-Agent can't train models)
4. ⚠️ Ensure outputs match step's verified_artifacts exactly

---

### 4. Action-Generator Agent
**Prompt**: `03_START_ACTION.txt`
**Role**: Translate behavior context into executable notebook actions
**Input**: Behavior context, notebook state, execution results (effects)
**Output**: XML with actions (text, code, title updates, communications)

**Design Principles**:
- **Continuity-Aware**: Read complete notebook to avoid duplication
- **Language Quality**: Professional, clear, technically accurate writing
- **Artifact-Driven**: Every action sequence MUST produce verified_artifacts
- **Iterative Execution**: First call = setup + code; follow-up = analysis + continue
- **No Hallucination**: Only use variables from state.variables

**Key Pattern**: Explain-Then-Execute
```xml
<actions>
  <update-project-title>Professional Title</update-project-title>
  <add-text>
    Explanation of what we're about to do:
    - Why this step is important
    - What we'll accomplish
    - How it fits into larger goal
  </add-text>
  <add-code2run>
# Step 1: Execute task
result = perform_operation()
print(f"Result: {result}")

# Step 2: Create artifact variable
artifact_name = {
    'key': result
}
  </add-code2run>
</actions>
```

**Critical Execution Flow**:
1. **First Call** (effects.current is empty):
   - Add explanatory text
   - Add code to execute
   - **STOP** - do NOT analyze results you haven't seen
2. **Second Call** (effects.current contains output):
   - Analyze results
   - Add follow-up text or code
   - Mark artifacts as complete if criteria satisfied

**Common Pitfalls**:
❌ **WRONG**:
```xml
<add-code2run>df = pd.read_csv('data.csv')</add-code2run>
<add-text>The dataset has 1000 rows.</add-text>  <!-- Can't know this yet! -->
```

✅ **CORRECT**:
```xml
<add-text>Loading dataset to verify existence.</add-text>
<add-code2run>
df = pd.read_csv('data.csv')
print(f"Loaded {len(df)} rows")
</add-code2run>
<!-- Next API call will analyze the output -->
```

**Language Quality Guidelines**:
1. ✅ Professional data science terminology
2. ✅ Clear logical flow with smooth transitions
3. ✅ Use markdown formatting for emphasis (`**bold**`, `*italic*`, `code`)
4. ✅ Concise but informative (no fluff, no obvious repetition)
5. ⚠️ Avoid overly casual language ("Let's do this!", "Awesome!")
6. ⚠️ Match existing notebook style and tone

**Artifact Creation Pattern**:
```python
# Always create variables matching exact artifact names
data_existence_report = {
    'file_path': file_path,
    'exists': exists,
    'row_count': len(df),
    # ... all required fields
}

# Print to show progress
print(f"Created artifact: {type(data_existence_report)}")
```

---

### 5. Behavior Reflection Agent
**Prompt**: `04_COMPLETE_STEP.txt`
**Role**: Evaluate behavior execution and determine step completion
**Input**: Behavior execution results, variables produced, acceptance criteria
**Output**: XML reflection with decision

**Design Principles**:
- **Evidence-Based**: Base evaluation on actual execution results
- **Decisive**: Provide clear next_state decision with reasoning
- **Contextual**: Prepare context for next iteration/step

**Key Pattern**: Evaluation Framework
```xml
<reflection current_step_is_complete="true|false">
  <evaluation>
    <artifacts_produced>
      <artifact name="X" status="complete|incomplete|missing">
        Assessment: Variable X contains 2930 rows as expected
      </artifact>
    </artifacts_produced>
    <acceptance_validation>
      <criterion status="passed|failed">
        os.path.exists(...)==True ✓
      </criterion>
    </acceptance_validation>
    <execution_quality>
      <code_execution>success|failed</code_execution>
      <errors_found>None or description</errors_found>
    </execution_quality>
    <goal_achievement>
      <status>achieved|partial|not_achieved</status>
      <reasoning>All artifacts produced, criteria met</reasoning>
    </goal_achievement>
  </evaluation>

  <decision>
    <next_state>STEP_COMPLETED</next_state>
    <reasoning>Step goal fully achieved</reasoning>
  </decision>

  <context_for_next>
    <variables_produced>
      <variable name="X" value="description">Content</variable>
    </variables_produced>
    <whathappened>
      <overview>What was accomplished</overview>
      <key_findings>Important insights</key_findings>
    </whathappened>
    <recommendations_for_next>
      <if_moving_forward>Next step should focus on...</if_moving_forward>
    </recommendations_for_next>
  </context_for_next>

  <outputs_tracking_update>
    <produced><artifact>X</artifact></produced>
    <in_progress><artifact>Y</artifact></in_progress>
    <remaining><artifact>Z</artifact></remaining>
  </outputs_tracking_update>
</reflection>
```

**Decision Logic**:
- **STEP_RUNNING** (continue behavior): Artifacts incomplete OR criteria failed OR errors exist
- **STEP_COMPLETED**: All artifacts produced AND all criteria passed AND goal achieved

**Lessons Learned**:
1. ✅ Always reference actual variable values in evaluation
2. ✅ Provide specific reasoning for decisions (not generic)
3. ⚠️ Don't mark artifacts as complete if they don't exist in variables
4. ⚠️ If continuing behavior, give clear guidance on what to fix

---

### 6. Stage Reflection Agent
**Prompt**: `05_COMPELETE_STAGE_OPTIMIZED.txt`
**Role**: Evaluate stage progress and determine if stage is complete
**Input**: Completed step results, stage progress, stage artifacts status
**Output**: XML stage reflection with decision

**Design Principles**:
- **Conditional Complexity**: Output adapts to progress level
- **Variable Lifecycle Management**: Extract, retain, deprecate
- **Progressive Reflection**: Early stage = simple tracking; late stage = full experience summary
- **Conciseness**: Remove verbose descriptions, focus on actionable information

**Key Pattern**: Progressive Depth
```xml
<stage_reflection stage_is_complete="false">
  <step_evaluation>
    <step_id>completed_step_id</step_id>
    <completion_status>complete|incomplete</completion_status>
    <artifacts_produced>
      <artifact name="X" status="complete">Assessment</artifact>
    </artifacts_produced>
    <key_findings>
      <finding priority="high|medium|low">Discovery</finding>
    </key_findings>
  </step_evaluation>

  <stage_assessment>
    <progress>
      <completed_steps>1</completed_steps>
      <remaining_steps>4</remaining_steps>
      <percentage>20%</percentage>
    </progress>
    <stage_artifacts_status>
      <artifact name="X" status="complete|in_progress|missing">Status</artifact>
    </stage_artifacts_status>
    <goal_status>achieved|partial|not_achieved</goal_status>
  </stage_assessment>

  <!-- CONDITIONAL: Only if progress >50% OR major issues -->
  <stage_goal_review needs_update="false">
    <reasoning>Why goal doesn't need update</reasoning>
  </stage_goal_review>

  <!-- CONDITIONAL: Only if stage_is_complete=true -->
  <stage_experience from="stage_id">
    Concise narrative: key decisions, trade-offs, discoveries, wisdom.
  </stage_experience>

  <decision>
    <next_state>STEP_RUNNING</next_state>
    <next_focus>data_structure_discovery</next_focus>
    <reasoning>Stage only 20% complete, continue next step</reasoning>
  </decision>

  <variable_management>
    <extracted_from_notebook>
      <variable name="housing_data" type="DataFrame" source="cell_id">
        <summary>2930 rows × 82 columns</summary>
        <quality>complete</quality>
      </variable>
    </extracted_from_notebook>

    <retain>
      <variable name="raw_dataset" next_use="next_step_id">Why needed</variable>
    </retain>

    <deprecate>
      <variable name="user_submit_files" replacement="raw_dataset" safe="true">
        File list no longer needed after loading
      </variable>
    </deprecate>

    <!-- CONDITIONAL: Only if gaps exist -->
    <gaps>
      <missing name="X" needed_for="step_id" urgency="critical">
        <how_to_obtain>Description</how_to_obtain>
      </missing>
    </gaps>
  </variable_management>

  <outputs_update>
    <produced><artifact>X</artifact></produced>
    <in_progress><artifact>Y</artifact></in_progress>
    <remaining><artifact>Z</artifact></remaining>
  </outputs_update>

  <pcs_check>
    <predictability>Brief status</predictability>
    <computability>Brief status</computability>
    <stability>Brief status</stability>
  </pcs_check>
</stage_reflection>
```

**Conditional Output Rules**:
1. **stage_goal_review**: Only include if:
   - Progress > 50% OR
   - Major issues discovered requiring goal revision
2. **stage_experience**: Only include if:
   - `stage_is_complete=true`
3. **gaps**: Only include if:
   - Missing variables exist

**Optimization History**:
Based on evaluation document (`05_EVALUATION_AND_COMPARISON.md`):

| Issue | Severity | Original Problem | Optimization |
|-------|----------|-----------------|--------------|
| Premature experience summary | High | Generated full summary at 20% progress | Only generate when stage complete |
| Frequent goal review | Medium | Reviewed goal at every step | Only review at >50% or when issues arise |
| Branch redundancy | Medium | Three context branches, only one used | Dynamic output based on decision |
| Empty field noise | Low | Empty tags like `<gaps/>` | Conditional inclusion |

**Lessons Learned**:
1. ✅ Early stage (0-50%): Focus on progress tracking only
2. ✅ Mid stage (50-80%): Add goal review if anomalies detected
3. ✅ Late stage (80-100%): Full evaluation including experience
4. ✅ Stage complete: Comprehensive experience summary with lessons, challenges, best practices
5. ⚠️ Variable management is MANDATORY every time (extract, retain, deprecate)
6. ⚠️ Be concise - remove verbose descriptions that don't add value

---

## Cross-Cutting Patterns

### Pattern 1: XML Output Only
**All agents must**:
- Output ONLY valid XML
- No explanations outside XML
- No JSON, Markdown, or other formats
- Use exact schema provided in prompt

### Pattern 2: Artifact-First Design
**Every planning agent must**:
- Define concrete, named artifacts (not abstract goals)
- Specify artifact type and quality standards
- Create programmatic acceptance criteria
- Map artifacts to verified_artifacts in step/stage definitions

### Pattern 3: Variable Dependency Chain
**Ensure continuity**:
```
Stage A outputs: artifact_1
  ↓
Stage B requires: artifact_1
Stage B outputs: artifact_2
  ↓
Stage C requires: artifact_2
```

**Anti-pattern**: Skip-level dependencies
❌ Stage C requires artifact_1 from Stage A (skipping B)

### Pattern 4: PCS Integration
**All stages/steps must address**:
- **Predictability**: How does this support generalization?
- **Computability**: How do we ensure reproducibility?
- **Stability**: How do we test robustness?

**Example** (data loading step):
- Predictability: "Ensures dataset is consistently sourced and representative"
- Computability: "Standardizes file loading path and encoding for reproducibility"
- Stability: "Validates dataset integrity to prevent downstream errors"

### Pattern 5: Iterative Code Execution
**Action-Generator pattern**:
1. **Setup Phase**: Add text → Add code → Wait for execution
2. **Analysis Phase**: Analyze results → Continue or complete
3. **Never**: Add analysis before seeing results

**Critical Rule**: End with code when you need to see execution results first.

### Pattern 6: Professional Language Quality
**All text-generating agents must**:
- Use professional data science terminology
- Maintain consistent tone and style
- Write clear, grammatically correct English
- Use markdown formatting appropriately
- Avoid obvious repetition or fluff

**Bad Example**:
> "Let's load the data! This is super important because we need data to do stuff."

**Good Example**:
> "We establish data existence through systematic collection and inventory. This foundational step ensures the **Ames Housing dataset** is accessible, complete, and ready for analysis."

### Pattern 7: Conditional Complexity
**Adapt output to context**:
- Early progress (0-50%): Minimal tracking
- Mid progress (50-80%): Add reviews if needed
- Late progress (80-100%): Full evaluation
- Complete: Comprehensive summary with lessons learned

**Implementation**: Use conditional XML sections that appear only when relevant.

---

## Common Anti-Patterns to Avoid

### ❌ Anti-Pattern 1: Vague Acceptance Criteria
**Bad**: "Data should be clean and ready"
**Good**: `df_cleaned.isnull().sum().sum() == 0 AND df_cleaned.shape[0] > 1000`

### ❌ Anti-Pattern 2: Hallucinated Variables
**Bad**: Using variable `processed_data` without it being in state.variables
**Good**: Check state.variables first, only use existing variables

### ❌ Anti-Pattern 3: Premature Analysis
**Bad**: Adding text analyzing code results before code executes
**Good**: Add code → wait for execution → analyze in next call

### ❌ Anti-Pattern 4: Generic PCS Boilerplate
**Bad**: "Ensures reproducibility and stability"
**Good**: "Uses fixed random seed (42) and logs sklearn version (1.3.0) for reproducibility"

### ❌ Anti-Pattern 5: Overengineering Output
**Bad**: Generating full experience summary at 10% progress
**Good**: Simple tracking early; detailed summary only when complete

### ❌ Anti-Pattern 6: Duplicate Content
**Bad**: Repeating same explanations agent already wrote
**Good**: Read notebook context, continue naturally from where it left off

### ❌ Anti-Pattern 7: Unclear Variable Types
**Bad**: `<variable name="report">Some report</variable>`
**Good**: `<variable name="report">dict with keys: file_path, row_count, type: dict</variable>`

---

## Prompt Optimization Checklist

### For Planning Agents (Stage/Step-Planner)
- [ ] Goals include both Artifacts AND Acceptance
- [ ] Acceptance criteria are programmatically checkable
- [ ] Variable dependencies form valid chain (no skip-level)
- [ ] PCS considerations are specific, not generic
- [ ] IDs use snake_case and semantic names
- [ ] Output is XML only, no extra text

### For Arrangement Agent (Behavior)
- [ ] Agent selection matches task capability
- [ ] Task instructions are specific (file paths, methods)
- [ ] Input variables use actual values from state
- [ ] Outputs match step's verified_artifacts exactly
- [ ] Acceptance criteria are executable
- [ ] Include whathappened if effects.current is useful

### For Action-Generator Agent
- [ ] Read complete notebook to avoid duplication
- [ ] Professional, clear language quality
- [ ] Artifact variables created with exact names
- [ ] Code execution pattern: explain → execute → wait
- [ ] No analysis of results not yet seen
- [ ] All variables from state.variables only

### For Reflection Agents (Behavior/Stage)
- [ ] Evaluation based on actual execution results
- [ ] Reference actual variable names and values
- [ ] Clear, decisive next_state with reasoning
- [ ] Conditional sections appear only when relevant
- [ ] Variable management complete (extract/retain/deprecate)
- [ ] Concise, actionable output (no verbose fluff)

---

## Lessons Learned Summary

### What Works Well ✅
1. **Artifact-First Design**: Concrete outputs with quality standards prevent ambiguity
2. **Programmatic Acceptance**: Executable criteria (code expressions) eliminate subjectivity
3. **Variable Dependency Chain**: Clear input/output mapping ensures continuity
4. **Conditional Complexity**: Adapting output depth to progress level reduces noise
5. **Iterative Execution**: Explain → Execute → Analyze pattern respects async execution
6. **Professional Language**: Clear, technical writing maintains credibility

### What to Avoid ⚠️
1. **Premature Summarization**: Don't generate experience summaries until stage complete
2. **Vague Criteria**: "Data looks good" → use `df.isnull().sum().sum() == 0`
3. **Hallucinated Variables**: Always check state.variables before using
4. **Duplicate Content**: Read notebook context first to avoid repetition
5. **Generic PCS**: "Ensures reproducibility" → specify seeds, versions, methods
6. **Analysis Before Execution**: Can't analyze results you haven't seen yet

---

## Prompt Template Library

### Template: Stage Definition
```xml
<stage id="snake_case_id" title="Human Title" [insert_after="previous_id"]>
  <goal>
    [Main objective in 1-2 sentences].
    Artifacts: artifact_1, artifact_2, artifact_3;
    Acceptance: [executable_check1] AND [executable_check2].
  </goal>
  <verified_artifacts>
    <variable name="artifact_1">[type], [quality standard]</variable>
    <variable name="artifact_2">[type], [quality standard]</variable>
  </verified_artifacts>
  <required_variables>
    <variable name="input_var">[description, source]</variable>
  </required_variables>
</stage>
```

### Template: Step Definition with PCS
```xml
<step id="step_id" title="Title">
  <goal>
    [Objective].
    Artifacts: X, Y;
    Acceptance: [condition1] AND [condition2].
  </goal>
  <verified_artifacts>
    <variable name="X">[description], [type], [standard]</variable>
  </verified_artifacts>
  <required_variables>
    <variable name="prev_output">[source]</variable>
  </required_variables>
  <pcs_considerations>
    <predictability>[How this supports generalization, 1-2 sentences]</predictability>
    <computability>[Reproducibility measures: seeds, versions, 1-2 sentences]</computability>
    <stability>[Robustness checks, sensitivity, 1-2 sentences]</stability>
  </pcs_considerations>
</step>
```

### Template: Behavior Assembly
```xml
<behavior id="step_id_b1" step_id="step_id">
  <agent>[AgentName based on task type]</agent>
  <task behavior_id="step_id_b1">
    [Specific instructions with]:
    - File paths: [actual_path]
    - Variable names: [actual_var]
    - Methods: [actual_method_calls]
  </task>
  <inputs>
    <variable name="input_var">[actual_value_from_state]</variable>
  </inputs>
  <effects>[True if effects.current should be communicated]</effects>
  <outputs>
    <artifact name="output_artifact">[description matching verified_artifacts]</artifact>
  </outputs>
  <acceptance>
    <criterion>[executable_condition]</criterion>
  </acceptance>
</behavior>
```

### Template: Action Sequence
```xml
<actions>
  <update-project-title>[Professional Title]</update-project-title>
  <update-section-title>[Stage Title]</update-section-title>
  <add-text>
[Professional explanation]:
- Context: [why this step]
- Objective: [what we'll accomplish]
- Approach: [how we'll do it]
[Use markdown formatting: **bold**, *italic*, `code`]
  </add-text>
  <add-code2run>
# Step 1: [Description]
[code_here]
print(f"[Progress indicator]")

# Step 2: Create artifacts
[artifact_var] = {
    'key': 'value'
}
print(f"Created: {type([artifact_var])}")
  </add-code2run>
</actions>
```

### Template: Reflection Decision
```xml
<reflection current_step_is_complete="[true|false]">
  <evaluation>
    <artifacts_produced>
      <artifact name="[name]" status="[complete|incomplete|missing]">
        [Assessment based on actual values]
      </artifact>
    </artifacts_produced>
    <acceptance_validation>
      <criterion status="[passed|failed]">[criterion description]</criterion>
    </acceptance_validation>
    <goal_achievement>
      <status>[achieved|partial|not_achieved]</status>
      <reasoning>[Evidence-based reasoning]</reasoning>
    </goal_achievement>
  </evaluation>

  <decision>
    <next_state>[STEP_RUNNING|STEP_COMPLETED]</next_state>
    <reasoning>[Clear explanation]</reasoning>
  </decision>

  <context_for_next>
    <variables_produced>
      <variable name="[var]" value="[description]">[Content]</variable>
    </variables_produced>
    <recommendations_for_next>
      <if_moving_forward>[Guidance for next step]</if_moving_forward>
    </recommendations_for_next>
  </context_for_next>

  <outputs_tracking_update>
    <produced><artifact>[name]</artifact></produced>
    <remaining><artifact>[name]</artifact></remaining>
  </outputs_tracking_update>
</reflection>
```

---

## Related Documents
- [State Machine Specification](./STATE_MACHINE_SPECIFICATION.md) - FSM states and transitions
- [API Requirements](./API_REQUIREMENTS.md) - API specification
- [Stage Catalog](./STAGE_CATALOG.md) - DSLC stage definitions
