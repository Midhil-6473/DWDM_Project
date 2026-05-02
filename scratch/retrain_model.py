import os
import sys

# Add backend to path so we can import app
sys.path.append(os.path.abspath("backend"))

from app.services.model_service import train_or_load_models

print("Starting model retraining...")
try:
    bundle = train_or_load_models(force_retrain=True)
    print("Retraining complete!")
    print(f"Metrics: {bundle.metrics}")
except Exception as e:
    print(f"Retraining failed: {e}")
    import traceback
    traceback.print_exc()
