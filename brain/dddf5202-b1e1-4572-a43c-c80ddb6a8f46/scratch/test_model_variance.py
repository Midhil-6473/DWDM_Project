import os
import joblib
import pandas as pd
from pathlib import Path
import sys

# Add cropai_app to path
sys.path.append(str(Path("d:/DWDM_Project/cropai_app")))

from utils.crop_constants import INPUT_COLUMNS, MODEL_DEFAULTS, CROPS
from utils.model_features import normalize_input_record

def test_models():
    model_dir = Path("d:/DWDM_Project/cropai_app/models")
    reg_path = model_dir / "random_forest_regressor.pkl"
    cls_path = model_dir / "random_forest_classifier.pkl"
    
    if not reg_path.exists():
        print(f"Regression model not found at {reg_path}")
        return
    if not cls_path.exists():
        print(f"Classification model not found at {cls_path}")
        return
        
    reg_model = joblib.load(reg_path)
    cls_model = joblib.load(cls_path)
    
    print(f"Models loaded successfully.")
    
    results = []
    for crop in CROPS:
        data = MODEL_DEFAULTS.copy()
        data["Crop_Type"] = crop
        
        # Adjust some values to be "low" to see if it changes
        data["Rainfall_mm"] = 10
        data["N_kgha"] = 5
        data["P_kgha"] = 5
        data["K_kgha"] = 5
        
        record = normalize_input_record(data)
        df = pd.DataFrame([record], columns=INPUT_COLUMNS)
        
        # Try to predict
        # We need to handle features correctly as safe_predict does
        # For simplicity in test script, we'll try to find feature names
        feat_in = getattr(reg_model, "feature_names_in_", None)
        if feat_in is not None:
            input_df = df[feat_in]
        else:
            input_df = df
            
        reg_pred = reg_model.predict(input_df)[0]
        cls_pred = cls_model.predict(input_df)[0]
        
        results.append({
            "Crop": crop,
            "Reg": reg_pred,
            "Cls": cls_pred
        })
        
    for res in results:
        print(f"Crop: {res['Crop']:10} | Yield: {res['Reg']:10.2f} | Cat: {res['Cls']}")

if __name__ == "__main__":
    test_models()
