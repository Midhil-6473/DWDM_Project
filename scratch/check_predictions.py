import sys
from pathlib import Path
import pandas as pd

# Add backend to path
sys.path.append(str(Path("d:/DWDM_Project/backend")))

from app.services.model_service import predict_single, train_or_load_models
from app.services.data_service import get_dataframe

def check():
    print("Loading models...")
    train_or_load_models()
    
    df = get_dataframe()
    crops = df["Crop_Type"].unique()
    
    print(f"{'Crop':15} | {'Yield (kg/ha)':15} | {'Category':10}")
    print("-" * 45)
    
    for crop in crops:
        # Create a "low" condition record
        payload = {
            "Season": "Kharif",
            "State": "Andhra Pradesh",
            "Crop_Type": crop,
            "Soil_Type": "Clay Loam",
            "Irrigation_Method": "Drip",
            "Fertilizer_Type": "Dap",
            "Avg_Temp_C": 42.0,  # Extreme Heat
            "Rainfall_mm": 5.0,   # Extremely Low rainfall
            "Humidity_Pct": 20.0, # Very Dry
            "Water_Stress_Index": 0.95, # Extreme stress
            "Soil_pH": 9.0, # Alkaline soil
            "N_kgha": 0.0, # Zero nitrogen
            "P_kgha": 0.0,
            "K_kgha": 0.0,
            "NDVI": 0.05 # Barely any vegetation
        }
        
        try:
            res = predict_single(payload)
            print(f"{crop:15} | {res['predicted_yield_kg_ha']:15.2f} | {res['predicted_category']:10}")
        except Exception as e:
            print(f"{crop:15} | Error: {e}")

if __name__ == "__main__":
    check()
