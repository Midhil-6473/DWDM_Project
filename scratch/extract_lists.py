import pandas as pd
from pathlib import Path

dataset_path = Path(r"d:\DWDM_Project\crop_yield_cleaned_dataset.csv")

if not dataset_path.exists():
    print(f"Dataset not found at {dataset_path}")
    exit(1)

print(f"Reading dataset: {dataset_path}...")
df = pd.read_csv(dataset_path, low_memory=False)

cols = ["State", "Crop_Type", "Soil_Type", "Season", "Irrigation_Method", "Fertilizer_Type"]

for col in cols:
    if col in df.columns:
        unique_values = sorted(df[col].dropna().unique().tolist())
        print(f"\n--- {col} ---")
        for val in unique_values:
            print(f"- {val}")
    else:
        print(f"\n--- {col} (NOT FOUND) ---")
