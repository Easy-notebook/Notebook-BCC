from typing import Dict, Any, Optional
from app.core.config import llm, DataCleaningAndEDA_Agent
from app.models.StepTemplate import StepTemplate

def generate_data_cleaning_sequence_step4(
    step: Dict[str, Any], 
    state: Optional[Dict[str, Any]] = None,
    stream: bool = False
) -> Dict[str, Any]:
    state = state or {}
        
    step_template = StepTemplate(step, state)
    
    if step_template.event("start"):
        step_template.new_section("Data Integrity Analysis") \
                    .add_text("I will perform comprehensive data integrity checks to identify potential data quality issues.") \
                    .next_thinking_event(event_tag="check_current_data_info",
                                        textArray=["Data Cleaning Agent is working...","Checking current data information..."])
        
        return step_template.end_event()
    
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
    
    if step_template.think_event("check_current_data_info"):
        step_template.add_text("Let me first check the current state of our dataset after previous cleaning steps:") \
                    .add_code(
                            f"""import pandas as pd
data = pd.read_csv('{csv_file_path}')
print("Dataset Information:")
print(data.info())
print("\\nDataset Shape:", data.shape)
print("\\nFirst few rows:")
print(data.head())
""") \
                    .exe_code_cli() \
                    .next_thinking_event(event_tag="generate_integrity_check_code",
                                        textArray=["Data Cleaning Agent is working...","Generating data integrity check code..."])
        
        return step_template.end_event()
    
    if step_template.think_event("generate_integrity_check_code"):
        
        dataInfo = step_template.get_current_effect()
        step_template.add_variable("data_info", dataInfo)
        
        data_integrity_check_code = clean_agent.generate_data_integrity_check_code_cli(csv_file_path)
        
        step_template.add_text("Now I'll run comprehensive integrity checks to identify any data quality issues:") \
                    .add_code(data_integrity_check_code) \
                    .exe_code_cli(mark_finnish="run comprehensive integrity checks") \
                    .next_thinking_event(event_tag="analyze_integrity_results",
                                        textArray=["Data Cleaning Agent is analyzing...","Analyzing data integrity check results..."])
        
        return step_template.end_event()
    
    if step_template.think_event("analyze_integrity_results"):
        
        data_integrity_check_result = step_template.get_current_effect()
        integrity_problems = clean_agent.analyze_and_generate_fillna_operations_cli(data_integrity_check_result)
        
        if integrity_problems == "no problem":
            step_template.add_text("Excellent! The data integrity analysis shows no significant issues with the dataset.") \
                        .add_text("Data cleaning process completed successfully!") 
        else:
            markdown_str = step_template.to_tableh(integrity_problems)
            
            step_template \
                        .add_variable("data_integrity_problems", integrity_problems) \
                        .add_text("The integrity analysis revealed the following issues that need to be resolved:") \
                        .add_text(markdown_str) \
                        .next_thinking_event(event_tag="resolve_integrity_issues",
                                            textArray=["Data Cleaning Agent is working...","Resolving data integrity issues..."])
        
        return step_template.end_event()
    
    if step_template.think_event("resolve_integrity_issues"):
        
        one_of_issue, issue_left = step_template.pop_last_sub_variable("data_integrity_problems")
        data_info = step_template.get_variable("data_info")
        
        if one_of_issue:
            step_template.add_text(f"Resolving Issue: {one_of_issue.get('problem', 'Data Integrity Issue')}") \
                        .add_text("Generating cleaning code to resolve this specific integrity issue:") \
                        .add_code(clean_agent.generate_cleaning_code_cli(
                            csv_file_path, 
                            one_of_issue, 
                            context_description, 
                            variables, 
                            unit_check, 
                            data_info, 
                            "integrity_problem_resolved.csv"
                        )) \
                        .update_variable("csv_file_path", "integrity_problem_resolved.csv") \
                        .exe_code_cli(mark_finnish="resolved data integrity issue")                       
            
            if issue_left:
                step_template.next_thinking_event(event_tag="resolve_integrity_issues",
                                                textArray=["Data Cleaning Agent is working...","Processing next integrity issue..."])
            else:
                step_template.add_text("") \
                           .add_text("All data integrity issues have been resolved!") \
                           .add_text("Data Cleaning Process Complete!") \
                           .add_text("- Dimension analysis completed") \
                           .add_text("- Invalid values handled") \
                           .add_text("- Missing values processed") \
                           .add_text("- Data integrity issues resolved")
                
        else:
            step_template.add_text("No data integrity problems found.") \
                        .add_text("Data cleaning process completed successfully!")
        
        return step_template.end_event()
    
    return None
    