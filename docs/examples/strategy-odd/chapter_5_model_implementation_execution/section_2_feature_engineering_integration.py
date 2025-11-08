from typing import Dict, Any, Optional
from app.core.config import llm, ModelAgent
from app.models.StepTemplate import StepTemplate

async def model_training_and_evaluation_step1(
    step: Dict[str, Any], 
    state: Optional[Dict[str, Any]] = None,
    stream: bool = False
) -> Dict[str, Any]:
    state = state or {}
        
    step_template = StepTemplate(step, state)
    
    if step_template.event("start"):
        step_template.new_section("Feature Engineering Methods Suggestion") \
                    .add_text("I will analyze the dataset characteristics and suggest appropriate feature engineering techniques to improve model performance.") \
                    .next_thinking_event(event_tag="suggest_feature_engineering",
                                        textArray=["Prediction Agent is analyzing...","Suggesting feature engineering methods..."])

        return step_template.end_event()
    
    stage3_feature_methods = step_template.get_variable("feature_engineering_methods")
    
    if step_template.think_event("suggest_feature_engineering"):
        
        # 直接使用Stage 3生成的特征工程方法，不重新生成
        feature_engineering_table = step_template.to_tableh(stage3_feature_methods)
        
        step_template \
            .add_variable("feature_engineering_methods", stage3_feature_methods) \
            .add_text("Using the feature engineering methods recommended in Stage 3 Method Proposal:") \
            .add_text(feature_engineering_table) \
            .add_text("✅ Ready to proceed with model training using these feature engineering approaches.")
        
        return step_template.end_event()
            
    return None