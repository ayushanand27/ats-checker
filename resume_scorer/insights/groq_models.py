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
# The GROQ_MODEL override that was active when _working_model was found. If the
# override changes, the remembered model is stale and is ignored.
_working_for_override: str = ""


def model_candidates() -> list[str]:
    """Preferred model first (env override, then last known good), then fallbacks."""
    override = os.getenv("GROQ_MODEL", "").strip()
    working = _working_model if _working_for_override == override else None
    # A model that already worked goes first, so an unavailable override is not
    # retried (and failed) on every call.
    ordered = [working or "", override, *DEFAULT_MODELS]
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
        # Org/project admins can block a single model with HTTP 403; fall back,
        # but do not treat every 403 as model-unavailable.
        or "model_permission_blocked" in text
        or "decommissioned" in text
        or "does not exist or you do not have access" in text
    )


def chat_completion(client: Any, **kwargs: Any) -> Any:
    """client.chat.completions.create with model fallback on model-unavailable errors."""
    global _working_model, _working_for_override
    last: Exception | None = None
    for model in model_candidates():
        try:
            response = client.chat.completions.create(model=model, **kwargs)
            _working_model = model
            _working_for_override = os.getenv("GROQ_MODEL", "").strip()
            return response
        except Exception as exc:  # noqa: BLE001
            if _is_model_unavailable(exc):
                last = exc
                continue
            raise
    raise last if last else RuntimeError("No Groq model available")
