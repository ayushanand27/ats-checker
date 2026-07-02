"""Industry-standard keyword match analysis — exact + synonym placement & density."""

from __future__ import annotations

import re
from typing import Any, Optional

from scoring.skill_aliases import _build_lookup

# Industry guidance: 1–3 natural uses per keyword; flag excessive repetition
DENSITY_WARN_THRESHOLD = 4
SYNONYM_MATCH_WEIGHT = 0.8


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _keyword_in_text(keyword: str, haystack: str) -> bool:
    """Word-boundary aware match for multi-word skills."""
    kw = re.escape(keyword.lower().strip())
    return bool(re.search(rf"(?<![a-z0-9]){kw}(?![a-z0-9])", haystack, re.I))


def _count_occurrences(keyword: str, text: str) -> int:
    kw = re.escape(keyword.lower().strip())
    return len(re.findall(rf"(?<![a-z0-9]){kw}(?![a-z0-9])", text.lower()))


def _resume_search_corpus(resume: dict[str, Any]) -> dict[str, str]:
    summary = _normalize(resume.get("summary") or "")
    skills = _normalize(", ".join(resume.get("skills") or []))
    exp_bullets = []
    for exp in resume.get("experience") or []:
        exp_bullets.extend(exp.get("bullets") or [])
    experience = _normalize(" ".join(str(b) for b in exp_bullets))
    raw = _normalize(resume.get("raw_text") or "")
    return {
        "summary": summary,
        "skills": skills,
        "experience": experience,
        "full": raw or _normalize(f"{summary} {skills} {experience}"),
    }


def _term_in_section(term: str, section: str) -> bool:
    if _keyword_in_text(term, section):
        return True
    lookup = _build_lookup()
    for alias in lookup.get(term.lower().strip(), ()):
        if _keyword_in_text(alias, section):
            return True
    return False


def _match_keyword(keyword: str, corpus: dict[str, str]) -> tuple[bool, float, list[str]]:
    """Return matched, weight (1.0 exact / 0.8 synonym), placement list."""
    full = corpus["full"]
    lookup = _build_lookup()
    key = keyword.lower().strip()

    if _keyword_in_text(keyword, full):
        weight = 1.0
    else:
        matched_alias = False
        for alias in lookup.get(key, ()):
            if _keyword_in_text(alias, full):
                matched_alias = True
                weight = SYNONYM_MATCH_WEIGHT
                break
        if not matched_alias:
            return False, 0.0, []

    placements: list[str] = []
    if _term_in_section(keyword, corpus["summary"]):
        placements.append("summary")
    if _term_in_section(keyword, corpus["skills"]):
        placements.append("skills")
    if _term_in_section(keyword, corpus["experience"]):
        placements.append("experience")
    if not placements:
        placements.append("resume")

    return True, weight, placements


def analyze_keywords(
    resume: dict[str, Any],
    jd: Optional[dict[str, Any]],
) -> Optional[dict[str, Any]]:
    """
    Industry-style keyword report when JD is provided.
    Mirrors 30–40% keyword weighting used by Workday/Taleo-style checkers.
    """
    if not jd:
        return None

    required = list(jd.get("required_skills") or [])
    preferred = list(jd.get("preferred_skills") or [])
    all_skills = list(jd.get("all_skills") or [])
    keywords = required + [p for p in preferred if p not in required]
    if not keywords:
        keywords = all_skills
    if not keywords:
        return None

    corpus = _resume_search_corpus(resume)
    raw_display = resume.get("raw_text") or ""

    matched: list[dict[str, Any]] = []
    missing: list[str] = []
    placement_summary = {"summary": 0, "skills": 0, "experience": 0, "resume_only": 0}
    total_weight = 0.0
    earned_weight = 0.0

    for kw in keywords:
        is_required = kw in required
        base_weight = 2.0 if is_required else 1.0
        total_weight += base_weight

        ok, match_w, placements = _match_keyword(kw, corpus)

        if ok:
            earned_weight += base_weight * match_w
            for p in placements:
                if p in placement_summary:
                    placement_summary[p] += 1
                elif p == "resume":
                    placement_summary["resume_only"] += 1
            matched.append({
                "keyword": kw,
                "required": is_required,
                "match_type": "exact" if match_w >= 1.0 else "synonym",
                "placements": placements,
                "count": _count_occurrences(kw, corpus["full"]),
            })
        else:
            missing.append(kw)

    keyword_score = round((earned_weight / total_weight) * 100, 1) if total_weight else 0.0

    # Density / stuffing warnings (industry: penalize unnatural repetition)
    density_warnings: list[str] = []
    for item in matched:
        if item["count"] >= DENSITY_WARN_THRESHOLD:
            density_warnings.append(
                f"'{item['keyword']}' appears {item['count']} times — "
                "ATS may flag keyword stuffing; aim for 1–3 natural uses"
            )

    # Highlights for UI — which lines contain missing required keywords
    highlights: list[dict[str, Any]] = []
    for item in matched:
        kw = item["keyword"]
        pattern = re.compile(re.escape(kw), re.I)
        for line in raw_display.splitlines():
            if pattern.search(line):
                highlights.append({"keyword": kw, "line": line.strip()[:200], "status": "matched"})
                break

    for kw in missing[:12]:
        highlights.append({"keyword": kw, "line": None, "status": "missing"})

    return {
        "keyword_score": keyword_score,
        "match_rate_percent": keyword_score,
        "matched_keywords": matched,
        "missing_keywords": missing,
        "placement_summary": placement_summary,
        "density_warnings": density_warnings,
        "highlights": highlights,
        "total_jd_keywords": len(keywords),
        "matched_count": len(matched),
    }
