from typing import Dict, Any, Optional
from app.core.config import llm, DataCleaningAndEDA_Agent
from app.models.StepTemplate import StepTemplate

def generate_data_cleaning_sequence_step3(
    step: Dict[str, Any], 
    state: Optional[Dict[str, Any]] = None,
    stream: bool = False
) -> Dict[str, Any]:
    state = state or {}
        
    step_template = StepTemplate(step, state)
    
    if step_template.event("start"):
        step_template.new_section("Missing Value Analysis") \
                    .add_text("I will analyze missing values in the dataset to identify data quality issues.") \
                    .next_thinking_event(event_tag="check_data_info",
                                        textArray=["Data Cleaning Agent is working...","Checking data information..."])
        
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
    
    if step_template.think_event("check_data_info"):
        step_template.add_text("First, let me check the basic information about our dataset:") \
                    .add_code(
                            f"""from vdstools import DataPreview
data_preview = DataPreview("{csv_file_path}")
data_preview.data_info()
""") \
                    .exe_code_cli() \
                    .next_thinking_event(event_tag="analyze_missing_values",
                                        textArray=["Data Cleaning Agent is analyzing...","Analyzing missing values..."])
        
        return step_template.end_event()
    
    if step_template.think_event("analyze_missing_values"):
        
        dataInfo = step_template.get_current_effect()
        step_template.add_variable("data_info", dataInfo)
        
        step_template.add_text("Now let me check for missing values in each column:") \
                    .add_code(
f"""import pandas as pd
data = pd.read_csv("{csv_file_path}")
missing_data = data.isna().sum() / len(data.index)
missing_data_sorted = missing_data.sort_values(ascending=False)    
missing_data_str = missing_data_sorted.to_string()
print("Missing value percentages by column (sorted):")
print(missing_data_str)
""" 
                    ) \
                    .exe_code_cli() \
                    .next_thinking_event(event_tag="generate_missing_value_visualization",
                                        textArray=["Data Cleaning Agent is working...","Generating missing value visualization..."])
                    
        return step_template.end_event()
    
    if step_template.think_event("generate_missing_value_visualization"):
        
        missing_value_str = step_template.get_current_effect()
        step_template.add_variable("missing_value_str", missing_value_str)
        
        # Create a simple, focused missing value bar chart
        step_template.add_text("Creating a focused overview of missing value percentages:") \
                    .add_code(f"""import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read data and calculate missing values
data = pd.read_csv('{csv_file_path}')
missing_percentages = data.isna().sum() / len(data) * 100

# Filter columns with missing values
missing_cols = missing_percentages[missing_percentages > 0].sort_values(ascending=False)

# Create visualization only if there are missing values
if len(missing_cols) > 0:
    plt.figure(figsize=(10, 6))
    bars = plt.bar(range(len(missing_cols)), missing_cols.values, color='lightcoral', alpha=0.7)
    
    # Add value labels on bars
    for i, bar in enumerate(bars):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{{height:.1f}}%', ha='center', va='bottom')
    
    plt.title('Missing Value Percentages by Column', fontsize=14, fontweight='bold')
    plt.xlabel('Columns', fontsize=12)
    plt.ylabel('Missing Value Percentage (%)', fontsize=12)
    plt.xticks(range(len(missing_cols)), missing_cols.index, rotation=45, ha='right')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    
    # Save the plot
    plt.savefig('data_cleaning_missing_value_overview.png', dpi=300, bbox_inches='tight')
    plt.show()
    plt.close()
    
    print(f"Missing value analysis complete. Found {{len(missing_cols)}} columns with missing values.")
    print("Generated missing value overview chart: data_cleaning_missing_value_overview.png")
else:
    print("No missing values found in the dataset.")
""") \
                    .exe_code_cli() \
                    .next_thinking_event(event_tag="analyze_missing_value_results",
                                        textArray=["Data Cleaning Agent is analyzing...","Analyzing missing value patterns..."])
                    
        return step_template.end_event()
    
    if step_template.think_event("analyze_missing_value_results"):
        
        missing_value_check_result = step_template.get_current_effect()
        
        # Analyze missing value results
        missing_value_problems = clean_agent.analyze_missing_values_result_cli(
            result=missing_value_check_result, 
            missing_data_str=step_template.get_variable("missing_value_str"), 
            data_unit=unit_check
        )
        
        if missing_value_problems == "no problem":
            step_template.add_text("Good news! The analysis shows no significant missing value problems in the dataset.") \
                        .add_text("Ready to proceed to the next step.")
        else:
            markdown_str = step_template.to_tableh(missing_value_problems)
            
            step_template \
                        .add_variable("missing_value_problems", missing_value_problems) \
                        .add_text("The analysis revealed the following missing value problems that need to be addressed:") \
                        .add_text(markdown_str) \
                        .next_thinking_event(event_tag="generate_cleaning_operations",
                                        textArray=["Data Cleaning Agent is working...","Generating cleaning operations..."])
        
        return step_template.end_event()    
    
    if step_template.think_event("generate_cleaning_operations"):
        
        one_of_issue, issue_left = step_template.pop_last_sub_variable("missing_value_problems")
        data_info = step_template.get_variable("data_info")
        
        if one_of_issue:
            step_template.add_text(f"Resolving Issue: {one_of_issue.get('problem', 'Missing Value Issue')}") \
                        .add_text("Generating cleaning code to resolve this specific issue:") \
                        .add_code(clean_agent.generate_cleaning_code_cli(
                            csv_file_path, 
                            one_of_issue, 
                            context_description, 
                            variables, 
                            unit_check, 
                            data_info,
                            "missing_value_resolved.csv"
                        )) \
                        .update_variable("csv_file_path", "missing_value_resolved.csv") \
                        .exe_code_cli()                       
            
            if issue_left:
                step_template.next_thinking_event(event_tag="generate_cleaning_operations",
                                        textArray=["Data Cleaning Agent is working...","Processing next cleaning operation..."])
            else:
                step_template.add_text("") \
                           .add_text("All missing value issues have been resolved!") \
                           .add_text("Ready to proceed to the next data integrity check.")
                
        else:
            step_template.add_text("No missing value problems found.") \
                        .add_text("Ready to proceed to the next step.")
            
        return step_template.end_event()
    
    return None
    