from __future__ import annotations

from functools import lru_cache
from typing import Any

import pandas as pd

from app.config import DATASET_PATH, FALLBACK_DATASET_PATH

CLASSIFICATION_TARGET = "Yield_Category"
REGRESSION_TARGET = "Crop_Yield_kg_ha"
IMPORTANT_FEATURES = [
    "Season",
    "State",
    "Crop_Type",
    "Soil_Type",
    "Irrigation_Method",
    "Fertilizer_Type",
    "Avg_Temp_C",
    "Rainfall_mm",
    "Humidity_Pct",
    "Water_Stress_Index",
    "Soil_pH",
    "N_kgha",
    "P_kgha",
    "K_kgha",
    "NDVI",
]


def resolve_dataset_path():
    if DATASET_PATH.exists():
        return DATASET_PATH
    if FALLBACK_DATASET_PATH.exists():
        return FALLBACK_DATASET_PATH
    raise FileNotFoundError(
        f"Dataset not found. Tried: '{DATASET_PATH.name}' and '{FALLBACK_DATASET_PATH.name}'."
    )


@lru_cache(maxsize=1)
def get_dataframe() -> pd.DataFrame:
    path = resolve_dataset_path()
    try:
        print(f"Loading dataset from {path}...")
        df = pd.read_csv(path, low_memory=False)
        print(f"Successfully loaded dataset with {len(df)} rows.")
    except Exception as e:
        print(f"Error loading dataset: {e}")
        raise
    required = {CLASSIFICATION_TARGET, REGRESSION_TARGET}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required target columns: {sorted(missing)}")
    return df


def get_feature_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in IMPORTANT_FEATURES if c in df.columns]


def split_feature_types(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    feature_cols = get_feature_columns(df)
    numeric_cols = df[feature_cols].select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = [c for c in feature_cols if c not in numeric_cols]
    return numeric_cols, categorical_cols


@lru_cache(maxsize=1)
def get_crop_stats() -> dict[str, dict[str, float]]:
    df = get_dataframe()
    stats = {}
    for crop in df["Crop_Type"].unique():
        mask = df["Crop_Type"] == crop
        yields = df.loc[mask, REGRESSION_TARGET]
        stats[str(crop)] = {
            "mean": float(yields.mean()),
            "p33": float(yields.quantile(0.33)),
            "p66": float(yields.quantile(0.66)),
        }
    return stats


def get_metadata(df: pd.DataFrame) -> dict[str, Any]:
    numeric_cols, categorical_cols = split_feature_types(df)
    categories: dict[str, list[str]] = {}
    numeric_ranges: dict[str, dict[str, float]] = {}
    for col in categorical_cols:
        values = (
            df[col]
            .dropna()
            .astype(str)
            .sort_values()
            .unique()
            .tolist()
        )
        categories[col] = values
    for col in numeric_cols:
        series = df[col].dropna()
        if series.empty:
            continue
        numeric_ranges[col] = {
            "min": float(series.min()),
            "max": float(series.max()),
        }
    return {
        "dataset_path": str(resolve_dataset_path()),
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "category_values": categories,
        "numeric_ranges": numeric_ranges,
        "targets": {
            "classification": CLASSIFICATION_TARGET,
            "regression": REGRESSION_TARGET,
        },
    }
