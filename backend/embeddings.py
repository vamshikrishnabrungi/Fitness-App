"""Local, free, offline text embeddings for semantic exercise retrieval.

Uses fastembed (ONNX, no torch). Fully optional and guarded: if fastembed isn't installed, the
model can't load, or EXERCISE_EMBEDDINGS_ENABLED is false, every function degrades to "disabled"
and retrieval falls back to keyword-only scoring with no error.
"""
from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import List, Optional, Sequence

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")


def embeddings_enabled() -> bool:
    return (os.environ.get("EXERCISE_EMBEDDINGS_ENABLED", "true") or "true").strip().lower() in {"1", "true", "yes", "on"}


@lru_cache(maxsize=1)
def _model():
    if not embeddings_enabled():
        return None
    try:
        from fastembed import TextEmbedding

        model = TextEmbedding(model_name=EMBEDDING_MODEL)
        logger.info("Loaded embedding model %s", EMBEDDING_MODEL)
        return model
    except Exception as exc:  # missing dep, download failure, etc.
        logger.warning("Embeddings disabled (model unavailable): %s", exc)
        return None


def embeddings_available() -> bool:
    return _model() is not None


def embed_texts(texts: Sequence[str]) -> Optional[List[List[float]]]:
    model = _model()
    if model is None or not texts:
        return None
    try:
        return [list(map(float, vec)) for vec in model.embed(list(texts))]
    except Exception as exc:
        logger.warning("embed_texts failed: %s", exc)
        return None


def embed_query(text: str) -> Optional[List[float]]:
    out = embed_texts([text])
    return out[0] if out else None


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def embedding_model_name() -> str:
    return EMBEDDING_MODEL
