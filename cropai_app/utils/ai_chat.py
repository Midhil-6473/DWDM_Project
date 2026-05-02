from __future__ import annotations

import os

import anthropic

def _ctx(context: dict, key: str, fallback: str = "N/A") -> str:
    val = context.get(key, context.get(key.lower(), fallback))
    return str(val if val not in (None, "") else fallback)


def explain_prediction(context: dict) -> str:
    crop = _ctx(context, "Crop_Type", "your crop")
    y = _ctx(context, "predicted_yield_kg_ha", "N/A")
    cat = _ctx(context, "predicted_category", "N/A")
    rain = _ctx(context, "Rainfall_mm", "N/A")
    n = _ctx(context, "N_kgha", "N/A")
    ph = _ctx(context, "Soil_pH", "N/A")
    return (
        f"For {crop}, your latest prediction is {y} kg/ha ({cat}).\n"
        f"- Key drivers to review first: Rainfall ({rain} mm), Nitrogen ({n} kg/ha), and Soil pH ({ph}).\n"
        "- Use the Live Yield Simulator to adjust one variable at a time and see the impact before making field changes."
    )


def fertilizer_advice(context: dict) -> str:
    crop = _ctx(context, "Crop_Type", "your crop")
    n = _ctx(context, "N_kgha", "N/A")
    p = _ctx(context, "P_kgha", "N/A")
    k = _ctx(context, "K_kgha", "N/A")
    return (
        f"Fertilizer guidance for {crop} (current NPK: {n}/{p}/{k} kg/ha):\n"
        "- Apply nitrogen in split doses (basal + top-dress) instead of one heavy dose.\n"
        "- Keep phosphorus for root establishment and potassium for stress tolerance.\n"
        "- Confirm doses with soil test reports and local extension guidance."
    )


def water_advice(context: dict) -> str:
    crop = _ctx(context, "Crop_Type", "your crop")
    rainfall = _ctx(context, "Rainfall_mm", "N/A")
    irrigation = _ctx(context, "Irrigation_Method", "N/A")
    return (
        f"Water strategy for {crop} (rainfall: {rainfall} mm, irrigation: {irrigation}):\n"
        "- Prioritize irrigation around flowering and grain/pod filling stages.\n"
        "- Avoid both long dry gaps and waterlogging.\n"
        "- Use mulch and field leveling to improve moisture efficiency."
    )


def crop_recommendation(context: dict) -> str:
    state = _ctx(context, "State", "your region")
    season = _ctx(context, "Season", "current season")
    return (
        f"For {state} in {season}, shortlist 2–3 crops and compare yields under identical conditions.\n"
        "- Kharif candidates: Rice, Maize, Soybean, Cotton.\n"
        "- Rabi candidates: Wheat, Mustard, Chickpea, Potato.\n"
        "- Use the Compare with Another Crop tool to choose the best fit from your own inputs."
    )


def soil_advice(context: dict) -> str:
    ph = _ctx(context, "Soil_pH", "N/A")
    moisture = _ctx(context, "Soil_Moisture_Pct", "N/A")
    return (
        f"Soil health snapshot: pH {ph}, moisture {moisture}%.\n"
        "- Low pH soils may need liming; high pH soils may need gypsum-based correction.\n"
        "- Improve organic matter using compost/green manure.\n"
        "- Re-test soil periodically to avoid over-correction."
    )


def feature_explanation(q: str) -> str:
    ql = q.lower()
    if "ndvi" in ql:
        return "NDVI is a vegetation index. Higher NDVI usually indicates healthier and denser crop canopy."
    if "water stress" in ql:
        return "Water stress index indicates whether crop water demand is higher than available moisture."
    if "bulk density" in ql:
        return "Bulk density reflects soil compaction; high values can reduce root growth and water movement."
    return "That input describes a field condition that influences yield. You can tune it on the Predict page and watch output changes."


def yield_improvement_tips(context: dict) -> str:
    crop = _ctx(context, "Crop_Type", "your crop")
    return (
        f"To improve {crop} yield:\n"
        "- Bring NPK and pH into crop-optimal ranges.\n"
        "- Reduce pest/disease incidence through weekly scouting.\n"
        "- Keep irrigation timing aligned with growth stage demand.\n"
        "- Re-check prediction after each major adjustment."
    )


def rule_based_response(question: str, context: dict) -> str:
    q = question.lower()
    if any(w in q for w in ["why", "medium", "low", "high", "explain", "result"]):
        return explain_prediction(context)
    if any(w in q for w in ["nitrogen", "fertilizer", "npk", "nutrient", "urea"]):
        return fertilizer_advice(context)
    if any(w in q for w in ["water", "irrigation", "rainfall", "drought"]):
        return water_advice(context)
    if any(w in q for w in ["best crop", "which crop", "recommend crop", "suitable", "compare crop"]):
        return crop_recommendation(context)
    if any(w in q for w in ["ph", "soil", "organic", "carbon", "texture"]):
        return soil_advice(context)
    if any(w in q for w in ["ndvi", "evapotranspiration", "et0", "water stress", "bulk density"]):
        return feature_explanation(q)
    if any(w in q for w in ["improve", "increase yield", "boost", "better yield"]):
        return yield_improvement_tips(context)
    return "I can help with crop yield, fertilizer planning, soil health, irrigation, and interpreting your prediction. Please ask a specific question."


def get_ai_response(user_message: str, prediction_context: dict, chat_history: list[dict]) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return rule_based_response(user_message, prediction_context)

    system_prompt = f"""
    You are CropAI, a friendly and knowledgeable agricultural assistant for an Indian crop yield prediction system. You help farmers, students, and researchers understand crop yield predictions and improve their farming practices.
    
    Current user prediction context:
    {prediction_context}
    
    Your knowledge base:
    - 10 Indian crops: Rice, Wheat, Maize, Sugarcane, Cotton, Soybean, Groundnut, Potato, Chickpea, Mustard
    - 15 Indian states and their typical crops
    - Optimal NPK ranges, pH levels, rainfall needs for each crop
    - Kharif season: June–November (monsoon crops)
    - Rabi season: October–March (winter crops)
    - Key yield factors: NPK nutrition, rainfall, temperature, soil pH, pest and disease management
    - The model uses Random Forest achieving R2=0.9649 for regression and 91.18% accuracy for classification
    
    Response guidelines:
    - Keep responses concise, clear, and practical
    - When user asks about their prediction, always refer to their specific values from the context
    - Give actionable recommendations with specific quantities where possible
    - Use simple language suitable for farmers but also suitable for students presenting this project
    - Do not mention model internals or technical ML details unless specifically asked
    - If asked what you cannot answer, say so politely and suggest what you can help with instead
    - Format responses with bullet points for readability when listing multiple items
    """
    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        # Anthropic requires messages to start with "user" and strictly alternate.
        # We will build a valid history from the bottom up.
        valid_history = []
        last_role = "assistant" # The message we are about to append is "user", so we want the one before it to be "assistant"
        
        for msg in reversed(chat_history[-10:]):
            role = msg.get("role", "user")
            if role in ("assistant", "model"):
                role = "assistant"
            else:
                role = "user"
                
            if role != last_role:
                valid_history.insert(0, {"role": role, "content": str(msg.get("content", ""))})
                last_role = role
                
        # If the history ended up starting with assistant, drop the first message
        if valid_history and valid_history[0]["role"] == "assistant":
            valid_history.pop(0)
            
        valid_history.append({"role": "user", "content": user_message})
        
        response = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=600,
            system=system_prompt,
            messages=valid_history
        )
        text = (response.content[0].text or "").strip()
        return text if text else rule_based_response(user_message, prediction_context)
    except Exception as exc:
        print(f"Anthropic error: {exc}")
        return rule_based_response(user_message, prediction_context)
