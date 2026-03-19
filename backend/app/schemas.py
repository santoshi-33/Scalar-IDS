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


class DetectionEntry(BaseModel):
    at: str  # ISO timestamp
    predicted_type: str
    confidence: float | None = None
    actual_type: str | None = None
    status: str | None = None  # "match" | "mismatch" | None
    protocol: str | None = None
    duration: float | None = None


class TrafficStats(BaseModel):
    total_traffic: int
    attacks_detected: int
    attack_rate: float  # 0..1
    detection_accuracy: float | None = None  # 0..1, only if actual labels available
    attack_type_distribution: dict[str, int]  # top types -> count
    timeline: list[dict[str, Any]]  # [{t: ISO minute, benign: n, attack: n}]

