"""Per-vendor 'how might this ATS see your resume' views.

Different ATS products match keywords differently (literal vs stemmed vs
semantic) and some do not score at all. This idea comes from ATS Screener
(sunnypatell, MIT), which simulates several vendors; this module is our own
small implementation.

IMPORTANT: these are rough illustrations built from publicly described
behaviour, not the vendors' real algorithms. The weights are illustrative and
NOT validated on labelled data, so they never change the core score.
"""

from __future__ import annotations

import re
from typing import Any, Optional

_TOKEN_RE = re.compile(r"[a-z0-9+#.]+")

DISCLAIMER = (
    "Illustrative approximation from public descriptions of each vendor; not the "
    "vendor's real algorithm and not validated. It does not affect your core score."
)

# name -> (matching strategy, weights for literal / stemmed / semantic / format, note)
PROFILES: dict[str, dict[str, Any]] = {
    "Taleo": {
        "strategy": "literal keyword match",
        "weights": {"literal": 0.75, "format": 0.25},
        "note": "Strictest: the exact JD wording must appear, so abbreviations and synonyms are missed.",
    },
    "Workday": {
        "strategy": "exact match plus AI ranking",
        "weights": {"literal": 0.50, "semantic": 0.20, "format": 0.30},
        "note": "Strict parser; formatting problems cost more here.",
    },
    "iCIMS": {
        "strategy": "semantic (ML) matching",
        "weights": {"semantic": 0.70, "literal": 0.10, "format": 0.20},
        "note": "More forgiving of synonyms and related skills.",
    },
    "Lever": {
        "strategy": "stemmed keyword search",
        "weights": {"stemmed": 0.70, "format": 0.30},
        "note": "Search-based; 'manage' finds 'managing', but abbreviations are not expanded.",
    },
    "SuccessFactors": {
        "strategy": "skills taxonomy normalisation",
        "weights": {"semantic": 0.60, "literal": 0.20, "format": 0.20},
        "note": "Maps skills to a taxonomy, so related skills count.",
    },
    "Greenhouse": {
        "strategy": "no automatic scoring",
        "weights": None,
        "note": "Humans read applications against scorecards; there is no auto-rank, so readability matters most.",
    },
}


def _stem(token: str) -> str:
    """Very light suffix stripper (enough to show stemming vs literal)."""
    for suffix in ("ing", "ed", "es", "s"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 3:
            return token[: -len(suffix)]
    return token


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _literal_hit(skill: str, text_lower: str) -> bool:
    pattern = r"(?<![\w+#])" + re.escape(skill.lower().strip()) + r"(?![\w+#])"
    return bool(re.search(pattern, text_lower))


def _stemmed_hit(skill: str, stemmed_stream: list[str]) -> bool:
    want = [_stem(t) for t in _tokens(skill)]
    if not want:
        return False
    n = len(want)
    return any(stemmed_stream[i : i + n] == want for i in range(len(stemmed_stream) - n + 1))


def _pct(hits: int, total: int) -> float:
    return round(100.0 * hits / total, 1) if total else 0.0


def format_fraction(formatting_checks: list[dict[str, Any]]) -> float:
    weight = sum(float(c.get("weight", 0)) for c in formatting_checks)
    earned = sum(float(c.get("score", 0)) for c in formatting_checks)
    return round(100.0 * earned / weight, 1) if weight else 100.0


def compute_vendor_views(
    resume_text: str,
    jd_skills: list[str],
    semantic_score: Optional[float],
    formatting_checks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """One entry per vendor; empty list when there is no JD skill list."""
    skills = [s for s in dict.fromkeys(jd_skills or []) if s and s.strip()]
    if not skills:
        return []
    lower = resume_text.lower()
    stream = [_stem(t) for t in _tokens(resume_text)]
    literal = _pct(sum(_literal_hit(s, lower) for s in skills), len(skills))
    stemmed = _pct(sum(_stemmed_hit(s, stream) for s in skills), len(skills))
    # Without the semantic layer, fall back to stemmed so the view still works.
    semantic = float(semantic_score) if semantic_score is not None else stemmed
    fmt = format_fraction(formatting_checks)
    parts = {"literal": literal, "stemmed": stemmed, "semantic": semantic, "format": fmt}

    out: list[dict[str, Any]] = []
    for name, prof in PROFILES.items():
        weights = prof["weights"]
        score = None if weights is None else round(sum(parts[k] * w for k, w in weights.items()), 1)
        out.append({
            "vendor": name,
            "strategy": prof["strategy"],
            "score": score,
            "note": prof["note"],
            "inputs": parts,
        })
    return out
