"""Rule/regex-based section and skill extraction — no API calls."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

_TAXONOMY_PATH = Path(__file__).parent / "skills_taxonomy.json"

SECTION_PATTERNS: dict[str, list[str]] = {
    "experience": [
        r"^experiences?$",
        r"^work\s+experiences?$",
        r"^professional\s+experiences?$",
        r"^employment\s+history$",
        r"^career\s+history$",
    ],
    "education": [
        r"^educations?$",
        r"^academic\s+background$",
        r"^qualifications?$",
    ],
    "skills": [
        r"^skills?$",
        r"^technical\s+skills?$",
        r"^core\s+competencies$",
        r"^technologies$",
        r"^tools?\s*(and|&)\s*technologies$",
    ],
    "projects": [
        r"^projects?$",
        r"^personal\s+projects?$",
        r"^key\s+projects?$",
    ],
    "summary": [
        r"^summary$",
        r"^professional\s+summary$",
        r"^profile$",
        r"^objective$",
        r"^about\s+me$",
    ],
}

EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)
PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[\s\-]?)?"
    r"(?:\(?\d{2,4}\)?[\s\-]?)?"
    r"\d{3,4}[\s\-]?\d{3,4}(?:[\s\-]?\d{2,4})?",
)
LINKEDIN_RE = re.compile(
    r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-]+/?",
    re.IGNORECASE,
)
GITHUB_RE = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/[\w\-]+/?",
    re.IGNORECASE,
)
DATE_RANGE_RE = re.compile(
    r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|"
    r"january|february|march|april|june|july|august|september|october|november|december)"
    r"[\w\s,.\-]*?"
    r"(?:\d{4}|present|current|now)",
    re.IGNORECASE,
)
METRIC_RE = re.compile(
    r"\d+%|\$\d+|\d+x|\d+\s*(?:years?|months?|yrs?|mos?)",
    re.IGNORECASE,
)
BULLET_RE = re.compile(r"^[\s]*(?:[•\-\*●▪▸►]|\d+[.)])\s+")
MONTH_MAP = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}


def _load_taxonomy() -> list[str]:
    with open(_TAXONOMY_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("skills", [])


def _compile_section_regex() -> re.Pattern[str]:
    all_patterns: list[str] = []
    for patterns in SECTION_PATTERNS.values():
        all_patterns.extend(patterns)
    combined = "|".join(f"(?:{p})" for p in all_patterns)
    return re.compile(rf"^\s*({combined})\s*:?\s*$", re.IGNORECASE | re.MULTILINE)


_SECTION_HEADER_RE = _compile_section_regex()


def _normalize_lines(text: str) -> list[str]:
    return [ln.rstrip() for ln in text.replace("\r\n", "\n").split("\n")]


def _detect_sections(lines: list[str]) -> dict[str, tuple[int, int]]:
    """Return section name -> (start_line, end_line) indices."""
    headers: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        m = _SECTION_HEADER_RE.match(stripped)
        if m:
            header_text = stripped.lower()
            for section, patterns in SECTION_PATTERNS.items():
                for pat in patterns:
                    if re.match(pat, header_text, re.IGNORECASE):
                        headers.append((i, section))
                        break
    sections: dict[str, tuple[int, int]] = {}
    for idx, (start, name) in enumerate(headers):
        end = headers[idx + 1][0] if idx + 1 < len(headers) else len(lines)
        sections[name] = (start + 1, end)
    return sections


def _extract_skills(text: str, taxonomy: list[str]) -> list[str]:
    found: list[str] = []
    text_lower = text.lower()
    for skill in taxonomy:
        pattern = rf"\b{re.escape(skill.lower())}\b"
        if re.search(pattern, text_lower):
            found.append(skill)
    return sorted(set(found), key=str.lower)


def _parse_month_year(token: str) -> Optional[tuple[int, int]]:
    token = token.strip().lower()
    if token in ("present", "current", "now"):
        return (9999, 12)
    m = re.search(
        r"(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|"
        r"january|february|march|april|june|july|august|september|october|november|december)"
        r"[\s,.\-]*(\d{4})",
        token,
        re.IGNORECASE,
    )
    if m:
        month = MONTH_MAP.get(m.group(1).lower(), 1)
        return (int(m.group(2)), month)
    m = re.search(r"(\d{4})", token)
    if m:
        return (int(m.group(1)), 1)
    return None


def _months_between(start: tuple[int, int], end: tuple[int, int]) -> int:
    return max(0, (end[0] - start[0]) * 12 + (end[1] - start[1]))


def _estimate_experience_years(text: str) -> float:
    ranges = DATE_RANGE_RE.findall(text)
    total_months = 0
    for chunk in ranges:
        parts = re.split(r"\s*(?:–|—|-|to)\s*", chunk, maxsplit=1)
        if len(parts) == 2:
            start = _parse_month_year(parts[0])
            end = _parse_month_year(parts[1])
            if start and end:
                total_months += _months_between(start, end)
    return round(total_months / 12.0, 1)


def _extract_bullets(lines: list[str]) -> list[dict[str, Any]]:
    bullets: list[dict[str, Any]] = []
    for line in lines:
        if BULLET_RE.match(line):
            text = BULLET_RE.sub("", line).strip()
            if text:
                bullets.append({
                    "text": text,
                    "has_metric": bool(METRIC_RE.search(text)),
                })
    return bullets


def _parse_experience_entries(lines: list[str]) -> list[dict[str, Any]]:
    """Heuristic parse of experience section into title/company/bullets."""
    entries: list[dict[str, Any]] = []
    current: dict[str, Any] = {"title": "", "company": "", "dates": "", "bullets": []}
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if BULLET_RE.match(stripped):
            bullet_text = BULLET_RE.sub("", stripped).strip()
            current["bullets"].append(bullet_text)
        elif DATE_RANGE_RE.search(stripped):
            if current.get("bullets") or current.get("title"):
                entries.append(current)
            current = {"title": "", "company": "", "dates": stripped, "bullets": []}
            title_part = DATE_RANGE_RE.split(stripped)[0].strip(" ,|–—-")
            if title_part:
                if "|" in title_part:
                    parts = [p.strip() for p in title_part.split("|")]
                    current["title"] = parts[0]
                    if len(parts) > 1:
                        current["company"] = parts[1]
                elif " at " in title_part.lower():
                    idx = title_part.lower().index(" at ")
                    current["title"] = title_part[:idx].strip()
                    current["company"] = title_part[idx + 4:].strip()
                else:
                    current["title"] = title_part
        elif not current["title"]:
            current["title"] = stripped
        elif not current["company"]:
            current["company"] = stripped
    if current.get("bullets") or current.get("title"):
        entries.append(current)
    return entries


def _parse_education(lines: list[str]) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or BULLET_RE.match(stripped):
            continue
        dates = ""
        dm = DATE_RANGE_RE.search(stripped)
        if dm:
            dates = dm.group(0)
            stripped = stripped.replace(dates, "").strip(" ,|–—-")
        degree, institution = stripped, ""
        if "|" in stripped:
            parts = [p.strip() for p in stripped.split("|")]
            degree = parts[0]
            institution = parts[1] if len(parts) > 1 else ""
        elif "," in stripped:
            parts = [p.strip() for p in stripped.split(",", 1)]
            degree = parts[0]
            institution = parts[1] if len(parts) > 1 else ""
        entries.append({"degree": degree, "institution": institution, "dates": dates})
    return entries


def _parse_projects(lines: list[str]) -> list[dict[str, Any]]:
    projects: list[dict[str, Any]] = []
    current: dict[str, Any] = {"name": "", "description": "", "bullets": []}
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if BULLET_RE.match(stripped):
            current["bullets"].append(BULLET_RE.sub("", stripped).strip())
        else:
            if current["name"]:
                projects.append(current)
            current = {"name": stripped, "description": "", "bullets": []}
    if current["name"]:
        projects.append(current)
    return projects


def _extract_contact(text: str) -> dict[str, Optional[str]]:
    emails = EMAIL_RE.findall(text)
    phones = PHONE_RE.findall(text)
    linkedin = LINKEDIN_RE.search(text)
    github = GITHUB_RE.search(text)
    return {
        "email": emails[0] if emails else None,
        "phone": phones[0] if phones else None,
        "linkedin": linkedin.group(0) if linkedin else None,
        "github": github.group(0) if github else None,
    }


def _guess_name(lines: list[str]) -> str:
    for line in lines[:5]:
        stripped = line.strip()
        if not stripped:
            continue
        if EMAIL_RE.search(stripped) or PHONE_RE.search(stripped):
            continue
        if _SECTION_HEADER_RE.match(stripped):
            continue
        if len(stripped.split()) <= 5 and len(stripped) < 60:
            return stripped
    return ""


def structure_resume(text: str) -> dict[str, Any]:
    """Extract structured resume JSON via rules/regex only."""
    lines = _normalize_lines(text)
    sections = _detect_sections(lines)
    taxonomy = _load_taxonomy()
    skills = _extract_skills(text, taxonomy)

    summary_text = ""
    if "summary" in sections:
        s, e = sections["summary"]
        summary_text = "\n".join(l.strip() for l in lines[s:e] if l.strip())

    experience_entries: list[dict[str, Any]] = []
    experience_bullets: list[dict[str, Any]] = []
    if "experience" in sections:
        s, e = sections["experience"]
        exp_lines = lines[s:e]
        experience_entries = _parse_experience_entries(exp_lines)
        experience_bullets = _extract_bullets(exp_lines)

    education: list[dict[str, str]] = []
    if "education" in sections:
        s, e = sections["education"]
        education = _parse_education(lines[s:e])

    projects: list[dict[str, Any]] = []
    if "projects" in sections:
        s, e = sections["projects"]
        projects = _parse_projects(lines[s:e])

    if "skills" in sections:
        s, e = sections["skills"]
        section_skills = _extract_skills("\n".join(lines[s:e]), taxonomy)
        skills = sorted(set(skills + section_skills), key=str.lower)

    contact = _extract_contact(text)
    exp_years = _estimate_experience_years(text)
    bullets_with_metrics = sum(1 for b in experience_bullets if b["has_metric"])
    total_bullets = len(experience_bullets)

    return {
        "name": _guess_name(lines),
        "contact": contact,
        "summary": summary_text,
        "skills": skills,
        "experience": experience_entries,
        "education": education,
        "projects": projects,
        "sections_found": list(sections.keys()),
        "experience_years": exp_years,
        "metrics": {
            "total_bullets": total_bullets,
            "bullets_with_metrics": bullets_with_metrics,
        },
        "raw_text": text,
    }


def _extract_jd_required_skills(text: str, taxonomy: list[str]) -> list[str]:
    required: list[str] = []
    blocks = re.split(
        r"(?:required|must\s+have|minimum\s+qualifications?|essential)",
        text,
        flags=re.IGNORECASE,
    )
    search_text = blocks[1] if len(blocks) > 1 else text
    required = _extract_skills(search_text[:2000], taxonomy)
    return required


def _extract_jd_preferred_skills(text: str, taxonomy: list[str]) -> list[str]:
    blocks = re.split(
        r"(?:preferred|nice\s+to\s+have|bonus|desired)",
        text,
        flags=re.IGNORECASE,
    )
    search_text = blocks[1] if len(blocks) > 1 else ""
    return _extract_skills(search_text[:1500], taxonomy)


def _extract_jd_title(text: str) -> str:
    lines = _normalize_lines(text)
    for line in lines[:8]:
        stripped = line.strip()
        if stripped and len(stripped) < 120:
            return stripped
    return ""


def _extract_min_experience(text: str) -> Optional[float]:
    patterns = [
        r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)",
        r"(?:minimum|at\s+least)\s+(\d+)\s*(?:years?|yrs?)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return float(m.group(1))
    return None


def structure_jd(text: str) -> dict[str, Any]:
    """Extract structured JD JSON via rules/regex only."""
    taxonomy = _load_taxonomy()
    all_skills = _extract_skills(text, taxonomy)
    required = _extract_jd_required_skills(text, taxonomy)
    preferred = _extract_jd_preferred_skills(text, taxonomy)
    if not required:
        required = all_skills[: max(len(all_skills) // 2, 1)]
    preferred = [s for s in preferred if s not in required]
    return {
        "title": _extract_jd_title(text),
        "required_skills": required,
        "preferred_skills": preferred,
        "all_skills": all_skills,
        "min_experience_years": _extract_min_experience(text),
        "raw_text": text,
        "jd_provided": True,
    }


def structure_jd_or_none(text: Optional[str]) -> Optional[dict[str, Any]]:
    if not text or not text.strip():
        return None
    return structure_jd(text.strip())
