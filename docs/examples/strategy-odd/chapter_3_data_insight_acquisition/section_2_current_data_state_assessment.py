from typing import Dict, Any, Optional
from app.models.StepTemplate import StepTemplate

def generate_exploratory_data_sequence_step1(
    step: Dict[str, Any], 
    state: Optional[Dict[str, Any]] = None,
    stream: bool = False
) -> Dict[str, Any]:
    state = state or {}
        
    # 初始化场景内agent（如果需要）
    step_template = StepTemplate(step, state)
    csv_file_path = step_template.get_variable("csv_file_path")
    
    # 分支1：待办事项为空
    if step_template.event("start"):
        step_template.new_section("Data preview") \
                     .add_text("read the first 5 rows of the CSV file and extract the variable n and data preview") \
                     .add_code(
                         f'''import pandas as pd
# Correcting the file path by wrapping it in quotes.
data = pd.read_csv("{csv_file_path}")  # File path needs to be a string.

# Using the head() function to preview the first few rows of data.
preview = data.head().to_dict(orient="records")

# Retrieving the column names.
variables = list(data.columns)

print(variables)''',
                     ) \
                    .exe_code_cli(
                        event_tag="finished_get_data_info",
                        mark_finnish="finished glance at the each column of the data"
                    )        
        return step_template.end_event()
    
    # 分支2：待办事项不为空且最后一个为 "code_exec_1"
    if step_template.event("finished_get_data_info"):
        
        data_info = step_template.get_current_effect()
        
        step_template \
            .add_variable("data_info", data_info) \
            .add_code("data.head()") \
            .exe_code_cli(
                event_tag="finished_get_data_preview",
                mark_finnish="finished glance at the top 5 rows of the data"
            )
        
        return step_template.end_event()
    
    if step_template.event("finished_get_data_preview"):
        
        data_preview = step_template.get_current_effect()
        
        step_template.add_variable("data_preview", data_preview) \
                    .add_text("ok we know current situation, let's talk about the EDA questions")
        
        return step_template.end_event()
            
    return None
    