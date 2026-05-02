import sys
from pathlib import Path
import pandas as pd

# Add backend to path
sys.path.append(str(Path("d:/DWDM_Project/backend")))

from app.services.data_service import get_dataframe

def analyze():
    df = get_dataframe()
    crops = ["Rice", "Wheat", "Chickpea", "Mustard"]
    
    for crop in crops:
        yields = df[df["Crop_Type"] == crop]["Crop_Yield_kg_ha"]
        print(f"--- {crop} ---")
        print(f"Min: {yields.min():.2f}")
        print(f"33%: {yields.quantile(0.33):.2f}")
        print(f"66%: {yields.quantile(0.66):.2f}")
        print(f"Max: {yields.quantile(1.0):.2f}")
        print(f"Mean: {yields.mean():.2f}")
        print()

if __name__ == "__main__":
    analyze()
