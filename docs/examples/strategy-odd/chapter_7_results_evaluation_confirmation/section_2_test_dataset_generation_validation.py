from typing import Dict, Any, Optional
from app.core.config import llm, ResultsEvaluationAgent
from app.models.StepTemplate import StepTemplate

async def results_evaluation_step1(
    step: Dict[str, Any], 
    state: Optional[Dict[str, Any]] = None,
    stream: bool = False
) -> Dict[str, Any]:
    state = state or {}
        
    step_template = StepTemplate(step, state)
    
    if step_template.event("start"):
        step_template.new_section("Test Dataset Generation and Validation") \
                    .add_text("I will generate comprehensive test dataset variations and establish validation procedures for robust final evaluation.") \
                    .next_thinking_event(event_tag="generate_test_datasets",
                                        textArray=["Results Agent is analyzing...","Generating test dataset variations..."])

        return step_template.end_event()
    
    problem_description = step_template.get_variable("problem_description")
    context_description = step_template.get_variable("context_description")
    stability_analysis_summary = step_template.get_variable("stability_analysis_summary")
    results_evaluation_framework = step_template.get_variable("results_evaluation_framework")
    test_dataset_strategy = step_template.get_variable("test_dataset_strategy")
    csv_file_path = step_template.get_variable("csv_file_path")
    
    results_agent = ResultsEvaluationAgent(
        problem_description=problem_description,
        context_description=context_description,
        best_five_result=str(stability_analysis_summary),
        llm=llm
    )
    
    if step_template.think_event("generate_test_datasets"):
        
        test_generation_plan = results_agent.generate_test_datasets_plan_cli(
            csv_file_path=csv_file_path,
            test_strategy=test_dataset_strategy,
            evaluation_framework=results_evaluation_framework
        )
        
        test_plan_table = step_template.to_tableh(test_generation_plan)
        
        step_template \
            .add_variable("test_generation_plan", test_generation_plan) \
            .add_text("The comprehensive plan for generating test dataset variations:") \
            .add_text(test_plan_table) \
            .next_thinking_event(event_tag="generate_validation_code",
                                textArray=["Results Agent is working...","Generating validation code..."])
        
        return step_template.end_event()
    
    if step_template.think_event("generate_validation_code"):
        
        test_validation_code = results_agent.generate_test_validation_code_cli(
            test_generation_plan=step_template.get_variable("test_generation_plan"),
            csv_file_path=csv_file_path
        )
        
        step_template \
            .add_variable("test_validation_code", test_validation_code) \
            .add_code(test_validation_code) \
            .exe_code_cli(mark_finnish="validated test dataset") \
            .next_thinking_event(event_tag="analyze_test_generation",
                                textArray=["Results Agent is analyzing...","Analyzing test dataset generation results..."])
        
        return step_template.end_event()
    
    if step_template.think_event("analyze_test_generation"):
        
        test_generation_results = step_template.get_current_effect()
        
        step_template \
            .add_variable("test_generation_results", test_generation_results) \
            .add_text("Multiple test dataset variations have been successfully generated and validated.") \
            .add_text(f"Generation Results:\n{test_generation_results}") \
            .add_text("✅ Test dataset generation and validation completed successfully.") \
        
        return step_template.end_event()
            
    return None