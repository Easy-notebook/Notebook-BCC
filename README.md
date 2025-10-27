# Notebook-BCC: Python Workflow System

**Complete Python Implementation of Easy-notebook-advance Frontend Workflow**

## 📋 Overview

Notebook-BCC is a complete Python reimplementation of the TypeScript/React workflow system from Easy-notebook-advance. It replicates the entire state machine, stores, executors, and notebook management system with high fidelity.

### Key Features

- ✅ **State Machine**: Full FSM with hierarchical states (Workflow → Stage → Step → Behavior → Action)
- ✅ **Variable Management**: Context-aware variable storage across workflow steps
- ✅ **TODO List Management**: Task tracking with completion status
- ✅ **Notebook System**: Cell management (code, markdown, thinking cells)
- ✅ **Code Execution**: Remote Jupyter kernel execution via HTTP API
- ✅ **API Integration**: Workflow (`/actions`, `/reflection`) and code execution APIs
- ✅ **Custom Context**: Inject user-defined context into API calls
- ✅ **Step Control**: Limit execution steps, pause/resume (breakpoint debugging)
- ✅ **Start Modes**: Choose reflection (feedback-driven) or generation (action-driven)
- ✅ **Markdown Rendering**: Terminal-friendly markdown display with colors
- ✅ **CLI Interface**: Command-line and interactive REPL modes
- ✅ **Persistence**: Save/load notebooks and export to markdown

## 🏗️ Architecture

```
Notebook-BCC/
├── core/                   # State machine core
│   ├── state_machine.py    # FSM implementation
│   ├── states.py           # State definitions
│   ├── events.py           # Event definitions
│   └── context.py          # Execution context
├── stores/                 # State management stores
│   ├── ai_context_store.py # Variables, TODOs, effects
│   ├── pipeline_store.py   # Workflow structure
│   ├── script_store.py     # Action management
│   └── notebook_store.py   # Cell management
├── models/                 # Data models
│   ├── workflow.py         # Workflow structure
│   ├── action.py           # Action definitions
│   └── cell.py             # Notebook cells
├── executors/              # Execution engines
│   ├── code_executor.py    # Python code execution
│   └── action_executor.py  # Action orchestration
├── notebook/               # Notebook management
│   ├── notebook_manager.py # File operations
│   ├── markdown_renderer.py# Markdown display
│   └── cell_renderer.py    # Cell rendering
└── cli/                    # Command-line interface
    ├── commands.py         # CLI commands
    └── repl.py             # Interactive REPL
```

## 🚀 Quick Start

### Installation

```bash
cd Notebook-BCC

# Install dependencies
pip install -r requirements.txt

# Or install manually
pip install requests aiohttp  # Required for API communication
pip install numpy pandas matplotlib  # Optional, for data science features
```

### Configuration

Notebook-BCC communicates with two backend services:
1. **Backend Jupyter Kernel** (default: `http://localhost:8000`) - Executes Python code
2. **DSLC Workflow API** (default: `http://localhost:8001`) - Manages workflow logic

#### Option 1: Environment Variables

Create a `.env` file from the template:

```bash
cp .env.example .env
# Edit .env with your settings
```

Example `.env`:
```bash
BACKEND_BASE_URL=http://localhost:8000
DSLC_BASE_URL=http://localhost:8001
NOTEBOOK_ID=  # Optional: existing notebook session ID
```

#### Option 2: Command-Line Arguments

Override configuration at runtime:

```bash
python main.py \
  --backend-url http://localhost:9000 \
  --dslc-url http://localhost:9001 \
  --notebook-id abc123 \
  start --problem "Analyze data"
```

Configuration precedence: **Command-line args > Environment variables > Defaults**

### Advanced Features

#### 1. Custom Context Injection

Inject custom data into API calls:

```bash
# Via JSON string
python main.py --custom-context '{"user":"alice","priority":"high"}' start

# Via file
python main.py --custom-context context.json start
```

#### 2. Step Limits & Breakpoints

Control execution for debugging:

```bash
# Limit to 10 steps
python main.py --max-steps 10 start --problem "Debug workflow"

# Interactive mode (pause at limits)
python main.py --max-steps 5 --interactive start
```

#### 3. Start Mode Selection

Choose workflow initiation strategy:

```bash
# Generation mode (default): Direct action execution
python main.py --start-mode generation start

# Reflection mode: Check goal completion first
python main.py --start-mode reflection start
```

**Reflection vs Generation:**
- **Generation**: Calls `/actions` API → executes actions immediately
- **Reflection**: Calls `/reflection` API first → skips actions if goal achieved

📖 **See [ADVANCED_USAGE.md](ADVANCED_USAGE.md) for detailed examples and best practices.**

### Usage

#### 1. Command-Line Interface

```bash
# Start a new workflow
python main.py start --problem "Analyze dataset" --context "Sales data Q4 2024"

# Start with custom backend services
python main.py --backend-url http://localhost:9000 start --problem "Data analysis"

# Use existing notebook session
python main.py --notebook-id abc123 start --problem "Continue analysis"

# Show workflow status
python main.py status

# List notebooks
python main.py list

# Show notebook content
python main.py show --notebook notebook_20240101_120000.json

# Export to markdown
python main.py export notebook_20240101_120000.json --output analysis.md
```

#### 2. Interactive REPL

```bash
# Start the REPL
python main.py repl
```

Inside the REPL:

```
(workflow) > start My Analysis Task
(workflow) > status
(workflow) > var set dataset_path "/data/analysis.csv"
(workflow) > todo add "Load dataset"
(workflow) > exec print("Hello from Python!")
(workflow) > save my_notebook.json
(workflow) > quit
```

### Example Workflow

```python
from Notebook-BCC import (
    WorkflowStateMachine,
    PipelineStore,
    ScriptStore,
    NotebookStore,
    AIPlanningContextStore,
    CodeExecutor
)

# Initialize stores
pipeline_store = PipelineStore()
notebook_store = NotebookStore()
ai_context_store = AIPlanningContextStore()
code_executor = CodeExecutor()

script_store = ScriptStore(
    notebook_store=notebook_store,
    ai_context_store=ai_context_store,
    code_executor=code_executor
)

# Create state machine
state_machine = WorkflowStateMachine(
    pipeline_store=pipeline_store,
    script_store=script_store,
    ai_context_store=ai_context_store
)

# Initialize workflow
workflow = pipeline_store.initialize_workflow({
    'problem_name': 'Data Analysis',
    'user_goal': 'Analyze sales data',
})

# Start execution
pipeline_store.start_workflow_execution(state_machine)

# Check status
print(state_machine.get_state_info())
```

## 🎯 State Machine

### States Hierarchy

```
IDLE
  ↓ START_WORKFLOW
STAGE_RUNNING
  ↓ START_STEP
STEP_RUNNING
  ↓ START_BEHAVIOR
BEHAVIOR_RUNNING
  ↓ START_ACTION
ACTION_RUNNING
  ↓ COMPLETE_ACTION
ACTION_COMPLETED
  ↓ (more actions or COMPLETE_BEHAVIOR)
BEHAVIOR_COMPLETED
  ↓ (feedback check)
STEP_COMPLETED
  ↓ (next step or COMPLETE_STAGE)
STAGE_COMPLETED
  ↓ (next stage or COMPLETE_WORKFLOW)
WORKFLOW_COMPLETED
```

### Events

- **START_***: Start workflow/stage/step/behavior/action
- **COMPLETE_***: Complete current level
- **NEXT_***: Move to next sibling at same level
- **UPDATE_***: Request workflow/step updates
- **FAIL/CANCEL/RESET**: Control events

## 📝 Notebook Features

### Cell Types

- **Markdown**: Text content with markdown formatting
- **Code**: Python code cells with execution
- **Thinking**: AI thinking display cells
- **Outcome**: Result display cells
- **Error**: Error display cells

### Code Execution

```python
# Execute code in isolated namespace
result = code_executor.execute("""
import pandas as pd
df = pd.DataFrame({'A': [1, 2, 3]})
print(df)
""")

# Access namespace
variables = code_executor.get_all_variables()
```

## 🎨 Rendering

### Markdown Rendering

Supports:
- Headers (# ## ###)
- Bold (**text**)
- Italic (*text*)
- Inline code (`code`)
- Links ([text](url))
- ANSI colors for terminal

### Cell Rendering

- Color-coded cell types
- Line numbers (optional)
- Output display
- Error highlighting

## 💾 Persistence

### Save Notebook

```python
from notebook import NotebookManager

manager = NotebookManager()

# Save notebook
path = manager.save_notebook(notebook_data, filename="analysis.json")

# Load notebook
notebook = manager.load_notebook("analysis.json")

# Export to markdown
md_path = manager.export_to_markdown(notebook_data)
```

## 🔧 Advanced Features

### Variable Management

```python
# Add variables
ai_context_store.add_variable("dataset_path", "/data/sales.csv")
ai_context_store.add_variable("start_date", "2024-01-01")

# Get variables
path = ai_context_store.get_variable("dataset_path")

# List all
context = ai_context_store.get_context()
print(context.variables)
```

### TODO List

```python
# Add TODOs
ai_context_store.add_to_do_list("Load dataset")
ai_context_store.add_to_do_list("Clean data")
ai_context_store.add_to_do_list("Train model")

# Check completion
if ai_context_store.is_cur_step_completed():
    print("All tasks done!")
```

### Effect Tracking

```python
# Add execution effects
ai_context_store.add_effect("Loaded 1000 rows")
ai_context_store.add_effect("Missing values: 5")

# Get effects
context = ai_context_store.get_context()
print(context.effect['current'])
```

## 📚 API Reference

### State Machine

```python
# Start workflow
state_machine.start_workflow(stage_id="stage_1", step_id="step_1")

# Manual transitions
state_machine.transition(WorkflowEvent.START_STEP)

# Get status
info = state_machine.get_state_info()

# Reset
state_machine.reset()
```

### Script Store

```python
# Add action
action = ScriptAction(
    id="action_1",
    type="code",
    content="print('Hello')"
)
script_store.add_action(action)

# Execute action
step = ExecutionStep(action="exec", codecell_id="action_1")
script_store.exec_action(step)
```

### Notebook Store

```python
# Add cell
cell_data = {
    'id': 'cell_1',
    'type': 'code',
    'content': 'print("Hello")'
}
notebook_store.add_cell(cell_data)

# Get cells
cells = notebook_store.cells

# Export
notebook_data = notebook_store.to_dict()
```

## 🔍 Debugging

### Enable Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Check State

```bash
(workflow) > status
```

### View History

```python
# Get execution history
history = state_machine.history
for entry in history:
    print(f"{entry.from_state} -> {entry.to_state} via {entry.event}")
```

## 🛠️ Development

### Running Tests

```bash
# Run example
python examples/simple_workflow.py

# Test CLI
python main.py repl
```

### Adding Custom Actions

```python
# Extend ACTION_TYPES in script_store.py
ACTION_TYPES['MY_ACTION'] = 'my_action'

# Add handler in exec_action
elif action_type == ACTION_TYPES['MY_ACTION']:
    # Your custom logic here
    pass
```

## 📖 Comparison with Frontend

| Feature | Frontend (TS) | Backend (Python) |
|---------|--------------|------------------|
| State Machine | ✅ Zustand | ✅ Class-based |
| Stores | ✅ Zustand | ✅ Class-based |
| Events | ✅ Enum | ✅ Enum |
| States | ✅ Enum | ✅ Enum |
| Actions | ✅ TypeScript | ✅ Python |
| Cells | ✅ React | ✅ Terminal |
| Persistence | ✅ Browser | ✅ File System |
| Rendering | ✅ HTML/CSS | ✅ ANSI/Terminal |

## 🤝 Contributing

This is a faithful Python recreation of the TypeScript workflow system. Contributions should maintain compatibility with the frontend design patterns.

## 📄 License

[Your License Here]

## 👥 Authors

- **Original Frontend**: Hu Silan
- **Python Implementation**: [Your Name]

## 🙏 Acknowledgments

- Based on Easy-notebook-advance frontend workflow system
- Implements the complete state machine and execution model
- Maintains architectural fidelity with the TypeScript original
