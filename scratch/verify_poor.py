import os
import sys
import pandas as pd

# Add backend to path
sys.path.append(os.path.abspath("backend"))

from app.services.model_service import predict_single, train_or_load_models

# Ensure models are loaded
train_or_load_models()

def test_prediction(crop, name):
    # POOR conditions
    payload = {
        "Year": 2024,
        "Season": "Rabi",
        "State": "Maharashtra",
        "Latitude": 19.0,
        "Longitude": 75.0,
        "Elevation_m": 500,
        "Crop_Type": crop,
        "Irrigation_Method": "Rainfed",
        "Fertilizer_Type": "Mixed",
        "Avg_Temp_C": 40.0, # Hot
        "Max_Temp_C": 45.0,
        "Min_Temp_C": 35.0,
        "Rainfall_mm": 50.0, # Low
        "Humidity_Pct": 10.0, # Dry
        "Solar_Radiation_MJm2": 25.0,
        "Wind_Speed_kmh": 30.0,
        "ET0_mm_day": 8.0,
        "Water_Stress_Index": 0.9, # High stress
        "Soil_Type": "Sandy",
        "Soil_pH": 8.5, # Alkaline
        "Soil_Moisture_Pct": 5.0, # Very low
        "Organic_Carbon_Pct": 0.1,
        "Bulk_Density_gcm3": 1.6,
        "N_kgha": 5.0, # Very low
        "P_kgha": 2.0,
        "K_kgha": 5.0,
        "Sulfur_kgha": 2.0,
        "Zinc_ppm": 0.1,
        "Iron_ppm": 1.0,
        "NDVI": 0.2, # Poor vigor
        "Pest_Incidence": "High",
        "Disease_Incidence": "High"
    }
    
    res = predict_single(payload)
    print(f"\n--- Results for POOR {name} ({crop}) ---")
    print(f"Predicted Yield: {res['predicted_yield_kg_ha']:.2f} kg/ha")
    print(f"Predicted Category: {res['predicted_category']}")
    print(f"Typical Mean: {res['typical_mean_yield']:.2f} kg/ha")
    
    from app.services.data_service import get_crop_stats
    stats = get_crop_stats()[crop]
    print(f"Thresholds: Low <= {stats['p33']:.1f}, High > {stats['p66']:.1f}")

test_prediction("Chickpea", "Poor Case 1")
test_prediction("Cotton", "Poor Case 2")
