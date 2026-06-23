"""Structured JSON → PDF via WeasyPrint + HTML Jinja2 — no LLM."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

_TEMPLATE_ROOT = Path(__file__).parent.parent / "templates"


def _template_dir(template_name: str) -> Path:
    mapping = {
        "jacks_tech": "jacks_tech",
        "classic_nontech": "classic_nontech",
    }
    folder = mapping.get(template_name, "jacks_tech")
    return _TEMPLATE_ROOT / folder


def render_pdf(data: dict[str, Any], template_name: str = "jacks_tech") -> bytes:
    """Render structured resume JSON to PDF bytes."""
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
