# 变更指南：如何从旧架构迁移到新架构

## 1. 核心变更概览

### 变更1：增加Behavior追踪层

**原来**：
```python
# 没有behavior概念，直接从step到actions
workflow_context = {
    "current_stage_id": "chapter_0",
    "current_step_id": "section_1"
}
```

**现在**：
```python
# 增加behavior层级追踪
workflow_context = {
    "current_stage_id": "chapter_0",
    "current_step_id": "section_1",
    "behavior_id": "behavior_003",         # 新增
    "behavior_iteration": 3                # 新增
}
```

**功能变化**：
- 一个step执行期间会有多次API交互（多个behaviors）
- 每个behavior返回一组actions
- 需要追踪当前是第几个behavior

**修改位置**：
- `core/context.py` - 在`WorkflowContext`中添加字段
- `utils/api_client.py` - 在请求中包含behavior信息
- `core/state_machine.py` - 追踪behavior_iteration

---

### 变更2：增加Section内容组织

**原来**：
```python
# Action中没有section标记
action = {
    "type": "add",
    "content": "## Section 2: Data Loading"
}
```

**现在**：
```python
# Action带有section元数据
action = {
    "type": "add_content",
    "content": "## Section 2: Data Loading",
    "metadata": {
        "is_section": true,           # 新增
        "section_id": "data_loading", # 新增
        "section_number": 2           # 新增
    }
}
```

**功能变化**：
- Notebook内容按section组织
- 可追踪哪些section已完成
- 支持结构化报告生成

**修改位置**：
- `models/action.py` - 在`ActionMetadata`中添加section字段
- `stores/script_store.py` - 处理section标记
- Context中添加`section_progress`追踪

---

### 变更3：TodoList升级为行为驱动器

**原来**：
```python
# 只是简单存储，没有特殊作用
context = {
    "toDoList": ["任务1", "任务2"]
}
```

**现在**：
```python
# TodoList驱动服务端行为生成
request = {
    "context": {
        "toDoList": [
            "Section 2: 数据评估",  # 服务端根据这个生成对应actions
            "Section 3: 变量定义"
        ]
    }
}

response = {
    "context_update": {
        "todo_list_update": {          # 新增
            "operation": "remove",     # 新增
            "items": ["Section 2: 数据评估"]
        }
    }
}
```

**功能变化**：
- 服务端读取todo_list决定生成什么内容
- 完成后服务端发送update指令移除已完成项
- 客户端必须响应todo_list_update

**修改位置**：
- 保持`todo_list`字段（已有）
- Response中添加`todo_list_update`处理
- `core/state_machine.py` - 处理todo_list更新

---

### 变更4：Behavior反馈机制

**原来**：
```python
# 只在reflection中隐式反馈
send_feedback(stage_id, step_id, context)
```

**现在**：
```python
# 显式的behavior反馈
request = {
    "behavior_feedback": {           # 新增整个块
        "behavior_id": "behavior_002",
        "actions_executed": 5,
        "actions_succeeded": 5,
        "sections_added": 1,
        "last_action_result": "success"
    }
}
```

**功能变化**：
- 服务端知道上一个behavior执行了什么
- 可根据执行结果调整下一个behavior
- 更精确的进度追踪

**修改位置**：
- `utils/api_client.py` - 构建behavior_feedback
- `core/state_machine.py` - 收集执行统计

---

### 变更5：服务端控制Behavior循环

**原来**：
```python
# 客户端不知道是否需要更多behaviors
if targetAchieved:
    complete_step()
```

**现在**：
```python
# 服务端明确告知
response = {
    "transition": {
        "continue_behaviors": true,    # 新增
        "target_achieved": false       # 新增
    }
}

# 客户端逻辑
if response.transition.continue_behaviors:
    # 继续下一个behavior
    behavior_iteration += 1
    fetch_next_behavior()
else:
    # Step完成
    complete_step()
```

**功能变化**：
- 服务端完全控制需要几个behaviors
- 客户端只需执行和反馈
- 消除客户端猜测

**修改位置**：
- Response添加`transition.continue_behaviors`
- `core/state_machine.py` - 根据标志决定是否继续

---

### 变更6：Section进度追踪

**原来**：
```python
# 没有section进度概念
context = {
    "variables": {...},
    "toDoList": [...]
}
```

**现在**：
```python
# 追踪section完成情况
context = {
    "variables": {...},
    "toDoList": [...],
    "section_progress": {              # 新增整个对象
        "current_section_id": "data_loading",
        "current_section_number": 2,
        "completed_sections": ["introduction", "data_loading"]
    }
}
```

**功能变化**：
- 知道当前在哪个section
- 知道哪些section已完成
- 可验证内容完整性

**修改位置**：
- Context添加`section_progress`
- `core/state_machine.py` - 更新section进度
- Response中可以更新`section_progress`

---

### 变更7：字段重命名

**原来 → 现在**：
```python
# 位置字段
"step_index"    → "current_step_id"   # 明确是ID不是index
"stage_id"      → "current_stage_id"  # 明确是当前位置

# Context字段
"state"         → "context"           # 避免与POMDP的state混淆
"toDoList"      → "toDoList"         # Python命名规范
"stageStatus"   → 删除                # 从不使用

# Response字段
"shotType"      → "content_type"      # 更清晰
"targetAchieved"→ "target_achieved"   # Python命名规范
```

**修改位置**：
- 所有使用这些字段的地方都需要更新
- 建议创建兼容层（PayloadAdapter）在过渡期支持两种格式

---

## 2. 具体代码修改

### 2.1 更新 `core/context.py`

```python
# 添加到WorkflowContext
@dataclass
class WorkflowContext:
    current_stage_id: Optional[str] = None
    current_step_id: Optional[str] = None

    # ⭐ 新增
    current_behavior_id: Optional[str] = None
    behavior_iteration: int = 0

    current_behavior_actions: List[Any] = field(default_factory=list)
    current_action_index: int = 0

# ⭐ 新增类
@dataclass
class SectionProgress:
    current_section_id: Optional[str] = None
    current_section_number: Optional[int] = None
    completed_sections: List[str] = field(default_factory=list)
```

### 2.2 更新 `models/action.py`

```python
@dataclass
class ActionMetadata:
    is_step: bool = False
    is_chapter: bool = False

    # ⭐ 新增
    is_section: bool = False
    section_id: Optional[str] = None
    section_number: Optional[int] = None

    finished_thinking: bool = False
```

### 2.3 更新 `utils/api_client.py`

```python
async def send_feedback(
    self,
    stage_id: str,
    step_id: str,  # 重命名自step_index
    context: Dict[str, Any],
    behavior_feedback: Optional[Dict] = None  # ⭐ 新增
):
    payload = {
        'observation': {  # ⭐ 新增包装
            'location': {
                'current_stage_id': stage_id,
                'current_step_id': step_id,
                'behavior_id': context.get('behavior_id'),  # ⭐ 新增
                'behavior_iteration': context.get('behavior_iteration', 0)  # ⭐ 新增
            },
            'context': {
                'variables': context.get('variables'),
                'todo_list': context.get('todo_list'),  # 重命名自toDoList
                'effects': context.get('effects'),
                'section_progress': context.get('section_progress'),  # ⭐ 新增
                'notebook': context.get('notebook')
            }
        },
        'behavior_feedback': behavior_feedback,  # ⭐ 新增
        'options': {'stream': stream}
    }
```

### 2.4 更新 `core/state_machine.py`

```python
def _effect_behavior_running(self, payload: Any = None):
    """Behavior运行时的效果"""
    ctx = self.execution_context.workflow_context

    # ⭐ 新增：生成behavior_id
    if not ctx.current_behavior_id:
        ctx.behavior_iteration += 1
        ctx.current_behavior_id = f"behavior_{ctx.behavior_iteration:03d}"

    # 获取actions
    actions = self.api_client.fetch_behavior_actions(
        stage_id=ctx.current_stage_id,
        step_id=ctx.current_step_id,
        context=self._build_context(),  # 包含behavior信息
        stream=True
    )

    ctx.current_behavior_actions = actions

def _effect_behavior_completed(self, payload: Any = None):
    """Behavior完成后的效果"""
    # 发送反馈
    response = self.api_client.send_feedback(
        stage_id=ctx.current_stage_id,
        step_id=ctx.current_step_id,
        context=self._build_context(),
        behavior_feedback=self._build_behavior_feedback()  # ⭐ 新增
    )

    # ⭐ 新增：检查是否需要更多behaviors
    transition = response.get('transition', {})
    if transition.get('continue_behaviors'):
        # 清理当前behavior状态
        ctx.current_behavior_id = None
        ctx.current_behavior_actions = []
        ctx.current_action_index = 0
        # 开始下一个behavior
        self.transition(WorkflowEvent.NEXT_BEHAVIOR)
    else:
        # Step完成
        self.transition(WorkflowEvent.COMPLETE_STEP)

    # ⭐ 新增：处理context更新
    context_update = response.get('context_update', {})
    self._apply_context_update(context_update)

def _build_behavior_feedback(self) -> Dict:
    """⭐ 新增方法：构建behavior反馈"""
    return {
        'behavior_id': self.execution_context.workflow_context.current_behavior_id,
        'actions_executed': len(self.execution_context.workflow_context.current_behavior_actions),
        'sections_added': self._count_sections_added(),
        'last_action_result': self._get_last_action_result()
    }

def _apply_context_update(self, update: Dict):
    """⭐ 新增方法：应用context更新"""
    # 更新variables
    if 'variables' in update:
        self.ai_context_store.update_variables(update['variables'])

    # ⭐ 处理todo_list更新
    if 'todo_list_update' in update:
        op = update['todo_list_update']['operation']
        items = update['todo_list_update']['items']
        if op == 'remove':
            for item in items:
                self.ai_context_store.remove_todo(item)
        elif op == 'add':
            for item in items:
                self.ai_context_store.add_todo(item)

    # ⭐ 更新section进度
    if 'section_progress' in update:
        self.ai_context_store.set_section_progress(update['section_progress'])
```

### 2.5 更新 `stores/ai_context_store.py`

```python
@dataclass
class AIContext:
    variables: Dict[str, Any] = field(default_factory=dict)
    todo_list: List[str] = field(default_factory=list)  # 重命名自toDoList
    effects: Dict[str, List[Any]] = field(default_factory=lambda: {'current': [], 'history': []})

    # ⭐ 新增
    section_progress: Optional[SectionProgress] = None

    # ❌ 删除
    # stageStatus: Dict[str, bool]  # 删除
    # checklist: Dict  # 删除

def to_dict(self) -> Dict[str, Any]:
    return {
        'variables': self.variables,
        'todo_list': self.todo_list,
        'effects': self.effects,
        'section_progress': self.section_progress.to_dict() if self.section_progress else None
    }
```

### 2.6 更新 `stores/script_store.py`

```python
def exec_action(self, action: ExecutionStep):
    """执行action"""
    # ... 现有逻辑

    # ⭐ 新增：处理section
    if action.metadata and action.metadata.is_section:
        self._handle_section(action)

def _handle_section(self, action: ExecutionStep):
    """⭐ 新增方法：处理section标记"""
    section_id = action.metadata.section_id
    section_number = action.metadata.section_number

    # 更新section进度
    if self.ai_context_store.section_progress:
        self.ai_context_store.section_progress.current_section_id = section_id
        self.ai_context_store.section_progress.current_section_number = section_number
        if section_id not in self.ai_context_store.section_progress.completed_sections:
            self.ai_context_store.section_progress.completed_sections.append(section_id)
```

---

## 3. 迁移步骤

### 步骤1：添加新数据结构（不破坏现有功能）
1. 在`core/context.py`添加behavior和section字段
2. 在`models/action.py`添加section元数据
3. 运行测试确保不破坏现有功能

### 步骤2：更新API通信层
1. 修改`utils/api_client.py`的payload构建
2. 创建兼容层支持新旧格式
3. 测试API调用

### 步骤3：更新State Machine
1. 在`_effect_behavior_completed`中处理`continue_behaviors`
2. 添加`_build_behavior_feedback`方法
3. 添加`_apply_context_update`方法
4. 测试behavior循环

### 步骤4：处理Section追踪
1. 在`script_store.py`中添加section处理
2. 更新context store的section_progress
3. 测试section组织

### 步骤5：字段重命名
1. 全局搜索替换（注意兼容性）
2. 更新所有引用
3. 删除旧字段

### 步骤6：删除无用字段
1. 删除`stageStatus`
2. 删除`checklist`
3. 删除`thinking`（从payload中）
4. 清理相关代码

---

## 4. 测试检查清单

- [ ] Behavior循环：一个step能执行多个behaviors
- [ ] Behavior反馈：每个behavior的执行结果被正确收集
- [ ] Section标记：actions带有正确的section元数据
- [ ] Section进度：completed_sections正确追踪
- [ ] TodoList更新：服务端的remove操作被正确应用
- [ ] continue_behaviors：正确决定是否继续下一个behavior
- [ ] 字段重命名：所有旧字段名已替换
- [ ] 兼容性：API能同时处理新旧格式（如果需要）
- [ ] Payload大小：确认payload减小了~15%

---

## 5. 常见问题

### Q: 如何判断一个step需要几个behaviors？
**A**: 由服务端决定。客户端根据`continue_behaviors`标志循环：
```python
while response.transition.continue_behaviors:
    fetch_next_behavior()
    execute_actions()
    send_feedback()
```

### Q: Section和Step有什么区别？
**A**:
- Step是workflow的结构单元（由服务端定义）
- Section是内容的组织单元（由actions动态生成）
- 一个Step可以生成多个Sections

### Q: TodoList如何驱动行为？
**A**: 服务端读取todo_list，根据其中的项目生成对应的actions：
```python
# 服务端逻辑
if "Section 2: 评估" in request.todo_list:
    return generate_section_2_actions()
```

### Q: 旧代码能否继续工作？
**A**: 建议创建PayloadAdapter兼容层，支持一段时间的新旧格式共存。

### Q: 迁移需要多久？
**A**:
- 添加新字段：1-2天
- 更新API层：2-3天
- 更新State Machine：2-3天
- 测试和调试：2-3天
- 总计：7-11天

---

## 6. 回滚方案

如果迁移出现问题：

1. **代码回滚**：
```bash
git revert <commit-hash>
```

2. **Feature Flag**：
```python
USE_NEW_BEHAVIOR_TRACKING = os.getenv('NEW_BEHAVIOR', 'false') == 'true'

if USE_NEW_BEHAVIOR_TRACKING:
    # 新逻辑
else:
    # 旧逻辑（兼容）
```

3. **分阶段启用**：
```
Week 1: 只添加字段，不使用
Week 2: 启用behavior追踪
Week 3: 启用section组织
Week 4: 完全切换
```
