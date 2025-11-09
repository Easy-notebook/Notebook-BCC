# Action Generation Prompt Builder Guide

This guide explains how to construct the optimized prompt from the real payload data.

## Architecture Overview

The prompt is split into two parts:

1. **SYSTEM PROMPT** (Fixed) - Agent definition, capabilities, and execution policies
2. **USER PROMPT** (Dynamic) - Context-driven from the actual payload

## Prompt Construction Flow

```
Real Payload (JSON) → Extract Context → Build USER PROMPT → Combine with SYSTEM PROMPT → Send to LLM
```

---

## Step 1: Extract Context from Payload

### Input: Real Payload Structure

See: `/docs/examples/ames_housing/payloads/03_STATE_Behavior_Running.json`

Key sections to extract:

```python
payload = {
  "observation": {
    "location": {
      "current": {...},      # Current position
      "progress": {          # Hierarchical progress
        "stages": {...},
        "steps": {...},
        "behaviors": {...}
      },
      "goals": "..."         # Behavior goals
    }
  },
  "state": {
    "variables": {...},      # Available variables
    "effects": {...},        # Execution results
    "notebook": {...},       # Notebook state
    "FSM": {...}             # State machine info
  }
}
```

---

## Step 2: Build USER PROMPT Sections

### 2.1 Task Request (Fixed Template)

```markdown
# Task Request

Generate valid XML containing executable actions that:
- Accomplish the behavior's task
- Produce all `verified_artifacts`
- Satisfy `acceptance_criteria`
- Use only available variables
- Continue from existing notebook content (do NOT repeat)

**Output**: XML only (wrapped in `<actions>...</actions>`), no explanations, no other text.
```

### 2.2 Current Observation (Extract from `observation.location`)

```python
# Extract location context
current = payload["observation"]["location"]["current"]
stages_progress = payload["observation"]["location"]["progress"]["stages"]
steps_progress = payload["observation"]["location"]["progress"]["steps"]
behaviors_progress = payload["observation"]["location"]["progress"]["behaviors"]

# Build section
current_observation = f"""
## Location Context

**Current Position**:
- **Stage ID**: {current["stage_id"]}
- **Step ID**: {current["step_id"]}
- **Behavior ID**: {current["behavior_id"]}
- **Behavior Iteration**: {current["behavior_iteration"]}

**Current Stage**:
- **Title**: {stages_progress["current"]["title"]}
- **Goal**: {stages_progress["current"]["goal"]}

**Current Step**:
- **Title**: {steps_progress["current"]["title"]}
- **Goal**: {steps_progress["current"]["goal"]}

**Current Behavior**:
- **Agent**: {behaviors_progress["current"]["agent"]}
- **Task**: {behaviors_progress["current"]["task"]}
- **Acceptance Criteria**:
{format_acceptance_criteria(behaviors_progress["current"]["acceptance"])}
"""
```

### 2.3 Progress Tracking (Extract from `observation.location.progress`)

```python
# Extract focus from different levels
stage_focus = stages_progress["focus"]
step_focus = steps_progress["focus"]
behavior_focus = behaviors_progress["focus"]

# Extract outputs tracking
current_outputs = behaviors_progress["current_outputs"]

progress_tracking = f"""
## Progress Tracking

**Stage Focus**:
{stage_focus}

**Step Focus**:
{step_focus}

**Behavior Focus**:
{behavior_focus}

**Current Outputs Tracking**:
- **Expected**:
{format_expected_outputs(current_outputs["expected"])}
- **Produced**: {current_outputs["produced"]}
- **In Progress**: {current_outputs["in_progress"]}
"""
```

### 2.4 Current State (Extract from `state`)

```python
# Extract state
variables = payload["state"]["variables"]
effects = payload["state"]["effects"]
notebook = payload["state"]["notebook"]
fsm = payload["state"]["FSM"]

# Check if first call
is_first_call = len(effects["current"]) == 0

current_state = f"""
## Variables
```json
{json.dumps(variables, indent=2, ensure_ascii=False)}
```

## Effects (Recent Execution)
```json
{json.dumps(effects, indent=2, ensure_ascii=False)}
```

**CRITICAL**:
{get_execution_guidance(is_first_call, effects)}

## Notebook State
- **Title**: {notebook.get("title", "null (empty)")}
- **Cell Count**: {notebook["cell_count"]}
- **Last Cell Type**: {notebook.get("last_cell_type", "null")}
- **Last Output**: {notebook.get("last_output", "null")}

**Complete Notebook Content (Markdown)**:
```
{get_notebook_markdown(notebook)}
```

{get_notebook_guidance(notebook)}
"""
```

#### Helper Function: Execution Guidance

```python
def get_execution_guidance(is_first_call, effects):
    if is_first_call:
        return """
- ⚠️ `effects.current` is **EMPTY** - This is the FIRST call for this behavior
- You have NOT seen any execution results yet
- Add explanatory text and code, but DO NOT add analysis of results you haven't seen
- End with code execution - let the next API call analyze results
"""
    else:
        return f"""
- ✅ `effects.current` contains execution results
- This is a FOLLOW-UP call - you can now analyze results
- Review execution output below and decide: continue with more code OR conclude
- Recent execution output:
{format_effects(effects["current"])}
"""
```

### 2.5 Behavior Context (Extract from `observation.location.progress.behaviors.current`)

```python
behavior = behaviors_progress["current"]

behavior_context = f"""
## Inputs (Available Variables)
```json
{json.dumps(behavior["inputs"], indent=2, ensure_ascii=False)}
```

## Expected Outputs (verified_artifacts)
```json
{json.dumps(behavior["outputs"], indent=2, ensure_ascii=False)}
```

## Acceptance Criteria
{format_acceptance_criteria(behavior["acceptance"])}

## What Happened (Previous Context)
{format_whathappened(behavior.get("whathappened", {}))}
"""
```

### 2.6 Agent-Specific Capabilities (Extract from agent registry)

```python
agent_name = behavior["agent"]

# Load agent capabilities from registry/config
agent_capabilities = get_agent_capabilities(agent_name)

agent_section = f"""
**Current Agent**: {agent_name}

**Capabilities**:
{format_capabilities(agent_capabilities["general"])}

**Recommended Tools for This Behavior**:
{format_recommended_tools(agent_capabilities["recommended"])}
"""
```

### 2.7 PCS Considerations (Extract from `steps.current.pcs_considerations`)

```python
pcs = steps_progress["current"]["pcs_considerations"]

pcs_section = f"""
**Predictability**: {pcs["predictability"]}

**Computability**: {pcs["computability"]}

**Stability**: {pcs["stability"]}
"""
```

### 2.8 Action Generation Instructions (Extract from step/behavior strategy)

```python
# This section provides concrete guidance on WHAT to generate
# Built from step strategy documents or behavior templates

step_strategy = load_step_strategy(
    stage_id=current["stage_id"],
    step_id=current["step_id"]
)

behavior_guidance = load_behavior_guidance(
    stage_id=current["stage_id"],
    step_id=current["step_id"],
    behavior_id=current["behavior_id"]
)

instructions = build_action_instructions(
    step_strategy=step_strategy,
    behavior_guidance=behavior_guidance,
    behavior_task=behavior["task"],
    outputs=behavior["outputs"],
    is_first_call=is_first_call
)
```

---

## Step 3: Combine SYSTEM + USER Prompts

```python
def build_full_prompt(payload, agent_registry, strategy_docs):
    # SYSTEM PROMPT (fixed)
    system_prompt = load_system_prompt_template()

    # USER PROMPT (dynamic)
    user_prompt_sections = [
        build_task_request(),
        build_current_observation(payload),
        build_progress_tracking(payload),
        build_current_state(payload),
        build_behavior_context(payload),
        build_agent_capabilities(payload, agent_registry),
        build_pcs_considerations(payload),
        build_action_instructions(payload, strategy_docs)
    ]

    user_prompt = "\n---\n".join(user_prompt_sections)

    # Combine
    full_prompt = f"{system_prompt}\n\n{user_prompt}"

    return full_prompt
```

---

## Step 4: Send to LLM

```python
# Format as messages
messages = [
    {
        "role": "system",
        "content": system_prompt
    },
    {
        "role": "user",
        "content": user_prompt
    }
]

# Call LLM
response = llm_client.generate(
    messages=messages,
    temperature=0.3,  # Lower for more deterministic output
    max_tokens=4000
)

# Parse XML response
actions = parse_xml_response(response)
```

---

## Key Optimization Principles

### 1. Separation of Concerns
- **SYSTEM PROMPT**: Agent definition, capabilities, policies (unchanging)
- **USER PROMPT**: Task context, state, data (changes per call)

### 2. Context Efficiency
- Only include relevant progress information
- Compress history if too long
- Use structured formats (JSON, markdown)

### 3. Clear Execution Guidance
- Explicitly state whether this is first call or follow-up
- Guide the agent on what to generate based on `effects.current`
- Prevent hallucination by marking available vs unavailable data

### 4. Hierarchical Context
- Provide context at multiple levels: Stage → Step → Behavior
- Include focus statements for each level
- Track outputs at each level

### 5. Concrete Instructions
- Don't just say "accomplish the task"
- Provide step-by-step breakdown based on behavior strategy
- Reference specific tools and methods
- Give examples of expected output format

---

## Example Builder Implementation

See: `/utils/prompt_builder.py` (to be created)

```python
class ActionGenerationPromptBuilder:
    def __init__(self,
                 system_prompt_path: str,
                 agent_registry: AgentRegistry,
                 strategy_loader: StrategyLoader):
        self.system_prompt = self._load_system_prompt(system_prompt_path)
        self.agent_registry = agent_registry
        self.strategy_loader = strategy_loader

    def build(self, payload: dict) -> str:
        """Build full prompt from payload."""
        user_prompt = self._build_user_prompt(payload)
        return f"{self.system_prompt}\n\n{user_prompt}"

    def _build_user_prompt(self, payload: dict) -> str:
        """Build dynamic USER PROMPT from payload."""
        sections = [
            self._task_request(),
            self._current_observation(payload),
            self._progress_tracking(payload),
            self._current_state(payload),
            self._behavior_context(payload),
            self._agent_capabilities(payload),
            self._pcs_considerations(payload),
            self._action_instructions(payload)
        ]
        return "\n---\n".join(sections)

    # ... implement each section builder
```

---

## Validation Checklist

Before sending the prompt, verify:

- [ ] All variables in `behavior.inputs` are present in `state.variables`
- [ ] `effects.current` status is correctly communicated (empty vs has results)
- [ ] Notebook state is accurate (title, cell_count)
- [ ] Agent capabilities match the assigned agent
- [ ] Acceptance criteria are clear and testable
- [ ] Action instructions are concrete and actionable
- [ ] No placeholder values (e.g., "TODO", "TBD")
- [ ] JSON formatting is valid
- [ ] Markdown formatting is correct

---

## Testing Strategy

1. **Unit Tests**: Test each section builder independently
2. **Integration Tests**: Test full prompt construction
3. **LLM Tests**: Verify LLM generates valid XML
4. **Action Tests**: Verify actions execute successfully

```python
# Test example
def test_prompt_builder_first_call():
    payload = load_test_payload("03_STATE_Behavior_Running.json")
    builder = ActionGenerationPromptBuilder(...)

    prompt = builder.build(payload)

    # Verify structure
    assert "SYSTEM PROMPT" in prompt
    assert "USER PROMPT" in prompt

    # Verify context
    assert "effects.current is **EMPTY**" in prompt
    assert "data_collection_inventory_b1" in prompt

    # Verify instructions
    assert "Update project title" in prompt
    assert "Add code" in prompt
```

---

## Performance Considerations

### Token Optimization

- **System Prompt**: ~3000 tokens (fixed)
- **User Prompt**: ~5000-8000 tokens (varies)
- **Total**: ~8000-11000 tokens per request

### Compression Strategies

1. **History Compression**: Only include recent effects, summarize older ones
2. **Progress Compression**: Only include current + immediate next items
3. **Schema Compression**: Use compact JSON format
4. **Strategy Compression**: Only include relevant behavior guidance

### Caching Opportunities

- System prompt can be cached (unchanging)
- Agent capabilities can be cached (per agent)
- Step strategies can be cached (per step)

---

## Next Steps

1. Implement `PromptBuilder` class in `/utils/prompt_builder.py`
2. Create unit tests in `/test/test_prompt_builder.py`
3. Add configuration for prompt templates
4. Implement token counting and optimization
5. Add logging for prompt construction debugging
