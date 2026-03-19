from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib


@dataclass(frozen=True)
class ModelState:
    model: Any | None
    model_path: Path
    load_error: str | None


def _default_model_path() -> Path:
    here = Path(__file__).resolve()
    return here.parent / "artifacts" / "ids_model.joblib"


def load_model() -> ModelState:
    model_path = Path(os.environ.get("MODEL_PATH", str(_default_model_path()))).expanduser()
    try:
        if not model_path.exists():
            return ModelState(model=None, model_path=model_path, load_error="Model artifact not found")
        model = joblib.load(model_path)
        return ModelState(model=model, model_path=model_path, load_error=None)
    except Exception as e:  # noqa: BLE001
        return ModelState(model=None, model_path=model_path, load_error=f"Failed to load model: {e}")

