from typing import Dict, Any, Optional
from app.core.config import llm, DataCleaningAndEDA_Agent
from app.models.StepTemplate import StepTemplate

def generate_exploratory_data_sequence_step2(
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
    
    
    if step_template.event("start"):
        
        step_template.new_section("Generate EDA questions") \
                    .add_text("ok we know the data structure, let's generate the EDA questions") \
                    .next_thinking_event(event_tag="generate_eda_questions",
                                        textArray=["Data Cleaning and EDA Agent is thinking...","generating EDA questions..."])
        
        return step_template.end_event()
    
    
    eda_agent = DataCleaningAndEDA_Agent(llm=llm,
                                        problem_description=problem_description,
                                        context_description=context_description,
                                        check_unit=unit_check,
                                        var_json=variables,
                                        hyp_json=hypothesis)
    
    data_info = step_template.get_variable("data_info") 
    data_preview = step_template.get_variable("data_preview")
    
    if step_template.think_event("generate_eda_questions"):
        eda_questions = eda_agent.generate_eda_questions_cli(problem_description, data_info, data_preview)
        
        markdown_str = step_template.to_tableh(eda_questions)
        
        step_template.add_variable("eda_questions", eda_questions) \
                    .add_text("I have generated the EDA questions, let's see:") \
                    .add_text(markdown_str) \
                    .add_text("ok we know the EDA questions, let's solve them one by one") \
                    .add_text("I will solve the EDA questions one by one, and you can see the result in the following steps.") \
        
        return step_template.end_event()
            
    return None
    