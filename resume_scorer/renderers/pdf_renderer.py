"""Structured JSON → PDF via WeasyPrint + HTML Jinja2 — no LLM."""

from __future__ import annotations

import sys
from io import BytesIO
from pathlib import Path
from typing import Any, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATE_ROOT = Path(__file__).parent.parent / "templates"

_WEASYPRINT_OK: Optional[bool] = None
_WEASYPRINT_ERROR: Optional[str] = None

_WINDOWS_PDF_HINT = (
    "PDF export needs WeasyPrint's Pango/GTK libraries, which are not bundled with pip on Windows. "
    "Use DOCX or TeX locally, or run the app in Docker (Linux) where system deps are pre-installed."
)


def _probe_weasyprint() -> bool:
    """Lazy-load WeasyPrint once; cache availability for this process."""
    global _WEASYPRINT_OK, _WEASYPRINT_ERROR
    if _WEASYPRINT_OK is not None:
        return _WEASYPRINT_OK
    if sys.platform == "win32":
        # GTK/Pango libs are not available via pip on Windows — skip import attempt.
        _WEASYPRINT_OK = False
        _WEASYPRINT_ERROR = _WINDOWS_PDF_HINT
        return False
    try:
        from weasyprint import HTML  # noqa: F401
        _WEASYPRINT_OK = True
        _WEASYPRINT_ERROR = None
    except OSError as exc:
        _WEASYPRINT_OK = False
        _WEASYPRINT_ERROR = f"{_WINDOWS_PDF_HINT} ({exc})"
    except Exception as exc:
        _WEASYPRINT_OK = False
        _WEASYPRINT_ERROR = f"PDF export unavailable: {exc}"
    return _WEASYPRINT_OK


def pdf_export_available() -> tuple[bool, Optional[str]]:
    """Return (available, error_message_if_unavailable)."""
    if _probe_weasyprint():
        return True, None
    return False, _WEASYPRINT_ERROR


def _template_dir(template_name: str) -> Path:
    mapping = {
        "jacks_tech": "jacks_tech",
        "classic_nontech": "classic_nontech",
    }
    folder = mapping.get(template_name, "jacks_tech")
    return _TEMPLATE_ROOT / folder


def render_pdf(data: dict[str, Any], template_name: str = "jacks_tech") -> bytes:
    """Render structured resume JSON to PDF bytes."""
    if not _probe_weasyprint():
        raise RuntimeError(_WEASYPRINT_ERROR or _WINDOWS_PDF_HINT)

    from weasyprint import HTML

    env = Environment(
        loader=FileSystemLoader(str(_template_dir(template_name))),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("template.html.jinja")
    html_str = template.render(
        name=data.get("name", ""),
        contact=data.get("contact", {}),
        summary=data.get("summary", ""),
        skills=data.get("skills", []),
        experience=data.get("experience", []),
        education=data.get("education", []),
        projects=data.get("projects", []),
        template_name=template_name,
    )
    pdf_buffer = BytesIO()
    HTML(string=html_str).write_pdf(pdf_buffer)
    return pdf_buffer.getvalue()
