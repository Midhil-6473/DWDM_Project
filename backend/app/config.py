from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent

# User asked to use this filename; fallback handled in data_service.
PRIMARY_DATASET_NAME = "crop_yield_cleaned_dataset.csv"
FALLBACK_DATASET_NAME = "crop_yield_cleaned_dataset.csv"

DATASET_PATH = PROJECT_ROOT / PRIMARY_DATASET_NAME
FALLBACK_DATASET_PATH = PROJECT_ROOT / FALLBACK_DATASET_NAME

MODEL_DIR = BACKEND_DIR / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION_MODEL_PATH = MODEL_DIR / "classification_pipeline.joblib"
REGRESSION_MODEL_PATH = MODEL_DIR / "regression_pipeline.joblib"
