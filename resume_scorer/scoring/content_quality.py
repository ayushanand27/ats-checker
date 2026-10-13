"""Writing-quality checks — what a recruiter notices after the ATS lets you through.

Modelled on the "impact / brevity / style" checks of commercial resume
reviewers: strong action verbs, no weak duty phrases, no first-person pronouns,
no clichés, short bullets, varied verbs. Reported as its own score; not part of
the ATS match score.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

ACTION_VERBS = frozenset("""
accelerated achieved administered analysed analyzed architected assembled assessed audited authored automated
built calculated championed coached collaborated compiled completed composed computed conceived configured
consolidated constructed consulted converted coordinated created cut debugged decreased defined delivered deployed
designed detected developed devised diagnosed directed discovered drafted drove eliminated enabled engineered
enhanced established evaluated executed expanded expedited extracted facilitated fixed forecasted formulated
founded generated grew guided halved handled headed identified implemented improved increased influenced
initiated innovated inspected installed integrated interpreted introduced investigated launched led leveraged
maintained managed mapped maximized measured mentored merged migrated minimized modeled modelled monitored
negotiated optimized optimised orchestrated organized organised outperformed overhauled oversaw partnered piloted
pioneered planned predicted prepared presented prioritized processed produced programmed prototyped published
raised ran rebuilt recommended redesigned reduced refactored remodeled reorganized replaced researched resolved
restructured revamped reviewed revised scaled scheduled scoped secured shipped simplified solved spearheaded
standardized streamlined strengthened structured supervised surpassed synthesized tested tracked trained
transformed translated troubleshot tuned unified upgraded validated visualized won wrote
owned ranked earned awarded conducted sourced screened onboarded recruited hired interviewed curated contributed
documented demonstrated captured boosted lowered saved generated answered serviced supported taught tutored
organised hosted volunteered represented secured streamlined containerized containerised benchmarked fine-tuned
finetuned trained labelled labeled annotated scraped crawled indexed queried cleaned preprocessed parsed
""".split())

WEAK_PHRASES = [
    "responsible for", "worked on", "helped", "assisted with", "assisted in", "duties included",
    "involved in", "tasked with", "participated in", "in charge of",
]
BUZZWORDS = [
    "team player", "hard-working", "hardworking", "go-getter", "detail-oriented", "results-driven",
    "self-motivated", "think outside the box", "synergy", "dynamic", "passionate", "proactive",
    "self-starter", "go getter", "best of breed", "value add",
]
PRONOUN_RE = re.compile(r"\b(i|me|my|mine|we|our|us)\b", re.I)
LONG_BULLET_WORDS = 35


def _bullets(resume: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for group in ("experience", "projects"):
        for entry in resume.get(group) or []:
            if isinstance(entry, dict):
                out += [str(b).strip() for b in entry.get("bullets") or [] if str(b).strip()]
    return out


def _first_word(bullet: str) -> str:
    m = re.match(r"[^A-Za-z]*([A-Za-z]+)", bullet)
    return m.group(1).lower() if m else ""


def _check(name: str, passed: bool, reason: str, weight: float, fraction: float | None = None) -> dict[str, Any]:
    frac = (1.0 if passed else 0.0) if fraction is None else max(0.0, min(1.0, fraction))
    return {"name": name, "passed": passed, "reason": reason, "weight": weight, "score": round(weight * frac, 2)}


def score_content_quality(resume: dict[str, Any]) -> dict[str, Any]:
    bullets = _bullets(resume)
    text = " ".join(bullets + [str(resume.get("summary") or "")])
    lower = text.lower()
    checks: list[dict[str, Any]] = []

    if bullets:
        firsts = [_first_word(b) for b in bullets]
        strong = sum(1 for w in firsts if w in ACTION_VERBS)
        ratio = strong / len(bullets)
        checks.append(_check(
            "Bullets start with action verbs", ratio >= 0.7,
            f"{strong}/{len(bullets)} bullets start with a strong verb (Built, Led, Reduced…)"
            + ("" if ratio >= 0.7 else " — start each bullet with what you did"),
            25, ratio))
        repeated = [w for w, c in Counter(w for w in firsts if w).items() if c >= 4]
        checks.append(_check(
            "Varied verbs", not repeated,
            "Verbs are varied" if not repeated else f"“{', '.join(repeated)}” starts 4+ bullets — vary your verbs",
            10))
        long_b = [b for b in bullets if len(b.split()) > LONG_BULLET_WORDS]
        checks.append(_check(
            "Concise bullets", len(long_b) <= max(1, len(bullets) // 10),
            "Bullets are concise" if not long_b else f"{len(long_b)} bullet(s) exceed {LONG_BULLET_WORDS} words — split or trim them",
            15, 1 - len(long_b) / len(bullets)))
    else:
        checks.append(_check("Bullets start with action verbs", False,
                             "No experience or project bullets found — describe your work as bullet points", 25, 0))

    weak = [p for p in WEAK_PHRASES if re.search(rf"\b{re.escape(p)}\b", lower)]
    checks.append(_check(
        "No weak duty phrases", len(weak) <= 1,
        "No weak phrases like “responsible for”" if not weak
        else f"Found {', '.join(repr(w) for w in weak[:4])} — replace with the action and its result",
        20, 1 - min(len(weak), 4) / 4))
    pronouns = sorted({m.group(1).lower() for m in PRONOUN_RE.finditer(" ".join(bullets))})
    checks.append(_check(
        "No first-person pronouns", not pronouns,
        "Bullets avoid I/my/we" if not pronouns else f"Bullets use {', '.join(pronouns)} — drop pronouns (“Led…”, not “I led…”)",
        15))
    buzz = [b for b in BUZZWORDS if b in lower]
    checks.append(_check(
        "No clichés", len(buzz) <= 1,
        "No clichés found" if not buzz else f"Clichés: {', '.join(buzz[:4])} — show the quality with evidence instead",
        15, 1 - min(len(buzz), 3) / 3))

    total = sum(c["weight"] for c in checks)
    score = round(100 * sum(c["score"] for c in checks) / total, 1) if total else 0.0
    return {"score": score, "checks": checks, "bullets_analysed": len(bullets)}
