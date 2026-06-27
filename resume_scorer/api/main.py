"""FastAPI application entrypoint for ResumeMatch."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import analyze, generate, rewrite
from api.schemas import HealthResponse

load_dotenv()

# Extend this list when deploying the Next.js frontend to production.
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

_extra_origins = os.getenv("CORS_ORIGINS", "")
if _extra_origins:
    CORS_ORIGINS.extend(o.strip() for o in _extra_origins.split(",") if o.strip())

app = FastAPI(
    title="ResumeMatch API",
    description="REST API for ATS scoring, AI rewrite, and resume generation",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router, prefix="/api", tags=["analyze"])
app.include_router(rewrite.router, prefix="/api", tags=["rewrite"])
app.include_router(generate.router, prefix="/api", tags=["generate"])


@app.get("/api/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok")
