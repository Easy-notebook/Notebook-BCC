# Explore-Agent Abilities

## Core Function: Data Cleaning, Preprocessing, and Exploratory Analysis

The Explore-Agent (𝒜_explore) is responsible for transforming raw data into analysis-ready format and conducting comprehensive exploratory data analysis.

## Primary Abilities

### 1. Data Cleaning Operations
- **handle_missing_values()**: Implements sophisticated missing value imputation strategies (mean, median, mode, group-based, predictive)
- **remove_duplicates()**: Identifies and removes duplicate records with configurable criteria
- **detect_outliers()**: Uses statistical methods (IQR, Z-score, isolation forest) to identify outliers
- **handle_outliers()**: Applies appropriate outlier treatment (removal, capping, transformation)
- **standardize_formats()**: Normalizes data formats, encodings, and representations
- **validate_data_types()**: Ensures correct data type assignment and conversion

### 2. Data Preprocessing
- **encode_categorical_variables()**: Applies one-hot encoding, label encoding, or target encoding
- **scale_numerical_features()**: Implements standardization, normalization, or robust scaling
- **transform_distributions()**: Applies log, sqrt, or other transformations to improve normality
- **handle_temporal_data()**: Processes dates, times, and extracts temporal features
- **create_derived_features()**: Generates new features from existing variables
- **handle_text_data()**: Processes text variables with tokenization, encoding, or embeddings

### 3. Exploratory Data Analysis (EDA)
- **generate_descriptive_statistics()**: Computes comprehensive statistical summaries
- **create_distribution_plots()**: Generates histograms, box plots, and density plots
- **analyze_correlations()**: Computes and visualizes correlation matrices
- **perform_bivariate_analysis()**: Examines relationships between variable pairs
- **conduct_multivariate_analysis()**: Explores complex multi-variable relationships
- **identify_patterns()**: Discovers trends, seasonality, and structural patterns

### 4. Data Visualization
- **create_univariate_plots()**: Generates single-variable distribution visualizations
- **generate_bivariate_plots()**: Creates scatter plots, box plots by group, etc.
- **build_correlation_heatmaps()**: Visualizes correlation structures
- **plot_missing_patterns()**: Visualizes missing data patterns and relationships
- **create_categorical_summaries()**: Generates bar charts and frequency plots
- **produce_time_series_plots()**: Creates temporal trend and seasonality visualizations

### 5. Data Quality Assessment
- **assess_data_completeness()**: Evaluates completeness after cleaning operations
- **validate_cleaning_results()**: Ensures cleaning operations were successful
- **check_data_consistency()**: Verifies logical consistency across variables
- **evaluate_feature_quality()**: Assesses feature informativeness and relevance
- **identify_remaining_issues()**: Detects any residual data quality problems
- **document_cleaning_decisions()**: Records all data transformation decisions

### 6. Advanced Analysis
- **perform_dimensionality_analysis()**: Analyzes feature space dimensionality and complexity
- **detect_data_imbalance()**: Identifies class imbalance in target variables
- **analyze_feature_interactions()**: Explores potential feature interaction effects
- **assess_data_leakage()**: Identifies potential data leakage issues
- **evaluate_sampling_bias()**: Analyzes potential sampling biases in the dataset
- **conduct_stability_checks()**: Performs initial stability analysis on cleaned data

## Integration with PCS Principles

### Predictability Focus
- Ensures data transformations preserve predictive relationships
- Validates that cleaning doesn't introduce bias affecting generalization
- Maintains data integrity for reliable model training

### Computability Focus
- Implements efficient and scalable data processing methods
- Ensures all transformations are reproducible and documentable
- Optimizes data structures for downstream processing

### Stability Focus
- Tests robustness of cleaning decisions through sensitivity analysis
- Generates multiple cleaned datasets using different parameter settings
- Evaluates stability of statistical patterns across different processing choices

## Tool Integration
- **Code Executor**: Executes data processing and visualization scripts
- **Debug Tool**: Handles errors in data processing pipelines
- **ML Tools Library**: Uses modular functions for preprocessing and analysis
- **Image-to-Text**: Analyzes generated visualizations for insights
- **Unit Testing**: Validates data integrity after each processing step

## Collaboration with PCS-Agent
- Receives guidance on which cleaning strategies to prioritize
- Generates multiple versions of cleaned data for stability testing
- Reports cleaning decisions and their potential impact on downstream analysis
- Participates in perturbation analysis by creating alternative processing paths

## Output Format
The Explore-Agent produces:
- Cleaned and preprocessed datasets
- Comprehensive EDA reports with visualizations
- Data quality assessment summaries
- Feature engineering recommendations
- Documentation of all data transformations
- Statistical summaries and pattern discoveries
- Recommendations for modeling approaches based on data characteristics