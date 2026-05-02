from fastapi import APIRouter, HTTPException

from app.schemas import PredictionInput, PredictionOutput
from app.services.data_service import get_dataframe, get_feature_columns
from app.services.model_service import predict_single

router = APIRouter(prefix="/predict", tags=["predict"])


@router.post("/both", response_model=PredictionOutput)
def predict_both(payload: PredictionInput):
    df = get_dataframe()
    feature_cols = get_feature_columns(df)
    if not feature_cols:
        raise HTTPException(status_code=500, detail="No valid model features configured.")
    missing = [c for c in feature_cols if c not in payload.features]
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Missing required features. First missing columns: {missing[:8]}",
        )
    return predict_single(payload.features)
