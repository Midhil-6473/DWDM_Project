import pandas as pd
import numpy as np

df = pd.read_csv('d:/DWDM_Project/crop_yield_cleaned_dataset.csv')

print("Target Columns Stats:")
print(df[['Crop_Yield_kg_ha', 'Yield_Category']].describe(include='all'))

print("\nYield stats per crop:")
crop_stats = df.groupby('Crop_Type')['Crop_Yield_kg_ha'].agg(['mean', 'median', 'min', 'max', 'std'])
print(crop_stats)

print("\nYield Category Distribution per Crop:")
cat_dist = pd.crosstab(df['Crop_Type'], df['Yield_Category'], normalize='index') * 100
print(cat_dist)

# Check for outliers
print("\nOutliers check (Yield > 5000):")
print(df[df['Crop_Yield_kg_ha'] > 5000]['Crop_Type'].value_counts())
