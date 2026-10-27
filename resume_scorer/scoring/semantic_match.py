"""Layer 2: embedding-based skill matching — local sentence-transformers.

Each JD skill is matched against the resume's skills (expanded with aliases):

* exact / alias match            → full credit
* embedding-only match (cos ≥ τ) → partial credit (``SEMANTIC_ONLY_CREDIT``),
  unless the pair is on the curated blocklist of false equivalences
* no match                       → 0

Credit is then multiplied by the evidence factor from ``scoring.evidence``:
skills that appear only in a skills list earn λ (default 0.5) of their credit.
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np

from scoring.evidence import EvidenceIndex, list_credit
from scoring.skill_aliases import _build_lookup, expand_skills_for_matching

SEMANTIC_MATCH_THRESHOLD = 0.6
SEMANTIC_ONLY_CREDIT = 0.75
REQUIRED_SKILL_WEIGHT = 2.0
PREFERRED_SKILL_WEIGHT = 1.0
LAYER2_SKIP_NO_SKILLS = (
    "Layer 2 not applicable: JD has no extractable skills to match against."
)

# (JD skill, resume skill) pairs that embeddings rate as similar but that a
# recruiter would not accept. Found by manually reviewing every embedding-only
# match on the public evaluation set (39 distinct pairs at τ = 0.6). Includes
# sibling technologies and "broader skill does not imply the specific one".
SEMANTIC_BLOCKLIST: frozenset[tuple[str, str]] = frozenset(
    (a.lower(), b.lower())
    for a, b in [
        ("Unit Testing", "Performance Testing"), ("Performance Testing", "Unit Testing"),
        ("CSS", "HTML"), ("HTML", "CSS"), ("JavaScript", "HTML"), ("HTML", "JavaScript"),
        ("CloudWatch", "google cloud"), ("CloudWatch", "Google Cloud Platform"),
        ("Product Management", "Vendor Management"), ("Product Management", "Project Management"),
        ("Project Management", "Product Management"), ("Project Management", "Team Management"),
        ("System Design", "Design Systems"), ("Design Systems", "System Design"),
        ("UI Design", "System Design"), ("EC2", "ECS"), ("ECS", "EC2"),
        ("Deep Learning", "Machine Learning"), ("Computer Vision", "Machine Learning"),
        ("jQuery", "JavaScript"), ("Scrum", "Agile"), ("Oracle", "SQL"), ("SQL Server", "SQL"),
        ("PostgreSQL", "SQL"), ("MySQL", "SQL"), ("Power BI", "bi"), ("EC2", "AWS"),
        ("C++", "Java"), ("Java", "C++"), ("C++", "C#"), ("C#", "C++"), ("R", "C"), ("C", "R"),
        ("AWS", "Salesforce"), ("Salesforce", "AWS"), ("Excel", "MATLAB"),
        ("Communication", "Networking"), ("Accounting", "Business Analysis"),
        ("Business Analysis", "Accounting"), ("Java", "Unix"), ("Salesforce", "Unix"),
        ("Apache", "PHP"), ("Apache Beam", "Apache"),
        # Found by running the tool on a real student resume: related fields, not substitutes.
        ("Data Science", "Big Data"), ("Big Data", "Data Science"),
        ("Data Science", "Data Analysis"), ("Data Science", "SQL"),
    ]
)


def jd_has_matchable_skills(jd: dict[str, Any]) -> bool:
    """True when the JD yields at least one skill to score against."""
    return bool(
        jd.get("required_skills")
        or jd.get("preferred_skills")
        or jd.get("all_skills")
    )


def _normalize_rows(m: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(m, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return m / norms


def _match_skills(
    resume_skills: list[str],
    target_skills: list[str],
    model: Any,
    evidence: Optional[EvidenceIndex] = None,
    lam: float = 1.0,
) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    """Return matched skills, missing skills, and per-skill match details."""
    if not target_skills:
        return [], [], []
    if not resume_skills:
        return [], list(target_skills), []

    lookup = _build_lookup()
    resume_lower = {s.lower().strip(): s for s in resume_skills}
    resume_embs = _normalize_rows(np.asarray(model.encode(resume_skills, convert_to_numpy=True), dtype=float))
    matched: list[str] = []
    missing: list[str] = []
    details: list[dict[str, Any]] = []

    for skill in target_skills:
        key = skill.lower().strip()
        via, similarity, source = None, 1.0, None
        if key in resume_lower:
            via, source = "exact", resume_lower[key]
        else:
            alias_hit = next((resume_lower[a] for a in lookup.get(key, ()) if a in resume_lower), None)
            if alias_hit:
                via, source = "alias", alias_hit
        if via is None:
            emb = np.asarray(model.encode([skill], convert_to_numpy=True)[0], dtype=float)
            emb = emb / (np.linalg.norm(emb) or 1.0)
            sims = resume_embs @ emb
            order = np.argsort(-sims)
            for idx in order:
                sim = float(sims[idx])
                if sim < SEMANTIC_MATCH_THRESHOLD:
                    break
                cand = resume_skills[int(idx)]
                if (key, cand.lower().strip()) in SEMANTIC_BLOCKLIST:
                    continue
                via, similarity, source = "semantic", sim, cand
                break
        if via is None:
            missing.append(skill)
            continue
        base = 1.0 if via in ("exact", "alias") else SEMANTIC_ONLY_CREDIT
        ev_factor = evidence.factor(source, lam) if evidence is not None else 1.0
        ev_status = evidence.status(source) if evidence is not None else "unknown"
        matched.append(skill)
        details.append({
            "jd_skill": skill,
            "resume_skill": source,
            "via": via,
            "similarity": round(similarity, 2),
            "evidence": ev_status,
            "credit": round(base * ev_factor, 2),
        })
    return matched, missing, details


def score_semantic_match(
    resume: dict[str, Any],
    jd: dict[str, Any],
    model: Any,
    lam: Optional[float] = None,
) -> Optional[dict[str, Any]]:
    """Score JD skill alignment out of 100 using exact, alias and embedding matches.

    Returns None when the JD has no extractable skills to match (Layer 2 N/A).
    """
    if not jd_has_matchable_skills(jd):
        return None

    lam = list_credit() if lam is None else lam
    resume_skills = expand_skills_for_matching(resume.get("skills", []))
    evidence = EvidenceIndex(resume.get("source_text") or resume.get("raw_text") or "", skills=resume_skills)
    required = jd.get("required_skills", [])
    preferred = jd.get("preferred_skills", [])
    if not required and not preferred:
        required = jd.get("all_skills", [])

    req_matched, req_missing, req_details = _match_skills(resume_skills, required, model, evidence, lam)
    pref_matched, pref_missing, pref_details = _match_skills(resume_skills, preferred, model, evidence, lam)

    total_weight = len(required) * REQUIRED_SKILL_WEIGHT + len(preferred) * PREFERRED_SKILL_WEIGHT
    if total_weight == 0:
        return None
    earned = sum(d["credit"] for d in req_details) * REQUIRED_SKILL_WEIGHT + sum(
        d["credit"] for d in pref_details
    ) * PREFERRED_SKILL_WEIGHT
    raw_earned = len(req_matched) * REQUIRED_SKILL_WEIGHT + len(pref_matched) * PREFERRED_SKILL_WEIGHT

    exp_years = resume.get("experience_years", 0)
    min_exp = jd.get("min_experience_years")
    exp_note = None
    if min_exp is not None and exp_years < min_exp:
        exp_note = (
            f"JD requires ~{min_exp} years experience; "
            f"resume shows ~{exp_years} years"
        )

    details = req_details + pref_details
    return {
        "score": round((earned / total_weight) * 100, 1),
        "raw_score": round((raw_earned / total_weight) * 100, 1),
        "matched_required": req_matched,
        "missing_required": req_missing,
        "matched_preferred": pref_matched,
        "missing_preferred": pref_missing,
        "experience_note": exp_note,
        "match_details": details,
        "listed_only": [d["jd_skill"] for d in details if d["evidence"] == "listed_only"],
        "semantic_matches": [d for d in details if d["via"] == "semantic"],
        "list_credit": lam,
    }
