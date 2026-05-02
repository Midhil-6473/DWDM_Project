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

from core.config import CLASSIFICATION_MODEL_PATH, REGRESSION_MODEL_PATH
from core.data_service import (
    CLASSIFICATION_TARGET,
    REGRESSION_TARGET,
    get_dataframe,
    get_feature_columns,
    split_feature_types,
)


@dataclass
class ModelBundle:
    classification_pipeline: Pipeline
    regression_pipeline: Pipeline
    feature_columns: list[str]
    metrics: dict[str, Any]


_bundle: ModelBundle | None = None
MAX_TRAIN_ROWS: int | None = None
MODEL_META_PATH = CLASSIFICATION_MODEL_PATH.with_suffix(".meta.json")


def _build_preprocessor(df: pd.DataFrame) -> ColumnTransformer:
    numeric_cols, categorical_cols = split_feature_types(df)
    numeric_pipe = Pipeline([("imputer", SimpleImputer(strategy="median"))])
    categorical_pipe = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
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
                    n_estimators=45,
                    random_state=42,
                    n_jobs=-1,
                    class_weight="balanced_subsample",
                    max_depth=14,
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
                    n_estimators=55,
                    random_state=42,
                    n_jobs=-1,
                    max_depth=16,
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
        CLASSIFICATION_MODEL_PATH.exists()
        and REGRESSION_MODEL_PATH.exists()
        and MODEL_META_PATH.exists()
        and not force_retrain
    ):
        try:
            meta = json.loads(MODEL_META_PATH.read_text(encoding="utf-8"))
            if (
                meta.get("feature_columns") == expected_features
                and meta.get("max_train_rows") == MAX_TRAIN_ROWS
            ):
                cls_pipe = joblib.load(CLASSIFICATION_MODEL_PATH)
                reg_pipe = joblib.load(REGRESSION_MODEL_PATH)
                _bundle = ModelBundle(
                    classification_pipeline=cls_pipe,
                    regression_pipeline=reg_pipe,
                    feature_columns=expected_features,
                    metrics={"info": "Loaded saved models."},
                )
                return _bundle
        except Exception:
            # If metadata/model loading fails, retrain fresh models.
            pass

    if MAX_TRAIN_ROWS is not None and len(df) > MAX_TRAIN_ROWS:
        # Faster first training for responsive app usage.
        df = df.sample(n=MAX_TRAIN_ROWS, random_state=42)
    feature_cols = [c for c in expected_features if c in df.columns]
    X = df[feature_cols]
    y_cls = df[CLASSIFICATION_TARGET].astype(str)
    y_reg = df[REGRESSION_TARGET].astype(float)

    X_train, X_test, y_cls_train, y_cls_test, y_reg_train, y_reg_test = train_test_split(
        X, y_cls, y_reg, test_size=0.2, random_state=42
    )

    cls_pipe = _build_classification_pipeline(df)
    reg_pipe = _build_regression_pipeline(df)

    cls_pipe.fit(X_train, y_cls_train)
    reg_pipe.fit(X_train, y_reg_train)

    y_cls_pred = cls_pipe.predict(X_test)
    y_reg_pred = reg_pipe.predict(X_test)

    metrics = {
        "classification_accuracy": float(accuracy_score(y_cls_test, y_cls_pred)),
        "regression_mae": float(mean_absolute_error(y_reg_test, y_reg_pred)),
        "regression_r2": float(r2_score(y_reg_test, y_reg_pred)),
    }

    joblib.dump(cls_pipe, CLASSIFICATION_MODEL_PATH)
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
        classification_pipeline=cls_pipe,
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
    crop_values = _candidate_crops_for_conditions(payload, df)
    ranked: list[dict[str, float | str]] = []
    for crop in crop_values:
        candidate = dict(payload)
        candidate["Crop_Type"] = crop
        candidate_row = pd.DataFrame([candidate], columns=bundle.feature_columns)
        crop_yield = float(bundle.regression_pipeline.predict(candidate_row)[0])
        ranked.append({"crop": crop, "predicted_yield": crop_yield})
    ranked.sort(key=lambda x: float(x["predicted_yield"]), reverse=True)
    return ranked[: max(1, limit)]


def predict_single(payload: dict[str, Any]) -> dict[str, Any]:
    bundle = train_or_load_models(force_retrain=False)
    row = pd.DataFrame([payload], columns=bundle.feature_columns)
    reg_pred = float(bundle.regression_pipeline.predict(row)[0])
    cls_pred = str(bundle.classification_pipeline.predict(row)[0])
    selected_crop = str(payload.get("Crop_Type", "Unknown"))

    ranked = rank_crops_by_conditions(payload, limit=5)
    best_crop = selected_crop
    best_crop_yield = reg_pred
    if ranked:
        best_crop = str(ranked[0]["crop"])
        best_crop_yield = float(ranked[0]["predicted_yield"])

    df = get_dataframe()
    candidate_crops = _candidate_crops_for_conditions(payload, df)
    is_typical = selected_crop in candidate_crops
    typical_mean = float(df[df["Crop_Type"] == selected_crop][REGRESSION_TARGET].mean()) if selected_crop in df["Crop_Type"].values else 0.0

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
