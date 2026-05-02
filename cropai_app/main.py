from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import joblib
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json

load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

from routers.batch import router as batch_router
from routers.chat import router as chat_router
from routers.predict import router as predict_router
from routers.meta import router as meta_router
from routers.analytics import router as analytics_router
from routers.dwdm_predict import router as dwdm_predict_router

from utils.crop_constants import BATCH_REQUIRED_COLUMNS, CROP_EMOJI, CROPS, FERTILIZERS, INCIDENCE_LEVELS, IRRIGATION, OPTIMAL_HINTS, OPTIMAL_PRESET, OPTIMAL_RANGES, SEASONS, SEASON_RULES, SEASON_WARN_DETAIL, SLIDER_LIMITS, SOIL_TYPES, STATES

BASE = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE / "templates"))
templates.env.filters["tojson"] = lambda x: json.dumps(x)

def _load_any(paths: list[Path]):
    for path in paths:
        if path.exists():
            return joblib.load(path)
    raise FileNotFoundError(f"None of these model files found: {[str(p) for p in paths]}")

def _load_optional(paths: list[Path]) -> Any | None:
    for path in paths:
        if path.exists():
            return joblib.load(path)
    return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    model_dir = BASE / "models"
    app.state.reg_model = _load_any(
        [
            model_dir / "regression_pipeline.joblib",
            model_dir / "random_forest_regressor.pkl",
            BASE.parent / "backend" / "models" / "regression_pipeline.joblib",
        ]
    )
    app.state.cls_model = _load_any(
        [
            model_dir / "classification_pipeline.joblib",
            model_dir / "random_forest_classifier.pkl",
            BASE.parent / "backend" / "models" / "classification_pipeline.joblib",
        ]
    )
    app.state.preprocessor = _load_optional([model_dir / "preprocessor.pkl"])
    app.state.batch_sessions = {}
    app.state.anthropic_configured = bool(ANTHROPIC_API_KEY)
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")
app.mount("/assets", StaticFiles(directory=str(BASE / "static" / "react_dist" / "assets")), name="react_assets")

app.include_router(predict_router)
app.include_router(batch_router)
app.include_router(chat_router)
app.include_router(meta_router)
app.include_router(analytics_router)
app.include_router(dwdm_predict_router)


@app.get("/health")
def health():
    return {"status": "ok"}


def _common_ctx(page: str):
    return {
        "active_page": page,
        "crops": CROPS,
        "crop_emoji": CROP_EMOJI,
        "seasons": SEASONS,
        "states": STATES,
        "irrigation": IRRIGATION,
        "fertilizers": FERTILIZERS,
        "soil_types": SOIL_TYPES,
        "incidence_levels": INCIDENCE_LEVELS,
        "optimal_preset": OPTIMAL_PRESET,
        "season_rules": SEASON_RULES,
        "season_warn_detail": SEASON_WARN_DETAIL,
        "optimal_ranges": OPTIMAL_RANGES,
        "optimal_hints": OPTIMAL_HINTS,
        "slider_limits": SLIDER_LIMITS,
        "batch_required_columns": BATCH_REQUIRED_COLUMNS,
    }


@app.get("/", response_class=HTMLResponse)
def predict_page(request: Request):
    return templates.TemplateResponse(request, "predict.html", _common_ctx("predict"))


@app.get("/batch", response_class=HTMLResponse)
def batch_page(request: Request):
    return templates.TemplateResponse(request, "batch.html", _common_ctx("batch"))


@app.get("/chat", response_class=HTMLResponse)
def chat_page(request: Request):
    return templates.TemplateResponse(request, "chat.html", _common_ctx("chat"))


@app.get("/analytics", response_class=HTMLResponse)
def analytics_page(request: Request):
    return templates.TemplateResponse(request, "analytics.html", _common_ctx("analytics"))
