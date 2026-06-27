"""Pydantic request/response models for the ResumeMatch API."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


TemplateChoice = Literal["jacks_tech", "classic_nontech", "custom"]
OutputFormat = Literal["docx", "pdf", "tex"]


class ScoreGaps(BaseModel):
    missing_required: list[str] = Field(default_factory=list)
    missing_preferred: list[str] = Field(default_factory=list)
    experience_note: Optional[str] = None


class Layer1Result(BaseModel):
    score: float
    checks: list[dict[str, Any]]
    word_count: int


class Layer2Result(BaseModel):
    score: float
    matched_required: list[str]
    missing_required: list[str]
    matched_preferred: list[str]
    missing_preferred: list[str]
    experience_note: Optional[str] = None


class AnalyzeResponse(BaseModel):
    core_score: float
    jd_provided: bool
    template: TemplateChoice
    parse_warning: Optional[str] = None
    resume_struct: dict[str, Any]
    jd_struct: Optional[dict[str, Any]] = None
    layer1: Layer1Result
    layer2: Optional[Layer2Result] = None
    gaps: ScoreGaps


class RewriteRequest(BaseModel):
    resume_struct: dict[str, Any]
    jd_struct: Optional[dict[str, Any]] = None
    gaps: ScoreGaps = Field(default_factory=ScoreGaps)


class RewriteResponse(BaseModel):
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    experience: list[dict[str, Any]] = Field(default_factory=list)
    education: list[dict[str, Any]] = Field(default_factory=list)
    projects: list[dict[str, Any]] = Field(default_factory=list)
    change_log: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str = "ok"


class ErrorResponse(BaseModel):
    detail: str
