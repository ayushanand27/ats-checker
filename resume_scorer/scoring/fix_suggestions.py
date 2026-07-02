"""Prioritized actionable fix list — industry-standard ATS coaching."""

from __future__ import annotations

from typing import Any, Optional


def _fix(
    priority: int,
    title: str,
    detail: str,
    severity: str = "high",
) -> dict[str, Any]:
    return {
        "priority": priority,
        "title": title,
        "detail": detail,
        "severity": severity,
    }


def build_top_fixes(
    core_score: float,
    layer1: dict[str, Any],
    layer2: Optional[dict[str, Any]],
    gaps: dict[str, Any],
    parse_warning: Optional[str],
    jd_provided: bool,
) -> list[dict[str, Any]]:
    """Return up to 7 prioritized fixes ordered by impact."""
    fixes: list[dict[str, Any]] = []
    p = 1

    if parse_warning:
        fixes.append(_fix(
            p,
            "Fix resume parsing issue",
            parse_warning.split("|")[0].strip(),
            "high",
        ))
        p += 1

    for check in layer1.get("checks", []):
        if not check.get("passed"):
            fixes.append(_fix(
                p,
                f"Layer 1: {check.get('name', 'Check')}",
                check.get("reason", "Failed structure check"),
                "high" if check.get("weight", 0) >= 15 else "medium",
            ))
            p += 1

    for check in layer1.get("formatting_checks", []):
        if not check.get("passed"):
            fixes.append(_fix(
                p,
                f"Formatting: {check.get('name', 'Check')}",
                check.get("reason", "ATS formatting issue"),
                "medium",
            ))
            p += 1

    missing_req = gaps.get("missing_required") or []
    if missing_req and jd_provided:
        top = missing_req[:4]
        fixes.append(_fix(
            p,
            "Add missing required JD skills",
            f"Include where truthful: {', '.join(top)}"
            + (f" (+{len(missing_req) - 4} more)" if len(missing_req) > 4 else ""),
            "high",
        ))
        p += 1

    missing_pref = gaps.get("missing_preferred") or []
    if missing_pref and jd_provided and len(fixes) < 6:
        fixes.append(_fix(
            p,
            "Add preferred JD skills",
            f"Nice-to-have: {', '.join(missing_pref[:5])}",
            "medium",
        ))
        p += 1

    exp_note = gaps.get("experience_note") or (layer2 or {}).get("experience_note")
    if exp_note:
        fixes.append(_fix(
            p,
            "Experience level gap",
            exp_note,
            "medium",
        ))
        p += 1

    metrics = layer1.get("metrics") or {}
    total = metrics.get("total_bullets", 0)
    with_m = metrics.get("bullets_with_metrics", 0)
    if total and with_m / total < 0.3:
        fixes.append(_fix(
            p,
            "Add quantified achievements",
            f"Only {with_m}/{total} bullets include metrics — add %, $, counts, or time saved (SOAR method)",
            "high",
        ))
        p += 1

    if core_score < 80 and jd_provided and len(fixes) < 7:
        fixes.append(_fix(
            p,
            "Tailor summary to the JD",
            "Rewrite your 3–4 line summary to mirror the role title and top 3 JD requirements using natural language",
            "medium",
        ))
        p += 1

    fixes.sort(key=lambda f: (0 if f["severity"] == "high" else 1, f["priority"]))
    for i, fix in enumerate(fixes[:7], start=1):
        fix["priority"] = i
    return fixes[:7]


def score_band_label(score: float, jd_provided: bool) -> str:
    """Industry-standard score interpretation bands."""
    if not jd_provided:
        if score >= 85:
            return "Strong structure — add a JD for tailored skill matching"
        if score >= 70:
            return "Good structure — add a JD for full ATS match score"
        return "Structure needs work before applying"

    if score >= 90:
        return "Excellent match (90+) — strong alignment with this JD"
    if score >= 80:
        return "Strong match (80+) — competitive for this role; polish remaining gaps"
    if score >= 70:
        return "Good match (70–79) — address missing skills and formatting before applying"
    if score >= 60:
        return "Fair match (60–69) — significant gaps; tailor resume to this JD"
    return "Needs work (<60) — major gaps vs this job description"
