"""Resume builder chat — Groq-powered JD-tailored interview."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.schemas import ChatMessage, ResumeChatRequest, ResumeChatResponse
from insights.resume_chat import resume_chat_turn

router = APIRouter()


@router.post("/chat/resume", response_model=ResumeChatResponse)
async def resume_chat(body: ResumeChatRequest) -> ResumeChatResponse:
    messages = [m.model_dump() for m in body.messages]
    try:
        result = resume_chat_turn(
            jd_text=body.jd_text,
            messages=messages,
            draft=body.draft,
            user_message=body.user_message,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ResumeChatResponse(
        message=result["message"],
        messages=[ChatMessage(**m) for m in result["messages"]],
        draft=result["draft"],
        is_complete=result["is_complete"],
        progress_percent=result["progress_percent"],
    )
