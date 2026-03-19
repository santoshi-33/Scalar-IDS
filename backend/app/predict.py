from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _predict_proba(model: Any, X: pd.DataFrame) -> np.ndarray | None:
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)
        if isinstance(proba, list):
            proba = np.asarray(proba)
        return proba
    return None


def predict_one(model: Any, features: dict[str, Any]) -> tuple[str, float | None]:
    X = pd.DataFrame([features])
    proba = _predict_proba(model, X)
    pred = model.predict(X)
    label = str(pred[0])

    if proba is None:
        return label, None

    # Map to predicted class probability when available.
    try:
        classes = getattr(model, "classes_", None)
        if classes is None:
            return label, float(np.max(proba[0]))
        idx = int(np.where(classes == pred[0])[0][0])
        return label, float(proba[0][idx])
    except Exception:  # noqa: BLE001
        return label, float(np.max(proba[0]))


def predict_batch(model: Any, df: pd.DataFrame) -> list[tuple[str, float | None]]:
    proba = _predict_proba(model, df)
    pred = model.predict(df)

    results: list[tuple[str, float | None]] = []
    if proba is None:
        for p in pred:
            results.append((str(p), None))
        return results

    classes = getattr(model, "classes_", None)
    for i, p in enumerate(pred):
        label = str(p)
        if classes is None:
            results.append((label, float(np.max(proba[i]))))
            continue
        try:
            idx = int(np.where(classes == p)[0][0])
            results.append((label, float(proba[i][idx])))
        except Exception:  # noqa: BLE001
            results.append((label, float(np.max(proba[i]))))
    return results

