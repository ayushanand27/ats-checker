"""Layer 1: rule-based ATS checks — pure Python, no API calls."""

from __future__ import annotations

from typing import Any

from parser import alphanumeric_ratio
from scoring.formatting import check_formatting


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


def _graded(
    name: str,
    fraction: float,
    passed: bool,
    reason: str,
    weight: float,
) -> dict[str, Any]:
    """A check whose score scales with a 0–1 fraction instead of pass/fail.

    Used for inherently continuous signals (e.g. quantified-bullet ratio,
    parse cleanliness) so a partially-met check no longer earns full marks.
    ``passed`` still drives the green/attention badge in the UI.
    """
    fraction = max(0.0, min(1.0, fraction))
    return {
        "name": name,
        "passed": passed,
        "reason": reason,
        "weight": weight,
        "score": round(weight * fraction, 2),
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
    # Graded: 0 at/below 0.5 (corruption floor), full at 0.85+. Normal clean
    # text sits ~0.78–0.82, so even a well-parsed resume gives up a couple of
    # points here — real ATS parse fidelity is rarely called "perfect".
    parse_fraction = (ratio - 0.5) / (0.85 - 0.5)
    checks.append(_graded(
        "Parse quality",
        parse_fraction,
        parse_ok,
        f"Alphanumeric ratio {ratio:.0%} — text extracted cleanly"
        if parse_ok
        else f"Alphanumeric ratio {ratio:.0%} — possible corruption or image PDF",
        15,
    ))

    metrics = resume.get("metrics", {})
    total_bullets = metrics.get("total_bullets", 0)
    with_metrics = metrics.get("bullets_with_metrics", 0)
    metric_ratio = (with_metrics / total_bullets) if total_bullets else 0.0
    if total_bullets == 0:
        # No bullets parsed — can't quantify. Neutral (half) rather than a
        # free full pass, since a bullet-less experience section is itself weak.
        metrics_fraction = 0.5
        metrics_ok = False
        metrics_reason = "No quantified experience bullets detected — add metrics (e.g. 'cut latency 40%')"
    else:
        # Linear with the quantified ratio: full marks only when (nearly) every
        # bullet carries a metric. 2/4 = 50% now earns 50% of the weight.
        metrics_fraction = metric_ratio
        metrics_ok = metric_ratio >= 0.6
        metrics_reason = (
            f"{with_metrics}/{total_bullets} experience bullets include metrics"
            + ("" if metrics_ok else " — quantify more bullets for a higher score")
        )
    checks.append(_graded(
        "Quantified bullets",
        metrics_fraction,
        metrics_ok,
        metrics_reason,
        15,
    ))

    # Skills breadth: below 5 is thin; 5–10 scales; 10+ is full.
    skills_count = len(resume.get("skills", []))
    skills_ok = skills_count >= 5
    skills_fraction = skills_count / 10.0
    checks.append(_graded(
        "Skills breadth",
        skills_fraction,
        skills_ok,
        f"{skills_count} skills detected" if skills_ok else f"Only {skills_count} skills detected — add more relevant keywords",
        15,
    ))

    formatting_checks = check_formatting(resume)
    hygiene_checks = checks
    all_checks = hygiene_checks + formatting_checks

    total_weight = sum(c["weight"] for c in all_checks)
    earned = sum(c["score"] for c in all_checks)
    score = round((earned / total_weight) * 100, 1) if total_weight else 0.0

    return {
        "score": score,
        "checks": hygiene_checks,
        "formatting_checks": formatting_checks,
        "word_count": word_count,
        "metrics": metrics,
    }
