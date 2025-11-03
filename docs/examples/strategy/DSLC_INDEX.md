# DSLC Strategy Index

Canonical DSLC stages under `docs/examples/strategy`:

- data_preparation
  - step_1_data_collection_and_inventory
  - step_2_data_quality_audit
  - step_3_missing_value_handling
  - step_4_outlier_detection_and_treatment
  - step_5_dataset_finalization
- data_analysis
  - step_1_univariate_analysis
  - step_2_bivariate_correlation
  - step_3_multivariate_analysis
  - step_4_target_variable_analysis
- model_selection
  - step_1_baseline_models
  - step_2_algorithm_suitability_assessment
  - step_3_model_comparison_and_selection
- model_training
  - step_1_feature_engineering_pipeline
  - step_2_training_workflow_execution
  - step_3_hyperparameter_optimization
  - step_4_model_persistence
- model_evaluation
  - step_1_cross_validation_assessment
  - step_2_holdout_test_evaluation
  - step_3_residual_and_error_analysis
  - step_4_pcs_validation
- model_deployment
  - step_1_prediction_generation
  - step_2_result_export_and_artifacts
  - step_3_model_card_and_usage_docs

Each step has:
- goal.txt (GOAL, PCS, OUTPUTS, ACCEPTANCE, DSLC ALIGNMENT)
- behavior_*.txt (GOAL, RECOMMENDED AGENT, ACTIONS, OUTPUT ARTIFACTS, DSLC HOOKS)
