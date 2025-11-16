# Actions Module - Refactored Architecture

## Overview

The actions module has been completely refactored from function-based handlers to a clean, object-oriented class-based system using the decorator pattern.

## Architecture

```
actions/
├── __init__.py                    # Main module with detailed documentation
├── base.py                        # ActionBase class and @action decorator
├── utils.py                       # Shared utilities (content cleaning)
├── content/                       # Content creation actions
│   ├── __init__.py
│   ├── add_action.py             # AddAction, AddTextAction
│   ├── new_chapter_action.py     # NewChapterAction
│   ├── new_section_action.py     # NewSectionAction
│   ├── new_step_action.py        # NewStepAction
│   └── comment_result_action.py  # CommentResultAction
├── code/                          # Code execution actions
│   ├── __init__.py
│   ├── exec_code_action.py       # ExecCodeAction
│   └── set_effect_thinking_action.py  # SetEffectThinkingAction
├── thinking/                      # Thinking visualization actions
│   ├── __init__.py
│   ├── is_thinking_action.py     # IsThinkingAction
│   └── finish_thinking_action.py # FinishThinkingAction
└── workflow/                      # Workflow metadata actions
    ├── __init__.py
    ├── update_title_action.py    # UpdateTitleAction
    └── update_last_text_action.py  # UpdateLastTextAction
```

## Key Improvements

### 1. **Object-Oriented Design**
- Each action is now a class inheriting from `ActionBase`
- Clear separation of concerns
- Better code organization and readability

### 2. **Decorator-Based Registration**
```python
@action('add')
class AddAction(ActionBase):
    def execute(self, step: ExecutionStep) -> Optional[str]:
        # Implementation
        pass
```

### 3. **Automatic Discovery**
- Actions are automatically registered when imported
- No manual registration needed
- Simply import the module to register all actions

### 4. **Category Organization**
- Actions are grouped by functionality
- Each category has its own folder with `__init__.py`
- Easy to find and maintain

### 5. **Clean Code**
- Minimal use of try-except blocks
- One file per action class
- Detailed documentation in each module

## How It Works

### Registration Flow

1. **Define an Action**:
   ```python
   @action('my_action')
   class MyAction(ActionBase):
       def execute(self, step: ExecutionStep) -> Any:
           # Your implementation
           return result
   ```

2. **Automatic Registration**:
   - The `@action` decorator registers the class in `_action_registry`
   - When `actions` module is imported, all actions are registered

3. **ScriptStore Initialization**:
   - `ScriptStore.__init__()` calls `_initialize_actions()`
   - Creates an instance of each action class
   - Stores instances in `_action_instances` dict

4. **Action Execution**:
   ```python
   action = script_store.get_action('add')
   result = action.execute(step)
   ```

## Registered Actions

### Content Actions (content/)
| Action Type      | Class              | Description                    |
|------------------|--------------------|--------------------------------|
| `add`            | AddAction          | Adds text or code cells        |
| `add-text`       | AddTextAction      | Alias for add action           |
| `new_chapter`    | NewChapterAction   | Creates level 1 heading (#)    |
| `new_section`    | NewSectionAction   | Creates level 2 heading (##)   |
| `new_step`       | NewStepAction      | Creates level 3 heading (###)  |
| `comment_result` | CommentResultAction| Adds content + moves to history|

### Code Actions (code/)
| Action Type              | Class                    | Description                      |
|--------------------------|--------------------------|----------------------------------|
| `exec`                   | ExecCodeAction           | Executes code cells              |
| `set_effect_as_thinking` | SetEffectThinkingAction  | Marks code as finished thinking  |

### Thinking Actions (thinking/)
| Action Type       | Class                | Description                 |
|-------------------|----------------------|-----------------------------|
| `is_thinking`     | IsThinkingAction     | Shows thinking indicator    |
| `finish_thinking` | FinishThinkingAction | Removes thinking indicator  |

### Workflow Actions (workflow/)
| Action Type        | Class                | Description                   |
|--------------------|----------------------|-------------------------------|
| `update_title`     | UpdateTitleAction    | Updates notebook title        |
| `update_last_text` | UpdateLastTextAction | Updates last text cell content|

## Usage Examples

### Using an Action
```python
from stores.script_store import ScriptStore
from models.action import ExecutionStep

# Initialize script store
script_store = ScriptStore()

# Create execution step
step = ExecutionStep(
    action='add',
    content='Hello, World!',
    shot_type='markdown'
)

# Execute action
result = script_store.exec_action(step)
```

### Creating a Custom Action
```python
from actions import ActionBase, action
from models.action import ExecutionStep

@action('my_custom_action')
class MyCustomAction(ActionBase):
    """Custom action for special processing."""

    def execute(self, step: ExecutionStep) -> str:
        """Execute custom action."""
        # Access script_store, notebook_store, ai_context_store, code_executor
        self.script_store.info("Executing custom action")

        # Your implementation here
        return "Success"
```

### Querying Registered Actions
```python
from actions import get_all_action_types, get_action_class

# Get all registered action types
action_types = get_all_action_types()
print(f"Total actions: {len(action_types)}")

# Get specific action class
AddAction = get_action_class('add')
print(f"Action class: {AddAction.__name__}")
```

## Migration Notes

### Old System (Function-Based)
```python
# stores/handlers/content_handlers.py
def handle_add_action(script_store, step: ExecutionStep) -> Optional[str]:
    try:
        # Implementation
        pass
    except Exception as e:
        script_store.error(...)
```

### New System (Class-Based)
```python
# actions/content/add_action.py
@action('add')
class AddAction(ActionBase):
    def execute(self, step: ExecutionStep) -> Optional[str]:
        # Implementation - cleaner, no try-except needed
        pass
```

## Benefits

1. **Better Organization**: Actions grouped by category
2. **Cleaner Code**: Less boilerplate, no excessive try-except
3. **Easier Testing**: Each action is an independent class
4. **Better Extensibility**: Simple to add new actions
5. **Type Safety**: Clear interfaces and type hints
6. **Self-Documenting**: Decorator pattern makes registration obvious

## Future Enhancements

- Add action validation decorators
- Implement action pipelines
- Add action middleware support
- Create action composition utilities
