from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from utils.charts import input_radar, npk_bar, yield_gauge
from utils.crop_constants import NATIONAL_AVG, OPTIMAL_PRESET, OPTIMAL_RANGES, RADAR_MAX, YIELD_MIN_MAX, resolve_calendar
from utils.model_features import frame_from_form_dict, normalize_category_label, safe_predict
from utils.recommendations import field_health_score, generate_recommendations

router = APIRouter(prefix="/api", tags=["predict"])


class PredictPayload(BaseModel):
    data: dict[str, Any]


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _radar_payload(data: dict[str, Any], crop: str) -> tuple[list[float], list[float], list[str]]:
    labels = ["Nitrogen", "Phosphorus", "Potassium", "Rainfall", "Temperature", "Soil pH"]
    max_ref = RADAR_MAX.get(crop, RADAR_MAX["Rice"])
    user = [
        _clamp01(float(data.get("N_kgha", 0)) / max(1.0, max_ref["N"])),
        _clamp01(float(data.get("P_kgha", 0)) / max(1.0, max_ref["P"])),
        _clamp01(float(data.get("K_kgha", 0)) / max(1.0, max_ref["K"])),
        _clamp01(float(data.get("Rainfall_mm", 0)) / max(1.0, max_ref["Rainfall"])),
        _clamp01(float(data.get("Avg_Temp_C", 0)) / max(1.0, max_ref["Temp"])),
        _clamp01(float(data.get("Soil_pH", 0)) / max(1.0, max_ref["pH"])),
    ]
    n_mid = sum(OPTIMAL_RANGES["N_kgha"][crop]) / 2
    p_mid = sum(OPTIMAL_RANGES["P_kgha"][crop]) / 2
    k_mid = sum(OPTIMAL_RANGES["K_kgha"][crop]) / 2
    r_mid = sum(OPTIMAL_RANGES["Rainfall_mm"][crop]) / 2
    t_mid = sum(OPTIMAL_RANGES["Avg_Temp_C"][crop]) / 2
    ph_mid = sum(OPTIMAL_RANGES["Soil_pH"][crop]) / 2
    optimal = [
        _clamp01(n_mid / max_ref["N"]),
        _clamp01(p_mid / max_ref["P"]),
        _clamp01(k_mid / max_ref["K"]),
        _clamp01(r_mid / max_ref["Rainfall"]),
        _clamp01(t_mid / max_ref["Temp"]),
        _clamp01(ph_mid / max_ref["pH"]),
    ]
    return user, optimal, labels


@router.post("/predict")
def predict(payload: PredictPayload, request: Request):
    data = payload.data or {}
    crop = str(data.get("Crop_Type", "Rice") or "Rice")
    season = str(data.get("Season", "Kharif") or "Kharif")
    if crop not in YIELD_MIN_MAX:
        crop = "Rice"
    frame = frame_from_form_dict(data)

    try:
        pre = request.app.state.preprocessor
        reg_pred = safe_predict(request.app.state.reg_model, frame, pre)
        cls_pred = safe_predict(request.app.state.cls_model, frame, pre)
        pred_yield = float(reg_pred[0])
        pred_cat = normalize_category_label(cls_pred[0])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc!s}") from exc

    y_min, y_max = YIELD_MIN_MAX[crop]
    progress = _clamp01((pred_yield - y_min) / max(1.0, (y_max - y_min)))
    progress_pct = round(progress * 100, 1)
    nat_avg = float(NATIONAL_AVG.get(crop, (y_min + y_max) / 2))
    delta_pct = ((pred_yield - nat_avg) / max(1.0, nat_avg)) * 100.0
    score, score_label = field_health_score(data, crop)
    recs = generate_recommendations(data, crop)
    sow, harvest, days = resolve_calendar(crop, season)

    if pred_cat == "Low":
        bar_color = "#d32f2f"
    elif pred_cat == "Medium":
        bar_color = "#f59e0b"
    else:
        bar_color = "#2e7d32"

    user_radar, optimal_radar, radar_labels = _radar_payload(data, crop)
    opt = OPTIMAL_PRESET.get(crop, OPTIMAL_PRESET["Rice"])

    return {
        "predicted_yield_kg_ha": pred_yield,
        "predicted_category": pred_cat,
        "yield_progress": progress,
        "yield_progress_pct": progress_pct,
        "yield_progress_color": bar_color,
        "min_yield": y_min,
        "max_yield": y_max,
        "national_average": nat_avg,
        "delta_from_national_pct": delta_pct,
        "recommendations": recs,
        "field_health_score": score,
        "field_health_label": score_label,
        "calendar": {"sowing": sow, "harvest": harvest, "days_to_maturity": days},
        "charts": {
            "gauge": yield_gauge(pred_yield, y_max),
            "radar": input_radar(user_radar, optimal_radar, radar_labels),
            "npk": npk_bar(
                float(data.get("N_kgha", 0)),
                float(data.get("P_kgha", 0)),
                float(data.get("K_kgha", 0)),
                float(opt["N_kgha"]),
                float(opt["P_kgha"]),
                float(opt["K_kgha"]),
            ),
        },
    }
