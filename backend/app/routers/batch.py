import io
import uuid
import time
import pandas as pd
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Request
from fastapi.responses import FileResponse, StreamingResponse

from app.utils.crop_constants import BATCH_REQUIRED_COLUMNS, NATIONAL_AVG, SLIDER_LIMITS, MODEL_DEFAULTS, normalize_state_name, normalize_category_label
from app.services.model_service import train_or_load_models
from app.services.data_service import get_crop_stats

router = APIRouter(prefix="/api/batch", tags=["batch"])
BASE = Path(__file__).resolve().parents[2]

@router.get("/sample-template")
def sample_template():
    path = BASE / "app" / "data" / "sample_template.csv"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Template not found.")
    return FileResponse(path, filename="sample_template.csv")

def _session_or_404(request: Request, session_id: str) -> dict:
    session = request.app.state.batch_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return session

@router.post("/upload")
async def upload_csv(request: Request, file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")
    blob = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(blob))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {exc}")
    
    session_id = str(uuid.uuid4())
    request.app.state.batch_sessions[session_id] = {
        "filename": file.filename,
        "size": len(blob),
        "df": df,
    }
    return {"session_id": session_id}

@router.get("/validate")
def validate_csv(request: Request, session_id: str = Query(...)):
    session = _session_or_404(request, session_id)
    df = session["df"]
    missing_columns = [col for col in BATCH_REQUIRED_COLUMNS if col not in df.columns]
    
    ready = len(missing_columns) == 0
    issues = []
    if missing_columns:
        issues.append(f"Missing required columns: {', '.join(missing_columns)}")
        
    return {
        "stats": {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "file_size": session["size"],
        },
        "missing_columns": missing_columns,
        "issues": issues,
        "ready": ready,
        "preview": df.head(10).fillna("").to_dict(orient="records"),
    }

@router.post("/predict")
def batch_predict(request: Request, session_id: str = Query(...)):
    session = _session_or_404(request, session_id)
    df = session["df"].copy()
    
    # Fill missing required columns with defaults
    for col in BATCH_REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = MODEL_DEFAULTS.get(col, 0)

    start = time.perf_counter()
    
    # Fast batch prediction: use vectorized pipeline predict instead of row-by-row
    bundle = train_or_load_models(force_retrain=False)
    crop_stats = get_crop_stats()
    
    try:
        # Build feature matrix for all rows at once
        X = pd.DataFrame(df, columns=bundle.feature_columns)
        
        # Fill NaN in feature columns with defaults
        for col in bundle.feature_columns:
            if col not in X.columns:
                X[col] = MODEL_DEFAULTS.get(col, 0)
            X[col] = X[col].fillna(MODEL_DEFAULTS.get(col, 0))
        
        # Vectorized regression prediction (all rows at once)
        yields = bundle.regression_pipeline.predict(X)
        
        # Classify each row based on per-crop quantiles
        categories = []
        for i, row in df.iterrows():
            crop = str(row.get("Crop_Type", "Unknown"))
            y = float(yields[i]) if i < len(yields) else 0.0
            stats = crop_stats.get(crop, {"mean": 0.0, "p33": 0.0, "p66": 0.0})
            if y <= stats["p33"]:
                categories.append("Low")
            elif y > stats["p66"]:
                categories.append("High")
            else:
                categories.append("Medium")
        
        df["Predicted_Yield_kg_ha"] = [round(float(y), 2) for y in yields]
        df["Yield_Category"] = categories
        
    except Exception as e:
        print(f"Batch prediction error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
    
    elapsed = round(time.perf_counter() - start, 2)
    
    session["result_df"] = df
    
    # Calculate summary stats
    cat_counts = df["Yield_Category"].value_counts().to_dict()
    avg_yield = round(float(df["Predicted_Yield_kg_ha"].mean()), 2)
    
    return {
        "elapsed_sec": elapsed,
        "rows": len(df),
        "avg_yield": avg_yield,
        "category_counts": cat_counts,
        "records": df.head(5000).fillna("").to_dict(orient="records"),
        "columns": list(df.columns),
    }

@router.get("/download")
def download_batch(request: Request, session_id: str = Query(...)):
    session = _session_or_404(request, session_id)
    if "result_df" not in session:
        raise HTTPException(status_code=404, detail="No results found.")
    output = io.StringIO()
    session["result_df"].to_csv(output, index=False)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=batch_predictions.csv"},
    )
