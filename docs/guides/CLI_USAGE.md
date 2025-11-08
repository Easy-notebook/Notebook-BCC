# CLI Complete Usage Guide

## 📖 Overview

This comprehensive guide covers all CLI commands for Notebook-BCC, including state file operations, API testing, and workflow management.

## 🎯 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Preview request without sending (auto-infers API type from state)
python main.py test-request --state-file state.json

# Send actual API request (auto-infers API type from state)
python main.py send-api --state-file state.json

# Apply transition to update state
python main.py apply-transition \
  --state-file state.json \
  --transition-file transition.xml \
  --output updated_state.json
```

---

## 📋 CLI Commands

### 1. `test-request` - Preview API Request

Preview and export API request payloads **without sending** them to the server.

**Basic Usage:**
```bash
# Auto-infer API type from FSM state
python main.py test-request --state-file state.json

# Specify API type explicitly
python main.py test-request \
  --state-file state.json \
  --api-type planning

# Export to file (pretty format)
python main.py test-request \
  --state-file state.json \
  --output request_payload.json \
  --format pretty

# Export compact JSON
python main.py test-request \
  --state-file state.json \
  --output compact_request.json \
  --format json
```

**Parameters:**
- `--state-file <path>`: Path to state JSON file (required)
- `--api-type <type>`: API type - planning, generating, or reflecting (optional, auto-inferred if not specified)
- `--output <file>`: Export request payload to file (optional)
- `--format <format>`: Output format - json or pretty (default: pretty) (optional)

**Features:**
- 🔍 Preview exact request payload before sending
- 💾 Export payload to file for testing
- 📊 View request statistics
- 🎨 Rich syntax highlighting
- ✅ Safe - never sends to server
- 🤖 Auto-infers API type from FSM state (IDLE → planning, STEP_RUNNING → planning, etc.)

**Auto-Inference Logic:**
- **IDLE** → `planning` (start workflow)
- **STAGE_RUNNING** → `planning` (start step)
- **STEP_RUNNING** → `planning` (check target achieved)
- **BEHAVIOR_RUNNING** → `reflecting` (behavior feedback)
- **Default** → `planning`

**Output Example:**
```
📂 Loading state from: ./state.json

🤖 Auto-inferred API type: planning
   (You can override with --api-type)

======================================================================
 REQUEST PREVIEW (Will NOT be sent)
======================================================================

╭───────────────────────────────  API Request ───────────────────────────────╮
│ API Type     │ PLANNING                        │
│ URL          │ http://localhost:28600/planning │
│ Payload Size │ 1115 bytes (1.09 KB)            │
╰──────────────────────────────────────────────────────────────────────────────╯

======================================================================
 REQUEST PAYLOAD
======================================================================
{
  "observation": {
    "location": {...},
    "context": {...}
  },
  "options": {"stream": false}
}

======================================================================
📊 REQUEST STATISTICS
======================================================================
API Type:       PLANNING
Payload Size:   1731 bytes (1.69 KB)
Variables:      2

💾 Request payload exported to: request.json

======================================================================
✅ Request preview completed (NOT sent to server)
======================================================================

To actually send this request, use:
  python main.py send-api --state-file ./state.json
```

**Use Cases:**
- 🔍 Debug request format before sending
- 📝 Export payload for curl/Postman testing
- 📚 Generate documentation examples
- ✅ Validate state file structure
- 🧪 Test API integration offline

---

### 2. `send-api` - Send API Request

Send actual API requests (planning, generating, reflecting) to the server.

**Basic Usage:**
```bash
# Auto-infer API type from FSM state
python main.py send-api --state-file state.json

# Specify API type explicitly
python main.py send-api \
  --state-file state.json \
  --api-type planning

# Send with streaming (for generating API)
python main.py send-api \
  --state-file state.json \
  --api-type generating \
  --stream

# Save response to file
python main.py send-api \
  --state-file state.json \
  --api-type reflecting \
  --output response.json
```

**Parameters:**
- `--state-file <path>`: Path to state JSON file (required)
- `--api-type <type>`: API type - planning, generating, or reflecting (optional, auto-inferred if not specified)
- `--output <file>`: Save response to file (optional)
- `--stream`: Use streaming for generating API (optional)

**Output Example:**
```
📂 Loading state from: ./state.json

🤖 Auto-inferred API type: planning
   (You can override with --api-type)

╭───────────────────  API Request ───────────────────────╮
│ API Type      PLANNING                                    │
│ URL           http://localhost:28600/planning             │
│ Stage ID      data_existence_establishment                │
│ Step ID       none                                        │
╰───────────────────────────────────────────────────────────╯

⠋ Sending PLANNING API request...

╭───────── ✅ PLANNING API Response Summary ──────────╮
│ Target Achieved      ○ No                           │
│ Continue Behaviors   Yes                            │
╰──────────────────────────────────────────────────────╯

💾 Response saved to: response.json
✅ API request completed successfully
```

---

### 3. `apply-transition` - Apply Transition to State

Apply workflow transition XML responses to state files to generate updated states offline.

**Basic Usage:**
```bash
# Apply START_WORKFLOW transition
python main.py apply-transition \
  --state-file ./state_idle.json \
  --transition-file ./transition_start_workflow.xml \
  --output ./state_stage_running.json

# Apply with pretty format (default)
python main.py apply-transition \
  --state-file state.json \
  --transition-file transition.xml \
  --output updated_state.json \
  --format pretty

# Apply with compact JSON
python main.py apply-transition \
  --state-file state.json \
  --transition-file transition.xml \
  --output updated_state.json \
  --format json
```

**Parameters:**
- `--state-file <path>`: Path to input state JSON file (required)
- `--transition-file <path>`: Path to transition XML file (required)
- `--output <path>`: Output file for updated state JSON (required)
- `--format <format>`: Output format - json or pretty (default: pretty) (optional)

**Features:**
- 🔄 Apply workflow transitions offline without server
- 📊 See before/after state comparison
- 🧪 Test state transformation logic
- 💾 Export updated state to file
- 🎨 Rich display with change summary
- ✅ Validate transition XML format

**Supported Transitions:**
- **START_WORKFLOW** (IDLE → STAGE_RUNNING)
  - Extracts stages from `<stages>` block
  - Updates progress.stages with workflow structure
  - Sets FSM state to STAGE_RUNNING

- **START_STEP** (STAGE_RUNNING → STEP_RUNNING)
  - Extracts steps from `<steps>` block
  - Updates progress.steps with step structure
  - Sets current step_id
  - Updates FSM state to STEP_RUNNING

**Output Example:**
```
📂 Loading state from: ./state_idle.json

 Original State:
╭─────────────────────────  Loaded State Information ──────────────────────────╮
│ Stage ID        │ None                         │
│ Step ID         │ None                         │
│ FSM State       │ IDLE                         │
│ Last Transition │ None                         │
╰──────────────────────────────────────────────────────────────────────────────╯

📄 Loading transition from: ./transition_start_workflow.xml
   ✓ Loaded 5234 bytes

🔄 Applying transition...

✅ Transition Applied Successfully!

 Updated State:
╭─────────────────────────  Loaded State Information ──────────────────────────╮
│ Stage ID        │ data_existence_establishment │
│ Step ID         │ None                         │
│ FSM State       │ STAGE_RUNNING                │
│ Last Transition │ START_WORKFLOW               │
╰──────────────────────────────────────────────────────────────────────────────╯

📊 Changes:
   FSM State: IDLE → STAGE_RUNNING
   Last Transition: None → START_WORKFLOW
   Stage ID: None → data_existence_establishment

💾 Updated state exported to: ./state_stage_running.json
   Format: pretty
   Size: 8234 bytes (8.04 KB)

======================================================================
✅ Transition applied and state exported successfully
======================================================================
```

**Use Cases:**
- 🔄 Test state transitions offline
- 🧪 Validate transition XML structure
- 📊 Debug state transformation logic
- 💾 Generate test states for different scenarios
- 🎯 Chain transitions to simulate workflow progression

**Example Workflow:**
```bash
# 1. Start from IDLE
python main.py apply-transition \
  --state-file 00_STATE_IDLE.json \
  --transition-file 00_Transition_planning_START_WORKFLOW.xml \
  --output 01_STATE_Stage_Running.json

# 2. Start first step
python main.py apply-transition \
  --state-file 01_STATE_Stage_Running.json \
  --transition-file 01_Transition_planning_START_STEP.xml \
  --output 02_STATE_Step_Running.json

# 3. Continue chaining transitions...
```

---

### 4. `resume` - Resume Workflow

Load workflow state from a file and optionally continue execution.

**Basic Usage:**
```bash
# Load state without continuing
python main.py resume --state-file state.json

# Load state and attempt to continue (not fully implemented)
python main.py resume --state-file state.json --continue
```

**Parameters:**
- `--state-file <path>`: Path to state JSON file (required)
- `--continue`: Attempt to continue workflow execution (optional)

---

## 🖥️ REPL Commands

Start the REPL:
```bash
python main.py repl
```

### Available REPL Commands

#### `load_state` - Load State File
```
(workflow) > load_state ./state.json
```

Loads the state file and restores:
- Variables
- Effects (current and history)
- FSM state information
- Workflow position (stage, step, behavior)

#### `test_request` - Preview Request in REPL
```
# Auto-infer API type
(workflow) > test_request

# Specify API type
(workflow) > test_request planning

# Export to file
(workflow) > test_request --output request.json --format pretty
```

**Note:** Must call `load_state` first.

#### `send_api` - Send API in REPL
```
# Auto-infer API type
(workflow) > send_api

# Specify API type
(workflow) > send_api planning

# Use streaming
(workflow) > send_api generating --stream
```

**Note:** Must call `load_state` first.

#### `apply_transition` - Apply Transition in REPL
```
(workflow) > apply_transition ./transition.xml --output ./result.json
(workflow) > apply_transition ./transition.xml --output ./result.json --format json
```

**Features:**
- Automatically chains transitions - loaded state updates after each apply
- Shows before/after comparison
- Displays what changed (FSM state, stage, step)

**Note:** Must call `load_state` first.

---

## 🎨 Rich Display Features

The CLI uses the `rich` library for beautiful terminal output:

- **Panels** - Framed information boxes with titles
- **Tables** - Structured data display
- **Syntax Highlighting** - JSON responses with color
- **Progress Spinners** - Visual feedback during API calls
- **Color Coding** - Status indicators (green=success, red=error, yellow=warning)

### Without Rich Library

If `rich` is not installed, commands fall back to simple text output:

```bash
# Install rich for enhanced display
pip install rich>=13.7.0

# Or use without rich (plain text output)
python main.py send-api --state-file state.json
```

---

## 🔧 Configuration

### API Endpoints

Commands use configured API endpoints from `.env` or command-line args:

```bash
# Override API URLs
python main.py \
  --dslc-url http://custom-server:28600 \
  send-api --state-file state.json
```

### State File Format

State files should follow this structure:

```json
{
  "observation": {
    "location": {
      "current": {
        "stage_id": "stage_name",
        "step_id": "step_name",
        "behavior_id": null,
        "behavior_iteration": null
      },
      "progress": {
        "stages": {...},
        "steps": {...},
        "behaviors": {...}
      },
      "goals": "..."
    }
  },
  "state": {
    "variables": {...},
    "effects": {
      "current": [],
      "history": []
    },
    "notebook": {...},
    "FSM": {
      "state": "STAGE_RUNNING",
      "last_transition": "START_WORKFLOW"
    }
  }
}
```

---

## 🐛 Troubleshooting

### State File Not Found

```bash
❌ Error: State file not found: ./path/to/state.json
```

**Solution:** Check the file path is correct and the file exists.

### Invalid JSON

```bash
❌ Invalid JSON: Expecting property name enclosed in double quotes: line 5 column 3 (char 45)
```

**Solution:** Validate the JSON file:
```bash
cat state.json | python -m json.tool
```

### API Connection Error

```bash
❌ PLANNING API Failed:
   Error: Cannot connect to http://localhost:28600/planning
```

**Solution:**
1. Check if the DSLC server is running
2. Verify the URL with `curl http://localhost:28600/planning -X POST`
3. Override with `--dslc-url`

### No State Loaded (REPL)

```
❌ No state loaded. Use 'load_state <file>' first
```

**Solution:** Call `load_state` before other commands:
```
(workflow) > load_state ./state.json
(workflow) > send_api
```

### Transition XML Parse Error

```bash
❌ Error parsing transition XML: not well-formed (invalid token)
```

**Solution:** Validate XML structure:
```bash
xmllint --noout transition.xml
```

---

## 📚 Complete Examples

### Example 1: Development Workflow

```bash
# 1. Preview request to verify format
python main.py test-request --state-file state.json

# 2. Send actual request
python main.py send-api --state-file state.json

# 3. Apply transition from response
python main.py apply-transition \
  --state-file state.json \
  --transition-file response_transition.xml \
  --output updated_state.json
```

### Example 2: Testing API with curl

```bash
# 1. Export payload
python main.py test-request \
  --state-file state.json \
  --output payload.json \
  --format json

# 2. Test with curl
curl -X POST http://localhost:28600/planning \
  -H "Content-Type: application/json" \
  -d @payload.json
```

### Example 3: REPL Session

```bash
# Start REPL
python main.py repl

# In REPL:
(workflow) > load_state ./state.json
(workflow) > test_request
(workflow) > send_api
(workflow) > apply_transition ./transition.xml --output ./new_state.json
(workflow) > quit
```

### Example 4: Transition Chain

```bash
# Simulate complete workflow offline
python main.py apply-transition \
  --state-file 00_IDLE.json \
  --transition-file t1_start_workflow.xml \
  --output 01_STAGE_RUNNING.json

python main.py apply-transition \
  --state-file 01_STAGE_RUNNING.json \
  --transition-file t2_start_step.xml \
  --output 02_STEP_RUNNING.json
```

---

## 🎯 Use Cases

### 1. API Development & Testing
- Preview requests before implementation
- Export payloads for API testing tools
- Validate request/response formats

### 2. Debugging Workflows
- Load saved states and inspect variables
- Test state transitions offline
- Verify FSM state changes

### 3. Documentation Generation
- Export example payloads for docs
- Generate test cases
- Create tutorial examples

### 4. Integration Testing
- Chain transitions to simulate workflows
- Generate test states for different scenarios
- Validate state transformation logic

---

## 📖 CLI Help

```bash
# Show all commands
python main.py --help

# Show specific command help
python main.py test-request --help
python main.py send-api --help
python main.py apply-transition --help
python main.py resume --help
```

---

## 🔗 Related Documentation

- [Quick Reference](./QUICK_REFERENCE.md) - Command cheat sheet
- [State Machine Protocol](../protocols/STATE_MACHINE.md) - FSM states and transitions
- [API Protocol](../protocols/API.md) - API request/response formats
- [Observation Protocol](../protocols/OBSERVATION.md) - State file structure

---

**Last Updated:** 2025-11-08
