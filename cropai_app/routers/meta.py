from fastapi import APIRouter

from core.data_service import get_dataframe, get_metadata

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("/form")
def form_metadata():
    df = get_dataframe()
    metadata = get_metadata(df)
    metadata["model_metrics"] = {"info": "Models load/train on first prediction request."}
    return metadata
