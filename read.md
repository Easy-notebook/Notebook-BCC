# Housing Price Prediction Project

Welcome to the Housing Price Prediction Project. 
The objective of this project is to build a predictive model for housing prices based on the given dataset. 
The model aims to meet the specified criteria:
- RMSE (Root Mean Square Error) below 25,000.
- R² (Coefficient of Determination) greater than 0.85.

These objectives align with the PCS framework, emphasizing Predictability, Computability, and Stability.

To begin, we will verify the existence of the input dataset and perform a basic inspection of its content to ensure it is ready for further analysis.

In this section, we will verify the existence of the provided dataset file (`housing.csv`) and load it into our environment. 
This is a critical step to ensure we have the necessary data for model development.

Once the dataset is successfully loaded, we will gather basic information about its structure, such as dimensions and column names.

```python
import os
import pandas as pd

# Verify file existence
file_path = './assets/housing.csv'
if not os.path.exists(file_path):
    raise FileNotFoundError(f"The file {file_path} does not exist.")

# Load dataset
df = pd.read_csv(file_path)

# Display basic dataset information
print("Dataset loaded successfully.")
print(f"Number of rows: {df.shape[0]}")
print(f"Number of columns: {df.shape[1]}")
print("Column names:", df.columns.tolist())
```

<output>
Dataset loaded successfully.
Number of rows: 2930
Number of columns: 82
Column names: ['Order', 'PID', 'MS SubClass', 'MS Zoning', 'Lot Frontage', 'Lot Area', 'Street', 'Alley', 'Lot Shape', 'Land Contour', 'Utilities', 'Lot Config', 'Land Slope', 'Neighborhood', 'Condition 1', 'Condition 2', 'Bldg Type', 'House Style', 'Overall Qual', 'Overall Cond', 'Year Built', 'Year Remod/Add', 'Roof Style', 'Roof Matl', 'Exterior 1st', 'Exterior 2nd', 'Mas Vnr Type', 'Mas Vnr Area', 'Exter Qual', 'Exter Cond', 'Foundation', 'Bsmt Qual', 'Bsmt Cond', 'Bsmt Exposure', 'BsmtFin Type 1', 'BsmtFin SF 1', 'BsmtFin Type 2', 'BsmtFin SF 2', 'Bsmt Unf SF', 'Total Bsmt SF', 'Heating', 'Heating QC', 'Central Air', 'Electrical', '1st Flr SF', '2nd Flr SF', 'Low Qual Fin SF', 'Gr Liv Area', 'Bsmt Full Bath', 'Bsmt Half Bath', 'Full Bath', 'Half Bath', 'Bedroom AbvGr', 'Kitchen AbvGr', 'Kitchen Qual', 'TotRms AbvGrd', 'Functional', 'Fireplaces', 'Fireplace Qu', 'Garage Type', 'Garage Yr Blt', 'Garage Finish', 'Garage Cars', 'Garage Area', 'Garage Qual', 'Garage Cond', 'Paved Drive', 'Wood Deck SF', 'Open Porch SF', 'Enclosed Porch', '3Ssn Porch', 'Screen Porch', 'Pool Area', 'Pool QC', 'Fence', 'Misc Feature', 'Misc Val', 'Mo Sold', 'Yr Sold', 'Sale Type', 'Sale Condition', 'SalePrice']
</output>

The dataset has been successfully loaded, containing 2930 rows and 82 columns. We will now proceed to the analysis phase, where we will assess the dataset for any missing values, anomalies, and the overall data quality. This is a critical step in preparing the data for building a robust house price prediction model.

```python
import pandas as pd

# Calculate the number of missing values in each column
missing_values = df.isnull().sum()

# Compute the percentage of missing data for each column
missing_percentage = (missing_values / len(df)) * 100

# Create a DataFrame to view the missing value percentage
missing_data_report = pd.DataFrame({'Missing Values': missing_values, 'Percentage': missing_percentage})

print("Missing Data Report:")
print(missing_data_report)
```

<output>
Missing Data Report:
                Missing Values  Percentage
Order                        0    0.000000
PID                          0    0.000000
MS SubClass                  0    0.000000
MS Zoning                    0    0.000000
Lot Frontage               490   16.723549
...                        ...         ...
Mo Sold                      0    0.000000
Yr Sold                      0    0.000000
Sale Type                    0    0.000000
Sale Condition               0    0.000000
SalePrice                    0    0.000000

[82 rows x 2 columns]
</output>

The dataset has been successfully loaded with 2930 rows and 82 columns. Based on the missing data report, several features have missing values, with 'Lot Frontage' having a relatively high percentage at about 16.73%. We will now proceed to perform data cleaning by addressing these missing values. This step is crucial to ensure accurate modeling results, as missing data can adversely affect the predictive performance of our model.

```python
import pandas as pd

# Reload the dataset
df = pd.read_csv('./assets/housing.csv')

# Define a function to fill missing values
def fill_missing_values(df):
    # Fill missing 'Lot Frontage' with median
    df['Lot Frontage'].fillna(df['Lot Frontage'].median(), inplace=True)

    # Fill missing categorical features with mode
    categorical_cols_with_missing = [col for col in df.columns if df[col].isnull().any() and df[col].dtype == 'object']
    for col in categorical_cols_with_missing:
        df[col].fillna(df[col].mode()[0], inplace=True)

    # Fill missing numerical features with median
    numerical_cols_with_missing = [col for col in df.columns if df[col].isnull().any() and df[col].dtype != 'object']
    for col in numerical_cols_with_missing:
        df[col].fillna(df[col].median(), inplace=True)

    return df

# Apply the function to clean the data
df_cleaned = fill_missing_values(df)

# Verify no missing data remains
missing_data_report = df_cleaned.isnull().sum().sum()
print(f"Total missing values after cleaning: {missing_data_report}")
```

<output>
Total missing values after cleaning: 0
</output>
<output>
/var/folders/n5/f2xb58b575b5890ps_4fwbd40000gn/T/ipykernel_2374/1743658469.py:9: FutureWarning: A value is trying to be set on a copy of a DataFrame or Series through chained assignment using an inplace method.
The behavior will change in pandas 3.0. This inplace method will never work because the intermediate object on which we are setting values always behaves as a copy.

For example, when doing 'df[col].method(value, inplace=True)', try using 'df.method({col: value}, inplace=True)' or df[col] = df[col].method(value) instead, to perform the operation inplace on the original object.


  df['Lot Frontage'].fillna(df['Lot Frontage'].median(), inplace=True)
/var/folders/n5/f2xb58b575b5890ps_4fwbd40000gn/T/ipykernel_2374/1743658469.py:14: FutureWarning: A value is trying to be set on a copy of a DataFrame or Series through chained assignment using an inplace method.
The behavior will change in pandas 3.0. This inplace method will never work because the intermediate object on which we are setting values always behaves as a copy.

For example, when doing 'df[col].method(value, inplace=True)', try using 'df.method({col: value}, inplace=True)' or df[col] = df[col].method(value) instead, to perform the operation inplace on the original object.


  df[col].fillna(df[col].mode()[0], inplace=True)
/var/folders/n5/f2xb58b575b5890ps_4fwbd40000gn/T/ipykernel_2374/1743658469.py:19: FutureWarning: A value is trying to be set on a copy of a DataFrame or Series through chained assignment using an inplace method.
The behavior will change in pandas 3.0. This inplace method will never work because the intermediate object on which we are setting values always behaves as a copy.

For example, when doing 'df[col].method(value, inplace=True)', try using 'df.method({col: value}, inplace=True)' or df[col] = df[col].method(value) instead, to perform the operation inplace on the original object.


  df[col].fillna(df[col].median(), inplace=True)
/var/folders/n5/f2xb58b575b5890ps_4fwbd40000gn/T/ipykernel_2374/1743658469.py:19: FutureWarning: A value is trying to be set on a copy of a DataFrame or Series through chained assignment using an inplace method.
The behavior will change in pandas 3.0. This inplace method will never work because the intermediate object on which we are setting values always behaves as a copy.

For example, when doing 'df[col].method(value, inplace=True)', try using 'df.method({col: value}, inplace=True)' or df[col] = df[col].method(value) instead, to perform the operation inplace on the original object.


  df[col].fillna(df[col].median(), inplace=True)
/var/folders/n5/f2xb58b575b5890ps_4fwbd40000gn/T/ipykernel_2374/1743658469.py:19: FutureWarning: A value is trying to be set on a copy of a DataFrame or Series through chained assignment using an inplace method.
The behavior will change in pandas 3.0. This inplace method will never work because the intermediate object on which we are setting values always behaves as a copy.

For example, when doing 'df[col].method(value, inplace=True)', try using 'df.method({col: value}, inplace=True)' or df[col] = df[col].method(value) instead, to perform the operation inplace on the original object.


  df[col].fillna(df[col].median(), inplace=True)
/var/folders/n5/f2xb58b575b5890ps_4fwbd40000gn/T/ipykernel_2374/1743658469.py:19: FutureWarning: A value is trying to be set on a copy of a DataFrame or Series through chained assignment using an inplace method.
The behavior will change in pandas 3.0. This inplace method will never work because the intermediate object on which we are setting values always behaves as a copy.

For example, when doing 'df[col].method(value, inplace=True)', try using 'df.method({col: value}, inplace=True)' or df[col] = df[col].method(value) instead, to perform the operation inplace on the original object.


  df[col].fillna(df[col].median(), inplace=True)
/var/folders/n5/f2xb58b575b5890ps_4fwbd40000gn/T/ipykernel_2374/1743658469.py:19: FutureWarning: A value is trying to be set on a copy of a DataFrame or Series through chained assignment using an inplace method.
The behavior will change in pandas 3.0. This inplace method will never work because the intermediate object on which we are setting values always behaves as a copy.

For example, when doing 'df[col].method(value, inplace=True)', try using 'df.method({col: value}, inplace=True)' or df[col] = df[col].method(value) instead, to perform the operation inplace on the original object.


  df[col].fillna(df[col].median(), inplace=True)
/var/folders/n5/f2xb58b575b5890ps_4fwbd40000gn/T/ipykernel_2374/1743658469.py:19: FutureWarning: A value is trying to be set on a copy of a DataFrame or Series through chained assignment using an inplace method.
The behavior will change in pandas 3.0. This inplace method will never work because the intermediate object on which we are setting values always behaves as a copy.

For example, when doing 'df[col].method(value, inplace=True)', try using 'df.method({col: value}, inplace=True)' or df[col] = df[col].method(value) instead, to perform the operation inplace on the original object.


  df[col].fillna(df[col].median(), inplace=True)
/var/folders/n5/f2xb58b575b5890ps_4fwbd40000gn/T/ipykernel_2374/1743658469.py:19: FutureWarning: A value is trying to be set on a copy of a DataFrame or Series through chained assignment using an inplace method.
The behavior will change in pandas 3.0. This inplace method will never work because the intermediate object on which we are setting values always behaves as a copy.

For example, when doing 'df[col].method(value, inplace=True)', try using 'df.method({col: value}, inplace=True)' or df[col] = df[col].method(value) instead, to perform the operation inplace on the original object.


  df[col].fillna(df[col].median(), inplace=True)
/var/folders/n5/f2xb58b575b5890ps_4fwbd40000gn/T/ipykernel_2374/1743658469.py:19: FutureWarning: A value is trying to be set on a copy of a DataFrame or Series through chained assignment using an inplace method.
The behavior will change in pandas 3.0. This inplace method will never work because the intermediate object on which we are setting values always behaves as a copy.

For example, when doing 'df[col].method(value, inplace=True)', try using 'df.method({col: value}, inplace=True)' or df[col] = df[col].method(value) instead, to perform the operation inplace on the original object.


  df[col].fillna(df[col].median(), inplace=True)
/var/folders/n5/f2xb58b575b5890ps_4fwbd40000gn/T/ipykernel_2374/1743658469.py:19: FutureWarning: A value is trying to be set on a copy of a DataFrame or Series through chained assignment using an inplace method.
The behavior will change in pandas 3.0. This inplace method will never work because the intermediate object on which we are setting values always behaves as a copy.

For example, when doing 'df[col].method(value, inplace=True)', try using 'df.method({col: value}, inplace=True)' or df[col] = df[col].method(value) instead, to perform the operation inplace on the original object.


  df[col].fillna(df[col].median(), inplace=True)
/var/folders/n5/f2xb58b575b5890ps_4fwbd40000gn/T/ipykernel_2374/1743658469.py:19: FutureWarning: A value is trying to be set on a copy of a DataFrame or Series through chained assignment using an inplace method.
The behavior will change in pandas 3.0. This inplace method will never work because the intermediate object on which we are setting values always behaves as a copy.

For example, when doing 'df[col].method(value, inplace=True)', try using 'df.method({col: value}, inplace=True)' or df[col] = df[col].method(value) instead, to perform the operation inplace on the original object.


  df[col].fillna(df[col].median(), inplace=True)
</output>
