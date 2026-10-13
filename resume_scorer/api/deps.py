"""Shared dependencies and helpers for the API layer."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Optional

# Legacy two-layer weights (used when the contextual model is unavailable)
LAYER1_WEIGHT_WITH_JD = 0.35
LAYER2_WEIGHT_WITH_JD = 0.65
LAYER1_WEIGHT_NO_JD = 1.0

# Three-layer weights (v2). On the public evaluation set (docs/eval_results_v2.json)
# v2 raised ROC-AUC from 0.54 to 0.61, within-JD AUC from 0.63 to 0.70 and
# ranking MRR from 0.44 to 0.49, while keeping the explainable skill layer large.
WEIGHTS_FULL = {"structure": 0.20, "skills": 0.40, "context": 0.40}
WEIGHTS_NO_SKILLS = {"structure": 0.40, "context": 0.60}

VALID_TEMPLATES = frozenset({"jacks_tech", "classic_nontech", "custom"})
VALID_FORMATS = frozenset({"docx", "pdf", "tex"})


def layer2_enabled() -> bool:
    """False when SKIP_LAYER2=1 — for low-memory deploy (Render free tier)."""
    return os.getenv("SKIP_LAYER2", "").strip().lower() not in ("1", "true", "yes")


def compose_score(
    layer1: float,
    layer2: Optional[float],
    jd_provided: bool,
    context: Optional[float] = None,
) -> float:
    return compose_score_detailed(layer1, layer2, jd_provided, context)["score"]


def compose_score_detailed(
    layer1: float,
    layer2: Optional[float],
    jd_provided: bool,
    context: Optional[float] = None,
) -> dict[str, Any]:
    """Combine layer scores and explain which formula was used."""
    if not jd_provided:
        return {"score": round(layer1, 1), "mode": "structure_only",
                "weights": {"structure": 1.0}, "components": {"structure": layer1}}
    if layer2 is not None and context is not None:
        w = WEIGHTS_FULL
        score = w["structure"] * layer1 + w["skills"] * layer2 + w["context"] * context
        return {"score": round(score, 1), "mode": "full",
                "weights": dict(w), "components": {"structure": layer1, "skills": layer2, "context": context}}
    if layer2 is not None:
        score = LAYER1_WEIGHT_WITH_JD * layer1 + LAYER2_WEIGHT_WITH_JD * layer2
        return {"score": round(score, 1), "mode": "structure_skills",
                "weights": {"structure": LAYER1_WEIGHT_WITH_JD, "skills": LAYER2_WEIGHT_WITH_JD},
                "components": {"structure": layer1, "skills": layer2}}
    if context is not None:
        w = WEIGHTS_NO_SKILLS
        score = w["structure"] * layer1 + w["context"] * context
        return {"score": round(score, 1), "mode": "structure_context",
                "weights": dict(w), "components": {"structure": layer1, "context": context}}
    # JD given but neither skill nor context match available: be explicit that
    # this is NOT a match score (earlier versions silently showed Layer 1 here).
    return {"score": round(layer1, 1), "mode": "structure_only_jd_unmatched",
            "weights": {"structure": 1.0}, "components": {"structure": layer1}}


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
    """Load the skill-matching sentence-transformers model once per process."""
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception as exc:
        raise RuntimeError(
            "Could not load embedding model all-MiniLM-L6-v2. Check that torch and "
            f"sentence-transformers are installed and the model can be downloaded once. Original error: {exc}"
        ) from exc


@lru_cache(maxsize=1)
def get_context_model():
    """Load the contextual (whole-document) model once per process."""
    from scoring.contextual_match import CONTEXT_MODEL_NAME
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(CONTEXT_MODEL_NAME)
    except Exception as exc:
        raise RuntimeError(
            f"Could not load contextual model {CONTEXT_MODEL_NAME}. Original error: {exc}"
        ) from exc
