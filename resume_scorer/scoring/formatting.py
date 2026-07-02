"""ATS formatting compatibility checks — industry-standard layout rules."""

from __future__ import annotations

import re
from typing import Any, Optional

BULLET_RE = re.compile(r"^[\s]*(?:[•\-\*●▪▸►]|\d+[.)])\s+")

# Standard ATS section headers (lowercase)
STANDARD_HEADERS = {
    "experience", "experiences", "work experience", "professional experience",
    "employment history", "career history",
    "education", "educations", "academic background", "qualifications",
    "skills", "skill", "technical skills", "core competencies", "technologies",
    "tools and technologies", "technical proficiencies", "competencies",
    "areas of expertise",
    "projects", "personal projects", "key projects",
    "summary", "professional summary", "profile", "objective", "about me",
    "certifications", "certificates", "achievements", "awards",
    "contact", "references",
}

DATE_SLASH = re.compile(r"\d{1,2}/\d{4}", re.I)
DATE_MONTH = re.compile(
    r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|"
    r"january|february|march|april|june|july|august|september|october|november|december)"
    r"\s*,?\s*\d{4}",
    re.I,
)
DATE_YEAR = re.compile(r"\b(19|20)\d{2}\s*[-–—]\s*(?:\((19|20)\d{2}\)|present|current|now|\d{4})", re.I)
NONSTANDARD_PRESENT = re.compile(r"\b(?:current|ongoing|till date|till now)\b", re.I)

# A line only counts as a *section header* candidate when it carries a strong
# header signal: ALL-CAPS (e.g. "WORK HISTORY") or a trailing colon
# (e.g. "Employment:"). This avoids flagging names, institutions, and
# PDF-wrapped bullet fragments that happen to be Title-Case.
HEADER_LIKE = re.compile(r"^[A-Z][A-Za-z\s&]{2,40}$")
ALL_CAPS_HEADER = re.compile(r"^[A-Z][A-Z\s&/]{2,40}$")
CONTACT_HINT_RE = re.compile(r"[@0-9]|https?://|www\.|linkedin|github", re.I)
INSTITUTION_HINT_RE = re.compile(
    r"\b(?:university|college|institute|institution|school|academy|polytechnic)\b",
    re.I,
)


def _fmt_check(name: str, passed: bool, reason: str, weight: float = 0) -> dict[str, Any]:
    return {
        "name": name,
        "passed": passed,
        "reason": reason,
        "weight": weight,
        "score": weight if passed else 0.0,
    }


def check_formatting(
    resume: dict[str, Any],
    parse_flags: Optional[dict[str, Any]] = None,
) -> list[dict[str, Any]]:
    """Return ATS formatting checks (informational; included in Layer 1 checks)."""
    raw = resume.get("raw_text", "") or ""
    flags = parse_flags or resume.get("parse_flags") or {}
    checks: list[dict[str, Any]] = []

    multi_col = flags.get("multi_column_layout", False)
    checks.append(_fmt_check(
        "Single-column layout",
        not multi_col,
        "Multi-column PDF detected — many ATS parsers scramble sidebar content"
        if multi_col
        else "No multi-column layout detected",
        10,
    ))

    has_tables = flags.get("docx_tables", False)
    checks.append(_fmt_check(
        "No table-based layout",
        not has_tables,
        "DOCX contains tables — some ATS systems (Taleo, Workday) parse table cells unreliably"
        if has_tables
        else "No table structures detected in DOCX",
        8,
    ))

    # Non-standard section headers.
    # Cross-reference the structurer's parsed output so we never flag the
    # candidate's name, education institutions, or wrapped bullet text as
    # "headers". A real section header carries a strong signal: it is ALL-CAPS
    # or ends with a colon, and sits on its own line (blank line before/after).
    name = (resume.get("name") or "").strip().lower()
    edu_institutions = {
        (entry.get("institution") or entry.get("school") or "").strip().lower()
        for entry in (resume.get("education") or [])
        if isinstance(entry, dict)
    }
    edu_institutions.discard("")

    lines = raw.splitlines()

    def _is_blank(idx: int) -> bool:
        return idx < 0 or idx >= len(lines) or not lines[idx].strip()

    custom_headers: list[str] = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or len(stripped) > 45 or BULLET_RE.match(stripped):
            continue

        strong_header = bool(ALL_CAPS_HEADER.match(stripped)) or stripped.endswith(":")
        if not strong_header or not HEADER_LIKE.match(stripped.rstrip(":")):
            continue

        lower = stripped.lower().rstrip(":")

        # Skip anything the structurer already identified as non-header content.
        if lower == name or lower in edu_institutions:
            continue
        if CONTACT_HINT_RE.search(stripped) or INSTITUTION_HINT_RE.search(stripped):
            continue

        # Real headers are visually isolated; require a blank line on at least
        # one side so mid-paragraph or wrapped lines aren't mistaken for headers.
        if not (_is_blank(i - 1) or _is_blank(i + 1)):
            continue

        if lower not in STANDARD_HEADERS and not any(
            lower.startswith(h) for h in STANDARD_HEADERS
        ):
            custom_headers.append(stripped)
    custom_headers = list(dict.fromkeys(custom_headers))[:3]
    checks.append(_fmt_check(
        "Standard section headers",
        len(custom_headers) == 0,
        f"Non-standard headers found: {', '.join(custom_headers)} — use Experience, Education, Skills"
        if custom_headers
        else "Section headers follow ATS-recognized naming",
        10,
    ))

    # Date format consistency
    has_slash = bool(DATE_SLASH.search(raw))
    has_month = bool(DATE_MONTH.search(raw))
    has_year_only = bool(DATE_YEAR.search(raw))
    fmt_count = sum([has_slash, has_month, has_year_only])
    dates_ok = fmt_count <= 1 or (fmt_count == 2 and not has_slash)
    checks.append(_fmt_check(
        "Consistent date formats",
        dates_ok,
        "Mixed date formats detected — pick one style (e.g. Mar 2024 – Present) throughout"
        if not dates_ok
        else "Date formatting appears consistent",
        7,
    ))

    # Present vs Current
    uses_current = bool(NONSTANDARD_PRESENT.search(raw))
    checks.append(_fmt_check(
        "Uses 'Present' for ongoing roles",
        not uses_current,
        "Use 'Present' instead of 'Current' or 'Ongoing' — ATS date parsers prefer 'Present'"
        if uses_current
        else "Ongoing dates use ATS-friendly wording",
        5,
    ))

    # Special character density (icons, decorative chars)
    if raw:
        special = sum(1 for c in raw if ord(c) > 127 or c in "★●◆►▸▪■□")
        ratio = special / len(raw)
        special_ok = ratio < 0.02
        checks.append(_fmt_check(
            "No icons or decorative symbols",
            special_ok,
            f"Decorative Unicode/icons detected ({ratio:.1%}) — ATS may ignore or misparse them"
            if not special_ok
            else "No excessive decorative characters",
            5,
        ))
    else:
        checks.append(_fmt_check(
            "No icons or decorative symbols",
            True,
            "No text to evaluate",
            5,
        ))

    return checks
