from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from utils.ai_chat import get_ai_response

router = APIRouter(prefix="/api", tags=["chat"])


class ChatPayload(BaseModel):
    message: str
    prediction_context: dict = Field(default_factory=dict)
    chat_history: list[dict] = Field(default_factory=list)


@router.post("/chat")
def chat(payload: ChatPayload):
    response = get_ai_response(payload.message, payload.prediction_context, payload.chat_history)
    return {"reply": response}
