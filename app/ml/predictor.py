from __future__ import annotations
from app.utils.translator import translate_to_id


import os
import pickle
from dataclasses import dataclass
from typing import Any, Optional, Tuple

import joblib

from app.core.config import settings

@dataclass
class MLResult:
    label: int               # 0 aman, 1 pelecehan
    confidence: float        # 0..1

_model_bundle: Optional[Any] = None  # cache global


def _load_bundle(path: str) -> Any:
    """
    Support:
    - joblib dump (.joblib / .pkl)
    - pickle (.pkl)
    """
    if not path:
        raise RuntimeError("ML_PIPELINE_PATH kosong. Set di .env")

    if not os.path.exists(path):
        raise RuntimeError(f"Model file tidak ditemukan: {path}")

    # coba joblib dulu (umum untuk sklearn)
    try:
        return joblib.load(path)
    except Exception:
        # fallback pickle
        with open(path, "rb") as f:
            return pickle.load(f)


def load_model_once() -> Any:
    global _model_bundle
    if _model_bundle is None:
        _model_bundle = _load_bundle(settings.ML_PIPELINE_PATH)
    return _model_bundle


def _extract_pipeline_and_threshold(bundle: Any) -> Tuple[Any, float]:
    """
    Bisa berupa:
    1) sklearn Pipeline langsung -> threshold default 0.5
    2) dict bundle -> {'pipeline': ..., 'threshold': 0.6, ...}
    """
    if isinstance(bundle, dict):
        pipeline = bundle.get("pipeline") or bundle.get("model") or bundle.get("clf")
        threshold = float(bundle.get("threshold", 0.5))
        if pipeline is None:
            raise RuntimeError("Bundle dict tidak punya key pipeline/model/clf.")
        return pipeline, threshold
    return bundle, 0.5


def _predict_proba_or_score(pipeline: Any, text: str) -> float:
    """
    Return confidence pelecehan (probabilitas kelas 1) kalau memungkinkan.
    Kalau tidak ada predict_proba, coba decision_function lalu sigmoid sederhana.
    """
    # sklearn proba
    if hasattr(pipeline, "predict_proba"):
        proba = pipeline.predict_proba([text])[0]
        # asumsi kelas 1 = pelecehan
        return float(proba[1]) if len(proba) > 1 else float(proba[0])

    # decision function (SVM)
    if hasattr(pipeline, "decision_function"):
        import math
        score = pipeline.decision_function([text])[0]
        # sigmoid untuk mapping ke 0..1 (approx, cukup untuk "confidence UI")
        return float(1 / (1 + math.exp(-float(score))))

    # fallback: predict saja (tanpa confidence real)
    pred = pipeline.predict([text])[0]
    return 1.0 if int(pred) == 1 else 0.0


def classify_text(text: str) -> MLResult:
    # TRANSLATE FIRST
    translated_text = translate_to_id(text)

    bundle = load_model_once()
    pipeline, _ = _extract_pipeline_and_threshold(bundle)

    pred = int(pipeline.predict([translated_text])[0])

    is_harassment = pred == 0

    conf = 1.0
    if hasattr(pipeline, "predict_proba"):
        proba = pipeline.predict_proba([translated_text])[0]
        conf = float(proba[pred])

    return MLResult(
        label=1 if is_harassment else 0,
        confidence=conf
    )

