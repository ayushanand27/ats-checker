"""User master-profile, JD auto-tailoring, and analysis history."""

from __future__ import annotations

import os
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException

from api import db
from api.analysis import run_analysis
from api.auth import get_current_user
from api.deps import VALID_TEMPLATES
from api.schemas import (
    HistoryDetailResponse,
    HistoryItem,
    HistoryListResponse,
    ProfileRequest,
    ProfileResponse,
    TailorRequest,
    TailorResponse,
)
from insights.llm_rewriter import get_rewrite_suggestions

router = APIRouter()


def _merge_rewrite(original: dict[str, Any], rewritten: dict[str, Any]) -> dict[str, Any]:
    """Merge AI rewrite fields into the master profile (mirrors frontend mergeRewrite)."""
    merged = dict(original)
    if rewritten.get("summary"):
        merged["summary"] = rewritten["summary"]
    if rewritten.get("skills"):
        merged["skills"] = rewritten["skills"]
    if rewritten.get("experience"):
        merged["experience"] = rewritten["experience"]
    if rewritten.get("education"):
        merged["education"] = rewritten["education"]
    if rewritten.get("projects"):
        merged["projects"] = rewritten["projects"]
    return merged


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(user: dict = Depends(get_current_user)) -> ProfileResponse:
    saved = db.get_profile(user["id"])
    if not saved:
        return ProfileResponse(profile=None, updated_at=None)
    return ProfileResponse(profile=saved["profile"], updated_at=saved["updated_at"])


@router.put("/profile", response_model=ProfileResponse)
async def save_profile(
    body: ProfileRequest, user: dict = Depends(get_current_user)
) -> ProfileResponse:
    if not body.profile:
        raise HTTPException(status_code=400, detail="Profile data is required.")
    db.upsert_profile(user["id"], body.profile)
    saved = db.get_profile(user["id"])
    return ProfileResponse(profile=saved["profile"], updated_at=saved["updated_at"])


@router.post("/profile/tailor", response_model=TailorResponse)
async def tailor_profile(
    body: TailorRequest, user: dict = Depends(get_current_user)
) -> TailorResponse:
    if body.template not in VALID_TEMPLATES:
        raise HTTPException(status_code=400, detail=f"Invalid template: {body.template}")

    saved = db.get_profile(user["id"])
    if not saved or not saved.get("profile"):
        raise HTTPException(
            status_code=400,
            detail="No saved profile yet. Save your master profile before tailoring.",
        )

    master = saved["profile"]
    jd_text = (body.jd_text or "").strip() or None

    base = run_analysis(
        resume_struct=master,
        jd_raw=jd_text,
        template=body.template,
        parse_warning=None,
    )

    tailored_resume = master
    rewrite_result = None
    ai_used = False
    final = base

    can_ai = body.use_ai and bool(os.getenv("GROQ_API_KEY", "").strip()) and jd_text
    if can_ai:
        try:
            rewrite_result = get_rewrite_suggestions(
                master,
                base.jd_struct,
                base.gaps.model_dump(),
                trace_user_id=str(user["id"]),
                trace_session_id=f"tailor-{user['id']}",
            )
            tailored_resume = _merge_rewrite(master, rewrite_result)
            final = run_analysis(
                resume_struct=tailored_resume,
                jd_raw=jd_text,
                template=body.template,
                parse_warning="Auto-tailored from your saved profile — review before exporting.",
            )
            ai_used = True
        except (ValueError, RuntimeError):
            # Fall back to non-AI prefill if Groq unavailable/fails.
            tailored_resume = master
            rewrite_result = None
            final = base
            ai_used = False

    analysis_id: Optional[int] = None
    if body.save:
        jd_title = None
        if final.jd_struct:
            jd_title = final.jd_struct.get("title")
        analysis_id = db.save_analysis(
            user_id=user["id"],
            jd_title=jd_title,
            jd_text=jd_text,
            core_score=final.core_score,
            result=final.model_dump(),
        )

    return TailorResponse(
        analysis=final,
        rewrite=rewrite_result,
        tailored_resume=tailored_resume,
        analysis_id=analysis_id,
        ai_used=ai_used,
    )


@router.get("/history", response_model=HistoryListResponse)
async def list_history(user: dict = Depends(get_current_user)) -> HistoryListResponse:
    items = db.list_analyses(user["id"])
    return HistoryListResponse(items=[HistoryItem(**it) for it in items])


@router.get("/history/{analysis_id}", response_model=HistoryDetailResponse)
async def get_history_item(
    analysis_id: int, user: dict = Depends(get_current_user)
) -> HistoryDetailResponse:
    item = db.get_analysis(user["id"], analysis_id)
    if not item:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return HistoryDetailResponse(
        id=item["id"],
        jd_title=item.get("jd_title"),
        jd_text=item.get("jd_text"),
        core_score=item.get("core_score"),
        created_at=item["created_at"],
        result=item["result"],
    )


@router.delete("/history/{analysis_id}")
async def delete_history_item(
    analysis_id: int, user: dict = Depends(get_current_user)
) -> dict[str, bool]:
    deleted = db.delete_analysis(user["id"], analysis_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return {"deleted": True}
