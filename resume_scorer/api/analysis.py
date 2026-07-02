"""Shared analysis pipeline for file-parsed and chat-built resumes."""

from __future__ import annotations

from typing import Any, Optional

from api.deps import build_gaps_from_layer2, compose_score, get_embedding_model, layer2_enabled
from api.schemas import AnalyzeResponse, Layer1Result, Layer2Result, ScoreGaps, TemplateChoice
from insights.resume_normalize import normalize_resume_struct
from scoring.deterministic import score_deterministic
from scoring.fix_suggestions import build_top_fixes, score_band_label
from scoring.semantic_match import LAYER2_SKIP_NO_SKILLS, score_semantic_match
from structurer import structure_jd_or_none


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

    layer1 = score_deterministic(resume_struct, jd_struct)
    layer2 = None
    layer2_error: Optional[str] = None
    layer2_skip: Optional[str] = None

    if jd_provided and jd_struct and layer2_enabled():
        try:
            model = get_embedding_model()
            layer2 = score_semantic_match(resume_struct, jd_struct, model)
            if layer2 is None and not layer2_error:
                layer2_skip = LAYER2_SKIP_NO_SKILLS
        except RuntimeError as exc:
            layer2_error = str(exc)
    elif jd_provided and jd_struct and not layer2_enabled():
        layer2_skip = "Layer 2 disabled (SKIP_LAYER2) — structure score only on this deployment"

    core = compose_score(
        layer1["score"],
        layer2["score"] if layer2 else None,
        jd_provided,
    )

    gaps = build_gaps_from_layer2(layer2)
    if layer2_error and parse_warning:
        parse_warning = f"{parse_warning} | Layer 2 skipped: {layer2_error}"
    elif layer2_error:
        parse_warning = f"Layer 2 skipped: {layer2_error}"
    elif layer2_skip:
        parse_warning = (
            f"{parse_warning} | {layer2_skip}" if parse_warning else layer2_skip
        )

    top_fixes = build_top_fixes(
        core, layer1, layer2, gaps, parse_warning, jd_provided
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
    )
