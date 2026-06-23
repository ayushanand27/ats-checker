"""Single optional Groq call — returns rewritten resume content as JSON."""

from __future__ import annotations

import json
import os
from typing import Any, Optional

from groq import Groq

GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are an expert resume writer focused on ATS optimization.

Your task: rewrite resume content to better match a job description while staying truthful.

HARD RULES — NEVER VIOLATE:
- Do NOT fabricate any factual claim, number, or credential not present in the source resume.
- Do NOT invent metrics, companies, dates, job titles, or experience that wasn't in the original.
- Only rephrase, reorganize, and surface existing JD-relevant keywords where truthfully applicable.
- If a metric doesn't exist in the source, do not add one — rephrase for impact without numbers instead.

Return ONLY valid JSON matching this exact schema:
{
  "summary": "rewritten 2-3 line professional summary",
  "skills": ["ordered skill list"],
  "experience": [
    {"title": "...", "company": "...", "dates": "...", "bullets": ["..."]}
  ],
  "education": [{"degree": "...", "institution": "...", "dates": "..."}],
  "projects": [{"name": "...", "description": "...", "bullets": ["..."]}],
  "change_log": ["short string per change made"]
}
"""


def _build_user_prompt(
    resume: dict[str, Any],
    jd: Optional[dict[str, Any]],
    gaps: dict[str, Any],
) -> str:
    resume_json = json.dumps({
        "summary": resume.get("summary", ""),
        "skills": resume.get("skills", []),
        "experience": resume.get("experience", []),
        "education": resume.get("education", []),
        "projects": resume.get("projects", []),
    }, indent=2)

    gap_lines = []
    if gaps.get("missing_required"):
        gap_lines.append(f"Missing required skills: {', '.join(gaps['missing_required'])}")
    if gaps.get("missing_preferred"):
        gap_lines.append(f"Missing preferred skills: {', '.join(gaps['missing_preferred'])}")
    if gaps.get("experience_note"):
        gap_lines.append(gaps["experience_note"])

    if jd:
        jd_json = json.dumps({
            "title": jd.get("title", ""),
            "required_skills": jd.get("required_skills", []),
            "preferred_skills": jd.get("preferred_skills", []),
        }, indent=2)
        instruction = (
            "Rewrite the resume to better align with this job description. "
            "Incorporate JD keywords only where they truthfully apply to the candidate's background."
        )
        return (
            f"{instruction}\n\n"
            f"## Job Description\n{jd_json}\n\n"
            f"## Current Resume\n{resume_json}\n\n"
            f"## Identified Gaps\n" + "\n".join(gap_lines or ["None identified"])
        )

    return (
        "Rewrite this resume to be more ATS-friendly using general best practices "
        "(clear summary, strong action verbs, keyword-rich skills, quantified bullets where metrics already exist).\n\n"
        f"## Current Resume\n{resume_json}\n\n"
        f"## Notes\n" + "\n".join(gap_lines or ["General ATS optimization requested"])
    )


def _parse_json_response(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [ln for ln in lines if not ln.strip().startswith("```")]
        cleaned = "\n".join(lines)
    return json.loads(cleaned)


def get_rewrite_suggestions(
    resume: dict[str, Any],
    jd: Optional[dict[str, Any]],
    gaps: dict[str, Any],
    api_key: Optional[str] = None,
) -> dict[str, Any]:
    """
    Single Groq API call returning structured rewritten resume JSON.
    Raises ValueError if no API key; raises RuntimeError on API/parse failure.
    """
    key = api_key or os.getenv("GROQ_API_KEY")
    if not key:
        raise ValueError("GROQ_API_KEY is not configured")

    client = Groq(api_key=key)
    user_prompt = _build_user_prompt(resume, jd, gaps)

    last_error: Exception | None = None
    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=4096,
            )
            content = response.choices[0].message.content or ""
            return _parse_json_response(content)
        except json.JSONDecodeError as exc:
            last_error = exc
        except Exception as exc:
            raise RuntimeError(f"Groq API error: {exc}") from exc

    raise RuntimeError(f"Failed to parse LLM JSON response after retry: {last_error}")
