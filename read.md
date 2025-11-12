# Housing Price Prediction Model

The objective of this project is to build a predictive model for housing prices using the Housing dataset. The model must meet specific accuracy criteria, achieving a Root Mean Squared Error (RMSE) of less than 25,000 and an R² score greater than 0.85. We will adhere to PCS (Predictability, Computability, Stability) standards throughout the project.

To begin, we will load the dataset from the provided CSV file and display its basic statistics to verify data existence and integrity.

```python
import pandas as pd

# Load the housing data
df = pd.read_csv('./assets/housing.csv')

# Display the shape of the dataframe
print(f"Dataset loaded with {df.shape[0]} rows and {df.shape[1]} columns.")
```

<output>
Dataset loaded with 2930 rows and 82 columns.
</output>

The dataset has been successfully loaded with 2930 rows and 82 columns. We will now proceed to examine the dataset structure and its basic properties. This will include checking for missing values, data types, and a summary of numerical features. 
Conducting this analysis will ensure that the dataset is ready for further processing and modeling.

```python
import pandas as pd

# Loading the previously verified dataset
df = pd.read_csv('./assets/housing.csv')

# Checking for missing values
missing_summary = df.isnull().sum().sort_values(ascending=False)

# Overview of data types
dtype_summary = df.dtypes.value_counts()

# Statistical summary of numerical features
numerical_summary = df.describe()

# Create analysis report
data_existence_report = {
    "missing_summary": missing_summary.to_dict(),
    "dtype_summary": dtype_summary.to_dict(),
    "numerical_summary": numerical_summary.to_dict()
}

# Displaying key indicators in preparation for further analysis
print(f"Missing values summary: {missing_summary.head()}")
print(f"Data types summary: {dtype_summary}")
print(f"Numerical summary:\n{numerical_summary}")
```

<output>
Missing values summary: Pool QC         2917
Misc Feature    2824
Alley           2732
Fence           2358
Mas Vnr Type    1775
dtype: int64
Data types summary: object     43
int64      28
float64    11
Name: count, dtype: int64
Numerical summary:
            Order           PID  MS SubClass  Lot Frontage       Lot Area  \
count  2930.00000  2.930000e+03  2930.000000   2440.000000    2930.000000   
mean   1465.50000  7.144645e+08    57.387372     69.224590   10147.921843   
std     845.96247  1.887308e+08    42.638025     23.365335    7880.017759   
min       1.00000  5.263011e+08    20.000000     21.000000    1300.000000   
25%     733.25000  5.284770e+08    20.000000     58.000000    7440.250000   
50%    1465.50000  5.354536e+08    50.000000     68.000000    9436.500000   
75%    2197.75000  9.071811e+08    70.000000     80.000000   11555.250000   
max    2930.00000  1.007100e+09   190.000000    313.000000  215245.000000   

       Overall Qual  Overall Cond   Year Built  Year Remod/Add  Mas Vnr Area  \
count   2930.000000   2930.000000  2930.000000     2930.000000   2907.000000   
mean       6.094881      5.563140  1971.356314     1984.266553    101.896801   
std        1.411026      1.111537    30.245361       20.860286    179.112611   
min        1.000000      1.000000  1872.000000     1950.000000      0.000000   
25%        5.000000      5.000000  1954.000000     1965.000000      0.000000   
50%        6.000000      5.000000  1973.000000     1993.000000      0.000000   
75%        7.000000      6.000000  2001.000000     2004.000000    164.000000   
max       10.000000      9.000000  2010.000000     2010.000000   1600.000000   

       ...  Wood Deck SF  Open Porch SF  Enclosed Porch   3Ssn Porch  \
count  ...   2930.000000    2930.000000     2930.000000  2930.000000   
mean   ...     93.751877      47.533447       23.011604     2.592491   
std    ...    126.361562      67.483400       64.139059    25.141331   
min    ...      0.000000       0.000000        0.000000     0.000000   
25%    ...      0.000000       0.000000        0.000000     0.000000   
50%    ...      0.000000      27.000000        0.000000     0.000000   
75%    ...    168.000000      70.000000        0.000000     0.000000   
max    ...   1424.000000     742.000000     1012.000000   508.000000   

       Screen Porch    Pool Area      Misc Val      Mo Sold      Yr Sold  \
count   2930.000000  2930.000000   2930.000000  2930.000000  2930.000000   
mean      16.002048     2.243345     50.635154     6.216041  2007.790444   
std       56.087370    35.597181    566.344288     2.714492     1.316613   
min        0.000000     0.000000      0.000000     1.000000  2006.000000   
25%        0.000000     0.000000      0.000000     4.000000  2007.000000   
50%        0.000000     0.000000      0.000000     6.000000  2008.000000   
75%        0.000000     0.000000      0.000000     8.000000  2009.000000   
max      576.000000   800.000000  17000.000000    12.000000  2010.000000   

           SalePrice  
count    2930.000000  
mean   180796.060068  
std     79886.692357  
min     12789.000000  
25%    129500.000000  
50%    160000.000000  
75%    213500.000000  
max    755000.000000  

[8 rows x 39 columns]
</output>
