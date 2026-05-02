# Simplified constants for Batch and Chat
CROPS = ["Rice", "Wheat", "Maize", "Sugarcane", "Cotton", "Soybean", "Groundnut", "Potato", "Chickpea", "Mustard"]
SEASONS = ["Kharif", "Rabi", "Annual"]
IRRIGATION = ["Drip", "Sprinkler", "Flood", "Furrow", "Rainfed"]
FERTILIZERS = ["Urea", "DAP", "MOP", "NPK Complex", "Organic", "Mixed"]
SOIL_TYPES = ["Sandy", "Sandy Loam", "Loamy", "Silt Loam", "Clay Loam", "Clay", "Red Laterite", "Black Cotton"]

NATIONAL_AVG = {
    "Rice": 2609, "Wheat": 2057, "Maize": 1796, "Sugarcane": 34209,
    "Cotton": 855, "Soybean": 975, "Groundnut": 784, "Potato": 11083,
    "Chickpea": 505, "Mustard": 561
}

BATCH_REQUIRED_COLUMNS = [
    "Season", "State", "Crop_Type", "Soil_Type", "Irrigation_Method", "Fertilizer_Type",
    "Avg_Temp_C", "Rainfall_mm", "Humidity_Pct", "Water_Stress_Index", "Soil_pH",
    "N_kgha", "P_kgha", "K_kgha", "NDVI"
]

SLIDER_LIMITS = {
    "Avg_Temp_C": (2, 45), "Rainfall_mm": (0, 500), "Humidity_Pct": (20, 98),
    "Soil_pH": (4.5, 9.0), "N_kgha": (0, 300), "P_kgha": (0, 150),
    "K_kgha": (0, 241), "NDVI": (0.1, 0.95), "Water_Stress_Index": (0, 1)
}

MODEL_DEFAULTS = {
    "Season": "Kharif", "State": "Andhra Pradesh", "Crop_Type": "Rice",
    "Soil_Type": "Loamy", "Irrigation_Method": "Drip", "Fertilizer_Type": "Urea",
    "Avg_Temp_C": 25.0, "Rainfall_mm": 120.0, "Humidity_Pct": 70.0,
    "Water_Stress_Index": 0.35, "Soil_pH": 6.5, "N_kgha": 90.0,
    "P_kgha": 45.0, "K_kgha": 50.0, "NDVI": 0.6
}

def normalize_state_name(name: str) -> str:
    return str(name).strip().title()

def normalize_category_label(label: Any) -> str:
    if isinstance(label, (int, float)):
        if label == 0: return "Low"
        if label == 1: return "Medium"
        return "High"
    return str(label).strip().capitalize()
