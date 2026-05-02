import pandas as pd

# Try reading only necessary columns and limit rows if needed
try:
    df = pd.read_csv('d:/DWDM_Project/crop_yield_cleaned_dataset.csv', 
                    usecols=['Crop_Type', 'Crop_Yield_kg_ha', 'Yield_Category'],
                    nrows=500000)
    
    print("Dataset loaded successfully.")
    print(f"Shape: {df.shape}")
    
    # Global stats
    print("\nYield Stats:")
    print(df['Crop_Yield_kg_ha'].describe())
    
    # Stats per crop
    print("\nMean Yield per Crop:")
    print(df.groupby('Crop_Type')['Crop_Yield_kg_ha'].mean().sort_values(ascending=False))
    
    # Category mapping check
    print("\nMin/Max Yield per Category:")
    cat_ranges = df.groupby('Yield_Category')['Crop_Yield_kg_ha'].agg(['min', 'max'])
    print(cat_ranges)

except Exception as e:
    print(f"Error: {e}")
