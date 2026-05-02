import pandas as pd
from pathlib import Path

df = pd.read_csv("d:/DWDM_Project/crop_yield_cleaned_dataset.csv")

crops = df["Crop_Type"].unique()

print(f"{'Crop':<15} | {'Category':<10} | {'Count':<6} | {'Mean Yield':<10}")
print("-" * 50)

for crop in sorted(crops):
    crop_df = df[df["Crop_Type"] == crop]
    for cat in ["Low", "Medium", "High"]:
        cat_df = crop_df[crop_df["Yield_Category"] == cat]
        if not cat_df.empty:
            print(f"{crop:<15} | {cat:<10} | {len(cat_df):<6} | {cat_df['Crop_Yield_kg_ha'].mean():.2f}")
    print("-" * 50)
