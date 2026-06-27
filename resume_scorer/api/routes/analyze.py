"""Analyze endpoint — parse, structure, and score resume + optional JD."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from api.deps import (
    VALID_TEMPLATES,
    build_gaps_from_layer2,
    compose_score,
    get_embedding_model,
)
from api.schemas import AnalyzeResponse, Layer1Result, Layer2Result, ScoreGaps, TemplateChoice
from parser import extract_text, validate_extracted_text
from scoring.deterministic import score_deterministic
from scoring.semantic_match import score_semantic_match
from structurer import structure_jd_or_none, structure_resume

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    resume: UploadFile = File(..., description="Resume file (.pdf, .docx, .txt)"),
    jd_text: Optional[str] = Form(
        None,
        description="Optional job description as plain text",
    ),
    jd_file: Optional[UploadFile] = File(
        None,
        description="Optional job description file (.pdf, .docx, .txt)",
    ),
    template: TemplateChoice = Form(
        "jacks_tech",
        description="Output template selection (jacks_tech | classic_nontech | custom)",
    ),
) -> AnalyzeResponse:
    if template not in VALID_TEMPLATES:
        raise HTTPException(status_code=400, detail=f"Invalid template: {template}")

    if not resume.filename:
        raise HTTPException(status_code=400, detail="Resume filename is required")

    resume_bytes = await resume.read()
    if not resume_bytes:
        raise HTTPException(status_code=400, detail="Resume file is empty")

    try:
        resume_raw = extract_text(resume_bytes, resume.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    parse_warning = validate_extracted_text(resume_raw)

    jd_raw = (jd_text or "").strip()
    if jd_file and jd_file.filename:
        jd_bytes = await jd_file.read()
        if jd_bytes:
            try:
                jd_raw = extract_text(jd_bytes, jd_file.filename)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc

    pdf_bytes = resume_bytes if resume.filename.lower().endswith(".pdf") else None
    resume_struct = structure_resume(resume_raw, pdf_bytes=pdf_bytes)
    jd_struct = structure_jd_or_none(jd_raw or None)
    jd_provided = jd_struct is not None

    layer1 = score_deterministic(resume_struct, jd_struct)
    layer2 = None
    layer2_error: Optional[str] = None

    if jd_provided and jd_struct:
        try:
            model = get_embedding_model()
            layer2 = score_semantic_match(resume_struct, jd_struct, model)
        except RuntimeError as exc:
            layer2_error = str(exc)

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
    )
