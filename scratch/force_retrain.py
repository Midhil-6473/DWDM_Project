import sys
from pathlib import Path
# Add backend to path
sys.path.append(str(Path("d:/DWDM_Project/backend")))
from app.services.model_service import train_or_load_models
bundle = train_or_load_models(force_retrain=True)
print("Retrained Model Metrics:", bundle.metrics)
