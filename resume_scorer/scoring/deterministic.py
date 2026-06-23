"""Layer 1: rule-based ATS checks — pure Python, no API calls."""

from __future__ import annotations

from typing import Any

from parser import alphanumeric_ratio


REQUIRED_SECTIONS = {"experience", "education", "skills"}
RECOMMENDED_SECTIONS = {"summary", "projects"}


def _check(name: str, passed: bool, reason: str, weight: float) -> dict[str, Any]:
    return {
        "name": name,
        "passed": passed,
        "reason": reason,
        "weight": weight,
        "score": weight if passed else 0.0,
    }


def score_deterministic(
    resume: dict[str, Any],
    jd: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Score resume structure and ATS hygiene out of 100."""
    checks: list[dict[str, Any]] = []
    contact = resume.get("contact", {})
    sections = set(resume.get("sections_found", []))
    raw = resume.get("raw_text", "")
    word_count = len(raw.split())

    has_email = bool(contact.get("email"))
    has_phone = bool(contact.get("phone"))
    has_link = bool(contact.get("linkedin") or contact.get("github"))
    checks.append(_check(
        "Contact email",
        has_email,
        "Email found" if has_email else "No email detected — ATS systems need contact info",
        10,
    ))
    checks.append(_check(
        "Contact phone or link",
        has_phone or has_link,
        "Phone or professional link found" if (has_phone or has_link) else "Add phone or LinkedIn/GitHub URL",
        5,
    ))

    missing_required = REQUIRED_SECTIONS - sections
    has_core_sections = len(missing_required) == 0
    checks.append(_check(
        "Core sections",
        has_core_sections,
        "Experience, Education, and Skills sections detected"
        if has_core_sections
        else f"Missing sections: {', '.join(sorted(missing_required))}",
        20,
    ))

    has_recommended = bool(sections & RECOMMENDED_SECTIONS)
    checks.append(_check(
        "Summary or Projects",
        has_recommended,
        "Summary or Projects section found" if has_recommended else "Consider adding a Summary or Projects section",
        5,
    ))

    length_ok = 100 <= word_count <= 1200
    if word_count < 100:
        length_reason = f"Resume appears too short ({word_count} words) — possible parse failure"
    elif word_count > 1200:
        length_reason = f"Resume is long ({word_count} words) — ATS prefers 1–2 pages (~400–800 words)"
    else:
        length_reason = f"Length looks good ({word_count} words)"
    checks.append(_check("Length sanity", length_ok, length_reason, 15))

    ratio = alphanumeric_ratio(raw)
    parse_ok = ratio >= 0.5
    checks.append(_check(
        "Parse quality",
        parse_ok,
        f"Alphanumeric ratio {ratio:.0%} — text extracted cleanly"
        if parse_ok
        else f"Alphanumeric ratio {ratio:.0%} — possible corruption or image PDF",
        15,
    ))

    metrics = resume.get("metrics", {})
    total_bullets = metrics.get("total_bullets", 0)
    with_metrics = metrics.get("bullets_with_metrics", 0)
    metric_ratio = (with_metrics / total_bullets) if total_bullets else 0
    metrics_ok = total_bullets == 0 or metric_ratio >= 0.3
    checks.append(_check(
        "Quantified bullets",
        metrics_ok,
        f"{with_metrics}/{total_bullets} experience bullets include metrics"
        if total_bullets
        else "No experience bullets detected to evaluate",
        15,
    ))

    skills_count = len(resume.get("skills", []))
    skills_ok = skills_count >= 5
    checks.append(_check(
        "Skills breadth",
        skills_ok,
        f"{skills_count} skills detected" if skills_ok else f"Only {skills_count} skills detected — add more relevant keywords",
        15,
    ))

    total_weight = sum(c["weight"] for c in checks)
    earned = sum(c["score"] for c in checks)
    score = round((earned / total_weight) * 100, 1) if total_weight else 0.0

    return {
        "score": score,
        "checks": checks,
        "word_count": word_count,
    }
