"""Utility endpoints for the ResumeMatch API."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from api.jd_fetch import fetch_jd_from_url
from api.schemas import JdUrlRequest, JdUrlResponse
from parser import extract_text

router = APIRouter()


@router.post("/jd/extract")
async def extract_jd_text(jd_file: UploadFile = File(...)) -> dict[str, str]:
    if not jd_file.filename:
        raise HTTPException(status_code=400, detail="JD filename is required")
    jd_bytes = await jd_file.read()
    if not jd_bytes:
        raise HTTPException(status_code=400, detail="JD file is empty")
    try:
        text = extract_text(jd_bytes, jd_file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"text": text}


@router.post("/jd/fetch", response_model=JdUrlResponse)
async def fetch_jd_url(body: JdUrlRequest) -> JdUrlResponse:
    try:
        text = fetch_jd_from_url(body.url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return JdUrlResponse(text=text)
