import os
import sys
import pandas as pd

# Add backend to path
sys.path.append(os.path.abspath("backend"))

from app.services.model_service import predict_single, train_or_load_models

# Ensure models are loaded
train_or_load_models()

def test_prediction(crop, name):
    # Mediocre conditions
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
        "Avg_Temp_C": 25.0,
        "Max_Temp_C": 30.0,
        "Min_Temp_C": 20.0,
        "Rainfall_mm": 400.0,
        "Humidity_Pct": 50.0,
        "Solar_Radiation_MJm2": 15.0,
        "Wind_Speed_kmh": 10.0,
        "ET0_mm_day": 4.0,
        "Water_Stress_Index": 0.3,
        "Soil_Type": "Loamy",
        "Soil_pH": 6.5,
        "Soil_Moisture_Pct": 40.0,
        "Organic_Carbon_Pct": 0.5,
        "Bulk_Density_gcm3": 1.3,
        "N_kgha": 50.0,
        "P_kgha": 25.0,
        "K_kgha": 35.0,
        "Sulfur_kgha": 15.0,
        "Zinc_ppm": 1.0,
        "Iron_ppm": 10.0,
        "NDVI": 0.5,
        "Pest_Incidence": "Moderate",
        "Disease_Incidence": "Moderate"
    }
    
    res = predict_single(payload)
    print(f"\n--- Results for {name} ({crop}) ---")
    print(f"Predicted Yield: {res['predicted_yield_kg_ha']:.2f} kg/ha")
    print(f"Predicted Category: {res['predicted_category']}")
    print(f"Typical Mean: {res['typical_mean_yield']:.2f} kg/ha")
    
    from app.services.data_service import get_crop_stats
    stats = get_crop_stats()[crop]
    print(f"Thresholds: Low <= {stats['p33']:.1f}, High > {stats['p66']:.1f}")
    
    expected = "Medium"
    if res['predicted_yield_kg_ha'] <= stats['p33']: expected = "Low"
    elif res['predicted_yield_kg_ha'] > stats['p66']: expected = "High"
    
    if res['predicted_category'] == expected:
        print("[PASS] Label is consistent with numerical yield.")
    else:
        print(f"[FAIL] Label inconsistency! Expected {expected} but got {res['predicted_category']}")

test_prediction("Chickpea", "User Case 1")
test_prediction("Cotton", "User Case 2")
test_prediction("Sugarcane", "High Yield Case")
