"""Analyze endpoint — parse, structure, and score resume + optional JD."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from api.analysis import run_analysis
from api.deps import VALID_TEMPLATES
from api.schemas import AnalyzeResponse, AnalyzeStructuredRequest, TemplateChoice
from parser import extract_text, validate_extracted_text
from structurer import structure_resume

router = APIRouter()


@router.post("/analyze/structured", response_model=AnalyzeResponse)
async def analyze_structured(body: AnalyzeStructuredRequest) -> AnalyzeResponse:
    if body.template not in VALID_TEMPLATES:
        raise HTTPException(status_code=400, detail=f"Invalid template: {body.template}")
    if not body.resume_struct:
        raise HTTPException(status_code=400, detail="resume_struct is required")
    return run_analysis(
        resume_struct=body.resume_struct,
        jd_raw=body.jd_text,
        template=body.template,
        parse_warning="Built via AI chat — review all content before exporting.",
    )


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

    return run_analysis(
        resume_struct=resume_struct,
        jd_raw=jd_raw or None,
        template=template,
        parse_warning=parse_warning,
    )
