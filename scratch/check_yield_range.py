import csv

max_yield = 0.0
min_yield = float('inf')
row_count = 0

with open('d:/DWDM_Project/crop_yield_cleaned_dataset.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            y = float(row['Crop_Yield_kg_ha'])
            if y > max_yield: max_yield = y
            if y < min_yield: min_yield = y
            row_count += 1
        except:
            continue

print(f"Rows: {row_count}")
print(f"Max Yield: {max_yield}")
print(f"Min Yield: {min_yield}")
