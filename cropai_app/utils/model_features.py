from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from utils.crop_constants import INPUT_COLUMNS, MODEL_DEFAULTS, NUMERIC_COLUMNS


def _to_float(value: Any, default: float) -> float:
    if value is None:
        return default
    try:
        if isinstance(value, str) and value.strip() == "":
            return default
        out = float(value)
        if np.isnan(out):
            return default
        return out
    except Exception:
        return default


def normalize_input_record(raw: dict[str, Any]) -> dict[str, Any]:
    record: dict[str, Any] = {}
    for col in INPUT_COLUMNS:
        default = MODEL_DEFAULTS.get(col)
        val = raw.get(col, default)
        if col in NUMERIC_COLUMNS:
            record[col] = _to_float(val, float(default))
        else:
            if val is None or str(val).strip() == "":
                record[col] = str(default)
            else:
                record[col] = str(val).strip()
    return record


def normalize_dataframe(source_df: pd.DataFrame) -> pd.DataFrame:
    rows = [normalize_input_record(rec) for rec in source_df.to_dict(orient="records")]
    return pd.DataFrame(rows, columns=INPUT_COLUMNS)


def frame_from_form_dict(raw: dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame([normalize_input_record(raw)], columns=INPUT_COLUMNS)


def _candidate_columns(obj: Any, frame: pd.DataFrame) -> list[list[str]]:
    out: list[list[str]] = []
    feat = getattr(obj, "feature_names_in_", None)
    if feat is not None:
        cols = [str(x) for x in feat if str(x) in frame.columns]
        if cols:
            out.append(cols)
    if hasattr(obj, "named_steps"):
        for step in obj.named_steps.values():
            feat2 = getattr(step, "feature_names_in_", None)
            if feat2 is not None:
                cols2 = [str(x) for x in feat2 if str(x) in frame.columns]
                if cols2:
                    out.append(cols2)
    dedup: list[list[str]] = []
    for cols in out:
        if cols not in dedup:
            dedup.append(cols)
    return dedup


def _safe_predict_model(estimator: Any, frame: pd.DataFrame) -> np.ndarray:
    errs: list[str] = []
    for cols in _candidate_columns(estimator, frame):
        try:
            return estimator.predict(frame[cols])
        except Exception as exc:
            errs.append(f"predict({len(cols)} cols): {exc!s}")
    try:
        return estimator.predict(frame)
    except Exception as exc:
        errs.append(f"predict(full frame): {exc!s}")
    raise RuntimeError("; ".join(errs))


def safe_predict(estimator: Any, frame: pd.DataFrame, preprocessor: Any | None = None) -> np.ndarray:
    errs: list[str] = []
    if preprocessor is not None:
        for cols in _candidate_columns(preprocessor, frame):
            try:
                transformed = preprocessor.transform(frame[cols])
                return estimator.predict(transformed)
            except Exception as exc:
                errs.append(f"preprocessor+predict({len(cols)} cols): {exc!s}")
        try:
            transformed = preprocessor.transform(frame)
            return estimator.predict(transformed)
        except Exception as exc:
            errs.append(f"preprocessor+predict(full frame): {exc!s}")
    try:
        return _safe_predict_model(estimator, frame)
    except Exception as exc:
        errs.append(str(exc))
    raise RuntimeError("; ".join(errs))


def normalize_category_label(value: Any) -> str:
    if isinstance(value, (int, float, np.integer, np.floating)):
        iv = int(round(float(value)))
        if iv <= 0:
            return "Low"
        if iv == 1:
            return "Medium"
        return "High"
    text = str(value).strip().lower()
    if "low" in text:
        return "Low"
    if "high" in text:
        return "High"
    if "med" in text:
        return "Medium"
    if text in {"0", "l"}:
        return "Low"
    if text in {"1", "m"}:
        return "Medium"
    if text in {"2", "h"}:
        return "High"
    return "Medium"
