# Notebook-BCC Documentation

Welcome to the Notebook-BCC documentation center. This guide will help you navigate the documentation based on your role and needs.

---

## 📚 Documentation Structure

```
docs/
├── README.md                    # This file - documentation index
│
├── protocols/                   # Core protocol specifications (4 files)
│   ├── STATE_MACHINE.md        # State machine FSM protocol
│   ├── OBSERVATION.md          # POMDP observation structure
│   ├── API.md                  # API interaction protocol
│   └── ACTION.md               # Action specifications
│
├── guides/                      # User guides (2 files)
│   ├── CLI_USAGE.md            # Complete CLI usage guide
│   └── QUICK_REFERENCE.md      # Quick reference cheat sheet
│
└── examples/                    # Example workflows and payloads
    └── ames_housing/           # Ames housing price prediction example
```

---

## 🎯 Quick Navigation

### For Backend Developers

**Building the Planning/Generating API?**

1. **[OBSERVATION Protocol](./protocols/OBSERVATION.md)** - Start here
   - Understand the complete observation structure
   - Learn about progress tracking (stages/steps/behaviors)
   - Understand context filtering and variable management

2. **[API Protocol](./protocols/API.md)** - Then read this
   - Implement Planning API endpoints
   - Implement Generating API endpoints
   - Handle streaming responses
   - Apply context filters

3. **[ACTION Protocol](./protocols/ACTION.md)** - Finally this
   - Generate 7 types of actions for Generating API
   - Understand action execution flow

### For Frontend/Client Developers

**Building the workflow execution client?**

1. **[STATE_MACHINE Protocol](./protocols/STATE_MACHINE.md)** - Start here
   - Understand FSM states and transitions
   - Learn event-driven state changes
   - Understand the "Planning First" protocol

2. **[OBSERVATION Protocol](./protocols/OBSERVATION.md)** - Then this
   - Build observation payloads for API calls
   - Track workflow progress
   - Manage variables and effects

3. **[API Protocol](./protocols/API.md)** - Next
   - Call Planning/Generating APIs correctly
   - Handle API responses
   - Apply context updates

4. **[ACTION Protocol](./protocols/ACTION.md)** - Finally
   - Execute actions received from APIs
   - Update notebook state
   - Track execution effects

### For CLI Users

**Using Notebook-BCC from command line?**

- **[CLI Usage Guide](./guides/CLI_USAGE.md)** - Complete reference
  - `test-request` - Preview API requests
  - `send-api` - Send API requests
  - `apply-transition` - Apply state transitions
  - REPL commands

- **[Quick Reference](./guides/QUICK_REFERENCE.md)** - Cheat sheet
  - Common commands
  - Quick examples

### For New Contributors

**Just getting started?**

1. Browse **[examples/ames_housing/](./examples/ames_housing/)** - See real workflow examples
2. Read **[STATE_MACHINE Protocol](./protocols/STATE_MACHINE.md)** - Understand the architecture
3. Read **[CLI Usage Guide](./guides/CLI_USAGE.md)** - Try the CLI tools

---

## 📖 Protocol Documents

### [State Machine Protocol](./protocols/STATE_MACHINE.md)

**The workflow control system**

Defines FSM states, events, and transition rules:
- 15 FSM states (IDLE → STAGE_RUNNING → STEP_RUNNING → BEHAVIOR_RUNNING → ...)
- 23 workflow events (START_WORKFLOW, START_STEP, COMPLETE_BEHAVIOR, ...)
- 40+ state transition rules
- "Planning First" protocol - when to call Planning API
- Client navigation responsibilities

**Key Concepts:**
- State hierarchy: `idle → stage → step → behavior → action`
- Mixed control: Planning API (decisions) + Client (navigation)
- Event-driven transitions

---

### [Observation Protocol](./protocols/OBSERVATION.md)

**The POMDP observation structure**

Complete specification of the observation payload sent to APIs:
- **Location**: Current position in workflow (stage_id, step_id, behavior_id)
- **Progress**: Hierarchical tracking (stages/steps/behaviors)
- **Goals**: Workflow objectives and focus
- **Context**: Variables, effects, notebook state, FSM state

**Key Features:**
- Three-state output tracking (expected/produced/in_progress)
- Temporary variable promotion rules
- Context filter protocol
- Effect tracking (code execution outputs)

---

### [API Protocol](./protocols/API.md)

**Planning and Generating API specifications**

How to call and implement the two core APIs:
- **Planning API** - Makes decisions (when to start/complete stages/steps)
- **Generating API** - Creates actions (notebook content generation)
- **Reflecting API** - Provides behavior feedback

**Request/Response Formats:**
- Observation payload structure
- Planning response (targetAchieved, transition, context_update)
- Generating response (7 action types, streaming)
- Context filter usage

---

### [Action Protocol](./protocols/ACTION.md)

**The 7 Generating Actions**

Detailed specifications for actions returned by Generating API:
1. **ADD_ACTION** - Add markdown/code/hybrid cells
2. **EXEC_CODE** - Execute code cells
3. **IS_THINKING** / **FINISH_THINKING** - Show thinking process
4. **NEW_CHAPTER** / **NEW_SECTION** - Structure markers
5. **UPDATE_TITLE** - Update notebook title

**Also Covers:**
- POMDP design principles
- Shot types (one-shot, multi-shot)
- Deprecated actions (moved to Planning API)
- Error handling

---

## 📘 User Guides

### [CLI Usage Guide](./guides/CLI_USAGE.md)

**Complete CLI reference**

All CLI commands with detailed examples:
- **`test-request`** - Preview API requests without sending (auto-infers API type)
- **`send-api`** - Send actual API requests (auto-infers API type)
- **`apply-transition`** - Apply transitions offline
- **`resume`** - Resume workflow from state file
- **REPL commands** - Interactive workflow shell

**Includes:**
- Parameter explanations
- Output examples
- Troubleshooting guide
- Use cases and workflows

---

### [Quick Reference](./guides/QUICK_REFERENCE.md)

**Command cheat sheet**

Quick lookup for common commands and patterns:
- Essential CLI commands
- REPL commands
- Common workflows
- Keyboard shortcuts

---

## 💡 Examples

### [Ames Housing Example](./examples/ames_housing/)

**Complete workflow example**

Real-world example showing:
- Full workflow definition (3 stages, multiple steps)
- State files for all FSM states
- Transition XML examples
- Planning/Generating API payloads
- Variable evolution through workflow

**Use this to:**
- Understand complete workflow flow
- Test your API implementation
- Generate test cases
- Debug state transitions

---

## 🔑 Core Concepts

### FSM States
The workflow progresses through hierarchical states:
```
IDLE
  → STAGE_RUNNING
    → STEP_RUNNING
      → BEHAVIOR_RUNNING
        → ACTION_RUNNING
          → ACTION_COMPLETED
```

See: [STATE_MACHINE Protocol](./protocols/STATE_MACHINE.md)

### Observation
Complete POMDP observation sent to APIs containing:
- **location**: Where we are (stage/step/behavior)
- **progress**: What's completed, current, remaining
- **goals**: What we're trying to achieve
- **context**: Variables, effects, notebook state

See: [OBSERVATION Protocol](./protocols/OBSERVATION.md)

### Planning First Protocol
Most state transitions require Planning API to decide next steps:
- **STAGE_RUNNING** → Planning decides which step to start
- **STEP_RUNNING** → Planning checks if target achieved
- **BEHAVIOR_COMPLETED** → Planning decides if behavior succeeded
- **STEP_COMPLETED** → Planning decides if stage is complete

See: [API Protocol](./protocols/API.md)

### Actions
7 types of actions generated by Generating API:
- Content creation (ADD_ACTION)
- Code execution (EXEC_CODE)
- Thinking process (IS_THINKING, FINISH_THINKING)
- Structure markers (NEW_CHAPTER, NEW_SECTION)
- Metadata update (UPDATE_TITLE)

See: [ACTION Protocol](./protocols/ACTION.md)

### Context Updates
Planning API returns context updates to modify:
- `workflow_update` - Update workflow template
- `stage_steps_update` - Update stage steps
- `progress_update` - Update hierarchical focus
- `variables` - Add/modify variables
- `effects` - Update execution effects

See: [API Protocol](./protocols/API.md#context-updates)

---

## 🚀 Getting Started

### Install
```bash
# Clone repository
git clone https://github.com/your-org/notebook-bcc.git
cd notebook-bcc

# Install dependencies
pip install -r requirements.txt
```

### Quick Test
```bash
# Preview a request
python main.py test-request \
  --state-file ./docs/examples/ames_housing/payloads/00_STATE_IDLE.json

# Send an actual request (requires server)
python main.py send-api \
  --state-file ./docs/examples/ames_housing/payloads/00_STATE_IDLE.json

# Start interactive REPL
python main.py repl
```

### Learn More
- Read the [CLI Usage Guide](./guides/CLI_USAGE.md)
- Explore [example workflows](./examples/ames_housing/)
- Review protocol specifications in `protocols/`

---

## 📝 Document Maintenance

### When to Update

**Update [STATE_MACHINE Protocol](./protocols/STATE_MACHINE.md) when:**
- Adding/removing FSM states
- Changing state transition rules
- Modifying event definitions

**Update [OBSERVATION Protocol](./protocols/OBSERVATION.md) when:**
- Changing observation payload structure
- Adding/removing fields in location/progress/context
- Modifying variable or effect tracking rules

**Update [API Protocol](./protocols/API.md) when:**
- Changing API request/response formats
- Adding new API endpoints
- Modifying context update structure

**Update [ACTION Protocol](./protocols/ACTION.md) when:**
- Adding/removing action types
- Changing action payload structure
- Modifying execution behavior

**Update [CLI Usage Guide](./guides/CLI_USAGE.md) when:**
- Adding new CLI commands
- Changing command parameters
- Adding new examples

---

## 🤝 Contributing

When updating documentation:
1. **Keep consistency** - Use the same terminology across all docs
2. **Add examples** - Every concept should have code examples
3. **Cross-reference** - Link to related concepts in other docs
4. **Version updates** - Mark significant changes with dates
5. **Test examples** - Ensure all code examples actually work

---

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/notebook-bcc/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/notebook-bcc/discussions)
- **Documentation**: You're reading it!

---

**Last Updated:** 2025-11-08
**Documentation Version:** 3.0
