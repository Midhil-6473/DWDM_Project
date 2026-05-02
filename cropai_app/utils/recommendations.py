from __future__ import annotations

from utils.crop_constants import OPTIMAL_RANGES


def _in_range(value: float, low: float, high: float) -> bool:
    return low <= value <= high


def _range_message(feature: str, value: float, low: float, high: float, unit: str, action: str) -> tuple[str, int]:
    unit_part = f" {unit}".rstrip()
    if _in_range(value, low, high):
        return (f"✅ {feature} is within the optimal range.", 0)
    if value < low:
        diff = round(low - value, 2)
        if diff >= 0.5 * (high - low):
            return (
                f"🔴 {feature} is critically low. Immediate action needed: {action}.",
                3,
            )
        return (
            f"⚠️ {feature} is {diff}{unit_part} below optimal range of {low}–{high}{unit_part}. Consider {action}.",
            2,
        )
    diff = round(value - high, 2)
    if diff >= 0.5 * (high - low):
        return (
            f"🔴 {feature} is critically high. Immediate action needed: {action}.",
            3,
        )
    return (
        f"⚠️ {feature} is {diff}{unit_part} above optimal range of {low}–{high}{unit_part}. Consider {action}.",
        2,
    )


def generate_recommendations(payload: dict, crop: str) -> list[str]:
    checks = [
        ("N_kgha", "Nitrogen", "kg/ha", "split nitrogen application and verify with a soil test"),
        ("Rainfall_mm", "Rainfall", "mm", "improving irrigation scheduling and moisture conservation"),
        ("Soil_pH", "Soil pH", "", "pH correction through lime/gypsum based on soil report"),
        ("K_kgha", "Potassium", "kg/ha", "balancing potash dose according to crop stage"),
    ]
    messages: list[tuple[str, int]] = []
    for key, label, unit, action in checks:
        low, high = OPTIMAL_RANGES[key][crop]
        val = float(payload.get(key, 0))
        messages.append(_range_message(label, val, low, high, unit, action))

    pest = str(payload.get("Pest_Incidence", "None"))
    disease = str(payload.get("Disease_Incidence", "None"))
    if pest == "High":
        messages.append(("🔴 High pest incidence detected. Apply appropriate pesticides immediately and consult local agricultural extension officer.", 3))
    elif pest == "Moderate":
        messages.append(("⚠️ Moderate pest pressure. Monitor closely and consider preventive treatment.", 2))
    else:
        messages.append(("✅ Pest pressure is minimal.", 0))

    if disease == "High":
        messages.append(("🔴 High disease incidence detected. Apply immediate crop protection and seek local agronomy support.", 3))
    elif disease == "Moderate":
        messages.append(("⚠️ Moderate disease pressure. Increase scouting and preventive disease management.", 2))
    else:
        messages.append(("✅ Disease pressure is minimal.", 0))

    if all(sev == 0 for _, sev in messages):
        return [f"🎉 Your field conditions are well-optimised for {crop} cultivation."]
    messages.sort(key=lambda x: x[1], reverse=True)
    return [m for m, _ in messages[:6]]


def field_health_score(payload: dict, crop: str) -> tuple[int, str]:
    weights = {
        "N_kgha": 1.4,
        "P_kgha": 1.0,
        "K_kgha": 1.2,
        "Rainfall_mm": 1.4,
        "Soil_pH": 1.2,
        "Avg_Temp_C": 1.0,
    }
    score_sum = 0.0
    total_w = 0.0
    for key, weight in weights.items():
        low, high = OPTIMAL_RANGES[key][crop]
        val = float(payload.get(key, 0))
        if _in_range(val, low, high):
            component = 1.0
        else:
            mid = (low + high) / 2.0
            spread = max(0.01, (high - low) / 2.0)
            dist = abs(val - mid) / spread
            component = max(0.2, 1.0 - 0.4 * dist)
        score_sum += weight * component
        total_w += weight

    def incidence_factor(level: str) -> float:
        if level in ("None", "Low"):
            return 1.0
        if level == "Moderate":
            return 0.7
        return 0.35

    for key in ("Pest_Incidence", "Disease_Incidence"):
        total_w += 0.9
        score_sum += 0.9 * incidence_factor(str(payload.get(key, "None")))

    score = int(round(100 * score_sum / max(0.01, total_w)))
    score = max(0, min(100, score))
    if score >= 90:
        return score, "Excellent"
    if score >= 70:
        return score, "Good"
    if score >= 50:
        return score, "Fair"
    return score, "Needs Attention"
