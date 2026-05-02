from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import os
import json

router = APIRouter(prefix="/api", tags=["chat"])

# Server-side prediction context store (shared across ports)
_prediction_context: dict = {}

# Gemini setup
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyCqLplY4Bb3l8lvXZtzIiQAEL05irln1v0")
_genai_client = None
GEMINI_MODEL = "gemini-2.5-flash-lite"

def _get_client():
    global _genai_client
    if not GEMINI_API_KEY:
        return None
    if _genai_client is not None:
        return _genai_client
    try:
        from google import genai
        _genai_client = genai.Client(api_key=GEMINI_API_KEY)
        return _genai_client
    except Exception as e:
        print(f"Gemini init error: {e}")
        return None


class ChatPayload(BaseModel):
    message: str
    prediction_context: Dict[str, Any] = Field(default_factory=dict)
    chat_history: List[Dict[str, Any]] = Field(default_factory=list)

class PredictionContext(BaseModel):
    context: Dict[str, Any] = Field(default_factory=dict)


@router.post("/prediction-context")
def save_prediction_context(payload: PredictionContext):
    global _prediction_context
    _prediction_context = payload.context
    return {"status": "ok"}

@router.get("/prediction-context")
def get_prediction_context():
    return {"context": _prediction_context}

@router.get("/chat/status")
def chat_status():
    return {
        "gemini_enabled": bool(GEMINI_API_KEY and _get_client()),
        "model": GEMINI_MODEL if GEMINI_API_KEY else "rule-based"
    }


def _build_system_prompt(ctx: dict) -> str:
    """Build a rich system prompt with the user's prediction context."""
    r = lambda v: str(round(float(v))) if v is not None else "N/A"
    
    ctx_block = ""
    if ctx and ctx.get("Crop_Type"):
        ctx_block = f"""
## Current Prediction Context
- **Crop:** {ctx.get('Crop_Type', 'N/A')}
- **State:** {ctx.get('State', 'N/A')}
- **Season:** {ctx.get('Season', 'N/A')}
- **Predicted Yield:** {r(ctx.get('predicted_yield_kg_ha'))} kg/ha
- **Category:** {ctx.get('predicted_category', 'N/A')}
- **Recommended Crop:** {ctx.get('recommended_crop', 'N/A')}
- **Nitrogen (N):** {r(ctx.get('N_kgha'))} kg/ha
- **Phosphorus (P):** {r(ctx.get('P_kgha'))} kg/ha
- **Potassium (K):** {r(ctx.get('K_kgha'))} kg/ha
- **Rainfall:** {r(ctx.get('Rainfall_mm'))} mm
- **Soil pH:** {float(ctx.get('Soil_pH', 0)):.1f}
- **NDVI:** {float(ctx.get('NDVI', 0)):.2f}
- **Avg Temperature:** {float(ctx.get('Avg_Temp_C', 0)):.1f}°C
- **Humidity:** {float(ctx.get('Humidity_Pct', 0)):.1f}%
- **Water Stress Index:** {float(ctx.get('Water_Stress_Index', 0)):.2f}
"""
    
    return f"""You are **CropAI**, an expert agricultural AI assistant for Indian farmers. You help users understand their crop yield predictions and give actionable advice.

{ctx_block}

## Rules
1. Always be helpful, specific, and practical. Give **actionable** recommendations.
2. Reference the user's actual prediction data (crop, yield, NPK, etc.) in your answers.
3. Use **bold** for key terms and bullet points for lists.
4. Keep responses concise — 3-5 short paragraphs max.
5. If the user's yield category is Low, proactively suggest improvements.
6. For NPK advice, reference Indian ICAR standards for the specific crop.
7. If you don't know something specific, say so honestly.
8. Format numbers nicely (e.g., 12,500 kg/ha instead of 12500).
9. Use Indian farming context (Kharif, Rabi, Zaid seasons; Indian states; INR costs).
"""


def _gemini_reply(message: str, ctx: dict, history: list) -> str | None:
    """Try to get a response from Gemini."""
    client = _get_client()
    if not client:
        return None
    
    try:
        system_prompt = _build_system_prompt(ctx)
        
        # Build the full prompt with history
        full_prompt = system_prompt + "\n\n"
        
        if history:
            recent = history[-6:]
            full_prompt += "## Recent Conversation:\n"
            for m in recent:
                role = "User" if m.get('role') == 'user' else "CropAI"
                full_prompt += f"{role}: {m.get('content', '')}\n"
            full_prompt += "\n"
        
        full_prompt += f"---\nUser: {message}\n\nCropAI:"
        
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=full_prompt
        )
        return response.text
    except Exception as e:
        print(f"Gemini error: {e}")
        return None


def simple_rule_based_ai(msg: str, ctx: dict) -> str:
    """Fallback rule-based responses when Gemini is not available."""
    msg_lower = msg.lower()
    crop = ctx.get("Crop_Type", "the selected crop")
    yield_val = ctx.get("predicted_yield_kg_ha", ctx.get("predicted_yield", "N/A"))
    if isinstance(yield_val, (int, float)):
        yield_val = f"{round(yield_val):,}"
    cat = ctx.get("predicted_category", ctx.get("category", "N/A"))
    rec = ctx.get("recommended_crop", "N/A")
    
    n = ctx.get("N_kgha", "N/A")
    p = ctx.get("P_kgha", "N/A")
    k = ctx.get("K_kgha", "N/A")
    if isinstance(n, float): n = round(n)
    if isinstance(p, float): p = round(p)
    if isinstance(k, float): k = round(k)
    
    rain = ctx.get("Rainfall_mm", "N/A")
    if isinstance(rain, float): rain = round(rain)
    
    ph = ctx.get("Soil_pH", "N/A")
    if isinstance(ph, float): ph = round(ph, 1)
    
    if not ctx.get("Crop_Type"):
        return "I don't have your prediction data yet. Please make a prediction on the **Predict** page first, then come back here to ask questions about your results!"
    
    if "yield" in msg_lower or "predict" in msg_lower or "result" in msg_lower:
        response = f"Based on your current conditions for **{crop}** in **{ctx.get('State', 'your region')}** ({ctx.get('Season', '')} season):\n\n"
        response += f"• **Predicted Yield:** {yield_val} kg/ha\n"
        response += f"• **Category:** {cat}\n"
        response += f"• **Recommended Crop:** {rec}\n\n"
        if cat == "Low":
            response += "⚠️ Your yield is classified as **Low**. Consider optimizing your NPK levels and ensuring adequate irrigation."
        elif cat == "High":
            response += "✅ Great news! Your conditions are optimal for a **High** yield. Keep maintaining these soil and climate conditions."
        else:
            response += "Your yield is **Medium**. There's room for improvement — try adjusting your fertilizer ratios or irrigation."
        return response
    
    if "increase" in msg_lower or "improve" in msg_lower or "boost" in msg_lower:
        return f"Here are actionable steps to **improve yield** for **{crop}**:\n\n**1. Optimize NPK Fertilizer:**\n• Current: N={n}, P={p}, K={k} kg/ha\n• Ensure Nitrogen is above 40 kg/ha for most crops\n• Balance P and K based on soil test results\n\n**2. Water Management:**\n• Current rainfall: {rain} mm\n• If below optimal, use drip/sprinkler irrigation\n• Avoid waterlogging — maintain proper drainage\n\n**3. Soil Health:**\n• Current pH: {ph}\n• Most crops prefer pH 6.0–7.5\n• Add lime if too acidic, gypsum if too alkaline\n\n**4. Crop Protection:**\n• Monitor for pests and diseases regularly\n• Use integrated pest management (IPM)"
    
    if "soil" in msg_lower or "npk" in msg_lower or "fertilizer" in msg_lower or "nutrient" in msg_lower:
        return f"**Soil & Nutrient Analysis for {crop}:**\n\n• **Nitrogen (N):** {n} kg/ha — Key for vegetative growth and leaf development\n• **Phosphorus (P):** {p} kg/ha — Essential for root development and flowering\n• **Potassium (K):** {k} kg/ha — Improves stress tolerance and grain quality\n• **Soil pH:** {ph}\n\n**Recommendation:** For {crop}, maintain a balanced NPK ratio. If yield category is {cat}, consider soil testing and applying fertilizers in split doses for better absorption."
    
    if "water" in msg_lower or "rain" in msg_lower or "irrigation" in msg_lower:
        return f"**Water & Irrigation for {crop}:**\n\n• Current rainfall: **{rain} mm**\n• Water Stress Index: **{ctx.get('Water_Stress_Index', 'N/A')}**\n\nFor {crop}, adequate water is critical especially during:\n• **Germination** — consistent moisture needed\n• **Flowering** — drought stress here reduces yield significantly\n• **Grain filling** — moderate water for quality grains\n\nIf rainfall is insufficient, use **drip irrigation** for 30-40% water savings compared to flood irrigation."
    
    if "best" in msg_lower or "recommend" in msg_lower or "crop" in msg_lower:
        return f"Based on your current field conditions (soil, climate, location):\n\n• **Your selected crop:** {crop}\n• **Best recommended crop:** {rec}\n\nThe recommendation considers your soil nutrients (N={n}, P={p}, K={k}), rainfall ({rain} mm), temperature, and regional suitability.\n\nThe recommended crop is predicted to give the **highest yield** under these exact conditions."
    
    if "ndvi" in msg_lower:
        ndvi = ctx.get("NDVI", "N/A")
        if isinstance(ndvi, float): ndvi = round(ndvi, 2)
        return f"**NDVI (Normalized Difference Vegetation Index):**\n\nYour NDVI value: **{ndvi}**\n\n• **> 0.6** — Dense, healthy vegetation ✅\n• **0.3 – 0.6** — Moderate vegetation health\n• **0.2 – 0.3** — Sparse vegetation ⚠️\n• **< 0.2** — Bare soil or very poor crop health ❌\n\nNDVI is measured via satellite imagery and indicates how well your crops are photosynthesizing."
    
    if "stress" in msg_lower:
        wsi = ctx.get("Water_Stress_Index", "N/A")
        if isinstance(wsi, float): wsi = round(wsi, 2)
        return f"**Water Stress Index:**\n\nYour value: **{wsi}**\n\n• **< 0.3** — No stress, adequate water ✅\n• **0.3 – 0.5** — Mild stress, monitor irrigation\n• **0.5 – 0.7** — Moderate stress ⚠️\n• **> 0.7** — Severe drought stress ❌\n\nHigh water stress significantly reduces {crop} yield. Consider supplemental irrigation if your index exceeds 0.5."
    
    if "temperature" in msg_lower or "temp" in msg_lower or "climate" in msg_lower:
        temp = ctx.get("Avg_Temp_C", "N/A")
        if isinstance(temp, float): temp = round(temp, 1)
        humidity = ctx.get("Humidity_Pct", "N/A")
        if isinstance(humidity, float): humidity = round(humidity, 1)
        return f"**Climate Conditions:**\n\n• **Average Temperature:** {temp}°C\n• **Humidity:** {humidity}%\n\nMost crops grow best between **15-35°C**. Extreme heat (>40°C) causes heat stress, while cold (<10°C) slows growth.\n\nHigh humidity (>80%) increases fungal disease risk. Low humidity (<30%) may cause water stress."
    
    return f"I'm **CropAI** — your agricultural assistant! I can help you with:\n\n• 📊 Understanding your **{crop}** yield prediction ({yield_val} kg/ha)\n• 🧪 **Soil & NPK** analysis and fertilizer advice\n• 💧 **Water & irrigation** management\n• 🌡️ **Climate** impact on your crops\n• 🌾 **Best crop** recommendations for your conditions\n\nTry asking me a specific question!"


@router.post("/chat")
def chat(payload: ChatPayload):
    ctx = payload.prediction_context if payload.prediction_context else _prediction_context
    
    # Try Gemini first
    gemini_reply = _gemini_reply(payload.message, ctx, payload.chat_history)
    if gemini_reply:
        return {"reply": gemini_reply, "source": "gemini"}
    
    # Fallback to rule-based
    reply = simple_rule_based_ai(payload.message, ctx)
    return {"reply": reply, "source": "rules"}
