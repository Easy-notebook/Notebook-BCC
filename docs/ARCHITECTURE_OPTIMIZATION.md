# Architecture Optimization Plan V2: POMDP-Aligned Workflow System
**Updated with Behavior & Section Support**

## Executive Summary

This document provides a **complete** optimization plan for the workflow system, aligning it with POMDP (Partially Observable Markov Decision Process) principles, removing unused fields, and **correctly handling the Behavior-Action hierarchy and Section organization**.

**Critical Update**: This V2 incorporates the previously missing **Behavior execution layer** and **Section content organization**, which are essential for the system to function correctly.

---

## 1. Problem Analysis (Complete)

### 1.1 Unused/Truly Useless Fields

| Field | Status | Evidence | Action |
|-------|--------|----------|--------|
| `stageStatus` | Never updated | Always `{}` in logs | ❌ **Remove** |
| `updated_steps` | Defined but unused | No usage in codebase | ❌ **Remove** |
| `checklist` | Never used | Always empty `{}` | ❌ **Remove** |
| `thinking` | Not in payload | Only used internally | ❌ **Remove from payload** |

### 1.2 Naming Confusion (Need Rename)

| Old Name | Issue | New Name |
|----------|-------|----------|
| `step_index` | It's an ID, not index | `current_step_id` |
| `stage_id` | Not clear it's "current" | `current_stage_id` |
| `state` | Overloaded term | `context` |
| `toDoList` | camelCase | `todo_list` |
| `shotType` | Unclear | `content_type` |

### 1.3 Missing Critical Fields (Previously Overlooked!)

| Field | Location | Importance | Issue |
|-------|----------|------------|-------|
| `behavior_id` | WorkflowContext | ⭐⭐⭐⭐⭐ | **Not in payload!** Behavior tracking missing |
| `behavior_iteration` | - | ⭐⭐⭐⭐ | **Not tracked!** Can't count behaviors |
| `current_behavior_actions` | WorkflowContext | ⭐⭐⭐⭐ | Internal only, needs consideration |
| `is_section` | ActionMetadata | ⭐⭐⭐⭐⭐ | **Critical!** Content organization |
| `section_id` | ActionMetadata | ⭐⭐⭐⭐ | **Missing!** Can't track sections |
| `section_number` | ActionMetadata | ⭐⭐⭐ | **Missing!** Lose section order |
| `todo_list` | Context | ⭐⭐⭐⭐⭐ | **Underestimated!** Drives behavior |
| `section_progress` | - | ⭐⭐⭐⭐ | **Missing!** Can't track content |

---

## 2. Execution Hierarchy (Critical Understanding)

### 2.1 The REAL Hierarchy

```
Workflow
  │
  └─ Stage (e.g., chapter_0_planning)
      │
      └─ Step (e.g., section_1_design_workflow)
          │
          └─ Behavior (one API round-trip) ⭐ THIS WAS MISSING!
              │
              └─ Action (add, execute, update, etc.)
                  │
                  └─ Section (optional content marker)
```

**Key Insight**: One Step ≠ One API call. One Step = **Multiple Behaviors**.

### 2.2 Behavior Loop Mechanism

```
Step Execution Loop:
  │
  ┌─────────────────────────────────────┐
  │  1. Fetch Behavior Actions          │
  │     GET /v1/actions                  │
  │     ← Returns: List[Action]          │
  │                                      │
  │  2. Execute Actions Locally          │
  │     • add_section                    │
  │     • add_content                    │
  │     • execute_code                   │
  │                                      │
  │  3. Send Feedback                    │
  │     POST /v1/reflection              │
  │     → Sends: execution results       │
  │     ← Returns: {targetAchieved: bool}│
  │                                      │
  │  4. Check Target                     │
  │     IF targetAchieved == false:      │
  │        └─→ LOOP BACK (more behaviors)│
  │     ELSE:                             │
  │        └─→ Step Complete             │
  └─────────────────────────────────────┘
```

**Why this matters**:
- Behavior state MUST be tracked in payload
- Server decides how many behaviors needed
- TodoList guides what each behavior does

### 2.3 Section Organization

**Sections structure notebook content**:

```json
{
  "action": "add",
  "content_type": "text",
  "content": "## Section 2: Data Loading",
  "metadata": {
    "is_section": true,
    "section_id": "data_loading",
    "section_number": 2
  }
}
```

**Purpose**:
- Create structured, chapter-based reports
- Track content completion
- Enable navigation in UI
- Guide behavior generation

---

## 3. POMDP Mapping (Corrected)

### 3.1 Server (Hidden State)

```
Server maintains:
  ├─ Complete Workflow Template
  │   ├─ All stages and steps
  │   └─ Expected sections per step
  │
  ├─ Behavior Generation Strategy
  │   ├─ How many behaviors needed per step
  │   ├─ What each behavior accomplishes
  │   └─ Completion criteria (targetAchieved)
  │
  └─ Content Organization
      ├─ Section templates
      ├─ Section ordering
      └─ Validation rules
```

### 3.2 Client (Belief State)

```
Client observes and maintains:
  ├─ Current Position
  │   ├─ current_stage_id
  │   ├─ current_step_id
  │   ├─ behavior_id          ⭐ NEW
  │   └─ behavior_iteration   ⭐ NEW
  │
  ├─ Execution Context
  │   ├─ variables (data state)
  │   ├─ todo_list (what's left)
  │   ├─ effects (results history)
  │   ├─ section_progress     ⭐ NEW
  │   └─ notebook (content)
  │
  └─ Local Execution
      ├─ current_behavior_actions (queue)
      ├─ current_action_index (progress)
      └─ execution_results
```

### 3.3 Communication Protocol

```
Request (Client → Server):
  └─ Observation
      ├─ Location (stage/step/behavior)
      ├─ Context (variables/todo/sections)
      └─ Behavior Feedback (execution results)

Response (Server → Client):
  └─ Decision
      ├─ Behavior (id, target, actions)
      ├─ Transition (next stage/step if needed)
      ├─ Context Update (variables/todo/sections)
      └─ Control (continue_behaviors, target_achieved)
```

---

## 4. Optimized Payload Structure (Complete)

### 4.1 Request Payload (Client → Server)

```json
{
  "observation": {
    "location": {
      "current_stage_id": "chapter_3_data_insight",
      "current_step_id": "section_1_workflow_initialization",

      // ⭐ NEW: Behavior tracking
      "behavior_id": "behavior_003",
      "behavior_iteration": 3
    },

    "context": {
      "variables": {
        "csv_file_path": "AmesHousing.csv",
        "problem_description": "请帮我训练一个模型预测房价",
        "data_loaded": true
      },

      // ⭐ CRITICAL: Guides behavior generation
      "toDoList": [
        "Section 2: Current Data State Assessment",
        "Section 3: Variable Definition",
        "Section 4: EDA Summary"
      ],

      "effects": {
        "current": [],
        "history": [
          {"action": "data_load", "result": "success"}
        ]
      },

      // ⭐ NEW: Section organization
      "section_progress": {
        "current_section_id": "data_loading",
        "current_section_number": 2,
        "completed_sections": ["introduction", "data_loading"],
        "total_expected": 5
      },

      "notebook": {
        "title": "Chapter 3: Data Insight Acquisition",
        "cells": [
          {
            "id": "cell_001",
            "type": "markdown",
            "content": "## Section 1: Introduction",
            "metadata": {
              "is_section": true,
              "section_id": "introduction",
              "section_number": 1
            }
          },
          {
            "id": "cell_002",
            "type": "code",
            "content": "import pandas as pd\ndata = pd.read_csv('AmesHousing.csv')"
          }
        ]
      }
    }
  },

  // ⭐ NEW: Behavior execution feedback
  "behavior_feedback": {
    "behavior_id": "behavior_002",
    "actions_executed": 5,
    "actions_succeeded": 5,
    "actions_failed": 0,
    "last_action_result": "success",
    "execution_time_ms": 1234,
    "sections_added": 1,
    "cells_added": 3,
    "code_cells_executed": 1
  },

  "options": {
    "stream": true,
    "include_workflow_segment": false
  }
}
```

**Size Comparison**:
- Old format: ~4.5KB
- New format: ~3.8KB (removed waste, added structure)
- Net: 15% reduction + better organization

### 4.2 Response Payload (Server → Client)

```json
{
  // ⭐ NEW: Behavior metadata
  "behavior": {
    "id": "behavior_004",
    "iteration": 4,
    "target": "Complete Section 2: Current Data State Assessment",
    "priority": "high"
  },

  "actions": [
    {
      "type": "add_content",
      "content_type": "text",
      "content": "## Section 2: Current Data State Assessment",
      "metadata": {
        // ⭐ Section markers
        "is_section": true,
        "section_id": "current_data_state",
        "section_number": 2,
        "belongs_to_chapter": "chapter_3"
      }
    },
    {
      "type": "add_content",
      "content_type": "text",
      "content": "Let's examine the current state of our data...",
      "metadata": {
        "belongs_to_section": "current_data_state"
      }
    },
    {
      "type": "add_content",
      "content_type": "code",
      "content": "print(data.shape)\nprint(data.dtypes)",
      "metadata": {
        "belongs_to_section": "current_data_state",
        "should_execute": true
      }
    }
  ],

  "transition": {
    "strategy": "server_controlled",

    // Stage/Step level (null = stay current)
    "next_stage_id": null,
    "next_step_id": null,

    // ⭐ NEW: Behavior level control
    "continue_behaviors": true,
    "target_achieved": false,
    "reason": "More analysis needed for Section 3",

    "workflow_update": null
  },

  "context_update": {
    "variables": {
      "data_shape": "(2930, 82)",
      "current_section": "current_data_state"
    },

    // ⭐ NEW: TodoList operations
    "todo_list_update": {
      "operation": "remove",
      "items": ["Section 2: Current Data State Assessment"]
    },

    // ⭐ NEW: Section progress
    "section_progress": {
      "current_section_id": "variable_definition",
      "current_section_number": 3,
      "completed_sections": ["introduction", "data_loading", "current_data_state"]
    }
  },

  "metadata": {
    "target_achieved": false,
    "step_complete": false,
    "stage_complete": false,
    "actions_count": 3,
    "estimated_remaining_behaviors": 2,
    "confidence": 0.85
  }
}
```

---

## 5. Field Renaming & New Fields

### 5.1 Renames (Python Conventions)

| Old | New | Category |
|-----|-----|----------|
| `step_index` | `current_step_id` | Position |
| `stage_id` | `current_stage_id` | Position |
| `state` | `context` | Semantic |
| `toDoList` | `todo_list` | Naming |
| `targetAchieved` | `target_achieved` | Naming |
| `shotType` | `content_type` | Semantic |
| `updated_workflow` | `workflow_update` | Consistency |
| `nextStageId` | `next_stage_id` | Naming |

### 5.2 New Fields (Critical Additions)

| Field | Type | Location | Purpose |
|-------|------|----------|---------|
| `behavior_id` | string | location | Track behavior instance |
| `behavior_iteration` | int | location | Count behaviors in step |
| `section_progress` | object | context | Track content structure |
| `behavior_feedback` | object | request | Execution results |
| `continue_behaviors` | bool | transition | Server control |
| `todo_list_update` | object | context_update | List operations |
| `is_section` | bool | metadata | Mark sections |
| `section_id` | string | metadata | Section identifier |
| `section_number` | int | metadata | Section order |

### 5.3 Removed Fields

| Field | Reason |
|-------|--------|
| `stageStatus` | Never updated, always `{}` |
| `checklist` | Never used, always empty |
| `thinking` | Internal only, not in API |
| `updated_steps` | Defined but never used |

---

## 6. Implementation Plan (Updated)

### Phase 1: Field Renaming + Compatibility (Days 1-2)
- Create `PayloadAdapter` with backward compatibility
- Rename fields internally
- Add deprecation warnings
- **Files**: `utils/payload_adapter.py`, `models/action.py`, `stores/ai_context_store.py`

### Phase 2: Add Behavior & Section Support (Days 3-5) ⭐ NEW
- Add `behavior_id` and `behavior_iteration` to `WorkflowContext`
- Create `SectionProgress` dataclass
- Add `behavior_feedback` to request payload
- Update `ActionMetadata` with section fields
- **Files**: `core/context.py`, `models/action.py`, `utils/api_client.py`

### Phase 3: Remove Unused Fields (Day 6)
- Remove `stageStatus`, `checklist`, `thinking`
- Update context compressor
- Clean up API logger
- **Files**: `stores/ai_context_store.py`, `utils/context_compressor.py`, `utils/api_logger.py`

### Phase 4: Payload Structure Optimization (Days 7-9)
- Implement new request/response structure
- Add `observation` wrapper
- Add `behavior` block to response
- Add `transition` with behavior control
- **Files**: `utils/api_client.py`, `utils/payload_adapter.py`

### Phase 5: Server-Controlled Navigation + Behavior Loop (Days 10-13) ⭐ CRITICAL
- Parse `transition.continue_behaviors`
- Handle `behavior.target`
- Implement `todo_list_update` operations
- Update `section_progress` tracking
- Server transition logic
- **Files**: `core/state_machine.py`, `stores/script_store.py`

### Phase 6: Testing (Days 14-16)
- Unit tests for behavior tracking
- Section organization tests
- TodoList operation tests
- Integration tests
- Performance tests

### Phase 7: Gradual Deployment (Days 17-20)
```
Week 1: All flags OFF, monitor
Week 2: CLEAN_UNUSED_FIELDS=true
Week 3: USE_NEW_PAYLOAD_FORMAT=true
Week 4: SERVER_CONTROLLED_NAVIGATION=true
Week 5: BEHAVIOR_TRACKING=true ⭐ NEW
```

---

## 7. Benefits (Updated)

### Technical Benefits
- ✅ 15% payload size reduction
- ✅ Zero sync issues (server-controlled)
- ✅ **Proper behavior tracking**
- ✅ **Structured content organization**
- ✅ POMDP-aligned architecture

### Content Quality Benefits ⭐ NEW
- ✅ **Section-based reports**
- ✅ **Clear content structure**
- ✅ **Progress tracking per section**
- ✅ **Guided content generation (todo_list)**

### Maintainability Benefits
- ✅ Cleaner code (removed unused)
- ✅ **Clear behavior lifecycle**
- ✅ Better testability
- ✅ Self-documenting structure

---

## 8. Risk Assessment (Updated)

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking changes | High | High | Backward compatibility layer |
| Behavior tracking bugs | Medium | High | Extensive testing + rollback |
| Section organization issues | Medium | Medium | Validation + fallback |
| TodoList sync problems | Low | Medium | Server authority |
| Performance regression | Low | Low | Profiling + benchmarks |

---

## 9. Success Criteria (Updated)

- [ ] Payload size reduced by >10%
- [ ] All unused fields removed
- [ ] 100% snake_case naming
- [ ] Zero client-server sync issues
- [ ] **Behavior tracking functional**
- [ ] **Section organization working**
- [ ] **TodoList-driven generation**
- [ ] Full test coverage (>90%)
- [ ] Server controls 100% of transitions

---

## 10. Reference Documents

1. **MISSING_FIELDS_ANALYSIS.md** - Detailed behavior & section analysis
2. **IMPLEMENTATION_GUIDE.md** - Code examples (to be updated)
3. **BEFORE_AFTER_COMPARISON.md** - Visual comparisons (to be updated)
4. **MIGRATION_CHECKLIST.md** - Step-by-step checklist (to be updated)

---

**Document Version**: 2.0 (Complete)
**Last Updated**: 2025-10-28
**Critical Changes**: Added Behavior & Section support
**Status**: Ready for Implementation
