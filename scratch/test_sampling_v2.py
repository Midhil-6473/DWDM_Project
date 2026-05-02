import pandas as pd
df = pd.read_csv('crop_yield_cleaned_dataset.csv', nrows=10000)
print("Original columns has Crop_Type?", 'Crop_Type' in df.columns)
MAX_TRAIN_ROWS = 5000
# Try the simpler way
df_sampled = df.groupby("Crop_Type", group_keys=True).sample(n=100, random_state=42)
print("Sampled columns with groupby.sample:", df_sampled.columns.tolist())
df_reset = df_sampled.reset_index(drop=True)
print("Reset columns has Crop_Type?", 'Crop_Type' in df_reset.columns)
