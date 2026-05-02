import sys
from pathlib import Path
import joblib
import pandas as pd
import numpy as np

# Add backend to path
sys.path.append(str(Path("d:/DWDM_Project/backend")))

from app.services.model_service import train_or_load_models

def check():
    bundle = train_or_load_models()
    model = bundle.regression_pipeline.named_steps["model"]
    preprocessor = bundle.regression_pipeline.named_steps["preprocess"]
    
    # Get feature names after preprocessing
    cat_features = preprocessor.named_transformers_["cat"].named_steps["encoder"].get_feature_names_out()
    num_features = preprocessor.named_transformers_["num"].named_steps["imputer"].feature_names_in_
    
    all_features = np.concatenate([num_features, cat_features])
    
    importances = model.feature_importances_
    
    feat_imp = pd.DataFrame({'feature': all_features, 'importance': importances})
    feat_imp = feat_imp.sort_values('importance', ascending=False)
    
    print("Top 20 Feature Importances:")
    print(feat_imp.head(20))
    
    # Check specifically for Rainfall and NPK
    critical = ["Rainfall_mm", "N_kgha", "P_kgha", "K_kgha", "Water_Stress_Index"]
    print("\nCritical Features Importance:")
    for c in critical:
        imp = feat_imp[feat_imp['feature'].str.contains(c)]
        print(f"{c:20}: {imp['importance'].sum():.4f}")

if __name__ == "__main__":
    check()
