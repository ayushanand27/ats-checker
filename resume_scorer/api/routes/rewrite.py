"""Rewrite endpoint — optional Groq-powered resume suggestions."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.schemas import RewriteRequest, RewriteResponse
from insights.llm_rewriter import get_rewrite_suggestions

router = APIRouter()


@router.post("/rewrite", response_model=RewriteResponse)
async def rewrite(body: RewriteRequest) -> RewriteResponse:
    gaps = body.gaps.model_dump()
    try:
        result = get_rewrite_suggestions(
            body.resume_struct,
            body.jd_struct,
            gaps,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return RewriteResponse(**result)
