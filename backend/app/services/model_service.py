from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from app.config import CLASSIFICATION_MODEL_PATH, REGRESSION_MODEL_PATH
from app.services.data_service import (
    CLASSIFICATION_TARGET,
    REGRESSION_TARGET,
    get_dataframe,
    get_feature_columns,
    split_feature_types,
)


@dataclass
class ModelBundle:
    regression_pipeline: Pipeline
    feature_columns: list[str]
    metrics: dict[str, Any]


_bundle: ModelBundle | None = None
MAX_TRAIN_ROWS: int | None = 80000
MODEL_META_PATH = CLASSIFICATION_MODEL_PATH.with_suffix(".meta.json")


def _build_preprocessor(df: pd.DataFrame) -> ColumnTransformer:
    numeric_cols, categorical_cols = split_feature_types(df)
    numeric_pipe = Pipeline([("imputer", SimpleImputer(strategy="median"))])
    categorical_pipe = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="constant", fill_value="None")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        [
            ("num", numeric_pipe, numeric_cols),
            ("cat", categorical_pipe, categorical_cols),
        ]
    )


def _build_classification_pipeline(df: pd.DataFrame) -> Pipeline:
    return Pipeline(
        [
            ("preprocess", _build_preprocessor(df)),
            (
                "model",
                RandomForestClassifier(
                    n_estimators=60,
                    random_state=42,
                    n_jobs=-1,
                    class_weight="balanced_subsample",
                    max_depth=16,
                ),
            ),
        ]
    )


def _build_regression_pipeline(df: pd.DataFrame) -> Pipeline:
    return Pipeline(
        [
            ("preprocess", _build_preprocessor(df)),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=200,
                    max_depth=30,
                    min_samples_leaf=2,
                    max_features=0.5,
                    n_jobs=-1,
                    random_state=42,
                ),
            ),
        ]
    )


def train_or_load_models(force_retrain: bool = False) -> ModelBundle:
    global _bundle
    if _bundle is not None and not force_retrain:
        return _bundle

    df = get_dataframe()
    expected_features = get_feature_columns(df)

    if (
        REGRESSION_MODEL_PATH.exists()
        and MODEL_META_PATH.exists()
        and not force_retrain
    ):
        try:
            meta = json.loads(MODEL_META_PATH.read_text(encoding="utf-8"))
            if (
                meta.get("feature_columns") == expected_features
                and meta.get("max_train_rows") == MAX_TRAIN_ROWS
            ):
                reg_pipe = joblib.load(REGRESSION_MODEL_PATH)
                _bundle = ModelBundle(
                    regression_pipeline=reg_pipe,
                    feature_columns=expected_features,
                    metrics={"info": "Loaded saved regression model."},
                )
                return _bundle
        except Exception:
            pass

    print(f"Retraining models with {MAX_TRAIN_ROWS} samples...")
    if MAX_TRAIN_ROWS is not None and len(df) > MAX_TRAIN_ROWS:
        # Use stratified sampling to ensure all crops are equally represented
        df = df.groupby("Crop_Type", group_keys=False).sample(n=MAX_TRAIN_ROWS // 10, random_state=42)
        df = df.reset_index(drop=True)
    
    feature_cols = [c for c in expected_features if c in df.columns]
    X = df[feature_cols]
    y_reg = df[REGRESSION_TARGET].astype(float)

    X_train, X_test, y_reg_train, y_reg_test = train_test_split(
        X, y_reg, test_size=0.2, random_state=42, stratify=df["Crop_Type"]
    )

    reg_pipe = _build_regression_pipeline(df)
    reg_pipe.fit(X_train, y_reg_train)

    y_reg_pred = reg_pipe.predict(X_test)

    metrics = {
        "regression_mae": float(mean_absolute_error(y_reg_test, y_reg_pred)),
        "regression_r2": float(r2_score(y_reg_test, y_reg_pred)),
    }

    joblib.dump(reg_pipe, REGRESSION_MODEL_PATH)
    MODEL_META_PATH.write_text(
        json.dumps(
            {
                "feature_columns": feature_cols,
                "max_train_rows": MAX_TRAIN_ROWS,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    _bundle = ModelBundle(
        regression_pipeline=reg_pipe,
        feature_columns=feature_cols,
        metrics=metrics,
    )
    return _bundle


def _candidate_crops_for_conditions(payload: dict[str, Any], df: pd.DataFrame) -> list[str]:
    state = payload.get("State")
    season = payload.get("Season")
    filt = df
    if "State" in df.columns and state is not None:
        filt = filt[filt["State"] == state]
    if "Season" in df.columns and season is not None:
        filt = filt[filt["Season"] == season]
    if filt.empty and "State" in df.columns:
        filt = df[df["State"] == state]
    if filt.empty and "Season" in df.columns:
        filt = df[df["Season"] == season]
    if filt.empty:
        filt = df
    crops = (
        filt["Crop_Type"].dropna().astype(str).sort_values().unique().tolist()
        if "Crop_Type" in filt.columns
        else []
    )
    return crops


def rank_crops_by_conditions(payload: dict[str, Any], limit: int = 5) -> list[dict[str, float | str]]:
    bundle = train_or_load_models(force_retrain=False)
    df = get_dataframe()
    # Consider ALL unique crops from the dataset for a complete comparison
    all_crops = df["Crop_Type"].dropna().unique().tolist()
    if not all_crops:
        return []
    
    # Batch predict all crops at once
    candidates = []
    for crop in all_crops:
        c = dict(payload)
        c["Crop_Type"] = crop
        candidates.append(c)
    
    X_batch = pd.DataFrame(candidates, columns=bundle.feature_columns)
    preds = bundle.regression_pipeline.predict(X_batch)
    
    ranked = []
    for crop, y in zip(all_crops, preds):
        ranked.append({"crop": str(crop), "predicted_yield": float(y)})
    
    ranked.sort(key=lambda x: x["predicted_yield"], reverse=True)
    return ranked[: max(1, limit)]


def predict_single(payload: dict[str, Any]) -> dict[str, Any]:
    bundle = train_or_load_models(force_retrain=False)
    row = pd.DataFrame([payload], columns=bundle.feature_columns)
    reg_pred = float(bundle.regression_pipeline.predict(row)[0])
    
    selected_crop = str(payload.get("Crop_Type", "Unknown"))
    from app.services.data_service import get_crop_stats
    crop_stats = get_crop_stats()
    stats = crop_stats.get(selected_crop, {"mean": 0.0, "p33": 0.0, "p66": 0.0})
    
    # Unified classification logic based on per-crop quantiles
    if reg_pred <= stats["p33"]:
        cls_pred = "Low"
    elif reg_pred > stats["p66"]:
        cls_pred = "High"
    else:
        cls_pred = "Medium"

    ranked = rank_crops_by_conditions(payload, limit=5)
    best_crop = selected_crop
    best_crop_yield = reg_pred
    if ranked:
        best_crop = str(ranked[0]["crop"])
        best_crop_yield = float(ranked[0]["predicted_yield"])

    df = get_dataframe()
    candidate_crops = _candidate_crops_for_conditions(payload, df)
    is_typical = selected_crop in candidate_crops
    typical_mean = stats["mean"]

    return {
        "selected_crop": selected_crop,
        "predicted_yield_kg_ha": reg_pred,
        "predicted_category": cls_pred,
        "recommended_crop": best_crop,
        "recommended_crop_predicted_yield_kg_ha": best_crop_yield,
        "is_recommended_crop_better": best_crop_yield > reg_pred,
        "is_typical_for_conditions": is_typical,
        "typical_mean_yield": typical_mean,
    }
