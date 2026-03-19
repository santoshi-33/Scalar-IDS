from __future__ import annotations

import os
from collections import Counter

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .model import load_model
from .predict import predict_batch, predict_one
from .schemas import (
    HealthResponse,
    PredictCsvResponse,
    PredictRequest,
    PredictResponse,
    PredictionRow,
)


def _allowed_origins() -> list[str]:
    raw = os.environ.get("ALLOWED_ORIGINS", "http://localhost:4200,http://localhost:4201")
    return [o.strip() for o in raw.split(",") if o.strip()]


app = FastAPI(title="IDS API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    state = load_model()
    return HealthResponse(ok=True, model_loaded=state.model is not None, detail=state.load_error)


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest) -> PredictResponse:
    state = load_model()
    if state.model is None:
        raise HTTPException(status_code=503, detail=f"Model not available: {state.load_error}")

    label, prob = predict_one(state.model, req.features)
    return PredictResponse(prediction=PredictionRow(label=label, probability=prob))


@app.post("/predict-csv", response_model=PredictCsvResponse)
async def predict_csv(file: UploadFile = File(...)) -> PredictCsvResponse:
    state = load_model()
    if state.model is None:
        raise HTTPException(status_code=503, detail=f"Model not available: {state.load_error}")

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file")

    content = await file.read()
    try:
        df = pd.read_csv(pd.io.common.BytesIO(content))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {e}") from e

    if df.empty:
        raise HTTPException(status_code=400, detail="CSV is empty")

    preds = predict_batch(state.model, df)
    rows = [PredictionRow(label=label, probability=prob) for label, prob in preds]
    summary = dict(Counter(r.label for r in rows))
    return PredictCsvResponse(rows=rows, summary=summary)

