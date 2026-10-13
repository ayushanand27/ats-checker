"""Shared fixtures. Unit tests use a tiny stub embedding model so they run in
seconds, offline, without downloading any model weights."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FIXTURES = ROOT / "api" / "test_fixtures"


class StubModel:
    """Deterministic fake encoder.

    Every string gets a pseudo-random unit vector (unrelated strings are nearly
    orthogonal). Strings listed in ``same`` share a vector, so tests can force
    a high cosine similarity between two different skill names.
    """

    def __init__(self, same: dict[str, str] | None = None, dim: int = 64):
        self.same = {k.lower(): v.lower() for k, v in (same or {}).items()}
        self.dim = dim

    def _vec(self, text: str) -> np.ndarray:
        key = self.same.get(text.lower(), text.lower())
        seed = int(hashlib.md5(key.encode()).hexdigest()[:8], 16)
        v = np.random.default_rng(seed).normal(size=self.dim)
        return v / np.linalg.norm(v)

    def encode(self, texts, convert_to_numpy=True, normalize_embeddings=False, **_):
        return np.stack([self._vec(t) for t in texts])


@pytest.fixture
def stub_model():
    return StubModel


@pytest.fixture
def ta_resume_text() -> str:
    return (FIXTURES / "resume_ayush_ta.txt").read_text(encoding="utf-8")


@pytest.fixture
def ta_jd_text() -> str:
    return (FIXTURES / "jd_talent_acquisition.txt").read_text(encoding="utf-8")
