"""Custom DOCX rendering via docxtpl (Jinja2-in-Word) — no LLM."""

from __future__ import annotations

import re
from io import BytesIO
from typing import Any

from docxtpl import DocxTemplate
from jinja2 import TemplateSyntaxError, UndefinedError


def _prepare_context(resume_json: dict[str, Any]) -> dict[str, Any]:
    """Normalize resume JSON for docxtpl — same keys as docx_renderer.py."""
    contact = resume_json.get("contact") or {}
    return {
        "name": resume_json.get("name", "") or "",
        "contact": {
            "email": contact.get("email") or "",
            "phone": contact.get("phone") or "",
            "linkedin": contact.get("linkedin") or "",
            "github": contact.get("github") or "",
        },
        "summary": resume_json.get("summary", "") or "",
        "skills": resume_json.get("skills") or [],
        "experience": resume_json.get("experience") or [],
        "education": resume_json.get("education") or [],
        "projects": resume_json.get("projects") or [],
    }


def _format_template_error(exc: Exception) -> str:
    """Build a user-facing message from a Jinja/docxtpl failure."""
    raw = str(exc).strip()
    var_match = re.search(r"'([^']+)'", raw)
    if var_match:
        var_name = var_match.group(1)
        return (
            f"Template error — unknown or missing field '{var_name}'. "
            f"Check that your .docx uses the exact placeholder names from the starter template."
        )
    if isinstance(exc, TemplateSyntaxError):
        return (
            f"Template syntax error near '{getattr(exc, 'lineno', '?')}': {raw}. "
            "Check {% for %} / {% endfor %} pairs and Jinja2 syntax."
        )
    if isinstance(exc, UndefinedError):
        return (
            f"Template references a variable that is not available: {raw}. "
            "Use only the field names from the starter template."
        )
    return f"Custom template render failed: {raw}"


def render_custom_docx(
    template_file_bytes: bytes,
    resume_json: dict[str, Any],
) -> tuple[bytes | None, str | None]:
    """
    Render uploaded .docx template with resume JSON via docxtpl.

    Returns:
        (docx_bytes, None) on success
        (None, error_message) on failure
    """
    try:
        template_io = BytesIO(template_file_bytes)
        doc = DocxTemplate(template_io)
        context = _prepare_context(resume_json)
        doc.render(context)
        out = BytesIO()
        doc.save(out)
        return out.getvalue(), None
    except (TemplateSyntaxError, UndefinedError) as exc:
        return None, _format_template_error(exc)
    except Exception as exc:
        message = str(exc).lower()
        if "jinja" in message or "template" in message or "undefined" in message:
            return None, _format_template_error(exc)
        return None, f"Custom template render failed: {exc}"
