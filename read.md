# Housing Price Prediction Model

Design and implement a housing price prediction model with rigorous RMSE and R² goals, according to PCS standards.

## Data Existence Establishment

### Data Collection and Initial Inventory

Loading the Housing dataset to begin exploration and preparation for building the price prediction model.

```python
import pandas as pd

# Load the dataset
housing_data = pd.read_csv('./assets/housing.csv')

# General overview of the dataset
housing_data_info = housing_data.info()
housing_data_head = housing_data.head()

# Display artifacts
housing_data_info, housing_data_head
```

<output>
<class 'pandas.core.frame.DataFrame'>
RangeIndex: 2930 entries, 0 to 2929
Data columns (total 82 columns):
 #   Column           Non-Null Count  Dtype  
---  ------           --------------  -----  
 0   Order            2930 non-null   int64  
 1   PID              2930 non-null   int64  
 2   MS SubClass      2930 non-null   int64  
 3   MS Zoning        2930 non-null   object 
 4   Lot Frontage     2440 non-null   float64
 5   Lot Area         2930 non-null   int64  
 6   Street           2930 non-null   object 
 7   Alley            198 non-null    object 
 8   Lot Shape        2930 non-null   object 
 9   Land Contour     2930 non-null   object 
 10  Utilities        2930 non-null   object 
 11  Lot Config       2930 non-null   object 
 12  Land Slope       2930 non-null   object 
 13  Neighborhood     2930 non-null   object 
 14  Condition 1      2930 non-null   object 
 15  Condition 2      2930 non-null   object 
 16  Bldg Type        2930 non-null   object 
 17  House Style      2930 non-null   object 
 18  Overall Qual     2930 non-null   int64  
 19  Overall Cond     2930 non-null   int64  
 20  Year Built       2930 non-null   int64  
 21  Year Remod/Add   2930 non-null   int64  
 22  Roof Style       2930 non-null   object 
 23  Roof Matl        2930 non-null   object 
 24  Exterior 1st     2930 non-null   object 
 25  Exterior 2nd     2930 non-null   object 
 26  Mas Vnr Type     1155 non-null   object 
 27  Mas Vnr Area     2907 non-null   float64
 28  Exter Qual       2930 non-null   object 
 29  Exter Cond       2930 non-null   object 
 30  Foundation       2930 non-null   object 
 31  Bsmt Qual        2850 non-null   object 
 32  Bsmt Cond        2850 non-null   object 
 33  Bsmt Exposure    2847 non-null   object 
 34  BsmtFin Type 1   2850 non-null   object 
 35  BsmtFin SF 1     2929 non-null   float64
 36  BsmtFin Type 2   2849 non-null   object 
 37  BsmtFin SF 2     2929 non-null   float64
 38  Bsmt Unf SF      2929 non-null   float64
 39  Total Bsmt SF    2929 non-null   float64
 40  Heating          2930 non-null   object 
 41  Heating QC       2930 non-null   object 
 42  Central Air      2930 non-null   object 
 43  Electrical       2929 non-null   object 
 44  1st Flr SF       2930 non-null   int64  
 45  2nd Flr SF       2930 non-null   int64  
 46  Low Qual Fin SF  2930 non-null   int64  
 47  Gr Liv Area      2930 non-null   int64  
 48  Bsmt Full Bath   2928 non-null   float64
 49  Bsmt Half Bath   2928 non-null   float64
 50  Full Bath        2930 non-null   int64  
 51  Half Bath        2930 non-null   int64  
 52  Bedroom AbvGr    2930 non-null   int64  
 53  Kitchen AbvGr    2930 non-null   int64  
 54  Kitchen Qual     2930 non-null   object 
 55  TotRms AbvGrd    2930 non-null   int64  
 56  Functional       2930 non-null   object 
 57  Fireplaces       2930 non-null   int64  
 58  Fireplace Qu     1508 non-null   object 
 59  Garage Type      2773 non-null   object 
 60  Garage Yr Blt    2771 non-null   float64
 61  Garage Finish    2771 non-null   object 
 62  Garage Cars      2929 non-null   float64
 63  Garage Area      2929 non-null   float64
 64  Garage Qual      2771 non-null   object 
 65  Garage Cond      2771 non-null   object 
 66  Paved Drive      2930 non-null   object 
 67  Wood Deck SF     2930 non-null   int64  
 68  Open Porch SF    2930 non-null   int64  
 69  Enclosed Porch   2930 non-null   int64  
 70  3Ssn Porch       2930 non-null   int64  
 71  Screen Porch     2930 non-null   int64  
 72  Pool Area        2930 non-null   int64  
 73  Pool QC          13 non-null     object 
 74  Fence            572 non-null    object 
 75  Misc Feature     106 non-null    object 
 76  Misc Val         2930 non-null   int64  
 77  Mo Sold          2930 non-null   int64  
 78  Yr Sold          2930 non-null   int64  
 79  Sale Type        2930 non-null   object 
 80  Sale Condition   2930 non-null   object 
 81  SalePrice        2930 non-null   int64  
dtypes: float64(11), int64(28), object(43)
memory usage: 1.8+ MB
</output>
<output>
(None,
    Order        PID  MS SubClass MS Zoning  Lot Frontage  Lot Area Street  \
 0      1  526301100           20        RL         141.0     31770   Pave   
 1      2  526350040           20        RH          80.0     11622   Pave   
 2      3  526351010           20        RL          81.0     14267   Pave   
 3      4  526353030           20        RL          93.0     11160   Pave   
 4      5  527105010           60        RL          74.0     13830   Pave   
 
   Alley Lot Shape Land Contour  ... Pool Area Pool QC  Fence Misc Feature  \
 0   NaN       IR1          Lvl  ...         0     NaN    NaN          NaN   
 1   NaN       Reg          Lvl  ...         0     NaN  MnPrv          NaN   
 2   NaN       IR1          Lvl  ...         0     NaN    NaN         Gar2   
 3   NaN       Reg          Lvl  ...         0     NaN    NaN          NaN   
 4   NaN       IR1          Lvl  ...         0     NaN  MnPrv          NaN   
 
   Misc Val Mo Sold Yr Sold Sale Type  Sale Condition  SalePrice  
 0        0       5    2010       WD           Normal     215000  
 1        0       6    2010       WD           Normal     105000  
 2    12500       6    2010       WD           Normal     172000  
 3        0       4    2010       WD           Normal     244000  
 4        0       3    2010       WD           Normal     189900  
 
 [5 rows x 82 columns])
</output>

The next step involves handling missing values and preparing the data for predictive modeling. It is essential to address these data quality issues to ensure the model's robustness and accuracy.

```python
import pandas as pd

# Load the dataset
df = pd.read_csv('./assets/housing.csv')

# Handling missing values
df['Lot Frontage'].fillna(df['Lot Frontage'].median(), inplace=True)
df['Mas Vnr Area'].fillna(0, inplace=True)
df['Electrical'].fillna(df['Electrical'].mode()[0], inplace=True)

# Dropping columns with too many missing values
df.drop(columns=['Alley', 'Pool QC', 'Fence', 'Misc Feature'], inplace=True)

# Verification of handling
df.isnull().sum().sum()
```

<output>
/var/folders/b2/6rjxtnps1xz417298vsyzk440000gn/T/ipykernel_19660/3067890822.py:7: FutureWarning: A value is trying to be set on a copy of a DataFrame or Series through chained assignment using an inplace method.
The behavior will change in pandas 3.0. This inplace method will never work because the intermediate object on which we are setting values always behaves as a copy.

For example, when doing 'df[col].method(value, inplace=True)', try using 'df.method({col: value}, inplace=True)' or df[col] = df[col].method(value) instead, to perform the operation inplace on the original object.


  df['Lot Frontage'].fillna(df['Lot Frontage'].median(), inplace=True)
/var/folders/b2/6rjxtnps1xz417298vsyzk440000gn/T/ipykernel_19660/3067890822.py:8: FutureWarning: A value is trying to be set on a copy of a DataFrame or Series through chained assignment using an inplace method.
The behavior will change in pandas 3.0. This inplace method will never work because the intermediate object on which we are setting values always behaves as a copy.

For example, when doing 'df[col].method(value, inplace=True)', try using 'df.method({col: value}, inplace=True)' or df[col] = df[col].method(value) instead, to perform the operation inplace on the original object.


  df['Mas Vnr Area'].fillna(0, inplace=True)
/var/folders/b2/6rjxtnps1xz417298vsyzk440000gn/T/ipykernel_19660/3067890822.py:9: FutureWarning: A value is trying to be set on a copy of a DataFrame or Series through chained assignment using an inplace method.
The behavior will change in pandas 3.0. This inplace method will never work because the intermediate object on which we are setting values always behaves as a copy.

For example, when doing 'df[col].method(value, inplace=True)', try using 'df.method({col: value}, inplace=True)' or df[col] = df[col].method(value) instead, to perform the operation inplace on the original object.


  df['Electrical'].fillna(df['Electrical'].mode()[0], inplace=True)
</output>
<output>
np.int64(4404)
</output>

Let's proceed by addressing these warnings and ensure our imputation approach is compatible with future Pandas releases. We will adjust our code to avoid the deprecated inplace modifications.

```python
import pandas as pd

# Reload the dataset to apply changes correctly without warnings
df = pd.read_csv('./assets/housing.csv')

# Correct approach to fill missing values
df['Lot Frontage'] = df['Lot Frontage'].fillna(df['Lot Frontage'].median())
df['Mas Vnr Area'] = df['Mas Vnr Area'].fillna(0)
df['Electrical'] = df['Electrical'].fillna(df['Electrical'].mode()[0])

print("Data imputation completed without utilizing deprecated inplace methods.")
```

<output>
Data imputation completed without utilizing deprecated inplace methods.
</output>

Now that we have cleaned the dataset by handling missing values, the next step is to perform feature selection and create a predictive model. Feature selection will help us reduce overfitting and improve the model's performance.

```python
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np

# Define target and features
df = pd.read_csv('./assets/housing.csv')
target = df['SalePrice']
features = df.drop(['SalePrice'], axis=1).select_dtypes(include=[np.number]) # Selecting only numerical features for simplicity

# Split the dataset
X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)

# Train a RandomForest model
model = RandomForestRegressor(random_state=42)
model.fit(X_train, y_train)

# Predict and evaluate the model
predictions = model.predict(X_test)
rmse = np.sqrt(mean_squared_error(y_test, predictions))
r2 = r2_score(y_test, predictions)

rmse, r2
```

<output>
(np.float64(27329.152709593356), 0.9068440133740853)
</output>

Next, we will refine the current model to optimize its parameters and features to minimize RMSE while retaining or improving the achieved R² value.

```python
from sklearn.model_selection import GridSearchCV
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

# Define the pipeline
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('model', Ridge())
])

# Define the parameter grid for hyperparameter tuning
param_grid = {
    'model__alpha': [0.01, 0.1, 1, 10, 100]
}

# Perform grid search for optimization
grid_search = GridSearchCV(pipeline, param_grid, cv=5, scoring='neg_root_mean_squared_error')
grid_search.fit(X_train, y_train)

# Extract the best model and its performance metrics
best_model = grid_search.best_estimator_
predictions = best_model.predict(X_test)
optimized_rmse = mean_squared_error(y_test, predictions, squared=False)
optimized_r2 = r2_score(y_test, predictions)

print(f"Optimized RMSE: {optimized_rmse}")
print(f"Optimized R²: {optimized_r2}")
```

<output>
Error: 
</output>

Adjusting the data preprocessing strategy by adding robust imputation steps to handle missing values and prevent errors in model training. We will verify the missing values and apply corrections.

```python
from sklearn.impute import SimpleImputer

# Load the dataset
import pandas as pd
df = pd.read_csv('./assets/housing.csv')

# Applying imputations
imputer = SimpleImputer(strategy="median")
df_imputed = pd.DataFrame(imputer.fit_transform(df.select_dtypes(include=['float64', 'int64'])))
df_imputed.columns = df.select_dtypes(include=['float64', 'int64']).columns
df[df_imputed.columns] = df_imputed

# Verifying all missing values are handled
print(df.isnull().sum())
```

<output>
Order             0
PID               0
MS SubClass       0
MS Zoning         0
Lot Frontage      0
                 ..
Mo Sold           0
Yr Sold           0
Sale Type         0
Sale Condition    0
SalePrice         0
Length: 82, dtype: int64
</output>

Proceeding with enhanced missing value handling across problematic columns to resolve imputation inadequacies and ensure the feature matrix is devoid of NaN values for seamless model optimization.

```python
from sklearn.impute import SimpleImputer

# Improved imputation process
imputer = SimpleImputer(strategy='median')
numeric_features = df.select_dtypes(include=['float64', 'int64']).columns
df[numeric_features] = imputer.fit_transform(df[numeric_features])

# Verification step
nan_count = df.isnull().sum().sum()
print(f"Total missing values after imputation: {nan_count}")
```

<output>
Total missing values after imputation: 15067
</output>

To address remaining missing values and ensure compatibility with Sklearn's pipeline, additional imputation or preprocessing steps will be implemented. This ensures effective modeling without errors due to NaN values.

```python
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer

# Identify numerical and categorical columns
numerical_features = df.select_dtypes(include=['int64', 'float64']).columns
categorical_features = df.select_dtypes(include=['object']).columns

# Define imputers for numerical and categorical data
numerical_imputer = SimpleImputer(strategy='median')  # Median for numerical data
categorical_imputer = SimpleImputer(strategy='most_frequent')  # Mode for categorical data

# Apply imputations using ColumnTransformer
data_transformer = ColumnTransformer(
    transformers=[
        ('num', numerical_imputer, numerical_features),
        ('cat', categorical_imputer, categorical_features)
    ]
)

df_transformed = pd.DataFrame(data_transformer.fit_transform(df), columns=df.columns)

# Check for remaining missing values
missing_summary = df_transformed.isnull().sum()
print(f"Missing values summary after additional preprocessing:\\n{missing_summary}")
print(f"Total missing values after preprocessing: {missing_summary.sum()}")
```

<output>
Missing values summary after additional preprocessing:\nOrder             0
PID               0
MS SubClass       0
MS Zoning         0
Lot Frontage      0
                 ..
Mo Sold           0
Yr Sold           0
Sale Type         0
Sale Condition    0
SalePrice         0
Length: 82, dtype: int64
Total missing values after preprocessing: 0
</output>
