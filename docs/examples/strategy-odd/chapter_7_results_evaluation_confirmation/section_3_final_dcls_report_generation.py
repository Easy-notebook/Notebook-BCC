from typing import Dict, Any, Optional
from app.core.config import llm, ResultsEvaluationAgent
from app.models.StepTemplate import StepTemplate

async def results_evaluation_step2(
    step: Dict[str, Any], 
    state: Optional[Dict[str, Any]] = None,
    stream: bool = False
) -> Dict[str, Any]:
    state = state or {}
        
    step_template = StepTemplate(step, state)
    
    if step_template.event("start"):
        step_template.new_section("Final Model Evaluation and DCLS Analysis Report") \
                    .add_text("I will conduct the final comprehensive evaluation and generate the complete DCLS analysis report with actionable insights and recommendations.") \
                    .next_thinking_event(event_tag="conduct_final_evaluation",
                                        textArray=["Results Agent is analyzing...","Conducting final model evaluation..."])

        return step_template.end_event()
    
    problem_description = step_template.get_variable("problem_description")
    context_description = step_template.get_variable("context_description")
    stability_analysis_summary = step_template.get_variable("stability_analysis_summary")
    results_evaluation_framework = step_template.get_variable("results_evaluation_framework")
    test_generation_plan = step_template.get_variable("test_generation_plan")
    test_validation_code = step_template.get_variable("test_validation_code")
    
    results_agent = ResultsEvaluationAgent(
        problem_description=problem_description,
        context_description=context_description,
        best_five_result=str(stability_analysis_summary),
        llm=llm
    )
    
    if step_template.think_event("conduct_final_evaluation"):
        
        final_evaluation_strategy = results_agent.generate_final_evaluation_strategy_cli(
            evaluation_framework=results_evaluation_framework,
            test_plan=test_generation_plan,
            validation_code=test_validation_code
        )
        
        final_evaluation_table = step_template.to_tableh(final_evaluation_strategy)
        
        step_template \
            .add_variable("final_evaluation_strategy", final_evaluation_strategy) \
            .add_text("Here is the comprehensive strategy for final model evaluation across all test variations:") \
            .add_text(final_evaluation_table) \
            .next_thinking_event(event_tag="execute_final_evaluation",
                                textArray=["Results Agent is working...","Executing final model evaluation..."])
        
        return step_template.end_event()
    
    if step_template.think_event("execute_final_evaluation"):
        
        # 生成最终评估代码
        final_evaluation_code = results_agent.generate_final_evaluation_code_cli(
            evaluation_strategy=step_template.get_variable("final_evaluation_strategy"),
            test_validation_code=step_template.get_variable("test_validation_code"),
            csv_file_path=step_template.get_variable("csv_file_path")
        )
        
        step_template \
            .add_variable("final_evaluation_code", final_evaluation_code) \
            .add_text("The following code will execute the comprehensive final evaluation across all test scenarios:") \
            .add_code(final_evaluation_code) \
            .exe_code_cli(mark_finnish="executed final model evaluation") \
            .next_thinking_event(event_tag="analyze_final_results",
                                textArray=["Results Agent is analyzing...","Analyzing final evaluation results..."])
        
        return step_template.end_event()
    
    if step_template.think_event("analyze_final_results"):
        
        final_evaluation_results = step_template.get_current_effect()
        
        step_template \
            .add_variable("final_evaluation_results", final_evaluation_results) \
            .add_text("The comprehensive final evaluation has been completed across all test scenarios.") \
            .add_text(f"Final Results:\n{final_evaluation_results}") \
            .next_thinking_event(event_tag="generate_final_report",
                                textArray=["Results Agent is finalizing...","Generating comprehensive DCLS report..."])
        
        return step_template.end_event()
    
    if step_template.think_event("generate_final_report"):
        
        dcls_final_report = results_agent.generate_dcls_final_report_cli(
            problem_description=problem_description,
            context_description=context_description,
            final_evaluation_strategy=step_template.get_variable("final_evaluation_strategy")
        )
        
        step_template \
            .add_variable("dcls_final_report", dcls_final_report) \
            .add_text("The complete DCLS methodology has been successfully applied. Here is the final comprehensive report:") \
            .add_text(dcls_final_report) \
            .next_thinking_event(event_tag="generate_recommendations",
                                textArray=["Results Agent is finalizing...","Generating actionable recommendations..."])
        
        return step_template.end_event()
    
    if step_template.think_event("generate_recommendations"):
        
        final_recommendations = results_agent.generate_actionable_recommendations_cli(
            dcls_report=step_template.get_variable("dcls_final_report")
        )
        
        recommendations_table = step_template.to_tableh(final_recommendations)
        
        step_template \
            .add_variable("final_recommendations", final_recommendations) \
            .add_text("Based on the comprehensive DCLS analysis, here are the key actionable recommendations:") \
            .add_text(recommendations_table) \
            .add_text("All 6 Stages of DCLS Methodology Executed:") \
            .add_text("1. Stage 1-3: Data Loading, Cleaning, and EDA ✓") \
            .add_text("2. Stage 4: Model Training and Evaluation ✓") \
            .add_text("3. Stage 5: Stability Analysis ✓") \
            .add_text("4. Stage 6: Results Evaluation ✓") \
            .add_text("Key Deliverables Generated:") \
            .add_text("- Comprehensive data analysis and cleaning strategy") \
            .add_text("- Feature engineering and model selection recommendations") \
            .add_text("- Stability analysis across multiple data variations") \
            .add_text("- Final model evaluation and validation results") \
            .add_text("- Complete DCLS analysis report with actionable insights") \
        
        return step_template.end_event()
            
    return None