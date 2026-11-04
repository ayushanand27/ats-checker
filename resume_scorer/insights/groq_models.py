"""Groq model selection with automatic fallback.

Groq retires and renames models, and an account may not have access to every
model. Instead of hard-coding one id, we try a short list and remember the first
that works. Override the preferred model with the GROQ_MODEL env var.
"""

from __future__ import annotations

import os
from typing import Any

DEFAULT_MODELS = (
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "llama-3.1-8b-instant",
)

_working_model: str | None = None


def model_candidates() -> list[str]:
    """Preferred model first (env override, then last known good), then fallbacks."""
    ordered = [os.getenv("GROQ_MODEL", "").strip(), _working_model or "", *DEFAULT_MODELS]
    seen: list[str] = []
    for name in ordered:
        if name and name not in seen:
            seen.append(name)
    return seen


def preferred_model() -> str:
    return model_candidates()[0]


def _is_model_unavailable(exc: Exception) -> bool:
    text = str(exc).lower()
    return (
        getattr(exc, "status_code", None) == 404
        or "model_not_found" in text
        or "decommissioned" in text
        or "does not exist or you do not have access" in text
    )


def chat_completion(client: Any, **kwargs: Any) -> Any:
    """client.chat.completions.create with model fallback on model-unavailable errors."""
    global _working_model
    last: Exception | None = None
    for model in model_candidates():
        try:
            response = client.chat.completions.create(model=model, **kwargs)
            _working_model = model
            return response
        except Exception as exc:  # noqa: BLE001
            if _is_model_unavailable(exc):
                last = exc
                continue
            raise
    raise last if last else RuntimeError("No Groq model available")
