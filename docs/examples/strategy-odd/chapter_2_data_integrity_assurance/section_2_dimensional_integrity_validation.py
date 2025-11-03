from typing import Dict, Any, Optional
from app.core.config import llm, DataCleaningAndEDA_Agent
from app.models.StepTemplate import StepTemplate

def generate_data_cleaning_sequence_step1(
    step: Dict[str, Any], 
    state: Optional[Dict[str, Any]] = None,
    stream: bool = False
) -> Dict[str, Any]:
    state = state or {}
        
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
    
    if step_template.event("start"):
        step_template.new_section("Dimension Analysis") \
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
        
        step_template.add_text("I need to generate the dimension check code") \
                    .next_thinking_event(event_tag="generate_dimension_check_code",
                                    textArray=["Data Cleaning and EDA Agent is thinking...","generating the dimension check code..."])
                    
        return step_template.end_event()
    
    if step_template.think_event("generate_dimension_check_code"):
        csv_file_path = step_template.get_variable("csv_file_path")
        dimension_check_code = clean_agent.dimension_analysis_cli(csv_file_path, context_description)

        step_template.add_text("I have generated the dimension check code and get the result, let's see:") \
                    .add_code(dimension_check_code) \
                    .exe_code_cli(
                                event_tag="finished_dimension_check",
                                mark_finnish="finnish dimension analysis")
                    
        return step_template.end_event()
    
    if step_template.think_event("finished_dimension_check"):  
        step_template.add_text("I am aiming to find the dimension problems of the data:") \
                    .next_thinking_event(event_tag="finish_dimension_analysis",
                                    textArray=["Data Cleaning and EDA Agent is thinking...","analyzing the dimension problems..."]) \
                    
        return step_template.end_event()
    
    if step_template.think_event("finish_dimension_analysis"):
        dimension_check_result = step_template.get_current_effect()
        dimension_problems = clean_agent.analyze_data_dimension_cli(dimension_check_result, context_description)
                
        if dimension_problems=="no problem":
            step_template.add_text("Ok, there is no problem with the data dimension, we can proceed to the next step.")
        
        else:
            markdown_str=step_template.to_tableh(dimension_problems)
            
            step_template.add_text("according to the dimension check result, we know there are some problems with the data:") \
                        .add_variable("dimension_problems",dimension_problems) \
                        .add_text(markdown_str) \
                        .next_thinking_event(event_tag="generate_cleaning_operations",
                                        textArray=["Data Cleaning and EDA Agent is thinking...","generating cleaning operations..."])
    
        return step_template.end_event()
    
    if step_template.think_event("generate_cleaning_operations"):
        one_of_issue, issue_left = step_template.pop_last_sub_variable("dimension_problems")
        data_info = step_template.get_variable("data_info")
        
        if one_of_issue:
            step_template.add_code(clean_agent.generate_cleaning_code_cli(csv_file_path, one_of_issue, context_description, variables, unit_check, data_info,"dimension_problems_resolved.csv")) \
                        .update_variable("csv_file_path","dimension_problems_resolved.csv")\
                        .exe_code_cli(mark_finnish="finished generate cleaning operations")                       
            if issue_left:
                step_template.next_thinking_event(event_tag="generate_cleaning_operations",
                                        textArray=["Data Cleaning and EDA Agent is thinking...","generating cleaning operations..."])

        else:
            step_template.add_text("Maybe there is no problem with the data dimension, let's proceed to the next step.")
            
        return step_template.end_event()
    
    
    return None
    