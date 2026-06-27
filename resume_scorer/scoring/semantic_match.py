"""Layer 2: embedding-based skill matching — local sentence-transformers."""

from __future__ import annotations

from typing import Any, Optional

import numpy as np

SEMANTIC_MATCH_THRESHOLD = 0.6
REQUIRED_SKILL_WEIGHT = 2.0
PREFERRED_SKILL_WEIGHT = 1.0
LAYER2_SKIP_NO_SKILLS = (
    "Layer 2 not applicable: JD has no extractable skills to match against."
)


def jd_has_matchable_skills(jd: dict[str, Any]) -> bool:
    """True when the JD yields at least one skill to score against."""
    return bool(
        jd.get("required_skills")
        or jd.get("preferred_skills")
        or jd.get("all_skills")
    )


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def _match_skills(
    resume_skills: list[str],
    target_skills: list[str],
    model: Any,
) -> tuple[list[str], list[str]]:
    if not target_skills:
        return [], []
    if not resume_skills:
        return [], list(target_skills)

    resume_embs = model.encode(resume_skills, convert_to_numpy=True)
    matched: list[str] = []
    missing: list[str] = []

    for skill in target_skills:
        skill_emb = model.encode([skill], convert_to_numpy=True)[0]
        best_sim = max(_cosine_similarity(skill_emb, r_emb) for r_emb in resume_embs)
        if best_sim >= SEMANTIC_MATCH_THRESHOLD:
            matched.append(skill)
        else:
            missing.append(skill)
    return matched, missing


def score_semantic_match(
    resume: dict[str, Any],
    jd: dict[str, Any],
    model: Any,
) -> Optional[dict[str, Any]]:
    """Score JD skill alignment out of 100 using semantic similarity.

    Returns None when the JD has no extractable skills to match (Layer 2 N/A).
    """
    if not jd_has_matchable_skills(jd):
        return None

    resume_skills = resume.get("skills", [])
    required = jd.get("required_skills", [])
    preferred = jd.get("preferred_skills", [])

    req_matched, req_missing = _match_skills(resume_skills, required, model)
    pref_matched, pref_missing = _match_skills(resume_skills, preferred, model)

    req_weight = len(required) * REQUIRED_SKILL_WEIGHT
    pref_weight = len(preferred) * PREFERRED_SKILL_WEIGHT
    total_weight = req_weight + pref_weight

    if total_weight == 0:
        all_jd_skills = jd.get("all_skills", [])
        if not all_jd_skills:
            return None
        req_matched, req_missing = _match_skills(resume_skills, all_jd_skills, model)
        total_weight = len(all_jd_skills) * REQUIRED_SKILL_WEIGHT
        earned = len(req_matched) * REQUIRED_SKILL_WEIGHT
    else:
        earned = (
            len(req_matched) * REQUIRED_SKILL_WEIGHT
            + len(pref_matched) * PREFERRED_SKILL_WEIGHT
        )

    if total_weight == 0:
        return None

    score = round((earned / total_weight) * 100, 1)

    exp_years = resume.get("experience_years", 0)
    min_exp = jd.get("min_experience_years")
    exp_note = None
    if min_exp is not None and exp_years < min_exp:
        exp_note = (
            f"JD requires ~{min_exp} years experience; "
            f"resume shows ~{exp_years} years"
        )

    return {
        "score": score,
        "matched_required": req_matched,
        "missing_required": req_missing,
        "matched_preferred": pref_matched,
        "missing_preferred": pref_missing,
        "experience_note": exp_note,
    }
