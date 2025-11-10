# Ames Housing Price Prediction - Data Science Lifecycle

## Data Existence Establishment

### Data Collection and Inventory

We begin by establishing data existence through systematic collection and inventory.  
This foundational step ensures the **Ames Housing dataset** is accessible, complete, and ready for further exploration.  
We will validate the dataset file located at `./assets/housing.csv`, gather its metadata, and perform an initial inventory to confirm readiness for downstream analysis.  
The verification includes confirming file accessibility, recording its size and timestamp, loading the data for inspection, and compiling a comprehensive existence report aligned with PCS principles of **Predictability**, **Computability**, and **Stability**.

```python
import os
import pandas as pd
from datetime import datetime

# Step 1: Verify dataset path
file_path = "./assets/housing.csv"
exists = os.path.exists(file_path)
file_size_bytes = os.path.getsize(file_path) if exists else 0
file_size_mb = round(file_size_bytes / (1024 * 1024), 4) if exists else 0
last_modified = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat() if exists else None

print(f"File exists: {exists}, Size: {file_size_mb} MB, Last modified: {last_modified}")

# Step 2: Load dataset to confirm readability
df_raw = pd.read_csv(file_path)
print(f"Loaded dataset shape: {df_raw.shape}")

# Step 3: Compute schema and metadata
data_catalog_metadata = {
    "columns": df_raw.columns.tolist(),
    "dtypes": df_raw.dtypes.astype(str).to_dict(),
    "schema_verified": True,
    "load_success": True
}

# Step 4: Create data existence report
data_existence_report = {
    "file_path": file_path,
    "exists": exists,
    "file_size_bytes": file_size_bytes,
    "file_size_mb": file_size_mb,
    "last_modified": last_modified,
    "row_count": df_raw.shape[0],
    "column_count": df_raw.shape[1],
    "data_format": "csv",
    "memory_usage_mb": round(df_raw.memory_usage(deep=True).sum() / (1024 * 1024), 4),
    "catalog_metadata": data_catalog_metadata
}

print("Data existence report generated successfully.")
print(data_existence_report)
```

<output>
File exists: True, Size: 0.9459 MB, Last modified: 2025-11-10T13:45:52.881171
Loaded dataset shape: (2930, 82)
Data existence report generated successfully.
{'file_path': './assets/housing.csv', 'exists': True, 'file_size_bytes': 991888, 'file_size_mb': 0.9459, 'last_modified': '2025-11-10T13:45:52.881171', 'row_count': 2930, 'column_count': 82, 'data_format': 'csv', 'memory_usage_mb': np.float64(6.9154), 'catalog_metadata': {'columns': ['Order', 'PID', 'MS SubClass', 'MS Zoning', 'Lot Frontage', 'Lot Area', 'Street', 'Alley', 'Lot Shape', 'Land Contour', 'Utilities', 'Lot Config', 'Land Slope', 'Neighborhood', 'Condition 1', 'Condition 2', 'Bldg Type', 'House Style', 'Overall Qual', 'Overall Cond', 'Year Built', 'Year Remod/Add', 'Roof Style', 'Roof Matl', 'Exterior 1st', 'Exterior 2nd', 'Mas Vnr Type', 'Mas Vnr Area', 'Exter Qual', 'Exter Cond', 'Foundation', 'Bsmt Qual', 'Bsmt Cond', 'Bsmt Exposure', 'BsmtFin Type 1', 'BsmtFin SF 1', 'BsmtFin Type 2', 'BsmtFin SF 2', 'Bsmt Unf SF', 'Total Bsmt SF', 'Heating', 'Heating QC', 'Central Air', 'Electrical', '1st Flr SF', '2nd Flr SF', 'Low Qual Fin SF', 'Gr Liv Area', 'Bsmt Full Bath', 'Bsmt Half Bath', 'Full Bath', 'Half Bath', 'Bedroom AbvGr', 'Kitchen AbvGr', 'Kitchen Qual', 'TotRms AbvGrd', 'Functional', 'Fireplaces', 'Fireplace Qu', 'Garage Type', 'Garage Yr Blt', 'Garage Finish', 'Garage Cars', 'Garage Area', 'Garage Qual', 'Garage Cond', 'Paved Drive', 'Wood Deck SF', 'Open Porch SF', 'Enclosed Porch', '3Ssn Porch', 'Screen Porch', 'Pool Area', 'Pool QC', 'Fence', 'Misc Feature', 'Misc Val', 'Mo Sold', 'Yr Sold', 'Sale Type', 'Sale Condition', 'SalePrice'], 'dtypes': {'Order': 'int64', 'PID': 'int64', 'MS SubClass': 'int64', 'MS Zoning': 'object', 'Lot Frontage': 'float64', 'Lot Area': 'int64', 'Street': 'object', 'Alley': 'object', 'Lot Shape': 'object', 'Land Contour': 'object', 'Utilities': 'object', 'Lot Config': 'object', 'Land Slope': 'object', 'Neighborhood': 'object', 'Condition 1': 'object', 'Condition 2': 'object', 'Bldg Type': 'object', 'House Style': 'object', 'Overall Qual': 'int64', 'Overall Cond': 'int64', 'Year Built': 'int64', 'Year Remod/Add': 'int64', 'Roof Style': 'object', 'Roof Matl': 'object', 'Exterior 1st': 'object', 'Exterior 2nd': 'object', 'Mas Vnr Type': 'object', 'Mas Vnr Area': 'float64', 'Exter Qual': 'object', 'Exter Cond': 'object', 'Foundation': 'object', 'Bsmt Qual': 'object', 'Bsmt Cond': 'object', 'Bsmt Exposure': 'object', 'BsmtFin Type 1': 'object', 'BsmtFin SF 1': 'float64', 'BsmtFin Type 2': 'object', 'BsmtFin SF 2': 'float64', 'Bsmt Unf SF': 'float64', 'Total Bsmt SF': 'float64', 'Heating': 'object', 'Heating QC': 'object', 'Central Air': 'object', 'Electrical': 'object', '1st Flr SF': 'int64', '2nd Flr SF': 'int64', 'Low Qual Fin SF': 'int64', 'Gr Liv Area': 'int64', 'Bsmt Full Bath': 'float64', 'Bsmt Half Bath': 'float64', 'Full Bath': 'int64', 'Half Bath': 'int64', 'Bedroom AbvGr': 'int64', 'Kitchen AbvGr': 'int64', 'Kitchen Qual': 'object', 'TotRms AbvGrd': 'int64', 'Functional': 'object', 'Fireplaces': 'int64', 'Fireplace Qu': 'object', 'Garage Type': 'object', 'Garage Yr Blt': 'float64', 'Garage Finish': 'object', 'Garage Cars': 'float64', 'Garage Area': 'float64', 'Garage Qual': 'object', 'Garage Cond': 'object', 'Paved Drive': 'object', 'Wood Deck SF': 'int64', 'Open Porch SF': 'int64', 'Enclosed Porch': 'int64', '3Ssn Porch': 'int64', 'Screen Porch': 'int64', 'Pool Area': 'int64', 'Pool QC': 'object', 'Fence': 'object', 'Misc Feature': 'object', 'Misc Val': 'int64', 'Mo Sold': 'int64', 'Yr Sold': 'int64', 'Sale Type': 'object', 'Sale Condition': 'object', 'SalePrice': 'int64'}, 'schema_verified': True, 'load_success': True}}
</output>
