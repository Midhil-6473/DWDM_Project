from __future__ import annotations

import io
import time
import uuid
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, StreamingResponse

from utils.charts import batch_category_donut, batch_crop_avg_bar, batch_yield_histogram, india_state_yield_map
from utils.crop_constants import BATCH_REQUIRED_COLUMNS, CROPS, MODEL_DEFAULTS, NATIONAL_AVG, SLIDER_LIMITS, normalize_state_name
from utils.model_features import normalize_category_label, normalize_dataframe, safe_predict

router = APIRouter(prefix="/api/batch", tags=["batch"])
BASE = Path(__file__).resolve().parents[1]
NUMERIC_BOUNDS = {k: tuple(v) for k, v in SLIDER_LIMITS.items()}


def _session_or_404(request: Request, session_id: str) -> dict:
    session = request.app.state.batch_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return session


@router.get("/sample-template")
def sample_template():
    return FileResponse(BASE / "data" / "sample_template.csv", filename="sample_template.csv")


@router.post("/upload")
async def upload_csv(request: Request, file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")
    blob = await file.read()
    if len(blob) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File exceeds 50MB limit.")
    try:
        df = pd.read_csv(io.BytesIO(blob))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {exc!s}") from exc
    session_id = str(uuid.uuid4())
    request.app.state.batch_sessions[session_id] = {
        "filename": file.filename,
        "size": len(blob),
        "df": df,
    }
    return {"session_id": session_id}


@router.get("/validate")
def validate_csv(request: Request, session_id: str = Query(...)):
    session = _session_or_404(request, session_id)
    df: pd.DataFrame = session["df"]
    missing_columns = [col for col in BATCH_REQUIRED_COLUMNS if col not in df.columns]

    missing_values = int(df.isna().sum().sum())
    missing_value_columns: list[dict] = []
    for col in df.columns:
        count = int(df[col].isna().sum())
        if count:
            missing_value_columns.append({"column": col, "count": count})

    unknown_crops: list[str] = []
    if "Crop_Type" in df.columns:
        crops = {str(x).strip() for x in df["Crop_Type"].dropna().unique()}
        unknown_crops = sorted(c for c in crops if c and c not in CROPS)

    range_issue_cells = 0
    for col, bounds in NUMERIC_BOUNDS.items():
        if col not in df.columns:
            continue
        lo, hi = bounds
        ser = pd.to_numeric(df[col], errors="coerce")
        range_issue_cells += int(((ser < lo) | (ser > hi)).sum())

    issues: list[str] = []
    if missing_columns:
        issues.append(f"Missing required columns: {', '.join(missing_columns)}")
    if missing_values:
        show = ", ".join(f"{x['column']} ({x['count']})" for x in missing_value_columns[:8])
        issues.append(f"Missing values detected: {missing_values} cells. {show}")
    if unknown_crops:
        issues.append(f"Unknown crop types found: {', '.join(unknown_crops[:8])}")
    if range_issue_cells:
        issues.append(f"Out-of-range values found in {range_issue_cells} cells. Values will be capped during prediction.")

    ready = len(missing_columns) == 0
    return {
        "stats": {
            "total_rows": int(len(df)),
            "total_columns": int(len(df.columns)),
            "missing_values": missing_values,
            "file_size": int(session["size"]),
        },
        "missing_columns": missing_columns,
        "missing_value_columns": missing_value_columns,
        "unknown_crops": unknown_crops,
        "range_issue_cells": range_issue_cells,
        "issues": issues,
        "ready": ready,
        "ready_message": "✅ File looks good. Ready to predict." if not issues else "Validation completed. Review warnings before running predictions.",
        "preview": df.head(10).fillna("").to_dict(orient="records"),
    }


def _prepare_batch_dataframe(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    df = raw_df.copy()
    for col in BATCH_REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = MODEL_DEFAULTS[col]
    df = normalize_dataframe(df)
    capped = 0
    for col, (lo, hi) in NUMERIC_BOUNDS.items():
        ser = pd.to_numeric(df[col], errors="coerce").fillna(float(MODEL_DEFAULTS[col]))
        out = (ser < lo) | (ser > hi)
        capped += int(out.sum())
        df[col] = ser.clip(lower=lo, upper=hi)
    return df, capped


@router.post("/predict")
def batch_predict(request: Request, session_id: str = Query(...)):
    session = _session_or_404(request, session_id)
    source_df: pd.DataFrame = session["df"].copy()
    prepared_df, capped_cells = _prepare_batch_dataframe(source_df)

    start = time.perf_counter()
    try:
        pre = request.app.state.preprocessor
        pred_yield = safe_predict(request.app.state.reg_model, prepared_df, pre)
        pred_cls_raw = safe_predict(request.app.state.cls_model, prepared_df, pre)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {exc!s}") from exc

    result_df = source_df.copy()
    result_df["Predicted_Yield_kg_ha"] = [float(x) for x in pred_yield]
    result_df["Yield_Category"] = [normalize_category_label(x) for x in pred_cls_raw]
    elapsed = round(time.perf_counter() - start, 2)

    counts = {
        "Low": int((result_df["Yield_Category"] == "Low").sum()),
        "Medium": int((result_df["Yield_Category"] == "Medium").sum()),
        "High": int((result_df["Yield_Category"] == "High").sum()),
    }
    if "Crop_Type" in prepared_df.columns and not prepared_df["Crop_Type"].empty:
        mode_crop = str(prepared_df["Crop_Type"].mode().iloc[0])
    else:
        mode_crop = "Rice"
    national_avg_line = float(NATIONAL_AVG.get(mode_crop, 2000))

    crop_rows: list[tuple[str, float, float, float, int]] = []
    for crop, grp in result_df.groupby("Crop_Type", observed=True):
        y = pd.to_numeric(grp["Predicted_Yield_kg_ha"], errors="coerce").dropna()
        if y.empty:
            continue
        crop_rows.append((str(crop), float(y.mean()), float(y.min()), float(y.max()), int(y.count())))

    state_avg: dict[str, float] = {}
    state_counts: dict[str, int] = {}
    if "State" in result_df.columns:
        tmp = result_df.copy()
        tmp["State"] = tmp["State"].astype(str).map(normalize_state_name)
        for state, grp in tmp.groupby("State", observed=True):
            y = pd.to_numeric(grp["Predicted_Yield_kg_ha"], errors="coerce").dropna()
            if y.empty:
                continue
            state_avg[str(state)] = float(y.mean())
            state_counts[str(state)] = int(y.count())

    yields = [float(x) for x in result_df["Predicted_Yield_kg_ha"].tolist()]
    charts = {
        "donut": batch_category_donut(counts),
        "histogram": batch_yield_histogram(yields, national_avg_line, mode_crop),
        "crop_bars": batch_crop_avg_bar(crop_rows if crop_rows else [("No data", 0.0, 0.0, 0.0, 0)]),
        "state_map": india_state_yield_map(state_avg, state_counts),
    }

    max_rows = 5000
    records_all = result_df.fillna("").to_dict(orient="records")
    truncated = len(records_all) > max_rows
    records = records_all[:max_rows] if truncated else records_all

    yields_by_crop: dict[str, list[float]] = {}
    for crop, grp in result_df.groupby("Crop_Type", observed=True):
        yields_by_crop[str(crop)] = [float(x) for x in grp["Predicted_Yield_kg_ha"].tolist()]

    session["result_df"] = result_df
    return {
        "elapsed_sec": elapsed,
        "rows": int(len(result_df)),
        "counts": counts,
        "avg_yield": float(result_df["Predicted_Yield_kg_ha"].mean()),
        "dominant_crop": mode_crop,
        "national_avg_line": national_avg_line,
        "national_avg_by_crop": dict(NATIONAL_AVG),
        "yields_by_crop": yields_by_crop,
        "charts": charts,
        "records": records,
        "columns": list(result_df.columns),
        "truncated": truncated,
        "capped_cells": capped_cells,
    }


@router.get("/download")
def download_batch(request: Request, session_id: str = Query(...)):
    session = _session_or_404(request, session_id)
    if "result_df" not in session:
        raise HTTPException(status_code=404, detail="No batch results available for this session.")
    output = io.StringIO()
    session["result_df"].to_csv(output, index=False)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=batch_predictions.csv"},
    )
