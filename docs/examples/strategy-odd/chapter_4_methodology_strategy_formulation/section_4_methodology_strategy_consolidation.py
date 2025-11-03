from typing import Dict, Any, Optional
from app.core.config import llm, ModelAgent
from app.models.StepTemplate import StepTemplate

def generate_method_proposal_sequence_step3(
    step: Dict[str, Any], 
    state: Optional[Dict[str, Any]] = None,
    stream: bool = False
) -> Dict[str, Any]:
    state = state or {}
    
    step_template = StepTemplate(step, state)
        
    if step_template.event("start"):
        step_template.new_section("Method Proposal Summary") \
                    .add_text("I will now provide a comprehensive summary of the proposed methods and training strategy for this data science project.") \
                    .next_thinking_event(event_tag="generate_summary",
                                        textArray=["Summary Generation Agent is thinking...","generating method summary..."])
        
        return step_template.end_event()
    
    problem_description = step_template.get_variable("problem_description")
    context_description = step_template.get_variable("context_description")
    eda_summary = step_template.get_variable("eda_summary")
    feature_engineering_methods = step_template.get_variable("feature_engineering_methods")
    model_methods = step_template.get_variable("model_methods")
    training_strategy = step_template.get_variable("training_strategy")

    if step_template.think_event("generate_summary"):
        
        # Generate a comprehensive summary
        step_template.add_text("**Method Proposal Summary**：") \
                    .add_text("📊 **Problem Context**：") \
                    .add_text(f"**Problem**: {problem_description}") \
                    .add_text(f"**Context**: {context_description}") \
                    .add_text("🔧 **Proposed Feature Engineering Methods**：")
        
        # Display feature engineering methods
        if feature_engineering_methods:
            fe_table = step_template.to_tableh(feature_engineering_methods)
            step_template.add_text(fe_table)
        
        step_template.add_text("🤖 **Proposed Modeling Methods**：")
        
        # Display modeling methods
        if model_methods:
            model_table = step_template.to_tableh(model_methods)
            step_template.add_text(model_table)
        
        step_template.add_text("📋 **Training and Evaluation Strategy**：")
        
        # Display training strategy
        if training_strategy:
            strategy_table = step_template.to_tableh(training_strategy)
            step_template.add_text(strategy_table)
        
        step_template.add_text("✅ **Next Steps**：") \
                    .add_text("1. **Model Training**: Implement the proposed feature engineering methods") \
                    .add_text("2. **Model Evaluation**: Train and evaluate the suggested models") \
                    .add_text("3. **Performance Analysis**: Compare model performance using the defined strategy") \
                    .add_text("4. **Result Interpretation**: Analyze and interpret the results") \
                    .add_text("") \
                    .add_text("The method proposal stage is now complete. We are ready to proceed to the model training and evaluation phase.")
        
        return step_template.end_event()
    
    return None
    