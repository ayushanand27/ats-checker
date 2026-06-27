"""Generate endpoint — render resume to DOCX, PDF, or TeX."""

from __future__ import annotations

import json

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from api.deps import VALID_FORMATS, VALID_TEMPLATES
from api.schemas import OutputFormat, TemplateChoice
from renderers.custom_docx_renderer import render_custom_docx
from renderers.docx_renderer import render_docx
from renderers.pdf_renderer import pdf_export_available, render_pdf
from renderers.tex_renderer import render_tex

router = APIRouter()

_CONTENT_TYPES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "tex": "application/x-tex",
}
_EXTENSIONS = {"pdf": "pdf", "docx": "docx", "tex": "tex"}


def _merge_for_render(
    original: dict,
    rewritten: dict | None,
) -> dict:
    if not rewritten:
        return original
    return {
        "name": original.get("name", ""),
        "contact": original.get("contact", {}),
        "summary": rewritten.get("summary", original.get("summary", "")),
        "skills": rewritten.get("skills", original.get("skills", [])),
        "experience": rewritten.get("experience", original.get("experience", [])),
        "education": rewritten.get("education", original.get("education", [])),
        "projects": rewritten.get("projects", original.get("projects", [])),
    }


@router.post("/generate")
async def generate(
    resume_json: str = Form(
        ...,
        description="Structured resume JSON (from /analyze or /rewrite, merged with contact/name)",
    ),
    template: TemplateChoice = Form("jacks_tech"),
    format: OutputFormat = Form("docx"),
    rewritten_json: str | None = Form(
        None,
        description="Optional rewritten content JSON from /rewrite (content fields only)",
    ),
    custom_template: UploadFile | None = File(
        None,
        description="Required when template=custom — .docx with Jinja2 placeholders",
    ),
) -> Response:
    if template not in VALID_TEMPLATES:
        raise HTTPException(status_code=400, detail=f"Invalid template: {template}")
    if format not in VALID_FORMATS:
        raise HTTPException(status_code=400, detail=f"Invalid format: {format}")

    try:
        resume_struct = json.loads(resume_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="resume_json is not valid JSON") from exc

    rewritten = None
    if rewritten_json:
        try:
            rewritten = json.loads(rewritten_json)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=400,
                detail="rewritten_json is not valid JSON",
            ) from exc

    payload = _merge_for_render(resume_struct, rewritten)

    if template == "custom":
        if format != "docx":
            raise HTTPException(
                status_code=400,
                detail="Custom templates support DOCX output only",
            )
        if not custom_template or not custom_template.filename:
            raise HTTPException(
                status_code=400,
                detail="custom_template file is required when template=custom",
            )
        tpl_bytes = await custom_template.read()
        docx_bytes, err = render_custom_docx(tpl_bytes, payload)
        if err:
            raise HTTPException(status_code=400, detail=err)
        content = docx_bytes
    elif format == "docx":
        try:
            content = render_docx(payload, template)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"DOCX generation failed: {exc}") from exc
    elif format == "pdf":
        pdf_ok, pdf_err = pdf_export_available()
        if not pdf_ok:
            raise HTTPException(
                status_code=503,
                detail=pdf_err or "PDF export unavailable on this system",
            )
        try:
            content = render_pdf(payload, template)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}") from exc
    elif format == "tex":
        try:
            tex_str = render_tex(payload, template)
            content = tex_str.encode("utf-8")
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"TeX generation failed: {exc}") from exc
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

    filename = f"resume.{_EXTENSIONS[format]}"
    return Response(
        content=content,
        media_type=_CONTENT_TYPES[format],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
