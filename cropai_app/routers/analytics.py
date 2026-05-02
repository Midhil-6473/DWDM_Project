from typing import Any

from fastapi import APIRouter, Query

from core.schemas import PredictionInput
from core.data_service import (
    CLASSIFICATION_TARGET,
    REGRESSION_TARGET,
    get_dataframe,
)
from core.model_service import rank_crops_by_conditions

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _apply_filters(df, state: str | None, crop_type: str | None, season: str | None):
    filt = df
    if state:
        filt = filt[filt["State"] == state]
    if crop_type:
        filt = filt[filt["Crop_Type"] == crop_type]
    if season:
        filt = filt[filt["Season"] == season]
    return filt


@router.get("/summary")
def summary(
    state: str | None = Query(default=None),
    crop_type: str | None = Query(default=None),
    season: str | None = Query(default=None),
):
    df = get_dataframe()
    filt = _apply_filters(df, state, crop_type, season)
    used_fallback = False
    selected_count = int(len(filt))
    if filt.empty:
        filt = df
        used_fallback = True

    return {
        "count": int(len(filt)),
        "selected_count": selected_count,
        "used_fallback": used_fallback,
        "mean_yield": float(filt[REGRESSION_TARGET].mean()),
        "median_yield": float(filt[REGRESSION_TARGET].median()),
        "min_yield": float(filt[REGRESSION_TARGET].min()),
        "max_yield": float(filt[REGRESSION_TARGET].max()),
    }


@router.get("/yield_distribution")
def yield_distribution(
    state: str | None = Query(default=None),
    crop_type: str | None = Query(default=None),
    season: str | None = Query(default=None),
):
    df = get_dataframe()
    filt = _apply_filters(df, state, crop_type, season)
    used_fallback = False
    if filt.empty:
        filt = df
        used_fallback = True
    bins = filt[REGRESSION_TARGET].dropna()
    hist = bins.round(-1).value_counts().sort_index()
    series = [{"label": str(int(idx)), "count": int(val)} for idx, val in hist.items()]
    return {"series": series, "used_fallback": used_fallback}


@router.get("/category_counts")
def category_counts(
    state: str | None = Query(default=None),
    crop_type: str | None = Query(default=None),
    season: str | None = Query(default=None),
):
    df = get_dataframe()
    filt = _apply_filters(df, state, crop_type, season)
    used_fallback = False
    if filt.empty:
        filt = df
        used_fallback = True
    counts = filt[CLASSIFICATION_TARGET].astype(str).value_counts()
    series = [{"label": idx, "count": int(val)} for idx, val in counts.items()]
    return {"series": series, "used_fallback": used_fallback}


@router.get("/state_crop_comparison")
def state_crop_comparison(
    state: str | None = Query(default=None),
    crop_type: str | None = Query(default=None),
    season: str | None = Query(default=None),
    predicted_yield: float | None = Query(default=None),
):
    df = get_dataframe()
    filt = _apply_filters(df, state, crop_type, season)
    used_fallback = False
    if filt.empty:
        filt = df
        used_fallback = True
    mean_sel = float(filt[REGRESSION_TARGET].mean())
    series: list[dict[str, Any]] = [
        {"label": "SelectedFilterAvg", "value": mean_sel},
        {"label": "DatasetAvg", "value": float(df[REGRESSION_TARGET].mean())},
    ]
    if predicted_yield is not None:
        series.append({"label": "YourPrediction", "value": float(predicted_yield)})
    return {"series": series, "used_fallback": used_fallback}


@router.get("/top_crops")
def top_crops(
    state: str | None = Query(default=None),
    season: str | None = Query(default=None),
    limit: int = Query(default=5),
):
    df = get_dataframe()
    filt = df
    if state:
        filt = filt[filt["State"] == state]
    if season:
        filt = filt[filt["Season"] == season]
    used_fallback = False
    if filt.empty:
        filt = df
        used_fallback = True
    grouped = (
        filt.groupby("Crop_Type", dropna=False)[REGRESSION_TARGET]
        .mean()
        .sort_values(ascending=False)
        .head(max(1, limit))
    )
    rows = [{"crop": str(crop), "avg_yield": float(val)} for crop, val in grouped.items()]
    return {"rows": rows, "used_fallback": used_fallback}


@router.post("/top_crops_by_conditions")
def top_crops_by_conditions(payload: PredictionInput, limit: int = Query(default=5)):
    ranked = rank_crops_by_conditions(payload.features, limit=limit)
    return {"rows": ranked}


@router.get("/condition_diagnostics")
def condition_diagnostics(
    avg_temp_c: float = Query(...),
    rainfall_mm: float = Query(...),
    humidity_pct: float = Query(...),
    water_stress_index: float = Query(...),
    soil_ph: float = Query(...),
    n_kgha: float = Query(...),
    p_kgha: float = Query(...),
    k_kgha: float = Query(...),
    ndvi: float = Query(...),
):
    diagnostics = []
    if not 20 <= avg_temp_c <= 32:
        diagnostics.append("Temperature is outside the ideal 20-32C range.")
    if rainfall_mm < 300:
        diagnostics.append("Rainfall appears low; irrigation support may be needed.")
    if water_stress_index > 0.5:
        diagnostics.append("Water stress is high; yield risk increases.")
    if not 5.8 <= soil_ph <= 7.5:
        diagnostics.append("Soil pH is not optimal for most crops.")
    if ndvi < 0.45:
        diagnostics.append("NDVI is low; vegetation vigor may be weak.")
    nutrient_note = (
        "Nutrients look balanced."
        if (n_kgha > 40 and p_kgha > 20 and k_kgha > 30)
        else "Consider improving NPK nutrient levels."
    )
    return {
        "alerts": diagnostics,
        "nutrient_note": nutrient_note,
        "condition_score": max(0, 100 - (len(diagnostics) * 15)),
    }
