"""Shared analysis pipeline for file-parsed and chat-built resumes."""

from __future__ import annotations

from typing import Any, Optional

from api.deps import (
    build_gaps_from_layer2,
    compose_score_detailed,
    get_context_model,
    get_embedding_model,
    layer2_enabled,
)
from api.schemas import (
    AnalyzeResponse,
    ContentQuality,
    ContextualResult,
    KeywordAnalysis,
    Layer1Result,
    Layer2Result,
    RequirementCheck,
    ScoreBreakdown,
    ScoreGaps,
    TemplateChoice,
)
from insights.resume_normalize import normalize_resume_struct
from scoring.content_quality import score_content_quality
from scoring.contextual_match import context_enabled, score_contextual_match
from scoring.deterministic import score_deterministic
from scoring.fix_suggestions import build_top_fixes, score_band_label
from scoring.keyword_analysis import analyze_keywords
from scoring.requirements_check import run_requirement_checks
from scoring.semantic_match import LAYER2_SKIP_NO_SKILLS, score_semantic_match
from structurer import structure_jd_or_none


def _join_warning(current: Optional[str], extra: Optional[str]) -> Optional[str]:
    if not extra:
        return current
    return f"{current} | {extra}" if current else extra


def run_analysis(
    resume_struct: dict[str, Any],
    jd_raw: Optional[str],
    template: TemplateChoice,
    parse_warning: Optional[str] = None,
) -> AnalyzeResponse:
    """Score a structured resume dict with optional JD text."""
    resume_struct = normalize_resume_struct(resume_struct)
    jd_struct = structure_jd_or_none((jd_raw or "").strip() or None)
    jd_provided = jd_struct is not None

    # Layer 1 — structure and formatting
    layer1 = score_deterministic(resume_struct, jd_struct)

    # Layer 2 — skill match (exact / alias / embedding, evidence-weighted)
    layer2 = None
    if jd_provided and jd_struct and layer2_enabled():
        try:
            layer2 = score_semantic_match(resume_struct, jd_struct, get_embedding_model())
            if layer2 is None:
                parse_warning = _join_warning(parse_warning, LAYER2_SKIP_NO_SKILLS)
        except RuntimeError as exc:
            parse_warning = _join_warning(parse_warning, f"Layer 2 skipped: {exc}")
    elif jd_provided and jd_struct:
        parse_warning = _join_warning(
            parse_warning, "Layer 2 disabled (SKIP_LAYER2) — skill match not computed on this deployment"
        )

    # Layer 3 — contextual whole-document match
    contextual = None
    if jd_provided and jd_struct and context_enabled():
        try:
            contextual = score_contextual_match(
                resume_struct.get("source_text") or resume_struct.get("raw_text") or "",
                jd_struct.get("raw_text") or jd_raw or "",
                get_context_model(),
            )
        except RuntimeError as exc:
            parse_warning = _join_warning(parse_warning, f"Contextual match skipped: {exc}")

    breakdown = compose_score_detailed(
        layer1["score"],
        layer2["score"] if layer2 else None,
        jd_provided,
        contextual["score"] if contextual else None,
    )
    core = breakdown["score"]
    if breakdown["mode"] == "structure_only_jd_unmatched":
        parse_warning = _join_warning(
            parse_warning,
            "No skills recognised in this JD and contextual match unavailable — the score shows structure only, not job match",
        )

    kw_raw = analyze_keywords(resume_struct, jd_struct)
    keyword_analysis = KeywordAnalysis(**kw_raw) if kw_raw else None
    requirements = run_requirement_checks(resume_struct, jd_struct, kw_raw)
    quality = score_content_quality(resume_struct)

    gaps = build_gaps_from_layer2(layer2)
    top_fixes = build_top_fixes(
        core, layer1, layer2, gaps, parse_warning, jd_provided,
        keyword_analysis=kw_raw, requirements=requirements, content_quality=quality,
    )
    band = score_band_label(core, jd_provided)

    return AnalyzeResponse(
        core_score=core,
        jd_provided=jd_provided,
        template=template,
        parse_warning=parse_warning,
        resume_struct=resume_struct,
        jd_struct=jd_struct,
        layer1=Layer1Result(**layer1),
        layer2=Layer2Result(**layer2) if layer2 else None,
        gaps=ScoreGaps(**gaps),
        top_fixes=top_fixes,
        score_band=band,
        keyword_analysis=keyword_analysis,
        contextual=ContextualResult(**contextual) if contextual else None,
        score_breakdown=ScoreBreakdown(**breakdown),
        requirements_checks=[RequirementCheck(**r) for r in requirements],
        content_quality=ContentQuality(**quality),
    )
