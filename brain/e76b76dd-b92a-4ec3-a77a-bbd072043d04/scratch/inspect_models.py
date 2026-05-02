import os
import joblib
import pandas as pd
from pathlib import Path
import sys

# Add cropai_app to path
BASE = Path("d:/DWDM_Project/cropai_app")
sys.path.append(str(BASE))

from utils.crop_constants import INPUT_COLUMNS, OPTIMAL_PRESET
from utils.model_features import frame_from_form_dict, normalize_category_label, safe_predict

def test_models():
    model_dir = BASE / "models"
    reg_model = joblib.load(model_dir / "regression_pipeline.joblib")
    cls_model = joblib.load(model_dir / "classification_pipeline.joblib")
    pre = None # Pipeline already has preprocessor

    print(f"Regression model type: {type(reg_model)}")
    print(f"Classification model type: {type(cls_model)}")

    crops_to_test = ["Rice", "Wheat", "Maize"]
    
    for crop in crops_to_test:
        print(f"\n--- Testing {crop} ---")
        # Optimal case
        data = dict(OPTIMAL_PRESET[crop])
        data["Crop_Type"] = crop
        data["Season"] = "Kharif" if crop != "Wheat" else "Rabi"
        data["State"] = "Punjab"
        
        frame = frame_from_form_dict(data)
        
        reg_pred = safe_predict(reg_model, frame, pre)
        cls_pred = safe_predict(cls_model, frame, pre)
        
        print(f"  Optimal Yield: {reg_pred[0]}")
        print(f"  Optimal Category Raw: {cls_pred[0]} ({type(cls_pred[0])})")
        print(f"  Optimal Category Normalized: {normalize_category_label(cls_pred[0])}")

        # Extreme High case
        high_data = data.copy()
        high_data["N_kgha"] = 300
        high_data["Rainfall_mm"] = 500
        high_data["Avg_Temp_C"] = 30
        
        frame_high = frame_from_form_dict(high_data)
        reg_pred_high = safe_predict(reg_model, frame_high, pre)
        cls_pred_high = safe_predict(cls_model, frame_high, pre)
        
        print(f"  High Yield: {reg_pred_high[0]}")
        print(f"  High Category Raw: {cls_pred_high[0]}")
        print(f"  High Category Normalized: {normalize_category_label(cls_pred_high[0])}")

        # Extreme Low case
        low_data = data.copy()
        low_data["N_kgha"] = 0
        low_data["Rainfall_mm"] = 0
        low_data["Avg_Temp_C"] = 10
        
        frame_low = frame_from_form_dict(low_data)
        reg_pred_low = safe_predict(reg_model, frame_low, pre)
        cls_pred_low = safe_predict(cls_model, frame_low, pre)
        
        print(f"  Low Yield: {reg_pred_low[0]}")
        print(f"  Low Category Raw: {cls_pred_low[0]}")
        print(f"  Low Category Normalized: {normalize_category_label(cls_pred_low[0])}")

if __name__ == "__main__":
    test_models()
