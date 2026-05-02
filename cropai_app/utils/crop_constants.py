from __future__ import annotations

CROPS = ["Rice", "Wheat", "Maize", "Sugarcane", "Cotton", "Soybean", "Groundnut", "Potato", "Chickpea", "Mustard"]
SEASONS = ["Kharif", "Rabi", "Annual"]
STATES = [
    "Punjab",
    "Haryana",
    "Uttar Pradesh",
    "West Bengal",
    "Tamil Nadu",
    "Andhra Pradesh",
    "Telangana",
    "Karnataka",
    "Maharashtra",
    "Madhya Pradesh",
    "Rajasthan",
    "Gujarat",
    "Bihar",
    "Odisha",
    "Assam",
]
IRRIGATION = ["Drip", "Sprinkler", "Flood", "Furrow", "Rainfed"]
FERTILIZERS = ["Urea", "DAP", "MOP", "NPK Complex", "Organic", "Mixed"]
SOIL_TYPES = ["Sandy", "Sandy Loam", "Loamy", "Silt Loam", "Clay Loam", "Clay", "Red Laterite", "Black Cotton"]
INCIDENCE_LEVELS = ["None", "Low", "Moderate", "High"]

CROP_EMOJI = {
    "Rice": "🌾",
    "Wheat": "🌾",
    "Maize": "🌽",
    "Sugarcane": "🎋",
    "Cotton": "🌿",
    "Soybean": "🫘",
    "Groundnut": "🥜",
    "Potato": "🥔",
    "Chickpea": "🫛",
    "Mustard": "🌻",
}

INPUT_COLUMNS = [
    "Crop_Type",
    "Season",
    "State",
    "Irrigation_Method",
    "Fertilizer_Type",
    "Avg_Temp_C",
    "Rainfall_mm",
    "Humidity_Pct",
    "Solar_Radiation_MJm2",
    "Wind_Speed_kmh",
    "Max_Temp_C",
    "Min_Temp_C",
    "Soil_Type",
    "Soil_pH",
    "Soil_Moisture_Pct",
    "Organic_Carbon_Pct",
    "Bulk_Density_gcm3",
    "N_kgha",
    "P_kgha",
    "K_kgha",
    "Sulfur_kgha",
    "Zinc_ppm",
    "Iron_ppm",
    "NDVI",
    "Water_Stress_Index",
    "Pest_Incidence",
    "Disease_Incidence",
]

NUMERIC_COLUMNS = [
    "Avg_Temp_C",
    "Rainfall_mm",
    "Humidity_Pct",
    "Solar_Radiation_MJm2",
    "Wind_Speed_kmh",
    "Max_Temp_C",
    "Min_Temp_C",
    "Soil_pH",
    "Soil_Moisture_Pct",
    "Organic_Carbon_Pct",
    "Bulk_Density_gcm3",
    "N_kgha",
    "P_kgha",
    "K_kgha",
    "Sulfur_kgha",
    "Zinc_ppm",
    "Iron_ppm",
    "NDVI",
    "Water_Stress_Index",
]

MODEL_DEFAULTS = {
    "Crop_Type": "Rice",
    "Season": "Kharif",
    "State": "Punjab",
    "Irrigation_Method": "Drip",
    "Fertilizer_Type": "Urea",
    "Avg_Temp_C": 25.0,
    "Rainfall_mm": 120.0,
    "Humidity_Pct": 70.0,
    "Solar_Radiation_MJm2": 20.0,
    "Wind_Speed_kmh": 8.0,
    "Max_Temp_C": 34.0,
    "Min_Temp_C": 18.0,
    "Soil_Type": "Loamy",
    "Soil_pH": 6.5,
    "Soil_Moisture_Pct": 45.0,
    "Organic_Carbon_Pct": 1.2,
    "Bulk_Density_gcm3": 1.35,
    "N_kgha": 90.0,
    "P_kgha": 45.0,
    "K_kgha": 50.0,
    "Sulfur_kgha": 20.0,
    "Zinc_ppm": 1.8,
    "Iron_ppm": 8.0,
    "NDVI": 0.6,
    "Pest_Incidence": "Low",
    "Disease_Incidence": "Low",
    # Backward-compatible optional training columns:
    "Water_Stress_Index": 0.35,
}

OPTIMAL_PRESET = {
    "Rice": {"Avg_Temp_C": 27, "Rainfall_mm": 200, "N_kgha": 110, "P_kgha": 45, "K_kgha": 60, "Soil_pH": 6.0},
    "Wheat": {"Avg_Temp_C": 17, "Rainfall_mm": 110, "N_kgha": 130, "P_kgha": 55, "K_kgha": 45, "Soil_pH": 6.5},
    "Maize": {"Avg_Temp_C": 24, "Rainfall_mm": 175, "N_kgha": 140, "P_kgha": 60, "K_kgha": 70, "Soil_pH": 6.4},
    "Sugarcane": {"Avg_Temp_C": 30, "Rainfall_mm": 225, "N_kgha": 200, "P_kgha": 75, "K_kgha": 150, "Soil_pH": 6.5},
    "Cotton": {"Avg_Temp_C": 29, "Rainfall_mm": 100, "N_kgha": 110, "P_kgha": 45, "K_kgha": 60, "Soil_pH": 7.0},
    "Soybean": {"Avg_Temp_C": 25, "Rainfall_mm": 150, "N_kgha": 30, "P_kgha": 60, "K_kgha": 75, "Soil_pH": 6.5},
    "Groundnut": {"Avg_Temp_C": 30, "Rainfall_mm": 85, "N_kgha": 22, "P_kgha": 55, "K_kgha": 60, "Soil_pH": 6.5},
    "Potato": {"Avg_Temp_C": 18, "Rainfall_mm": 112, "N_kgha": 160, "P_kgha": 80, "K_kgha": 150, "Soil_pH": 6.0},
    "Chickpea": {"Avg_Temp_C": 20, "Rainfall_mm": 70, "N_kgha": 22, "P_kgha": 55, "K_kgha": 35, "Soil_pH": 7.0},
    "Mustard": {"Avg_Temp_C": 15, "Rainfall_mm": 55, "N_kgha": 90, "P_kgha": 45, "K_kgha": 30, "Soil_pH": 6.5},
}

YIELD_MIN_MAX = {
    "Rice": (800, 6436),
    "Wheat": (500, 5001),
    "Maize": (600, 4459),
    "Sugarcane": (20000, 83737),
    "Cotton": (300, 2091),
    "Soybean": (400, 2573),
    "Groundnut": (400, 1987),
    "Potato": (5000, 26993),
    "Chickpea": (300, 1308),
    "Mustard": (300, 1440),
}

NATIONAL_AVG = {
    "Rice": 2609,
    "Wheat": 2057,
    "Maize": 1796,
    "Sugarcane": 34209,
    "Cotton": 855,
    "Soybean": 975,
    "Groundnut": 784,
    "Potato": 11083,
    "Chickpea": 505,
    "Mustard": 561,
}

OPTIMAL_RANGES = {
    "N_kgha": {
        "Rice": (80, 150),
        "Wheat": (100, 160),
        "Maize": (100, 180),
        "Sugarcane": (150, 250),
        "Cotton": (80, 140),
        "Soybean": (20, 40),
        "Groundnut": (15, 30),
        "Potato": (120, 200),
        "Chickpea": (15, 30),
        "Mustard": (60, 120),
    },
    "Rainfall_mm": {
        "Rice": (150, 300),
        "Wheat": (75, 150),
        "Maize": (100, 250),
        "Sugarcane": (150, 300),
        "Cotton": (70, 130),
        "Soybean": (100, 200),
        "Groundnut": (50, 120),
        "Potato": (75, 150),
        "Chickpea": (40, 100),
        "Mustard": (30, 80),
    },
    "Soil_pH": {
        "Rice": (5.5, 6.5),
        "Wheat": (6.0, 7.5),
        "Maize": (5.8, 7.0),
        "Sugarcane": (6.0, 7.5),
        "Cotton": (6.0, 8.0),
        "Soybean": (6.0, 7.0),
        "Groundnut": (6.0, 7.5),
        "Potato": (5.5, 6.5),
        "Chickpea": (6.0, 8.0),
        "Mustard": (6.0, 7.5),
    },
    "K_kgha": {
        "Rice": (40, 80),
        "Wheat": (30, 60),
        "Maize": (50, 90),
        "Sugarcane": (100, 200),
        "Cotton": (40, 80),
        "Soybean": (50, 100),
        "Groundnut": (40, 80),
        "Potato": (100, 200),
        "Chickpea": (20, 50),
        "Mustard": (20, 40),
    },
    "P_kgha": {
        "Rice": (30, 60),
        "Wheat": (40, 70),
        "Maize": (40, 70),
        "Sugarcane": (50, 100),
        "Cotton": (30, 60),
        "Soybean": (40, 80),
        "Groundnut": (35, 75),
        "Potato": (60, 100),
        "Chickpea": (35, 70),
        "Mustard": (30, 60),
    },
    "Avg_Temp_C": {
        "Rice": (23, 32),
        "Wheat": (12, 25),
        "Maize": (18, 30),
        "Sugarcane": (24, 35),
        "Cotton": (23, 34),
        "Soybean": (20, 30),
        "Groundnut": (24, 34),
        "Potato": (14, 24),
        "Chickpea": (16, 28),
        "Mustard": (10, 22),
    },
}

OPTIMAL_HINTS = {
    "Humidity_Pct": (55, 85, "%"),
    "Solar_Radiation_MJm2": (16, 24, "MJ/m²"),
    "Wind_Speed_kmh": (2, 18, "km/h"),
    "Max_Temp_C": (24, 38, "°C"),
    "Min_Temp_C": (8, 24, "°C"),
    "Soil_Moisture_Pct": (30, 70, "%"),
    "Organic_Carbon_Pct": (0.8, 2.2, "%"),
    "Bulk_Density_gcm3": (1.1, 1.5, "g/cm³"),
    "Sulfur_kgha": (15, 40, "kg/ha"),
    "Zinc_ppm": (1.0, 3.5, "ppm"),
    "Iron_ppm": (4, 18, "ppm"),
    "NDVI": (0.55, 0.85, ""),
}

SEASON_RULES = {
    "Rice": {"primary": ["Kharif"], "warn": ["Rabi"]},
    "Wheat": {"primary": ["Rabi"], "warn": ["Kharif"]},
    "Maize": {"primary": ["Kharif", "Rabi"], "warn": []},
    "Sugarcane": {"primary": ["Annual"], "warn": ["Kharif", "Rabi"]},
    "Cotton": {"primary": ["Kharif"], "warn": ["Rabi"]},
    "Soybean": {"primary": ["Kharif"], "warn": ["Rabi", "Annual"]},
    "Groundnut": {"primary": ["Kharif", "Rabi"], "warn": []},
    "Potato": {"primary": ["Rabi"], "warn": ["Kharif"]},
    "Chickpea": {"primary": ["Rabi"], "warn": ["Kharif", "Annual"]},
    "Mustard": {"primary": ["Rabi"], "warn": ["Kharif", "Annual"]},
}

SEASON_WARN_DETAIL = {
    "Rice|Rabi": "Rice is primarily a Kharif crop. Growing Rice in Rabi season may result in lower yield due to cooler temperatures and reduced sunlight. Consider Wheat or Mustard for Rabi season.",
    "Wheat|Kharif": "Wheat is primarily a Rabi crop. Growing Wheat in Kharif season may reduce yield due to heat and humidity stress.",
    "Cotton|Rabi": "Cotton is primarily a Kharif crop. Rabi cotton requires stricter moisture and pest management.",
    "Soybean|Rabi": "Soybean is generally suited for Kharif. Rabi soybean can underperform in many regions.",
    "Potato|Kharif": "Potato is primarily a Rabi crop. Kharif potato can face disease pressure in warm-wet conditions.",
    "Chickpea|Kharif": "Chickpea is primarily a Rabi crop; Kharif sowing is often sub-optimal.",
    "Mustard|Kharif": "Mustard is primarily a Rabi crop and usually performs better in cooler months.",
    "Sugarcane|Kharif": "Sugarcane is best treated as an annual cycle. Kharif-only tagging may not capture its growth duration.",
    "Sugarcane|Rabi": "Sugarcane is best treated as an annual cycle. Rabi-only tagging may not capture its growth duration.",
}

CALENDAR = {
    ("Rice", "Kharif"): ("Jun 15–Jul 15", "Oct–Nov", 130),
    ("Wheat", "Rabi"): ("Nov 1–Nov 30", "Mar–Apr", 120),
    ("Maize", "Kharif"): ("Jun–Jul", "Sep–Oct", 95),
    ("Maize", "Rabi"): ("Oct–Nov", "Feb–Mar", 100),
    ("Sugarcane", "Annual"): ("Feb–Mar", "Jan–Mar (next yr)", 330),
    ("Cotton", "Kharif"): ("May–Jun", "Oct–Feb", 180),
    ("Soybean", "Kharif"): ("Jun–Jul", "Oct–Nov", 100),
    ("Groundnut", "Kharif"): ("Jun–Jul", "Oct–Nov", 110),
    ("Groundnut", "Rabi"): ("Nov–Dec", "Mar–Apr", 120),
    ("Potato", "Rabi"): ("Oct–Nov", "Jan–Feb", 90),
    ("Chickpea", "Rabi"): ("Oct–Nov", "Feb–Mar", 100),
    ("Mustard", "Rabi"): ("Oct–Nov", "Feb–Mar", 110),
}

SLIDER_LIMITS = {
    "Avg_Temp_C": (2, 45),
    "Rainfall_mm": (0, 500),
    "Humidity_Pct": (20, 98),
    "Solar_Radiation_MJm2": (12.0, 28.0),
    "Wind_Speed_kmh": (0.0, 32.0),
    "Max_Temp_C": (5, 52),
    "Min_Temp_C": (-6, 40),
    "Soil_pH": (4.5, 9.0),
    "Soil_Moisture_Pct": (10, 85),
    "Organic_Carbon_Pct": (0.1, 3.5),
    "Bulk_Density_gcm3": (0.9, 1.8),
    "N_kgha": (0, 300),
    "P_kgha": (0, 150),
    "K_kgha": (0, 241),
    "Sulfur_kgha": (0, 60),
    "Zinc_ppm": (0, 6.5),
    "Iron_ppm": (0, 30),
    "NDVI": (0.1, 0.95),
}

RADAR_MAX = {
    "Rice": {"N": 150, "P": 60, "K": 80, "Rainfall": 300, "Temp": 32, "pH": 6.5},
    "Wheat": {"N": 160, "P": 70, "K": 60, "Rainfall": 150, "Temp": 25, "pH": 7.5},
    "Maize": {"N": 180, "P": 70, "K": 90, "Rainfall": 250, "Temp": 30, "pH": 7.0},
    "Sugarcane": {"N": 250, "P": 100, "K": 200, "Rainfall": 300, "Temp": 35, "pH": 7.5},
    "Cotton": {"N": 140, "P": 60, "K": 80, "Rainfall": 130, "Temp": 34, "pH": 8.0},
    "Soybean": {"N": 40, "P": 80, "K": 100, "Rainfall": 200, "Temp": 30, "pH": 7.0},
    "Groundnut": {"N": 30, "P": 75, "K": 80, "Rainfall": 120, "Temp": 34, "pH": 7.5},
    "Potato": {"N": 200, "P": 100, "K": 200, "Rainfall": 150, "Temp": 24, "pH": 6.5},
    "Chickpea": {"N": 30, "P": 70, "K": 50, "Rainfall": 100, "Temp": 28, "pH": 8.0},
    "Mustard": {"N": 120, "P": 60, "K": 40, "Rainfall": 80, "Temp": 22, "pH": 7.5},
}

BATCH_REQUIRED_COLUMNS = list(INPUT_COLUMNS)

INDIA_STATE_NAME_MAP = {
    "andhra pradesh": "Andhra Pradesh",
    "arunachal pradesh": "Arunachal Pradesh",
    "assam": "Assam",
    "bihar": "Bihar",
    "chhattisgarh": "Chhattisgarh",
    "goa": "Goa",
    "gujarat": "Gujarat",
    "haryana": "Haryana",
    "himachal pradesh": "Himachal Pradesh",
    "jharkhand": "Jharkhand",
    "karnataka": "Karnataka",
    "kerala": "Kerala",
    "madhya pradesh": "Madhya Pradesh",
    "maharashtra": "Maharashtra",
    "manipur": "Manipur",
    "meghalaya": "Meghalaya",
    "mizoram": "Mizoram",
    "nagaland": "Nagaland",
    "odisha": "Odisha",
    "punjab": "Punjab",
    "rajasthan": "Rajasthan",
    "sikkim": "Sikkim",
    "tamil nadu": "Tamil Nadu",
    "telangana": "Telangana",
    "tripura": "Tripura",
    "uttar pradesh": "Uttar Pradesh",
    "uttarakhand": "Uttarakhand",
    "west bengal": "West Bengal",
    "nct of delhi": "Delhi",
    "delhi": "Delhi",
    "jammu and kashmir": "Jammu and Kashmir",
    "ladakh": "Ladakh",
}


def resolve_calendar(crop: str, season: str) -> tuple[str, str, int]:
    if (crop, season) in CALENDAR:
        return CALENDAR[(crop, season)]
    if (crop, "Annual") in CALENDAR:
        return CALENDAR[(crop, "Annual")]
    if crop in ("Rice", "Maize", "Groundnut") and season == "Rabi":
        return ("Oct–Nov", "Feb–Mar", 110)
    return ("Consult local advisory", "Consult local advisory", 0)


def normalize_state_name(name: str) -> str:
    if not name:
        return ""
    key = str(name).strip().lower()
    return INDIA_STATE_NAME_MAP.get(key, str(name).strip())
