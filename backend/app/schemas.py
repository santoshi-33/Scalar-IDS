from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    ok: bool = True
    model_loaded: bool = False
    detail: str | None = None


class PredictRequest(BaseModel):
    features: dict[str, Any] = Field(
        ...,
        description="Feature name -> value. Must match the model's expected columns."
    )


class PredictionRow(BaseModel):
    label: str
    probability: float | None = None


class PredictResponse(BaseModel):
    prediction: PredictionRow


class PredictCsvResponse(BaseModel):
    rows: list[PredictionRow]
    summary: dict[str, int]

