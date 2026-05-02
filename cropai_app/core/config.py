from pathlib import Path

# Base directory for the cropai_app
BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parent

# Dataset paths
PRIMARY_DATASET_NAME = "crop_yield_cleaned_dataset.csv"
FALLBACK_DATASET_NAME = "crop_yield_cleaned_dataset.csv"

DATASET_PATH = PROJECT_ROOT / PRIMARY_DATASET_NAME
FALLBACK_DATASET_PATH = PROJECT_ROOT / FALLBACK_DATASET_NAME

# Model paths
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# Pipelines for the DWDM React frontend
CLASSIFICATION_MODEL_PATH = MODEL_DIR / "classification_pipeline.joblib"
REGRESSION_MODEL_PATH = MODEL_DIR / "regression_pipeline.joblib"
