"""JD requirement checks — the "searchability" checks recruiters' ATS searches rely on.

Mirrors checks that commercial resume scanners run beside the keyword match:
job title present, education level, years of experience, and acronyms written
in both forms. Shown to the user and turned into fixes; not part of the score.
"""

from __future__ import annotations

import re
from typing import Any, Optional

_SENIORITY = {
    "intern", "internship", "senior", "sr", "junior", "jr", "lead", "principal", "staff",
    "associate", "trainee", "graduate", "fresher", "entry", "level", "i", "ii", "iii", "iv",
    "the", "a", "an", "of", "for", "and", "&", "-", "–", "—",
}
_BAD_TITLE_HINTS = re.compile(r"\b(about|company|who we are|overview|description|apply|location)\b", re.I)

_EDU_LEVELS = [
    (3, "PhD", re.compile(r"\b(ph\.?\s?d|doctorate|doctoral)\b", re.I)),
    (2, "Master's", re.compile(r"\b(master'?s?|m\.?\s?tech|m\.?\s?sc|mba|m\.?\s?s\b|m\.?\s?e\b|mca|postgraduate)\b", re.I)),
    (1, "Bachelor's", re.compile(r"\b(bachelor'?s?|b\.?\s?tech|b\.?\s?sc|b\.?\s?e\b|b\.?\s?s\b|bca|b\.?\s?com|undergraduate|graduate degree|degree in)\b", re.I)),
]


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9+#.]+", (text or "").lower()) if t not in _SENIORITY]


def _edu_level(text: str) -> tuple[int, str]:
    for level, label, pattern in _EDU_LEVELS:
        if pattern.search(text or ""):
            return level, label
    return 0, ""


def _check(name: str, status: str, detail: str) -> dict[str, str]:
    return {"name": name, "status": status, "detail": detail}


def check_job_title(resume: dict[str, Any], jd: dict[str, Any]) -> dict[str, str]:
    title = (jd.get("title") or "").strip().rstrip(":")
    words = title.split()
    if not title or len(words) > 8 or _BAD_TITLE_HINTS.search(title):
        return _check("Job title match", "unknown", "Could not read a clear job title from the JD.")
    text = (resume.get("raw_text") or "").lower()
    if title.lower() in text:
        return _check("Job title match", "pass", f"Your resume contains the exact title “{title}”.")
    core = _tokens(title)
    if not core:
        return _check("Job title match", "unknown", "Could not read a clear job title from the JD.")
    present = [t for t in core if re.search(rf"(?<![a-z0-9]){re.escape(t)}(?![a-z0-9])", text)]
    if len(present) >= max(1, round(0.67 * len(core))):
        return _check("Job title match", "partial",
                      f"Title words {', '.join(present)} appear, but not the exact title “{title}”. "
                      "Recruiters often search by exact title — use it in your headline or summary if it is truthful.")
    return _check("Job title match", "fail",
                  f"The JD title “{title}” does not appear. Add it to your summary or headline where it honestly fits.")


def check_education(resume: dict[str, Any], jd: dict[str, Any]) -> dict[str, str]:
    jd_level, jd_label = _edu_level(jd.get("raw_text") or "")
    if not jd_level:
        return _check("Education level", "unknown", "The JD does not state a degree requirement.")
    edu_text = " ".join(
        f"{e.get('degree', '')} {e.get('institution', '')}" for e in (resume.get("education") or []) if isinstance(e, dict)
    ) or (resume.get("raw_text") or "")
    res_level, res_label = _edu_level(edu_text)
    if res_level >= jd_level:
        return _check("Education level", "pass", f"JD asks for a {jd_label} degree; your resume shows {res_label}.")
    if res_level == 0:
        return _check("Education level", "fail",
                      f"JD asks for a {jd_label} degree, but no degree was recognised. Write the degree name in full, "
                      "e.g. “Bachelor of Technology (B.Tech) in Computer Science”.")
    return _check("Education level", "fail", f"JD asks for a {jd_label} degree; your resume shows {res_label}.")


def check_experience(resume: dict[str, Any], jd: dict[str, Any]) -> dict[str, str]:
    need: Optional[float] = jd.get("min_experience_years")
    if need is None:
        return _check("Years of experience", "unknown", "The JD does not state a minimum number of years.")
    have = float(resume.get("experience_years") or 0)
    if have >= need:
        return _check("Years of experience", "pass", f"JD asks for {need:g}+ years; your dated roles add up to about {have:g}.")
    return _check("Years of experience", "fail",
                  f"JD asks for {need:g}+ years; your dated roles add up to about {have:g}. "
                  "Make sure every role has start and end dates (e.g. Jun 2024 – Present).")


def check_acronyms(keyword_analysis: Optional[dict[str, Any]]) -> dict[str, str]:
    if not keyword_analysis:
        return _check("Acronyms in both forms", "unknown", "No JD keywords to check.")
    synonyms = [m["keyword"] for m in keyword_analysis.get("matched_keywords", []) if m.get("match_type") == "synonym"]
    if not synonyms:
        return _check("Acronyms in both forms", "pass", "JD terms appear in the same form the JD uses.")
    return _check("Acronyms in both forms", "partial",
                  f"{', '.join(synonyms[:5])} matched only through an abbreviation or expansion. Strict ATS searches "
                  "may miss them — write both forms once, e.g. “Machine Learning (ML)”.")


def run_requirement_checks(
    resume: dict[str, Any],
    jd: Optional[dict[str, Any]],
    keyword_analysis: Optional[dict[str, Any]] = None,
) -> list[dict[str, str]]:
    if not jd:
        return []
    return [
        check_job_title(resume, jd),
        check_education(resume, jd),
        check_experience(resume, jd),
        check_acronyms(keyword_analysis),
    ]
