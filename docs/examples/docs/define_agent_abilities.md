# Define-Agent Abilities

## Core Function: Problem Formulation and Dataset Quality Evaluation

The Define-Agent (𝒜_define) serves as the entry point for the VDSAgents system, responsible for establishing the foundation of the data science project.

## Primary Abilities

### 1. Problem Formulation
- **analyze_problem_context()**: Analyzes the initial problem description and domain context
- **identify_target_variable()**: Determines the appropriate response/target variable for prediction
- **classify_problem_type()**: Categorizes the problem as classification, regression, or other ML task types
- **define_success_metrics()**: Establishes appropriate evaluation metrics based on problem type
- **set_project_constraints()**: Identifies computational, time, and resource constraints

### 2. Dataset Quality Assessment  
- **evaluate_dataset_structure()**: Analyzes dataset dimensions, column types, and basic structure
- **assess_data_completeness()**: Evaluates missing data patterns and completeness levels
- **analyze_data_distribution()**: Examines basic statistical distributions and data ranges
- **identify_data_quality_issues()**: Detects potential quality problems (duplicates, inconsistencies, outliers)
- **estimate_computational_requirements()**: Assesses memory usage and processing requirements

### 3. Data Understanding
- **examine_variable_types()**: Categorizes variables as continuous, categorical, ordinal, etc.
- **analyze_variable_relationships()**: Identifies potential relationships between variables
- **detect_data_hierarchy()**: Recognizes hierarchical or grouped data structures
- **assess_temporal_patterns()**: Identifies time-series or temporal characteristics if present
- **evaluate_domain_constraints()**: Understands domain-specific data constraints and meanings

### 4. Project Planning
- **create_analysis_roadmap()**: Develops high-level analysis strategy
- **identify_preprocessing_needs()**: Determines necessary data cleaning and preprocessing steps
- **suggest_modeling_approaches()**: Recommends appropriate modeling strategies based on data characteristics
- **estimate_complexity_level()**: Assesses overall project complexity and difficulty
- **define_validation_strategy()**: Plans appropriate validation and testing approaches

### 5. Quality Validation
- **validate_data_integrity()**: Performs initial data integrity checks
- **check_label_quality()**: Validates target variable quality and distribution
- **assess_feature_informativeness()**: Evaluates potential predictive power of features
- **identify_potential_biases()**: Detects potential data biases or collection issues
- **evaluate_representativeness()**: Assesses how well the dataset represents the target population

## Integration with PCS Principles

### Predictability Focus
- Ensures target variable is well-defined and measurable
- Validates that the dataset supports generalization goals
- Identifies factors that may impact model generalization

### Computability Focus  
- Assesses computational feasibility of the analysis
- Identifies resource requirements and constraints
- Ensures problem formulation is practically solvable

### Stability Focus
- Evaluates data robustness and consistency
- Identifies potential sources of instability in the dataset
- Plans for perturbation analysis in later stages

## Tool Integration
- **Code Executor**: Runs data exploration scripts
- **Debug Tool**: Handles execution errors and debugging
- **Unit Testing**: Validates data loading and basic integrity checks
- **Statistical Libraries**: Performs descriptive statistics and basic analysis

## Output Format
The Define-Agent produces structured reports including:
- Problem definition summary
- Dataset characteristics overview  
- Quality assessment results
- Recommended analysis strategy
- Identified risks and limitations
- Initial hypotheses and expectations