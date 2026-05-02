from typing import Any

from pydantic import BaseModel, Field


class PredictionInput(BaseModel):
    features: dict[str, Any] = Field(default_factory=dict)


class PredictionOutput(BaseModel):
    selected_crop: str
    predicted_yield_kg_ha: float
    predicted_category: str
    recommended_crop: str
    recommended_crop_predicted_yield_kg_ha: float
    is_recommended_crop_better: bool
    is_typical_for_conditions: bool
    typical_mean_yield: float


class GroupedSeries(BaseModel):
    label: str
    value: float


class CategorySeries(BaseModel):
    label: str
    count: int
