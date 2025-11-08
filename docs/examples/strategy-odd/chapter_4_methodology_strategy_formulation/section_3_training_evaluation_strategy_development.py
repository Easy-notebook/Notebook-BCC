from typing import Dict, Any, Optional
from app.core.config import llm, ModelAgent
from app.models.StepTemplate import StepTemplate

def generate_method_proposal_sequence_step2(
    step: Dict[str, Any], 
    state: Optional[Dict[str, Any]] = None,
    stream: bool = False
) -> Dict[str, Any]:
    state = state or {}
    
    step_template = StepTemplate(step, state)
    
    if step_template.event("start"):
        
        step_template.new_section("Training and Evaluation Strategy") \
                    .add_text("Based on the proposed feature engineering methods and models, I will generate a comprehensive training and evaluation strategy.") \
                    .next_thinking_event(event_tag="generate_strategy",
                                        textArray=["Strategy Generation Agent is thinking...","generating training strategy..."])
        
        return step_template.end_event()
    
    problem_description = step_template.get_variable("problem_description")
    context_description = step_template.get_variable("context_description")
    eda_summary = step_template.get_variable("eda_summary")
    feature_engineering_methods = step_template.get_variable("feature_engineering_methods")
    model_methods = step_template.get_variable("model_methods")
    
    prediction_agent = ModelAgent(
        problem_description=problem_description,
        context_description=context_description,
        eda_summary=eda_summary,
        llm=llm
    )
    
    if step_template.think_event("generate_strategy"):
        
        # Generate training and evaluation strategy using existing method
        training_strategy = prediction_agent.generate_training_evaluation_strategy_cli(
            feature_engineering_methods, model_methods
        )
        
        strategy_table = step_template.to_tableh(training_strategy)
        
        step_template \
            .add_variable("training_strategy", training_strategy) \
            .add_text("Here is the comprehensive training and evaluation strategy:") \
            .add_text(strategy_table) \
            .add_text("This strategy will guide us through the model training and evaluation phase.")
        
        return step_template.end_event()
            
    return None
    