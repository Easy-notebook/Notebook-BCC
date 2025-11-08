from typing import Dict, Any, Optional
from app.core.config import llm, DataCleaningAndEDA_Agent
from app.models.StepTemplate import StepTemplate

def generate_data_cleaning_sequence_step2(
    step: Dict[str, Any], 
    state: Optional[Dict[str, Any]] = None,
    stream: bool = False
) -> Dict[str, Any]:
    state = state or {}
    
    # 初始化场景内agent（如果需要）
    step_template = StepTemplate(step, state)
    problem_description = step_template.get_variable("problem_description")
    context_description = step_template.get_variable("context_description")
    unit_check = step_template.get_variable("unit_check")
    variables = step_template.get_variable("variables")
    hypothesis = step_template.get_variable("pcs_hypothesis")
    csv_file_path = step_template.get_variable("csv_file_path")

    clean_agent = DataCleaningAndEDA_Agent(llm=llm,
                                        problem_description=problem_description,
                                        context_description=context_description,
                                        check_unit=unit_check,
                                        var_json=variables,
                                        hyp_json=hypothesis)
    
    # 分支1：待办事项为空
    if step_template.event("start"):
        step_template.new_section("Invalid Value Analysis") \
                    .add_code(
                            f"""from vdstools import DataPreview
data_preview = DataPreview("{csv_file_path}")
data_preview.data_info()
""") \
                    .exe_code_cli(mark_finnish="glance at current data info.") \
                    .next_event("glance at current data info.")
        
        return step_template.end_event()
    
    if step_template.event("glance at current data info."):
        
        dataInfo = step_template.get_current_effect()
        step_template.add_variable("data_info",dataInfo) 
        
        step_template.add_text("Let's see the value range of each variable:") \
                    .add_code(
f"""
from vdstools import DataPreview
data_preview = DataPreview("{csv_file_path}")
data_preview.column_range()
"""
                    ) \
                    .exe_code_cli( 
                        event_tag="finished_code_execution",
                        mark_finnish="finished glance at the value range of each variable"
                    )
                    
        return step_template.end_event()

    
    if step_template.event("finished_code_execution"):

        step_template.add_text("I am aiming to find the invalid value problems of the data:") \
                    .next_thinking_event(event_tag="analyze_invalid_value_problems",
                                    textArray=["Data Cleaning and EDA Agent is thinking...","analyzing the invalid value problems..."])
        
        return step_template.end_event()
    
    if step_template.think_event("analyze_invalid_value_problems"):
        invalid_value_analysis_result = step_template.get_current_effect()
        invalid_value_problems = clean_agent.check_for_invalid_values_cli(invalid_value_analysis_result, context_description, variables)
        
        if invalid_value_problems =="no problem":
            step_template.add_text("I have checked the invalid value problems, and there is no problem with the data.") \
                        .add_text("Let's proceed to the next step.")
        
        else:
            markdown_str=step_template.to_tableh(invalid_value_problems)
            
            step_template.add_variable("invalid_value_problems",invalid_value_problems) \
                        .add_text("according to the invalid value analysis result, we know there are some problems with the data:") \
                        .add_text(markdown_str)\
                        .next_thinking_event(event_tag="generate_cleaning_operations",
                                        textArray=["Data Cleaning and EDA Agent is thinking...","generating cleaning operations..."])
        
        return step_template.end_event()
    
    if step_template.think_event("generate_cleaning_operations"):
        all_issues = step_template.get_variable("invalid_value_problems")
        data_info = step_template.get_variable("data_info")
        
        if all_issues:
            # Group issues by cleaning method type for batch processing
            grouped_issues = {}
            for issue in all_issues:
                method_type = issue.get('method', 'general')
                if method_type not in grouped_issues:
                    grouped_issues[method_type] = []
                grouped_issues[method_type].append(issue)
            
            step_template.add_text(f"Found {len(all_issues)} invalid value issues. Grouping by method type for efficient batch processing:")
            
            method_counter = 1
            final_output_filename = "invalid_value_resolved.csv"
            
            for method_type, issues in grouped_issues.items():
                issue_descriptions = [issue.get('problem', 'Invalid value issue') for issue in issues]
                step_template.add_text(f"#### Method Group {method_counter}: Processing {len(issues)} Issues")
                step_template.add_text(f"**Issues:** {', '.join(issue_descriptions)}")
                
                # 第一个batch使用原始文件，后续batch使用之前的输出结果
                if method_counter == 1:
                    input_csv_path = csv_file_path
                else:
                    input_csv_path = final_output_filename
                
                output_filename = final_output_filename
                
                # Pass all issues of same type at once for batch processing
                batch_cleaning_code = clean_agent.generate_cleaning_code_cli(
                    input_csv_path, issues, context_description, variables, 
                    unit_check, data_info, output_filename
                )
                
                step_template.add_code(batch_cleaning_code) \
                           .exe_code_cli(mark_finnish=f"resolved {len(issues)} issues in method group {method_counter}")
                
                method_counter += 1
            
            # Update the final CSV path
            step_template.update_variable("csv_file_path", final_output_filename)
            step_template.add_text("✅ **All invalid value issues have been resolved using batch processing!**") \
                       .add_text("🎯 **Ready to proceed to the next step.**")
        
        else:
            step_template.add_text("✅ **No invalid value problems found.**") \
                       .add_text("🎯 **Ready to proceed to the next step.**")
            
        return step_template.end_event()
    
    return None
    