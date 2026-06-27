"""Rule/regex-based section and skill extraction — no API calls."""

from __future__ import annotations

import json
import re
from datetime import datetime
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
        r"^tools?\s*(?:and|&)\s*technologies$",
        r"^technical\s+proficiencies$",
        r"^competencies$",
        r"^areas?\s+of\s+expertise$",
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
DATE_BOUNDARY_RE = re.compile(
    r"(?:"
    r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|"
    r"january|february|march|april|june|july|august|september|october|november|december)"
    r"\s*,?\s*\d{4}\s*[-–—to]+\s*"
    r"(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|"
    r"january|february|march|april|june|july|august|september|october|november|december)"
    r"\s*,?\s*)?(?:\d{4}|present|current|now)"
    r"|\d{1,2}/\d{4}\s*[-–—to]+\s*(?:\d{1,2}/\d{4}|present|current|now)"
    r"|\d{4}\s*[-–—to]+\s*(?:\d{4}|present|current|now)"
    r")",
    re.IGNORECASE,
)
TITLE_ROLE_RE = re.compile(
    r"\b(engineer|developer|manager|analyst|director|lead|intern|consultant|"
    r"architect|designer|specialist|scientist|coordinator|associate|vp|head)\b",
    re.IGNORECASE,
)
COMPANY_HINT_RE = re.compile(
    r"\b(inc\.?|llc|ltd\.?|corp\.?|co\.?|gmbh|technologies|systems|solutions|group)\b",
    re.IGNORECASE,
)
DATE_RANGE_RE = DATE_BOUNDARY_RE
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


def _clean_header_line(line: str) -> str:
    """Normalize a line for section-header matching."""
    cleaned = line.strip().strip("\ufeff")
    cleaned = re.sub(r"[\u200b\u00ad]", "", cleaned)
    return cleaned


def _pattern_core(pattern: str) -> str:
    """Strip anchors from a SECTION_PATTERNS entry for prefix matching."""
    return pattern.lstrip("^").rstrip("$").strip()


def _classify_section_header(stripped: str) -> Optional[str]:
    """
    Match a section header line — exact standalone header or header merged with
    inline content (common in multi-column PDF extraction, e.g. Jake's Resume).
    """
    cleaned = _clean_header_line(stripped)
    if not cleaned:
        return None

    if _SECTION_HEADER_RE.match(cleaned):
        header_text = cleaned.lower()
        for section, patterns in SECTION_PATTERNS.items():
            for pat in patterns:
                if re.match(pat, header_text, re.IGNORECASE):
                    return section
        return None

    # Prefix match: "Skills Python, SQL, ..." or "Technical Skills: Python, ..."
    for section, patterns in SECTION_PATTERNS.items():
        cores = "|".join(f"(?:{_pattern_core(p)})" for p in patterns)
        prefix_re = re.compile(
            rf"^\s*(?:{cores})\s*(?:[:\-–—|]\s*)?(?:.+)?\s*$",
            re.IGNORECASE,
        )
        if not prefix_re.match(cleaned):
            continue
        # Avoid false positives like "Experience with Python" for experience section
        if section == "experience" and re.search(
            r"\b(with|in|at|for|using|building|developing)\b", cleaned, re.IGNORECASE
        ):
            continue
        if section == "summary" and re.search(
            r"\b(of|for|with|about|from)\b", cleaned, re.IGNORECASE
        ):
            continue
        if section == "skills":
            remainder = prefix_re.sub("", cleaned).strip()
            if remainder and not re.search(r"[,|/]", remainder):
                # Single token after header — likely a sentence, not a skills block
                if len(remainder.split()) > 3:
                    continue
        return section

    return None


def _detect_sections(lines: list[str]) -> dict[str, tuple[int, int]]:
    """Return section name -> (start_line, end_line) indices."""
    headers: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        section = _classify_section_header(stripped)
        if section:
            headers.append((i, section))
    sections: dict[str, tuple[int, int]] = {}
    for idx, (start, name) in enumerate(headers):
        end = headers[idx + 1][0] if idx + 1 < len(headers) else len(lines)
        sections[name] = (start + 1, end)
    return sections


_AMBIGUOUS_SHORT_SKILLS = frozenset({"c", "r", "go"})


def _skill_match_pattern(skill: str) -> re.Pattern[str]:
    """Build regex for taxonomy skill; stricter boundaries for short ambiguous tokens."""
    escaped = re.escape(skill.lower())
    if skill.lower() in _AMBIGUOUS_SHORT_SKILLS:
        return re.compile(rf"(?<![a-z]){escaped}(?![a-z])", re.IGNORECASE)
    return re.compile(rf"\b{escaped}\b", re.IGNORECASE)


def _extract_skills(text: str, taxonomy: list[str]) -> list[str]:
    found: list[str] = []
    for skill in taxonomy:
        if _skill_match_pattern(skill).search(text):
            found.append(skill)
    return sorted(set(found), key=str.lower)


_PRESENT_END_RE = re.compile(
    r"^(?:present|current|now|till\s+date)$",
    re.IGNORECASE,
)


def _parse_month_year(token: str) -> Optional[tuple[int, int]]:
    token = re.sub(r"\s+", " ", token.strip().lower())
    if _PRESENT_END_RE.match(token):
        now = datetime.now()
        return (now.year, now.month)
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


def _month_index(year: int, month: int) -> int:
    return year * 12 + month


def _merge_experience_intervals(
    intervals: list[tuple[int, int, int, int]],
) -> list[tuple[int, int]]:
    """Merge overlapping (start_y, start_m, end_y, end_m) ranges into month spans."""
    if not intervals:
        return []
    month_spans = sorted(
        (_month_index(sy, sm), _month_index(ey, em))
        for sy, sm, ey, em in intervals
    )
    merged: list[tuple[int, int]] = [month_spans[0]]
    for start, end in month_spans[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def _estimate_experience_years(text: str) -> float:
    intervals: list[tuple[int, int, int, int]] = []
    for chunk in DATE_RANGE_RE.findall(text):
        parts = re.split(r"\s*(?:–|—|-|to)\s*", chunk, maxsplit=1, flags=re.IGNORECASE)
        if len(parts) == 2:
            start = _parse_month_year(parts[0])
            end = _parse_month_year(parts[1])
            if start and end:
                intervals.append((start[0], start[1], end[0], end[1]))
    merged = _merge_experience_intervals(intervals)
    total_months = sum(end - start for start, end in merged)
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


def _extract_date_range(line: str) -> Optional[tuple[str, str]]:
    """Return (dates_substring, remainder_with_date_removed) or None."""
    m = DATE_BOUNDARY_RE.search(line)
    if not m:
        return None
    dates = m.group(0).strip()
    remainder = (line[: m.start()] + line[m.end() :]).strip(" ,|–—-\t")
    return dates, remainder


def _looks_like_title(text: str) -> bool:
    return bool(TITLE_ROLE_RE.search(text))


def _looks_like_company(text: str) -> bool:
    return bool(COMPANY_HINT_RE.search(text))


def _assign_title_company(part_a: str, part_b: str) -> tuple[str, str]:
    """Resolve two text fragments into (title, company)."""
    a, b = part_a.strip(), part_b.strip()
    if not a:
        return b, ""
    if not b:
        return a, ""
    a_title, b_title = _looks_like_title(a), _looks_like_title(b)
    a_co, b_co = _looks_like_company(a), _looks_like_company(b)
    if a_title and not b_title:
        return a, b
    if b_title and not a_title:
        return b, a
    if a_co and not b_co:
        return b, a
    if b_co and not a_co:
        return a, b
    return a, b


def _resolve_entry_header(header_lines: list[str], inline_remainder: str) -> tuple[str, str]:
    """Combine buffered header lines + same-line remainder into title and company."""
    parts: list[str] = []
    for ln in header_lines:
        stripped = ln.strip()
        if stripped:
            parts.append(stripped)
    if inline_remainder:
        parts.append(inline_remainder.strip())

    if not parts:
        return "", ""

    if len(parts) == 1:
        single = parts[0]
        if "|" in single:
            pipe_parts = [p.strip() for p in single.split("|") if p.strip()]
            if len(pipe_parts) >= 2:
                return _assign_title_company(pipe_parts[0], pipe_parts[1])
            return pipe_parts[0], "" if pipe_parts else ("", "")
        if " at " in single.lower():
            idx = single.lower().index(" at ")
            return single[:idx].strip(), single[idx + 4 :].strip()
        return single, ""

    first, second = parts[0], parts[1]
    if "|" in second:
        left, right = [p.strip() for p in second.split("|", 1)]
        title, company = _assign_title_company(left, right)
        if not title:
            title, company = _assign_title_company(first, company or right)
        elif not company:
            company = first if first != title else right
        return title or first, company or second
    return _assign_title_company(first, second)


def _is_header_boundary_line(line: str) -> bool:
    """Short non-bullet line that can start a new experience entry."""
    stripped = line.strip()
    if not stripped or BULLET_RE.match(stripped):
        return False
    if _extract_date_range(stripped):
        return True
    return len(stripped) < 80


def _parse_experience_entries(lines: list[str]) -> list[dict[str, Any]]:
    """Parse experience section into title/company/dates/bullets entries."""
    entries: list[dict[str, Any]] = []
    current: dict[str, Any] = {"title": "", "company": "", "dates": "", "bullets": []}
    header_buffer: list[str] = []
    has_bullets = False

    def finalize_current() -> None:
        nonlocal current, header_buffer, has_bullets
        if not (current["title"] or current["company"] or current["dates"] or current["bullets"]):
            header_buffer = []
            has_bullets = False
            return
        if not current["title"] and not current["company"] and header_buffer:
            title, company = _resolve_entry_header(header_buffer, "")
            current["title"] = title
            current["company"] = company
        entries.append(current)
        current = {"title": "", "company": "", "dates": "", "bullets": []}
        header_buffer = []
        has_bullets = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if BULLET_RE.match(stripped):
            bullet_text = BULLET_RE.sub("", stripped).strip()
            if bullet_text:
                if not current["title"] and not current["company"] and header_buffer:
                    title, company = _resolve_entry_header(header_buffer, "")
                    current["title"] = title
                    current["company"] = company
                    header_buffer = []
                current["bullets"].append(bullet_text)
                has_bullets = True
            continue

        date_info = _extract_date_range(stripped)
        if date_info:
            dates, remainder = date_info
            if has_bullets:
                finalize_current()
            elif current["title"] or current["company"] or current["dates"]:
                finalize_current()

            title, company = _resolve_entry_header(header_buffer, remainder)
            current["title"] = title
            current["company"] = company
            current["dates"] = dates
            header_buffer = []
            continue

        if has_bullets and _is_header_boundary_line(stripped):
            finalize_current()

        if not current["dates"]:
            header_buffer.append(stripped)
        elif not has_bullets:
            if not current["company"] and current["title"]:
                _, company = _assign_title_company(current["title"], stripped)
                current["company"] = company if company != current["title"] else stripped
            elif not current["title"]:
                current["title"] = stripped
            else:
                header_buffer.append(stripped)

    if current["title"] or current["company"] or current["dates"] or current["bullets"] or header_buffer:
        if header_buffer and not current["title"] and not current["company"]:
            title, company = _resolve_entry_header(header_buffer, "")
            current["title"] = title
            current["company"] = company
        if current["title"] or current["company"] or current["dates"] or current["bullets"]:
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


_NAME_REJECT_HEADERS = frozenset({
    "experience", "education", "skills", "summary", "projects",
    "contact", "objective", "profile", "work experience", "technical skills",
})


def _is_valid_name_candidate(text: str) -> bool:
    """Reject names that look like contact lines, section headers, or garbage."""
    stripped = text.strip()
    if not stripped or len(stripped) > 60 or len(stripped.split()) > 5:
        return False
    if re.search(r"\d|@", stripped):
        return False
    if _SECTION_HEADER_RE.match(stripped):
        return False
    lower = stripped.lower().rstrip(":")
    if lower in _NAME_REJECT_HEADERS:
        return False
    for header in _NAME_REJECT_HEADERS:
        if lower.startswith(header + " "):
            return False
    return True


def _guess_name(lines: list[str], pdf_bytes: Optional[bytes] = None) -> str:
    if pdf_bytes:
        try:
            from parser import guess_name_from_pdf
            pdf_name = guess_name_from_pdf(pdf_bytes)
            if pdf_name and _is_valid_name_candidate(pdf_name):
                return pdf_name.strip()
        except Exception:
            pass

    for line in lines[:8]:
        stripped = line.strip()
        if not stripped:
            continue
        if EMAIL_RE.search(stripped) or PHONE_RE.search(stripped):
            continue
        if _is_valid_name_candidate(stripped):
            return stripped
    return ""


def structure_resume(text: str, pdf_bytes: Optional[bytes] = None) -> dict[str, Any]:
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
    elif len(skills) >= 5:
        # PDF column extraction may omit a standalone Skills header even when
        # skill keywords are present (e.g. Jake's Resume sidebar layout).
        sections["skills"] = (0, len(lines))

    contact = _extract_contact(text)
    exp_years = 0.0
    if "experience" in sections:
        s, e = sections["experience"]
        exp_years = _estimate_experience_years("\n".join(lines[s:e]))
    bullets_with_metrics = sum(1 for b in experience_bullets if b["has_metric"])
    total_bullets = len(experience_bullets)

    return {
        "name": _guess_name(lines, pdf_bytes),
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


_JD_REQUIRED_KEYWORDS = re.compile(
    r"\b(?:must|required|require|needs?|essential|mandatory|minimum)\b",
    re.IGNORECASE,
)
_JD_PREFERRED_KEYWORDS = re.compile(
    r"\b(?:nice\s+to\s+have|good\s+to\s+have|preferred|bonus|plus|desired|optional)\b",
    re.IGNORECASE,
)
_JD_REQUIRED_SECTION = re.compile(
    r"(?:\brequired\b|must[\s\-–—]+have|minimum\s+qualifications?|\bessential\b)",
    re.IGNORECASE,
)
_JD_PREFERRED_SECTION = re.compile(
    r"(?:\bpreferred\b|nice[\s\-–—]+to[\s\-–—]+have|good[\s\-–—]+to[\s\-–—]+have|\bbonus\b|\bdesired\b)",
    re.IGNORECASE,
)
_JD_REQUIRED_SPLIT = re.compile(
    r"(?:\brequired\b|must[\s\-–—]+have|minimum\s+qualifications?|\bessential\b)",
    re.IGNORECASE,
)
_JD_PREFERRED_SPLIT = re.compile(
    r"(?:\bpreferred\b|nice[\s\-–—]+to[\s\-–—]+have|good[\s\-–—]+to[\s\-–—]+have|\bbonus\b|\bdesired\b)",
    re.IGNORECASE,
)
_JD_CONTENT_START_MARKERS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"job\s+title",
        r"job\s+responsibilities",
        r"role\s+overview",
        r"key\s+responsibilities",
        r"\bresponsibilities\s*:",
        r"\brequirements\s*:",
        r"skills\s*(?:&|and)\s*experience",
        r"must[\s\-–—]+have",
        r"good[\s\-–—]+to[\s\-–—]+have",
    )
)


def _jd_skill_extraction_text(text: str) -> str:
    """
    Strip leading company boilerplate before skill/requirement extraction.
    If a job-specific marker is found, only text from that marker onward is used.
    """
    earliest: Optional[int] = None
    for pattern in _JD_CONTENT_START_MARKERS:
        match = pattern.search(text)
        if match and (earliest is None or match.start() < earliest):
            earliest = match.start()
    if earliest is not None:
        return text[earliest:]
    return text


def _sanitize_jd_skills(source_text: str, skills: list[str]) -> list[str]:
    """Drop known taxonomy false positives from corporate boilerplate."""
    cleaned: list[str] = []
    for skill in skills:
        if skill == "Kong" and re.search(r"Hong\s+Kong", source_text, re.IGNORECASE):
            continue
        if skill == "Storage" and re.search(
            r"server,\s*storage,\s*edge", source_text, re.IGNORECASE
        ):
            continue
        cleaned.append(skill)
    return cleaned


_JD_RESPONSIBILITIES_START = re.compile(
    r"(?:key\s+responsibilities|\bresponsibilities\s*:)",
    re.IGNORECASE,
)


def _extract_jd_responsibility_skills(extraction_text: str, taxonomy: list[str]) -> list[str]:
    """Skills explicitly mentioned in role/responsibility bullets (before Must-have)."""
    match = _JD_RESPONSIBILITIES_START.search(extraction_text)
    if not match:
        return []
    chunk = extraction_text[match.end() :]
    chunk = _JD_REQUIRED_SPLIT.split(chunk, maxsplit=1)[0]
    chunk = _JD_PREFERRED_SPLIT.split(chunk, maxsplit=1)[0]
    chunk = re.split(
        r"skills\s*(?:&|and)\s*experience",
        chunk,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    return _sanitize_jd_skills(
        extraction_text,
        _extract_skills(chunk[:2500], taxonomy),
    )
    """Classify a skill as required or preferred using keyword proximity."""
    pattern = _skill_match_pattern(skill)
    votes_required = 0
    votes_preferred = 0
    for match in pattern.finditer(text):
        ctx = text[max(0, match.start() - 100) : min(len(text), match.end() + 100)]
        has_required = bool(_JD_REQUIRED_KEYWORDS.search(ctx))
        has_preferred = bool(_JD_PREFERRED_KEYWORDS.search(ctx))
        in_intro = bool(pattern.search(intro))
        if has_preferred and not has_required:
            votes_preferred += 1
        elif has_required or in_intro:
            votes_required += 1
        else:
            votes_required += 1
    if votes_preferred and not votes_required:
        return "preferred"
    return "required"


def _bucket_jd_skills_heuristic(text: str, all_skills: list[str]) -> tuple[list[str], list[str]]:
    sentences = re.split(r"(?<=[.!?])\s+", text.replace("\n", " ").strip())
    intro = " ".join(sentences[:2]) if sentences else ""
    required: list[str] = []
    preferred: list[str] = []
    for skill in all_skills:
        if _skill_context_bucket(text, skill, intro) == "preferred":
            preferred.append(skill)
        else:
            required.append(skill)
    return required, preferred


def _extract_jd_required_skills(text: str, taxonomy: list[str]) -> list[str]:
    blocks = _JD_REQUIRED_SPLIT.split(text, maxsplit=1)
    search_text = blocks[1] if len(blocks) > 1 else ""
    if not search_text:
        return []
    pref_parts = _JD_PREFERRED_SPLIT.split(search_text, maxsplit=1)
    search_text = pref_parts[0]
    return _extract_skills(search_text[:2000], taxonomy)


def _extract_jd_preferred_skills(text: str, taxonomy: list[str]) -> list[str]:
    blocks = _JD_PREFERRED_SPLIT.split(text, maxsplit=1)
    search_text = blocks[1] if len(blocks) > 1 else ""
    return _extract_skills(search_text[:1500], taxonomy)


def _extract_jd_title(text: str) -> str:
    title_match = re.search(
        r"job\s+title\s+(.+?)(?:\n|$)",
        text,
        re.IGNORECASE,
    )
    if title_match:
        return title_match.group(1).strip()
    lines = _normalize_lines(text)
    for line in lines[:12]:
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
    extraction_text = _jd_skill_extraction_text(text)
    all_skills = _sanitize_jd_skills(
        extraction_text,
        _extract_skills(extraction_text, taxonomy),
    )

    has_required_section = bool(_JD_REQUIRED_SECTION.search(extraction_text))
    has_preferred_section = bool(_JD_PREFERRED_SECTION.search(extraction_text))

    if has_required_section or has_preferred_section:
        required = (
            _sanitize_jd_skills(
                extraction_text,
                _extract_jd_required_skills(extraction_text, taxonomy),
            )
            if has_required_section
            else []
        )
        preferred = (
            _sanitize_jd_skills(
                extraction_text,
                _extract_jd_preferred_skills(extraction_text, taxonomy),
            )
            if has_preferred_section
            else []
        )
        if has_required_section:
            resp_skills = _extract_jd_responsibility_skills(extraction_text, taxonomy)
            required = sorted(set(required + resp_skills), key=str.lower)
        preferred = [s for s in preferred if s not in required]
        # Only backfill required from global matches when no explicit required section exists
        if not required and not has_required_section:
            required = [s for s in all_skills if s not in preferred]
    else:
        required, preferred = _bucket_jd_skills_heuristic(extraction_text, all_skills)
        required = _sanitize_jd_skills(extraction_text, required)
        preferred = _sanitize_jd_skills(extraction_text, preferred)

    return {
        "title": _extract_jd_title(text),
        "required_skills": required,
        "preferred_skills": preferred,
        "all_skills": all_skills,
        "min_experience_years": _extract_min_experience(extraction_text),
        "raw_text": text,
        "jd_provided": True,
    }


def structure_jd_or_none(text: Optional[str]) -> Optional[dict[str, Any]]:
    if not text or not text.strip():
        return None
    return structure_jd(text.strip())
