from __future__ import annotations

import os
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import json

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware

from .model import load_model
from .predict import predict_batch, predict_one
from .schemas import (
    DetectionEntry,
    HealthResponse,
    PredictCsvResponse,
    PredictRequest,
    PredictResponse,
    PredictionRow,
    TrafficStats,
)


def _allowed_origins() -> list[str]:
    raw = os.environ.get("ALLOWED_ORIGINS", "http://localhost:4200,http://localhost:4201")
    return [o.strip() for o in raw.split(",") if o.strip()]


app = FastAPI(title="IDS API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    # Helpful for local dev when Angular runs on random ports.
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_DETECTIONS: list[DetectionEntry] = []
_DETECTIONS_MAX = 300


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_attack(label: str) -> bool:
    l = (label or "").strip().lower()
    return l not in {"normal", "benign", "benigntraffic", "benign_traffic", "0"}


def _push_detection(entry: DetectionEntry) -> None:
    _DETECTIONS.insert(0, entry)
    if len(_DETECTIONS) > _DETECTIONS_MAX:
        del _DETECTIONS[_DETECTIONS_MAX:]


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

    protocol = None
    duration = None
    for k in ("protocol", "protocol_type", "proto"):
        if k in req.features and req.features[k] is not None:
            protocol = str(req.features[k])
            break
    for k in ("duration", "dur", "flow_duration"):
        if k in req.features and req.features[k] is not None:
            try:
                duration = float(req.features[k])
            except Exception:
                duration = None
            break

    _push_detection(
        DetectionEntry(
            at=_now_iso(),
            predicted_type=label,
            confidence=prob,
            actual_type=None,
            status=None,
            protocol=protocol,
            duration=duration,
        )
    )
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

    # Optional: if the uploaded CSV includes a ground-truth label column, we can compute match/mismatch.
    actual_col = None
    for c in ("label", "Label", "class", "Class", "attack_cat", "category"):
        if c in df.columns:
            actual_col = c
            break

    actuals: list[str] | None = None
    X = df
    if actual_col is not None:
        actuals = df[actual_col].astype(str).tolist()
        X = df.drop(columns=[actual_col])

    try:
        preds = predict_batch(state.model, X)
    except Exception as e:  # noqa: BLE001
        # Common case: uploaded CSV columns don't match the model's expected columns.
        expected = None
        try:
            preprocess = state.model.named_steps.get("preprocess") if hasattr(state.model, "named_steps") else None
            if preprocess is not None and hasattr(preprocess, "feature_names_in_"):
                expected = list(preprocess.feature_names_in_)
        except Exception:
            expected = None
        detail = f"Prediction failed: {e}"
        if expected is not None:
            detail += f" | expected columns: {expected}"
        raise HTTPException(status_code=400, detail=detail) from e
    rows = [PredictionRow(label=label, probability=prob) for label, prob in preds]
    summary = dict(Counter(r.label for r in rows))

    # Push detections for dashboard (best-effort for protocol/duration if those columns exist).
    proto_col = next((c for c in ("protocol", "protocol_type", "proto") if c in X.columns), None)
    dur_col = next((c for c in ("duration", "dur", "flow_duration") if c in X.columns), None)

    for i, (label, prob) in enumerate(preds):
        actual = actuals[i] if actuals is not None and i < len(actuals) else None
        status = None
        if actual is not None:
            status = "match" if str(actual) == str(label) else "mismatch"
        protocol = str(X.iloc[i][proto_col]) if proto_col is not None else None
        duration = None
        if dur_col is not None:
            try:
                duration = float(X.iloc[i][dur_col])
            except Exception:
                duration = None
        _push_detection(
            DetectionEntry(
                at=_now_iso(),
                predicted_type=str(label),
                confidence=prob,
                actual_type=str(actual) if actual is not None else None,
                status=status,
                protocol=protocol,
                duration=duration,
            )
        )

    return PredictCsvResponse(rows=rows, summary=summary)


@app.get("/detections", response_model=list[DetectionEntry])
def detections(limit: int = Query(25, ge=1, le=200)) -> list[DetectionEntry]:
    return _DETECTIONS[:limit]


@app.get("/stats", response_model=TrafficStats)
def stats(minutes: int = Query(30, ge=1, le=24 * 60)) -> TrafficStats:
    total = len(_DETECTIONS)
    attacks = sum(1 for d in _DETECTIONS if _is_attack(d.predicted_type))
    attack_rate = (attacks / total) if total else 0.0

    # Accuracy only when actual labels exist.
    with_actual = [d for d in _DETECTIONS if d.actual_type is not None and d.status is not None]
    if with_actual:
        correct = sum(1 for d in with_actual if d.status == "match")
        detection_accuracy = correct / len(with_actual)
    else:
        detection_accuracy = None

    dist = Counter(d.predicted_type for d in _DETECTIONS)
    top10 = dict(dist.most_common(10))

    # Timeline by minute (UTC)
    now = datetime.now(timezone.utc)
    buckets: dict[str, dict[str, int]] = {}
    for d in _DETECTIONS:
        try:
            dt = datetime.fromisoformat(d.at.replace("Z", "+00:00"))
        except Exception:
            continue
        age_min = (now - dt).total_seconds() / 60.0
        if age_min > minutes:
            continue
        key = dt.replace(second=0, microsecond=0).isoformat()
        b = buckets.setdefault(key, {"t": key, "benign": 0, "attack": 0})
        if _is_attack(d.predicted_type):
            b["attack"] += 1
        else:
            b["benign"] += 1

    timeline = [buckets[k] for k in sorted(buckets.keys())][-60:]

    return TrafficStats(
        total_traffic=total,
        attacks_detected=attacks,
        attack_rate=float(attack_rate),
        detection_accuracy=(float(detection_accuracy) if detection_accuracy is not None else None),
        attack_type_distribution=top10,
        timeline=timeline,
    )


@app.post("/simulate", response_model=list[DetectionEntry])
def simulate(n: int = Query(10, ge=1, le=200)) -> list[DetectionEntry]:
    """
    Creates fake traffic/detection rows for UI demos (keeps UI dynamic).
    """
    attack_types = [
        "DDoS-ICMP_Flood",
        "DDoS-SynonymousIP_Flood",
        "DoS-UDP_Flood",
        "Recon-HostDiscovery",
        "DDoS-RSTFINFlood",
    ]
    benign_types = ["BenignTraffic", "Normal"]
    protos = ["TCP", "UDP", "ICMP", "N/A"]

    created: list[DetectionEntry] = []
    for _ in range(n):
        is_attack = random.random() < 0.32
        label = random.choice(attack_types if is_attack else benign_types)
        conf = round(random.uniform(0.78, 1.0), 4)
        protocol = random.choice(protos if is_attack else ["TCP", "UDP"])
        duration = round(random.uniform(1.0, 240.0), 2)
        entry = DetectionEntry(
            at=_now_iso(),
            predicted_type=label,
            confidence=conf,
            actual_type=label,
            status="match",
            protocol=protocol,
            duration=duration,
        )
        _push_detection(entry)
        created.append(entry)

    return created


@app.get("/model-info")
def model_info() -> dict:
    """
    Lightweight introspection for viva demos:
    - expected input columns (if available)
    - class labels
    - top logistic regression coefficients (if pipeline contains LogisticRegression)
    """
    state = load_model()
    if state.model is None:
        raise HTTPException(status_code=503, detail=f"Model not available: {state.load_error}")

    model = state.model
    classes_raw = getattr(model, "classes_", None)
    try:
        if classes_raw is None:
            classes = None
        else:
            classes = [str(x) for x in list(classes_raw)]
    except Exception:
        classes = None

    info: dict = {
        "model_path": str(state.model_path),
        "classes": classes,
        "expected_columns": None,
        "top_coefficients": None,
    }

    # Try to infer expected raw columns from the ColumnTransformer.
    try:
        preprocess = model.named_steps.get("preprocess") if hasattr(model, "named_steps") else None
        if preprocess is not None and hasattr(preprocess, "feature_names_in_"):
            info["expected_columns"] = list(preprocess.feature_names_in_)
    except Exception:
        pass

    # If this is a sklearn Pipeline with LogisticRegression, expose top coefficients.
    try:
        if hasattr(model, "named_steps") and "model" in model.named_steps:
            clf = model.named_steps["model"]
            pre = model.named_steps.get("preprocess")
            if clf.__class__.__name__ == "LogisticRegression" and hasattr(clf, "coef_") and pre is not None:
                # Get transformed feature names (after one-hot).
                feat_names = None
                if hasattr(pre, "get_feature_names_out"):
                    try:
                        feat_names = pre.get_feature_names_out()
                    except Exception:
                        feat_names = None

                coef = clf.coef_
                # For binary: shape (1, n_features). For multi-class: (n_classes, n_features)
                rows = []
                if coef.ndim == 2:
                    for class_i in range(coef.shape[0]):
                        c = coef[class_i]
                        idx = list(range(len(c)))
                        idx.sort(key=lambda i: abs(float(c[i])), reverse=True)
                        top = idx[:15]
                        rows.append(
                            {
                                "class": str(getattr(clf, "classes_", [class_i])[class_i]),
                                "top": [
                                    {
                                        "feature": (str(feat_names[i]) if feat_names is not None else str(i)),
                                        "coefficient": float(c[i]),
                                    }
                                    for i in top
                                ],
                            }
                        )
                info["top_coefficients"] = rows
    except Exception:
        # Don't fail the whole endpoint if introspection fails.
        pass

    return info


@app.get("/metrics")
def metrics() -> dict:
    """
    Returns last training metrics if `backend/app/artifacts/metrics.json` exists.
    """
    here = Path(__file__).resolve()
    metrics_path = here.parent / "artifacts" / "metrics.json"
    if not metrics_path.exists():
        raise HTTPException(status_code=404, detail="metrics.json not found. Run ml/train.py to generate it.")
    try:
        return json.loads(metrics_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read metrics.json: {e}") from e

