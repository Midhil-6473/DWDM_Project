from typing import Any
from fastapi import APIRouter, Query
import pandas as pd
import numpy as np

from app.schemas import PredictionInput
from app.services.data_service import (
    CLASSIFICATION_TARGET,
    REGRESSION_TARGET,
    get_dataframe,
)
from app.services.model_service import rank_crops_by_conditions

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

@router.get("/npk-impact")
def npk_impact(
    crop: str = Query("All"),
    season: str = Query("All"),
    state: str = Query("All"),
    nutrient: str = Query("N_kgha")
):
    df = get_dataframe()
    dff = _apply_filters(df, None if state == "All" else state, None if crop == "All" else crop, None if season == "All" else season)
    
    if dff.empty: return {"series": []}
    
    # Quantile cuts
    try:
        dff["tier"] = pd.qcut(dff[nutrient], q=3, labels=["Low", "Medium", "High"], duplicates='drop')
    except:
        # Fallback if not enough unique values
        dff["tier"] = "Medium"

    grouped = dff.groupby(["Crop_Type", "tier"])[REGRESSION_TARGET].mean().reset_index()
    grouped.columns = ["crop", "tier", "yield"]
    
    # Calculate insight
    pivot = grouped.pivot(index="crop", columns="tier", values="yield")
    insight = ""
    if "Low" in pivot.columns and "High" in pivot.columns:
        pivot["gap"] = pivot["High"] - pivot["Low"]
        top_crop = pivot["gap"].idxmax()
        top_gap = pivot["gap"].max()
        insight = f"{top_crop} shows the largest yield improvement ({top_gap:,.0f} kg/ha) when {nutrient.split('_')[0]} increases."

    return {
        "series": grouped.to_dict(orient="records"),
        "insight": insight
    }

@router.get("/rainfall-yield")
def rainfall_yield(
    crop: str = Query("All"),
    season: str = Query("All"),
    state: str = Query("All")
):
    df = get_dataframe()
    dff = _apply_filters(df, None if state == "All" else state, None if crop == "All" else crop, None if season == "All" else season)
    
    if dff.empty:
        return {"series": [], "optimal_range": None, "insight": ""}
    
    sample = dff.sample(min(2000, len(dff)), random_state=42)
    series = sample[["Rainfall_mm", REGRESSION_TARGET, CLASSIFICATION_TARGET]].to_dict(orient="records")
    
    OPTIMAL_RAIN = {
        "Rice": (150, 300), "Wheat": (75, 150), "Maize": (100, 250),
        "Sugarcane": (150, 300), "Cotton": (70, 130), "Soybean": (100, 200),
        "Groundnut": (50, 120), "Potato": (75, 150), "Chickpea": (40, 100), "Mustard": (30, 80)
    }
    
    optimal = OPTIMAL_RAIN.get(crop)
    insight = ""
    if optimal:
        in_zone = dff[dff["Rainfall_mm"].between(optimal[0], optimal[1])]
        pct = (len(in_zone) / len(dff) * 100) if not dff.empty else 0
        insight = f"{pct:.1f}% of {crop} records fall within the optimal range of {optimal[0]}–{optimal[1]}mm."

    return {
        "series": series,
        "optimal_range": optimal,
        "insight": insight
    }

@router.get("/heatmap")
def heatmap(
    crop: str = Query("All"),
    season: str = Query("All"),
    state: str = Query("All")
):
    df = get_dataframe()
    dff = _apply_filters(df, None if state == "All" else state, None if crop == "All" else crop, None if season == "All" else season)
    
    pivot_data = dff.groupby(["State", "Season"])[REGRESSION_TARGET].mean().reset_index()
    pivot_table = pivot_data.pivot(index="State", columns="Season", values=REGRESSION_TARGET).fillna(0)
    
    best_idx = pivot_data[REGRESSION_TARGET].idxmax() if not pivot_data.empty else None
    insight = ""
    if best_idx is not None:
        best = pivot_data.loc[best_idx]
        insight = f"Best Combination: {best['State']} × {best['Season']} — Average yield of {best[REGRESSION_TARGET]:,.0f} kg/ha"

    return {
        "z": pivot_table.values.tolist(),
        "x": pivot_table.columns.tolist(),
        "y": pivot_table.index.tolist(),
        "insight": insight
    }

@router.get("/pest-disease-impact")
def pest_disease_impact(
    crop: str = Query("All"),
    season: str = Query("All"),
    state: str = Query("All")
):
    df = get_dataframe()
    df["Pest_Incidence"] = df["Pest_Incidence"].fillna("None")
    df["Disease_Incidence"] = df["Disease_Incidence"].fillna("None")
    dff = _apply_filters(df, None if state == "All" else state, None if crop == "All" else crop, None if season == "All" else season)
    
    order = ["None", "Low", "Moderate", "High"]
    
    def get_avg(col):
        avg = dff.groupby(col)[REGRESSION_TARGET].mean().reindex(order).fillna(0)
        baseline = avg.get("None", 0)
        loss = (baseline - avg["High"]) if "High" in avg else 0
        return [{"level": k, "yield": v} for k, v in avg.items()], float(loss)

    pest_series, pest_loss = get_avg("Pest_Incidence")
    dis_series, dis_loss = get_avg("Disease_Incidence")
    
    return {
        "pest": pest_series,
        "disease": dis_series,
        "pest_loss_insight": f"High pest causes ~{pest_loss:,.0f} kg/ha loss." if pest_loss > 0 else "",
        "disease_loss_insight": f"High disease causes ~{dis_loss:,.0f} kg/ha loss." if dis_loss > 0 else ""
    }

@router.get("/feature-importance")
def feature_importance():
    data = {
        "Crop Type (Sugarcane)": 29.78, "Potassium K (kg/ha)": 18.50,
        "Nitrogen N (kg/ha)": 13.84, "Season: Rabi": 7.11,
        "Season: Kharif": 5.52, "Rainfall (mm)": 4.79,
        "Crop Type (Potato)": 2.73, "Phosphorus P (kg/ha)": 2.70,
        "Avg Temperature (°C)": 2.00, "Min Temperature (°C)": 1.80
    }
    series = [{"feature": k, "importance": v} for k, v in data.items()]
    series.sort(key=lambda x: x["importance"])
    return {"series": series}

@router.get("/yield-trend")
def yield_trend(
    crops: list[str] = Query(default=[]),
    state: str = Query("All")
):
    df = get_dataframe()
    dff = df if state == "All" else df[df["State"] == state]
    if crops:
        dff = dff[dff["Crop_Type"].isin(crops)]
    
    trend = dff.groupby(["Year", "Crop_Type"])[REGRESSION_TARGET].mean().reset_index()
    
    metrics = []
    for crop in (crops or dff["Crop_Type"].unique()[:5]):
        cdata = trend[trend["Crop_Type"] == crop].sort_values("Year")
        if len(cdata) >= 2:
            first, last = cdata.iloc[0][REGRESSION_TARGET], cdata.iloc[-1][REGRESSION_TARGET]
            change = ((last - first) / first * 100) if first > 0 else 0
            metrics.append({"crop": crop, "yield": last, "change": change})

    return {
        "series": trend.to_dict(orient="records"),
        "metrics": metrics
    }


# ─── Endpoints used by the Predict page's fetchAnalytics ───

@router.get("/yield_distribution")
def yield_distribution(
    state: str | None = Query(default=None),
    crop_type: str | None = Query(default=None),
    season: str | None = Query(default=None),
):
    df = get_dataframe()
    filt = _apply_filters(df, state, crop_type, season)
    if filt.empty:
        return {"series": []}

    bins = [0, 1000, 2000, 3000, 5000, 10000, 50000, float("inf")]
    labels = ["0-1k", "1k-2k", "2k-3k", "3k-5k", "5k-10k", "10k-50k", "50k+"]
    filt = filt.copy()
    filt["bin"] = pd.cut(filt[REGRESSION_TARGET], bins=bins, labels=labels, right=False)
    counts = filt["bin"].value_counts().reindex(labels, fill_value=0)
    series = [{"range": k, "count": int(v)} for k, v in counts.items()]
    return {"series": series}


@router.get("/category_counts")
def category_counts(
    state: str | None = Query(default=None),
    crop_type: str | None = Query(default=None),
    season: str | None = Query(default=None),
):
    df = get_dataframe()
    filt = _apply_filters(df, state, crop_type, season)
    if filt.empty:
        return {"series": []}

    counts = filt[CLASSIFICATION_TARGET].value_counts()
    series = [{"label": str(k), "count": int(v)} for k, v in counts.items()]
    return {"series": series}


@router.post("/top_crops_by_conditions")
def top_crops_by_conditions(body: dict, limit: int = Query(default=5)):
    features = body.get("features", body)
    rows = rank_crops_by_conditions(features, limit=limit)
    return {"rows": rows}


@router.get("/condition_diagnostics")
def condition_diagnostics(
    avg_temp_c: float = Query(default=25),
    rainfall_mm: float = Query(default=150),
    humidity_pct: float = Query(default=60),
    water_stress_index: float = Query(default=0.3),
    soil_ph: float = Query(default=6.5),
    n_kgha: float = Query(default=50),
    p_kgha: float = Query(default=30),
    k_kgha: float = Query(default=30),
    ndvi: float = Query(default=0.5),
):
    alerts: list[str] = []
    score = 100

    # Temperature check
    if avg_temp_c < 10:
        alerts.append(f"⚠️ Temperature is very low ({avg_temp_c}°C). Most crops prefer 15-35°C.")
        score -= 15
    elif avg_temp_c > 40:
        alerts.append(f"⚠️ Temperature is very high ({avg_temp_c}°C). Heat stress likely.")
        score -= 15

    # Rainfall check
    if rainfall_mm < 30:
        alerts.append(f"⚠️ Very low rainfall ({rainfall_mm}mm). Irrigation strongly recommended.")
        score -= 15
    elif rainfall_mm > 400:
        alerts.append(f"⚠️ Excessive rainfall ({rainfall_mm}mm). Flooding risk for many crops.")
        score -= 10

    # Soil pH
    if soil_ph < 4.5:
        alerts.append(f"⚠️ Soil is very acidic (pH {soil_ph}). Lime application recommended.")
        score -= 10
    elif soil_ph > 8.5:
        alerts.append(f"⚠️ Soil is very alkaline (pH {soil_ph}). Gypsum may help.")
        score -= 10

    # NDVI
    if ndvi < 0.2:
        alerts.append(f"⚠️ Very low NDVI ({ndvi}). Vegetation health is poor.")
        score -= 10

    # Water stress
    if water_stress_index > 0.7:
        alerts.append(f"⚠️ High water stress index ({water_stress_index}). Drought conditions likely.")
        score -= 10

    # Humidity
    if humidity_pct < 20:
        alerts.append("⚠️ Very low humidity. Arid conditions may limit growth.")
        score -= 5
    elif humidity_pct > 90:
        alerts.append("⚠️ Very high humidity. Fungal disease risk increases.")
        score -= 5

    # Nutrient check
    total_npk = n_kgha + p_kgha + k_kgha
    if total_npk < 30:
        nutrient_note = "Very low NPK levels. Fertilizer strongly recommended."
        score -= 15
    elif total_npk < 80:
        nutrient_note = "Moderate NPK levels. Consider topping up Nitrogen."
        score -= 5
    else:
        nutrient_note = "NPK levels are adequate for most crops."

    score = max(0, min(100, score))

    return {
        "condition_score": score,
        "alerts": alerts,
        "nutrient_note": nutrient_note,
    }
