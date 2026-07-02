"""Shared dependencies and helpers for the API layer."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Optional

LAYER1_WEIGHT_WITH_JD = 0.35
LAYER2_WEIGHT_WITH_JD = 0.65
LAYER1_WEIGHT_NO_JD = 1.0

VALID_TEMPLATES = frozenset({"jacks_tech", "classic_nontech", "custom"})
VALID_FORMATS = frozenset({"docx", "pdf", "tex"})


def layer2_enabled() -> bool:
    """False when SKIP_LAYER2=1 — for low-memory deploy (Render free tier)."""
    return os.getenv("SKIP_LAYER2", "").strip().lower() not in ("1", "true", "yes")


def compose_score(
    layer1: float,
    layer2: Optional[float],
    jd_provided: bool,
) -> float:
    if jd_provided and layer2 is not None:
        return round(
            layer1 * LAYER1_WEIGHT_WITH_JD + layer2 * LAYER2_WEIGHT_WITH_JD,
            1,
        )
    return round(layer1 * LAYER1_WEIGHT_NO_JD, 1)


def build_gaps_from_layer2(layer2: Optional[dict[str, Any]]) -> dict[str, Any]:
    if not layer2:
        return {
            "missing_required": [],
            "missing_preferred": [],
            "experience_note": None,
        }
    return {
        "missing_required": layer2.get("missing_required", []),
        "missing_preferred": layer2.get("missing_preferred", []),
        "experience_note": layer2.get("experience_note"),
    }


@lru_cache(maxsize=1)
def get_embedding_model():
    """Load sentence-transformers model once per process."""
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception as exc:
        raise RuntimeError(
            "Could not load embedding model. Ensure torch==2.6.0 and "
            f"torchvision==0.21.0 are installed. Original error: {exc}"
        ) from exc
