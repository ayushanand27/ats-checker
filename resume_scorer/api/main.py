"""FastAPI application entrypoint for ResumeMatch."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import analyze, chat, generate, rewrite, utility
from api.schemas import HealthResponse

load_dotenv()


def _cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if raw:
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    return ["http://localhost:3000"]


CORS_ORIGINS = _cors_origins()

app = FastAPI(
    title="ResumeMatch API",
    description="REST API for ATS scoring, AI rewrite, and resume generation",
    version="1.0.1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router, prefix="/api", tags=["analyze"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(utility.router, prefix="/api", tags=["utility"])
app.include_router(rewrite.router, prefix="/api", tags=["rewrite"])
app.include_router(generate.router, prefix="/api", tags=["generate"])


@app.get("/api/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok")
