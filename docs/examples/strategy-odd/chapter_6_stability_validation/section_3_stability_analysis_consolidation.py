from typing import Dict, Any, Optional
from app.core.config import llm, ModelAgent
from app.models.StepTemplate import StepTemplate

async def stability_analysis_step2(
    step: Dict[str, Any], 
    state: Optional[Dict[str, Any]] = None,
    stream: bool = False
) -> Dict[str, Any]:
    state = state or {}
        
    step_template = StepTemplate(step, state)
    
    if step_template.event("start"):
        step_template.new_section("Evaluation Results Summary and Analysis") \
                    .add_text("I will analyze and summarize the batch evaluation results to provide insights on model stability and performance across different data variations.") \
                    .next_thinking_event(event_tag="analyze_stability_results",
                                        textArray=["Prediction Agent is analyzing...","Summarizing evaluation results..."])

        return step_template.end_event()
    
    problem_description = step_template.get_variable("problem_description")
    context_description = step_template.get_variable("context_description")
    eda_summary = step_template.get_variable("eda_summary")
    batch_evaluation_strategy = step_template.get_variable("batch_evaluation_strategy")
    batch_evaluation_results = step_template.get_variable("batch_evaluation_results")
    batch_results_analysis = step_template.get_variable("batch_results_analysis")
    
    prediction_agent = ModelAgent(
        problem_description=problem_description,
        context_description=context_description,
        eda_summary=eda_summary,
        llm=llm
    )
    
    if step_template.think_event("analyze_stability_results"):
        
        stability_analysis_summary = prediction_agent.generate_stability_analysis_summary_cli(
            batch_evaluation_strategy=batch_evaluation_strategy,
            evaluation_approach=batch_results_analysis
        )
        
        stability_summary_table = step_template.to_tableh(stability_analysis_summary)
        
        step_template \
            .add_variable("stability_analysis_summary", stability_analysis_summary) \
            .add_text("The comprehensive analysis framework for evaluating model stability:") \
            .add_text(stability_summary_table) \
            .next_thinking_event(event_tag="generate_evaluation_report",
                                textArray=["Prediction Agent is working...","Generating evaluation report template..."])
        
        return step_template.end_event()
    
    if step_template.think_event("generate_evaluation_report"):
        
        evaluation_report_template = prediction_agent.generate_evaluation_report_template_cli(
            stability_summary=step_template.get_variable("stability_analysis_summary")
        )
        
        step_template \
            .add_variable("evaluation_report_template", evaluation_report_template) \
            .add_text("The following report template will be used to document the evaluation results:") \
            .add_text(evaluation_report_template) \
            .add_text("✅ Stability analysis and evaluation framework completed successfully.") \
        
        return step_template.end_event()
            
    return None