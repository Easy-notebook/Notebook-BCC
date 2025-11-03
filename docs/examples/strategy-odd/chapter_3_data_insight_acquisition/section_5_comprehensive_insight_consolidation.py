from typing import Dict, Any, Optional
from app.core.config import llm, DataCleaningAndEDA_Agent
from app.models.StepTemplate import StepTemplate

def generate_exploratory_data_sequence_step4(
    step: Dict[str, Any], 
    state: Optional[Dict[str, Any]] = None,
    stream: bool = False
) -> Dict[str, Any]:
    state = state or {}
    
    step_template = StepTemplate(step, state)
        
    if step_template.event("start"):
        step_template.new_section("EDA Summary and Analysis") \
                    .add_text("I will summarize all the EDA results and provide comprehensive insights from the exploratory data analysis.") \
                    .next_thinking_event(event_tag="generate_eda_summary",
                                        textArray=["Data Cleaning and EDA Agent is thinking...","generating EDA summary..."])
        return step_template.end_event()
    
    
    problem_description = step_template.get_variable("problem_description")
    context_description = step_template.get_variable("context_description")
    unit_check = step_template.get_variable("unit_check")
    variables = step_template.get_variable("variables")
    hypothesis = step_template.get_variable("pcs_hypothesis")
    csv_file_path = step_template.get_variable("csv_file_path")
    eda_summary = step_template.get_variable("eda_summary")

    
    clean_agent = DataCleaningAndEDA_Agent(llm=llm,
                                        problem_description=problem_description,
                                        context_description=context_description,
                                        check_unit=unit_check,
                                        var_json=variables,
                                        hyp_json=hypothesis)
    
    if step_template.think_event("generate_eda_summary"):
        
        # Generate comprehensive EDA summary
        comprehensive_summary = clean_agent.generate_eda_summary_cli(
            eda_results=eda_summary,
            problem_description=problem_description,
            context_description=context_description
        )
        
        step_template \
            .add_variable("comprehensive_eda_summary", comprehensive_summary) \
            .add_text("Based on all the exploratory data analysis questions and results, here is the comprehensive summary:") \
            .add_text(comprehensive_summary) \
            .add_text("✅ EDA Stage Completed Successfully!") \
            .add_text("Key Insights Discovered:") \
            .add_text("- Data patterns and distributions have been analyzed") \
            .add_text("- Variable relationships and correlations identified") \
            .add_text("- Data quality and integrity assessed") \
            .add_text("- Statistical properties and anomalies documented") \
        
        return step_template.end_event()
    
    return None