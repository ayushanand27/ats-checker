"""Structured JSON → LaTeX via Jinja2 — no LLM."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATE_ROOT = Path(__file__).parent.parent / "templates"

LATEX_SPECIAL = {
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    "\\": r"\textbackslash{}",
}


def escape_latex(text: str) -> str:
    """Escape LaTeX special characters in user/AI-generated content."""
    if not text:
        return ""
    # Backslash must be escaped first; other replacements add literal backslashes once.
    result = text.replace("\\", r"\textbackslash{}")
    for char, replacement in LATEX_SPECIAL.items():
        if char == "\\":
            continue
        result = result.replace(char, replacement)
    return result


def _template_dir(template_name: str) -> Path:
    mapping = {
        "jacks_tech": "jacks_tech",
        "classic_nontech": "classic_nontech",
    }
    folder = mapping.get(template_name, "jacks_tech")
    return _TEMPLATE_ROOT / folder


def render_tex(data: dict[str, Any], template_name: str = "jacks_tech") -> str:
    """Render structured resume JSON to a .tex source string."""
    env = Environment(
        loader=FileSystemLoader(str(_template_dir(template_name))),
        autoescape=select_autoescape(default=False),
    )
    env.filters["latex"] = escape_latex
    template = env.get_template("template.tex.jinja")
    return template.render(
        name=escape_latex(data.get("name", "")),
        contact=data.get("contact", {}),
        summary=escape_latex(data.get("summary", "")),
        skills=[escape_latex(s) for s in data.get("skills", [])],
        experience=data.get("experience", []),
        education=data.get("education", []),
        projects=data.get("projects", []),
        escape_latex=escape_latex,
    )
