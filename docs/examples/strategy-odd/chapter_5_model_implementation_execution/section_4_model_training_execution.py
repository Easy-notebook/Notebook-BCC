from typing import Dict, Any, Optional
from app.core.config import llm, ModelAgent
from app.models.StepTemplate import StepTemplate

async def model_training_and_evaluation_step3(
    step: Dict[str, Any], 
    state: Optional[Dict[str, Any]] = None,
    stream: bool = False
) -> Dict[str, Any]:
    state = state or {}
        
    step_template = StepTemplate(step, state)
    
    if step_template.event("start"):
        step_template.new_section("Model Training and Evaluation Strategy") \
                    .add_text("I will develop a comprehensive model training and evaluation strategy, combining the suggested feature engineering methods with the recommended models.") \
                    .next_thinking_event(event_tag="generate_training_strategy",
                                        textArray=["Prediction Agent is analyzing...","Generating model training strategy..."])

        return step_template.end_event()
    
    problem_description = step_template.get_variable("problem_description")
    context_description = step_template.get_variable("context_description")
    eda_summary = step_template.get_variable("eda_summary")
    csv_file_path = step_template.get_variable("csv_file_path")
    response_variable_analysis = step_template.get_variable("response_variable_analysis")
    feature_engineering_methods = step_template.get_variable("feature_engineering_methods")
    modeling_methods = step_template.get_variable("modeling_methods")  # 从step2获取
    
    prediction_agent = ModelAgent(
        problem_description=problem_description,
        context_description=context_description,
        eda_summary=eda_summary,
        llm=llm
    )
    
    if step_template.think_event("generate_training_strategy"):
        
        training_strategy = prediction_agent.generate_training_evaluation_strategy_cli(
            feature_methods=feature_engineering_methods,
            modeling_methods=modeling_methods
        )
        
        training_strategy_table = step_template.to_tableh(training_strategy)
        
        step_template \
            .add_variable("training_strategy", training_strategy) \
            .add_text(training_strategy_table) \
            .next_thinking_event(event_tag="generate_model_code",
                                textArray=["Prediction Agent is working...","Generating model training code..."])
        
        return step_template.end_event()
    
    if step_template.think_event("generate_model_code"):
        
        training_code = prediction_agent.generate_model_training_code_cli(
            training_strategy=step_template.get_variable("training_strategy"),
            csv_file_path=csv_file_path,
            response_variable_analysis=response_variable_analysis
        )
        
        step_template \
            .add_variable("model_training_code", training_code) \
            .add_text("The following code will train and evaluate multiple models using the selected strategies:") \
            .add_code(training_code) \
            .exe_code_cli(mark_finnish="trained and evaluated multiple models") \
            .next_thinking_event(event_tag="analyze_training_results",
                                textArray=["Prediction Agent is working...","Analyzing model training results..."])
        
        return step_template.end_event()
    
    if step_template.think_event("analyze_training_results"):
        
        training_results = step_template.get_current_effect()
        
        # 分析训练结果并生成总结
        results_analysis = prediction_agent.analyze_training_results_cli(
            training_results=training_results,
            training_strategy=step_template.get_variable("training_strategy")
        )
        
        results_table = step_template.to_tableh(results_analysis)
        
        step_template \
            .add_variable("training_results", training_results) \
            .add_variable("training_results_analysis", results_analysis) \
            .add_text("Here is the comprehensive analysis of the model training results:") \
            .add_text(results_table) \
            .add_text("✅ Model training and evaluation completed successfully.") \
        
        return step_template.end_event()
            
    return None