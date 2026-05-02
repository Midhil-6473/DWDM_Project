import pandas as pd
df = pd.read_csv('crop_yield_cleaned_dataset.csv', nrows=10000)
# Mock 10 crops if not enough
print("Original columns:", df.columns.tolist())
MAX_TRAIN_ROWS = 5000
df_sampled = df.groupby("Crop_Type", group_keys=False).apply(lambda x: x.sample(min(len(x), MAX_TRAIN_ROWS // 10), random_state=42))
print("Sampled columns:", df_sampled.columns.tolist())
df_reset = df_sampled.reset_index(drop=True)
print("Reset columns:", df_reset.columns.tolist())
