from typing import Dict, Any, Optional
from app.core.config import llm, ModelAgent
from app.models.StepTemplate import StepTemplate

async def model_training_and_evaluation_step2(
    step: Dict[str, Any], 
    state: Optional[Dict[str, Any]] = None,
    stream: bool = False
) -> Dict[str, Any]:
    state = state or {}
        
    step_template = StepTemplate(step, state)
    
    if step_template.event("start"):
        step_template.new_section("Modeling Methods Integration") \
                    .add_text("Building on the feature engineering methods from Step 1, I will integrate the modeling methods from Stage 3 to prepare for comprehensive model training.") \
                    .next_thinking_event(event_tag="suggest_modeling_methods",
                                        textArray=["Prediction Agent is analyzing...","Suggesting modeling methods..."])

        return step_template.end_event()
    
    problem_description = step_template.get_variable("problem_description")
    context_description = step_template.get_variable("context_description")
    eda_summary = step_template.get_variable("eda_summary")
    response_variable_analysis = step_template.get_variable("response_variable_analysis")
    # 从Step 1获取特征工程方法（确保Step 2依赖Step 1）
    feature_engineering_methods = step_template.get_variable("feature_engineering_methods")
    # 从Stage 3获取建模方法
    stage3_model_methods = step_template.get_variable("model_methods")
    
    prediction_agent = ModelAgent(
        problem_description=problem_description,
        context_description=context_description,
        eda_summary=eda_summary,
        llm=llm
    )
    
    if step_template.think_event("suggest_modeling_methods"):
        
        # 直接使用Stage 3生成的建模方法，不重新生成
        modeling_methods_table = step_template.to_tableh(stage3_model_methods)
        
        # 显示已经准备好的特征工程方法（来自Step 1）
        feature_engineering_table = step_template.to_tableh(feature_engineering_methods)
        
        step_template \
            .add_variable("modeling_methods", stage3_model_methods) \
            .add_text("Feature Engineering Methods (from Step 1):") \
            .add_text(feature_engineering_table) \
            .add_text("Modeling Methods (from Stage 3):") \
            .add_text(modeling_methods_table) \
            .add_text("✅ Both feature engineering and modeling methods are now integrated and ready for comprehensive training.")
        
        return step_template.end_event()
            
    return None