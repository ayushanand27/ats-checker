"""Layer 3: contextual (whole-document) match — local BGE-small embeddings.

Skill matching only sees skills that are in the taxonomy. This layer compares
the *whole* resume with the *whole* job description, so it also credits
paraphrases ("built statistical models" ~ "machine learning") and domain fit.

* Model: ``BAAI/bge-small-en-v1.5`` (33M parameters, ~130 MB, runs on CPU).
* The resume is split into overlapping ~180-word chunks and the chunk
  embeddings are mean-pooled, so long resumes are read in full instead of being
  truncated at the model's 512-token limit.
* Raw cosine similarity is mapped to 0–100 with fixed calibration points taken
  from the public evaluation set (5th percentile ≈ 0.60 → 0, 95th ≈ 0.80 → 100).

On 1,759 labelled resume–JD pairs this signal reached ROC-AUC 0.62 (within-JD
0.72), the strongest single signal we measured.
"""

from __future__ import annotations

import os
from typing import Any, Optional

import numpy as np

CONTEXT_MODEL_NAME = os.getenv("CONTEXT_MODEL", "BAAI/bge-small-en-v1.5")
COS_LOW = 0.60
COS_HIGH = 0.80
CHUNK_WORDS = 180
CHUNK_STEP = 150


def context_enabled() -> bool:
    """False when SKIP_CONTEXT=1 (low-memory hosts)."""
    return os.getenv("SKIP_CONTEXT", "").strip().lower() not in ("1", "true", "yes")


def chunk_words(text: str, size: int = CHUNK_WORDS, step: int = CHUNK_STEP) -> list[str]:
    words = (text or "").split()
    if not words:
        return []
    if len(words) <= size:
        return [" ".join(words)]
    return [" ".join(words[i:i + size]) for i in range(0, len(words) - size + step, step)]


def _unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n else v


def calibrate(cosine: float) -> float:
    return round(float(np.clip((cosine - COS_LOW) / (COS_HIGH - COS_LOW), 0.0, 1.0)) * 100, 1)


def score_contextual_match(resume_text: str, jd_text: str, model: Any) -> Optional[dict[str, Any]]:
    """Whole-document similarity between resume and JD, 0–100."""
    chunks = chunk_words(resume_text)
    jd = (jd_text or "").strip()
    if not chunks or not jd:
        return None
    emb = np.asarray(model.encode(chunks + [jd], normalize_embeddings=True), dtype=float)
    resume_vec = _unit(emb[:-1].mean(axis=0))
    jd_vec = _unit(emb[-1])
    cosine = float(resume_vec @ jd_vec)
    chunk_sims = emb[:-1] @ jd_vec
    best = int(np.argmax(chunk_sims))
    score = calibrate(cosine)
    if score >= 70:
        verdict = "Strong overall fit — the resume reads like this role"
    elif score >= 45:
        verdict = "Moderate fit — related background, but the resume's focus differs from the JD"
    else:
        verdict = "Weak fit — the resume's content is mostly about other work than this JD"
    return {
        "score": score,
        "cosine": round(cosine, 3),
        "chunks": len(chunks),
        "best_chunk_preview": chunks[best][:220] + ("…" if len(chunks[best]) > 220 else ""),
        "verdict": verdict,
        "model": CONTEXT_MODEL_NAME,
    }
