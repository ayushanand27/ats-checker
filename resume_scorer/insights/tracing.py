"""Optional Langfuse LLM observability (SDK v2).

Fully non-breaking: if LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY are unset,
the langfuse package is missing, or any tracing call fails, everything
degrades to a no-op so the app keeps working.

Usage:
    from insights.tracing import start_generation

    gen = start_generation(
        name="resume_rewrite",
        model=GROQ_MODEL,
        input=messages,
        metadata={"temperature": 0.3},
        user_id="42",
        session_id="rewrite-42",
        tags=["rewrite"],
    )
    try:
        response = client.chat.completions.create(...)
        gen.end(output=content, usage=usage_from_response(response))
    except Exception as exc:
        gen.error(exc)
        raise
"""

from __future__ import annotations

import os
from typing import Any, Optional

_client: Any = None
_checked = False


def _get_client() -> Any:
    global _client, _checked
    if _checked:
        return _client
    _checked = True
    if not (os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")):
        _client = None
        return None
    # Langfuse v2 uses LANGFUSE_HOST; dashboard/docs often show LANGFUSE_BASE_URL
    if not os.getenv("LANGFUSE_HOST") and os.getenv("LANGFUSE_BASE_URL"):
        os.environ["LANGFUSE_HOST"] = os.environ["LANGFUSE_BASE_URL"]
    try:
        from langfuse import Langfuse

        _client = Langfuse()
    except Exception:
        _client = None
    return _client


def langfuse_enabled() -> bool:
    return _get_client() is not None


def usage_from_response(response: Any) -> Optional[dict[str, Any]]:
    """Extract token usage from a Groq/OpenAI-style response."""
    try:
        u = response.usage
        return {
            "input": getattr(u, "prompt_tokens", None),
            "output": getattr(u, "completion_tokens", None),
            "total": getattr(u, "total_tokens", None),
            "unit": "TOKENS",
        }
    except Exception:
        return None


class _NoopGeneration:
    def end(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
        pass

    def error(self, *args: Any, **kwargs: Any) -> None:
        pass


class _LiveGeneration:
    def __init__(self, client: Any, trace: Any, generation: Any) -> None:
        self._client = client
        self._trace = trace
        self._gen = generation

    def end(self, output: Any = None, usage: Optional[dict[str, Any]] = None) -> None:
        try:
            self._gen.end(output=output, usage=usage)
            self._trace.update(output=output)
            self._client.flush()
        except Exception:
            pass

    def error(self, exc: BaseException) -> None:
        try:
            self._gen.end(level="ERROR", status_message=str(exc))
            self._trace.update(output={"error": str(exc)})
            self._client.flush()
        except Exception:
            pass


def start_generation(
    name: str,
    model: str,
    input: Any = None,
    metadata: Optional[dict[str, Any]] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> Any:
    """Begin a Langfuse trace + generation. Returns a no-op handle if disabled."""
    client = _get_client()
    if client is None:
        return _NoopGeneration()
    try:
        trace = client.trace(
            name=name,
            user_id=user_id,
            session_id=session_id,
            input=input,
            tags=tags or [],
        )
        generation = trace.generation(
            name=name,
            model=model,
            input=input,
            model_parameters=metadata or {},
        )
        return _LiveGeneration(client, trace, generation)
    except Exception:
        return _NoopGeneration()
