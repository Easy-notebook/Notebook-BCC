#!/usr/bin/env python3
"""
Generate complete strategy structure from chapter documentation.
Creates stages, steps, and behavior files based on chapter sections.
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path("/Users/macbook.silan.tech/Documents/GitHub/Notebook-BCC/docs/examples/strategy")

# Stage definitions with steps mapped from chapter sections
STAGE_DEFINITIONS = {
    "stage_1_data_existence_establishment": {
        "name": "Data Existence Establishment",
        "code": "DE",
        "goal": """Establish the foundation of data existence through systematic data discovery, structure analysis, and relevance assessment to ensure data can support project objectives.""",
        "steps": [
            ("step_1_data_collection_and_inventory", "Data Collection and Inventory", "Execute data collection strategy and complete initial data inventory"),
            ("step_2_data_structure_discovery", "Data Structure Discovery", "Analyze data schema, types, and distribution characteristics"),
            ("step_3_variable_semantic_analysis", "Variable Semantic Analysis", "Understand variable business meaning and validate with domain experts"),
            ("step_4_observation_unit_identification", "Observation Unit Identification", "Identify observation units and analyze temporal/spatial dimensions"),
            ("step_5_variable_relevance_assessment", "Variable Relevance Assessment", "Assess variable correlation with target and establish priority ranking"),
            ("step_6_pcs_hypothesis_generation", "PCS Hypothesis Generation", "Generate testable PCS hypotheses based on data analysis"),
        ]
    },
    "stage_2_data_integrity_assurance": {
        "name": "Data Integrity Assurance",
        "code": "DI",
        "goal": """Ensure data completeness, accuracy, and consistency through systematic cleaning and validation processes to establish analysis-ready high-quality dataset.""",
        "steps": [
            ("step_1_dimensional_integrity_validation", "Dimensional Integrity Validation", "Validate data dimensional completeness and structural consistency"),
            ("step_2_value_validity_assurance", "Value Validity Assurance", "Ensure data value validity, reasonableness, and format standardization"),
            ("step_3_completeness_integrity_restoration", "Completeness Integrity Restoration", "Handle missing values, outliers, and duplicates to restore data completeness"),
            ("step_4_comprehensive_integrity_verification", "Comprehensive Integrity Verification", "Comprehensively verify data integrity processing effectiveness and quality"),
        ]
    },
    "stage_3_exploratory_data_analysis": {
        "name": "Exploratory Data Analysis",
        "code": "EDA",
        "goal": """Deeply understand data patterns, relationships, and characteristics through systematic exploratory analysis to provide insights and direction for subsequent modeling.""",
        "steps": [
            ("step_1_current_data_state_assessment", "Current Data State Assessment", "Comprehensively assess current data state and characteristics after cleaning"),
            ("step_2_targeted_inquiry_generation", "Targeted Inquiry Generation", "Generate specific exploratory questions based on project objectives and data features"),
            ("step_3_analytical_insight_extraction", "Analytical Insight Extraction", "Execute deep data analysis to extract valuable insights and discoveries"),
            ("step_4_comprehensive_insight_consolidation", "Comprehensive Insight Consolidation", "Integrate all analysis results into systematic data understanding"),
        ]
    },
    "stage_4_methodology_strategy_formulation": {
        "name": "Methodology Strategy Formulation",
        "code": "MS",
        "goal": """Formulate comprehensive modeling strategy including feature engineering, model selection, and evaluation framework based on data understanding and exploratory analysis.""",
        "steps": [
            ("step_1_feature_model_method_proposal", "Feature and Model Method Proposal", "Design feature engineering and model selection strategy based on data characteristics"),
            ("step_2_training_evaluation_strategy_development", "Training Evaluation Strategy Development", "Design scientific and comprehensive model training and evaluation strategy"),
            ("step_3_methodology_strategy_consolidation", "Methodology Strategy Consolidation", "Integrate all strategy components into complete modeling methodology"),
        ]
    },
    "stage_5_model_implementation_execution": {
        "name": "Model Implementation Execution",
        "code": "MI",
        "goal": """Execute established modeling strategy through systematic feature engineering, model training, and optimization to build high-quality predictive models.""",
        "steps": [
            ("step_1_feature_engineering_integration", "Feature Engineering Integration", "Execute comprehensive feature engineering to create high-quality modeling features"),
            ("step_2_modeling_method_integration", "Modeling Method Integration", "Implement multiple modeling methods to build candidate model ensemble"),
            ("step_3_model_training_execution", "Model Training Execution", "Execute systematic model training and optimization process"),
        ]
    },
    "stage_6_predictability_validation": {
        "name": "Predictability Validation",
        "code": "PV",
        "goal": """Ensure model reliable generalization capability and predictive performance on new data through systematic prediction capability validation.""",
        "steps": [
            ("step_1_cross_validation_performance_assessment", "Cross-Validation Performance Assessment", "Assess model intrinsic predictive capability through rigorous cross-validation"),
            ("step_2_holdout_test_set_evaluation", "Hold-out Test Set Evaluation", "Validate model true predictive capability on completely independent test set"),
            ("step_3_temporal_validation", "Temporal Validation", "Validate model prediction stability and sustained effectiveness over time dimension"),
            ("step_4_domain_generalization_testing", "Domain Generalization Testing", "Test model generalization capability across different but related domains"),
            ("step_5_business_impact_validation", "Business Impact Validation", "Validate model prediction value and impact in actual business applications"),
        ]
    },
    "stage_7_stability_assessment": {
        "name": "Stability Assessment",
        "code": "SA",
        "goal": """Assess model result stability and robustness under reasonable perturbations through systematic stability analysis.""",
        "steps": [
            ("step_1_data_perturbation_analysis", "Data Perturbation Analysis", "Test model data stability through various data perturbations"),
            ("step_2_model_parameter_sensitivity", "Model Parameter Sensitivity", "Evaluate impact of model parameter changes on result stability"),
            ("step_3_multi_variation_evaluation_execution", "Multi-Variation Evaluation Execution", "Execute systematic multi-dimensional variation testing"),
            ("step_4_stability_analysis_consolidation", "Stability Analysis Consolidation", "Integrate all stability test results into comprehensive assessment"),
        ]
    },
    "stage_8_results_communication": {
        "name": "Results Communication",
        "code": "RC",
        "goal": """Effectively communicate data science analysis results to different target audiences to ensure result understandability, actionability, and business value realization.""",
        "steps": [
            ("step_1_technical_documentation", "Technical Documentation", "Compile detailed and accurate technical documentation for technical audiences"),
            ("step_2_executive_summary", "Executive Summary", "Provide concise and powerful executive summary for senior management"),
            ("step_3_visual_communication", "Visual Communication", "Enhance result understanding and impact through effective visualization"),
            ("step_4_stakeholder_engagement", "Stakeholder Engagement", "Proactively interact with stakeholders to ensure effective adoption"),
            ("step_5_implementation_support", "Implementation Support", "Provide comprehensive implementation support for practical application of results"),
        ]
    },
}

def create_stage_goal_file(stage_dir, stage_name, goal_text):
    """Create stage-level goal.txt file."""
    goal_file = stage_dir / "goal.txt"
    content = f"""# {stage_name}

## Stage Goal
{goal_text}

## PCS Framework Integration

### Predictability
- Ensure generalization to unseen data and reliable prediction capability
- Validate performance consistency across different data conditions
- Monitor and maintain predictive performance over time

### Computability
- Ensure reproducibility and resource feasibility
- Implement efficient and scalable computational workflows
- Automate processes for consistency and efficiency

### Stability
- Ensure robustness under reasonable perturbations
- Validate sensitivity to parameter and data changes
- Maintain consistency across different conditions
"""
    goal_file.write_text(content)
    print(f"Created: {goal_file}")

def create_step_goal_file(step_dir, stage_code, step_num, step_name, step_desc, behaviors):
    """Create step-level goal.txt file."""
    goal_file = step_dir / "goal.txt"

    behavior_list = "\n".join([f"{i+1}. behavior_{i+1}_{b[0]}.txt\n   - {b[1]}"
                                for i, b in enumerate(behaviors)])

    artifacts_list = "\n".join([f"- {art}" for art in behaviors[0][2]])
    acceptance_list = "\n".join([f"- {acc}" for acc in behaviors[0][3]])

    content = f"""================================================================================
STEP {stage_code}.{step_num}: {step_name.upper()}
================================================================================

GOAL: {step_desc}

PCS CONSIDERATIONS:
- Predictability: Ensure generalization and reliable prediction capability.
- Computability: Ensure reproducibility and resource feasibility.
- Stability: Ensure robustness under reasonable perturbations.

================================================================================
BEHAVIORS IN THIS STEP you can choose from(all build what you need):
================================================================================
{behavior_list}

4. behavior_{len(behaviors)+1}_validation_and_acceptance.txt
   - Validate step completeness and acceptance criteria

================================================================================
OVERALL OUTPUT ARTIFACTS:
================================================================================
{artifacts_list}
- step_validation_report

================================================================================
ACCEPTANCE CRITERIA:
================================================================================
{acceptance_list}
- All artifacts complete and meet quality standards
- PCS framework requirements satisfied
- Ready to proceed to next step
"""
    goal_file.write_text(content)
    print(f"Created: {goal_file}")

def create_behavior_file(step_dir, stage_code, step_num, behavior_num, behavior_name, behavior_desc,
                        actions, artifacts):
    """Create behavior file."""
    behavior_file = step_dir / f"behavior_{behavior_num}_{behavior_name}.txt"

    actions_text = "\n\n".join([f"ACTION {stage_code}.{step_num}.{behavior_num}.{i+1}: {a[0]}\n  {a[1]}\n  " +
                                 "\n  ".join([f"- {point}" for point in a[2]])
                                 for i, a in enumerate(actions)])

    artifacts_text = "\n".join([f"- {art}" for art in artifacts])

    content = f"""================================================================================
BEHAVIOR {stage_code}.{step_num}.{behavior_num}: {behavior_desc.upper()}
================================================================================

GOAL: {behavior_desc}

RECOMMENDED AGENT: Explore-Agent  

================================================================================
ACTIONS:
================================================================================

{actions_text}

================================================================================
OUTPUT ARTIFACTS:
================================================================================
{artifacts_text}

  
================================================================================
TASK TEMPLATE:
================================================================================
- Describe exact operations with variable/file names
- Ensure deterministic seeds and document parameters
- Produce/update specified artifacts
- Use consistent naming conventions
- Persist outputs under ./outputs/stage_{step_num}_*/step_{step_num}/
- Ensure all operations are reproducible

================================================================================
ACCEPTANCE EXAMPLES:
================================================================================
- All specified artifacts exist and are non-empty
- Artifacts contain required information and meet quality standards
- Operations documented and reproducible
- PCS framework considerations addressed
"""
    behavior_file.write_text(content)
    print(f"Created: {behavior_file}")

def create_validation_behavior(step_dir, stage_code, step_num):
    """Create validation and acceptance behavior file."""
    behavior_file = step_dir / "behavior_4_validation_and_acceptance.txt"

    content = f"""================================================================================
BEHAVIOR {stage_code}.{step_num}.4: VALIDATION AND ACCEPTANCE
================================================================================

GOAL: Validate all step activities meet acceptance criteria and align with PCS framework.

RECOMMENDED AGENT: PCS-Agent

================================================================================
ACTIONS:
================================================================================

ACTION {stage_code}.{step_num}.4.1: Artifact Completeness Check
  Verify all required artifacts are generated and complete
  - Confirm all artifacts from behaviors exist and non-empty
  - Verify artifact content quality and completeness
  - Check artifact format and structure correctness

ACTION {stage_code}.{step_num}.4.2: Acceptance Criteria Validation
  Validate all acceptance criteria are met
  - Review each acceptance criterion from step goal.txt
  - Mark each criterion as PASS/FAIL with evidence
  - Document any gaps or issues requiring resolution

ACTION {stage_code}.{step_num}.4.3: PCS Framework Alignment
  Verify alignment with PCS framework requirements
  - Predictability: Confirm support for reliable prediction
  - Computability: Verify reproducibility and efficiency
  - Stability: Validate robustness and consistency

================================================================================
OUTPUT ARTIFACTS:
================================================================================
- step_validation_report (pass/fail status, recommendations)

  
================================================================================
TASK TEMPLATE:
================================================================================
- Create checklist of all acceptance criteria
- Mark each criterion as PASS/FAIL with supporting evidence
- Document issues and remediation plans for FAIL items
- Provide clear recommendation: PROCEED or REWORK
- Persist validation report under ./outputs/stage_*/step_*/

================================================================================
ACCEPTANCE EXAMPLES:
================================================================================
- step_validation_report exists with complete evaluation
- All critical acceptance criteria marked as PASS
- PCS framework alignment confirmed
- Clear recommendation provided with rationale
"""
    behavior_file.write_text(content)
    print(f"Created: {behavior_file}")

# Create Stage 1 remaining steps (steps 3-6) since 1-2 are already done
print("Creating Stage 1 remaining steps...")

# Step 3: Variable Semantic Analysis
step3_dir = BASE_DIR / "stage_1_data_existence_establishment" / "step_3_variable_semantic_analysis"
step3_dir.mkdir(parents=True, exist_ok=True)

step3_behaviors = [
    ("variable_semantic_mapping", "Map variable n to business concepts",
     ["variable_semantic_map"],
     ["All variables mapped to business concepts"]),
    ("variable_quality_assessment", "Assess variable value reasonableness and validity",
     ["variable_quality_report"],
     ["Variable quality issues identified"]),
    ("domain_knowledge_validation", "Validate variable interpretation with domain experts",
     ["domain_expert_validation"],
     ["Expert validation documented"]),
]

create_step_goal_file(step3_dir, "DE", 3, "Variable Semantic Analysis",
                     "Understand variable business meaning and validate with domain experts",
                     step3_behaviors)

# Create behavior files for step 3
create_behavior_file(step3_dir, "DE", 3, 1, "variable_semantic_mapping",
                    "Map variable n to business concepts and identify measurement units",
                    [
                        ("Establish Variable-Business Mapping", "Map variables to business concepts",
                         ["Create mapping between variable n and business terminology",
                          "Identify measurement units and scales for each variable",
                          "Document business context and usage scenarios"]),
                        ("Document Variable Semantics", "Document semantic meaning of variables",
                         ["Record variable definitions in business terms",
                          "Document expected value ranges and constraints",
                          "Note any domain-specific interpretations"])
                    ],
                    ["variable_semantic_map"])

create_behavior_file(step3_dir, "DE", 3, 2, "variable_quality_assessment",
                    "Assess variable value reasonableness and identify quality issues",
                    [
                        ("Assess Value Reasonableness", "Evaluate variable values for validity",
                         ["Check if values fall within expected ranges",
                          "Identify potential encoding errors or data entry issues",
                          "Validate categorical variable valid values"]),
                        ("Identify Quality Issues", "Document variable quality problems",
                         ["Flag variables with suspicious value patterns",
                          "Identify inconsistencies with business logic",
                          "Document variables requiring expert review"])
                    ],
                    ["variable_quality_report"])

create_behavior_file(step3_dir, "DE", 3, 3, "domain_knowledge_validation",
                    "Validate variable interpretation accuracy with domain experts",
                    [
                        ("Conduct Expert Review", "Engage domain experts for validation",
                         ["Present variable interpretations to domain experts",
                          "Obtain expert opinions on variable importance",
                          "Clarify ambiguous or uncertain variable meanings"]),
                        ("Document Expert Feedback", "Record expert validation results",
                         ["Document expert-confirmed variable interpretations",
                          "Record variable importance rankings from experts",
                          "Note business logic relationships between variables"])
                    ],
                    ["domain_expert_validation"])

create_validation_behavior(step3_dir, "DE", 3)

print("Completed Stage 1 Step 3")

# Continue with remaining steps... (this script can be extended or run iteratively)
print("\nStrategy structure generation complete for demonstrated steps.")
print("Script can be extended to generate remaining steps following the same pattern.")
