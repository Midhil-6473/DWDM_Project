import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path

from app.routers.analytics import router as analytics_router
from app.routers.meta import router as meta_router
from app.routers.predict import router as predict_router
from app.routers.batch import router as batch_router
from app.routers.chat import router as chat_router

BASE = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE / "templates"))

from contextlib import asynccontextmanager
from app.services.model_service import train_or_load_models
from app.services.data_service import get_dataframe

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run heavy startup tasks in a background thread so the server starts instantly
    def background_startup():
        try:
            print("Background: Loading dataset and warming up models...")
            get_dataframe()
            from app.services.model_service import train_or_load_models
            train_or_load_models()
            print("Background: Startup tasks complete.")
        except Exception as e:
            print(f"Background Startup error: {e}")

    import threading
    threading.Thread(target=background_startup, daemon=True).start()
    yield

app = FastAPI(title="DWDM Crop Yield API", version="1.0.0", lifespan=lifespan)
app.state.batch_sessions = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")

# Mount frontend assets
FRONTEND_DIST = BASE.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

from fastapi.responses import RedirectResponse, FileResponse

@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse(request, "landing.html")

@app.get("/predict")
def predict_page():
    index_path = FRONTEND_DIST / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return HTMLResponse("Frontend not built. Run 'npm run build' in frontend directory.")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/batch", response_class=HTMLResponse)
def batch_page(request: Request):
    return templates.TemplateResponse(request, "batch.html", {"active_page": "batch"})

@app.get("/chat", response_class=HTMLResponse)
def chat_page(request: Request):
    return templates.TemplateResponse(request, "chat.html", {"active_page": "chat"})

@app.get("/analytics-view", response_class=HTMLResponse)
def analytics_page(request: Request):
    return templates.TemplateResponse(request, "analytics.html", {"active_page": "analytics"})

app.include_router(meta_router)
app.include_router(predict_router)
app.include_router(analytics_router)
app.include_router(batch_router)
app.include_router(chat_router)
