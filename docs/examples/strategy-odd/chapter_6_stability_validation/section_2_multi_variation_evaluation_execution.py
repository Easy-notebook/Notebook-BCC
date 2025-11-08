from typing import Dict, Any, Optional
from app.core.config import llm, ModelAgent
from app.models.StepTemplate import StepTemplate

async def stability_analysis_step1(
    step: Dict[str, Any], 
    state: Optional[Dict[str, Any]] = None,
    stream: bool = False
) -> Dict[str, Any]:
    state = state or {}
        
    step_template = StepTemplate(step, state)
    
    if step_template.event("start"):
        step_template.new_section("Batch Model Evaluation Strategy") \
                    .add_text("I will design a comprehensive batch evaluation approach to assess model performance across all dataset variations.") \
                    .next_thinking_event(event_tag="generate_batch_evaluation",
                                        textArray=["Prediction Agent is analyzing...","Generating batch evaluation strategy..."])

        return step_template.end_event()
    
    problem_description = step_template.get_variable("problem_description")
    context_description = step_template.get_variable("context_description")
    eda_summary = step_template.get_variable("eda_summary")
    stability_strategy = step_template.get_variable("stability_strategy")
    dataset_variations = step_template.get_variable("dataset_variations")
    model_training_code = step_template.get_variable("model_training_code")
    
    prediction_agent = ModelAgent(
        problem_description=problem_description,
        context_description=context_description,
        eda_summary=eda_summary,
        llm=llm
    )
    
    if step_template.think_event("generate_batch_evaluation"):
        
        batch_evaluation_strategy = prediction_agent.generate_batch_evaluation_strategy_cli(
            stability_strategy=stability_strategy,
            dataset_variations=dataset_variations,
            model_training_code=model_training_code
        )
        
        batch_evaluation_table = step_template.to_tableh(batch_evaluation_strategy)
        
        step_template \
            .add_variable("batch_evaluation_strategy", batch_evaluation_strategy) \
            .add_text("The comprehensive approach for evaluating models across all dataset variations:") \
            .add_text(batch_evaluation_table) \
            .next_thinking_event(event_tag="generate_evaluation_code",
                                textArray=["Prediction Agent is working...","Generating batch evaluation code..."])
        
        return step_template.end_event()
    
    if step_template.think_event("generate_evaluation_code"):
        
        batch_evaluation_code = prediction_agent.generate_batch_evaluation_code_cli(
            batch_evaluation_strategy=step_template.get_variable("batch_evaluation_strategy"),
            csv_file_path=step_template.get_variable("csv_file_path"),
            model_training_code=model_training_code
        )
        
        step_template \
            .add_variable("batch_evaluation_code", batch_evaluation_code) \
            .add_text("The following code will execute model evaluation across all dataset variations:") \
            .add_code(batch_evaluation_code) \
            .exe_code_cli(mark_finnish="executed batch model evaluation") \
            .next_thinking_event(event_tag="analyze_batch_results",
                                textArray=["Prediction Agent is analyzing...","Analyzing batch evaluation results..."])
        
        return step_template.end_event()
    
    if step_template.think_event("analyze_batch_results"):
        
        batch_results = step_template.get_current_effect()
        
        # 分析批量评估结果
        batch_analysis = prediction_agent.analyze_batch_evaluation_results_cli(
            batch_results=batch_results,
            evaluation_strategy=step_template.get_variable("batch_evaluation_strategy")
        )
        
        analysis_table = step_template.to_tableh(batch_analysis)
        
        step_template \
            .add_variable("batch_evaluation_results", batch_results) \
            .add_variable("batch_results_analysis", batch_analysis) \
            .add_text("The comprehensive analysis of model performance across all dataset variations:") \
            .add_text(analysis_table) \
            .add_text("✅ Batch evaluation completed and analyzed successfully.") \
        
        return step_template.end_event()
            
    return None