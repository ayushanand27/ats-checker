"""Groq-powered conversational resume builder tailored to a job description."""

from __future__ import annotations

import json
import os
from typing import Any, Optional

from groq import Groq

from insights.interview_quality import (
    compute_interview_progress,
    is_interview_complete,
    quality_hints_for_llm,
)
from insights.resume_normalize import empty_resume_draft, normalize_resume_struct
from structurer import structure_jd

GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are an expert resume coach conducting a THOROUGH, professional interview to build an industry-standard ATS resume (comparable to top intern/new-grad tech resumes).

STYLE:
- Ask exactly ONE focused question per turn.
- Be warm but professional. Briefly acknowledge the user's last answer before asking the next question.
- Tailor every question to the job description — reference required skills, analytics tools, or responsibilities when relevant.
- This interview typically takes 18–30 questions. Do NOT rush to completion.

TRUTHFULNESS — NEVER VIOLATE:
- Record ONLY facts the user explicitly stated. Never invent companies, dates, metrics, credentials, or projects.
- When writing bullets in the draft, use strong action verbs and ONLY metrics/technologies the user provided.
- If the user gives a vague answer, ask a follow-up for specifics (tech stack, team size, outcome numbers) before adding a bullet.

BULLET QUALITY (when updating draft from user answers):
- Transform raw answers into resume bullets: "Verb + what you did + tech/tool + outcome/impact".
- Example input: "I built dashboards in Power BI for recruiting data"
  → bullet: "Built Power BI dashboards for recruiting data, enabling faster hiring decisions across APAC TA."
- Ask for numbers when missing: users, %, time saved, test pass rate, leaderboard rank, etc.

INTERVIEW FLOW — follow this order, one question at a time:

PHASE 1 — HEADER (questions 1–7):
1. Full name
2. City and state/country (for resume header)
3. Phone number
4. Email address
5. LinkedIn profile URL
6. GitHub profile URL
7. LeetCode, portfolio, or other link (user may skip)

PHASE 2 — EDUCATION (questions 8–9):
8. Degree, major/specialization, university name
9. CGPA/GPA (if applicable), expected graduation month/year, university location

PHASE 3 — SUMMARY (questions 10–11):
10. Ask user to describe why they're a strong fit for THIS role — degree, standout strengths, relevant tools
11. If summary in draft is under 45 words, ask one more targeted question (hackathons, certifications, domain exposure) then write a 3–4 sentence summary aligned to the JD

PHASE 4 — SKILLS (questions 12–14):
12. Programming languages and scripting tools they use
13. Frameworks, libraries, cloud, databases relevant to the JD
14. Analytics/ML/business tools (Excel, SQL, Power BI, Salesforce, etc.) — merge all into skills list (aim for 10–20 items)

PHASE 5 — EXPERIENCE (repeat per role, 4–6 questions each):
For each internship/job:
  a) Job title and company name
  b) Location (Remote/City) and start–end dates
  c) "What was your biggest technical or analytical achievement? Include tools used and any measurable result."
  d) "What was another significant contribution? (different project or responsibility)"
  e) "Any third bullet — leadership, testing, deployment, or cross-team work?"
  f) "Do you have another role to add? (yes/no)"
Aim for 3–4 bullets per role. Top resumes have 6–10 experience bullets total.

PHASE 6 — PROJECTS (repeat per project, 3–4 questions each):
For each project (aim for at least 2 projects):
  a) Project name, one-line purpose, and tech stack
  b) GitHub or demo link
  c) Key engineering/analytical achievement with metrics
  d) "Another highlight or second project to add?"
Each project should have 1–3 bullets in the draft.

PHASE 7 — ACHIEVEMENTS (questions 25–27):
- Certifications (CCNA, Trailhead, cloud badges, etc.)
- Hackathon wins, awards, publications, patents, Dean's list
- Add to achievements[] list

COMPLETION:
- Set is_complete=true ONLY when ALL quality gates are met AND you ask "Ready to finalize?" and user confirms OR server hints say all gates passed.
- Minimum bar: full contact header, 45+ word summary, education with dates, 10+ skills, 3+ experience bullets across role(s), 2 projects (or 1 with 3 bullets).

Return ONLY valid JSON:
{
  "assistant_message": "your reply with exactly one question (or completion message)",
  "draft": {
    "name": "",
    "contact": {
      "email": null, "phone": null, "location": null,
      "linkedin": null, "github": null, "leetcode": null, "portfolio": null
    },
    "summary": "",
    "skills": [],
    "skill_categories": {
      "languages": [], "frameworks": [], "tools": [], "other": []
    },
    "experience": [{"title": "", "company": "", "location": "", "dates": "", "bullets": []}],
    "education": [{"degree": "", "institution": "", "location": "", "dates": "", "gpa": ""}],
    "projects": [{"name": "", "description": "", "tech_stack": "", "link": "", "bullets": []}],
    "achievements": []
  },
  "is_complete": false,
  "progress_percent": 0
}
"""


def _parse_json_response(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [ln for ln in lines if not ln.strip().startswith("```")]
        cleaned = "\n".join(lines)
    return json.loads(cleaned)


def _jd_context(jd_text: str) -> str:
    jd_struct = structure_jd(jd_text)
    return json.dumps(
        {
            "title": jd_struct.get("title"),
            "required_skills": jd_struct.get("required_skills", []),
            "preferred_skills": jd_struct.get("preferred_skills", []),
            "min_experience_years": jd_struct.get("min_experience_years"),
        },
        indent=2,
    )


def _merge_draft(current: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    base = empty_resume_draft()
    merged = {**base, **current, **incoming}
    merged["contact"] = {**base["contact"], **(current.get("contact") or {}), **(incoming.get("contact") or {})}
    # Prefer longer summary / richer lists from incoming when provided
    if not (incoming.get("summary") or "").strip() and (current.get("summary") or "").strip():
        merged["summary"] = current["summary"]
    for key in ("skills", "experience", "education", "projects", "achievements"):
        if not incoming.get(key) and current.get(key):
            merged[key] = current[key]
    return merged


def resume_chat_turn(
    jd_text: str,
    messages: list[dict[str, str]],
    draft: Optional[dict[str, Any]] = None,
    user_message: Optional[str] = None,
    api_key: Optional[str] = None,
) -> dict[str, Any]:
    """
    One chat turn. Pass user_message=None with empty messages to start the interview.
    Returns assistant_message, updated draft, is_complete, progress_percent, and messages.
    """
    key = api_key or os.getenv("GROQ_API_KEY")
    if not key:
        raise ValueError("GROQ_API_KEY is not configured")

    jd_text = (jd_text or "").strip()
    if not jd_text:
        raise ValueError("Job description text is required for resume chat")

    current_draft = draft if draft else empty_resume_draft()
    client = Groq(api_key=key)

    groq_messages: list[dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "system",
            "content": (
                f"JOB DESCRIPTION (raw):\n{jd_text}\n\n"
                f"EXTRACTED JD FIELDS:\n{_jd_context(jd_text)}"
            ),
        },
        {
            "role": "system",
            "content": (
                f"CURRENT DRAFT RESUME:\n{json.dumps(current_draft, indent=2)}\n\n"
                f"QUALITY STATUS:\n{quality_hints_for_llm(current_draft)}"
            ),
        },
    ]

    history = list(messages)
    if user_message:
        history = history + [{"role": "user", "content": user_message.strip()}]

    for msg in history:
        if msg.get("role") in ("user", "assistant") and msg.get("content"):
            groq_messages.append({"role": msg["role"], "content": msg["content"]})

    if not history:
        groq_messages.append(
            {
                "role": "user",
                "content": (
                    "Start the thorough resume interview for this role. Greet me briefly, "
                    "explain we'll build a detailed industry-standard resume step by step, "
                    "and ask your first question (full name)."
                ),
            }
        )

    last_error: Exception | None = None
    for _attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=groq_messages,
                response_format={"type": "json_object"},
                temperature=0.35,
                max_tokens=4096,
            )
            content = response.choices[0].message.content or ""
            parsed = _parse_json_response(content)

            assistant_message = (parsed.get("assistant_message") or "").strip()
            if not assistant_message:
                raise json.JSONDecodeError("Missing assistant_message", content, 0)

            merged_draft = _merge_draft(current_draft, parsed.get("draft") or {})
            normalized = normalize_resume_struct(merged_draft)

            updated_messages = list(messages)
            if user_message:
                updated_messages.append({"role": "user", "content": user_message.strip()})
            updated_messages.append({"role": "assistant", "content": assistant_message})

            progress = compute_interview_progress(normalized)
            llm_complete = bool(parsed.get("is_complete"))
            user_confirmed = (user_message or "").strip().lower() in {
                "yes", "yes finalize", "finalize", "done", "complete", "looks good", "confirm",
            }
            is_complete = is_interview_complete(normalized) and (llm_complete or user_confirmed)

            return {
                "message": assistant_message,
                "messages": updated_messages,
                "draft": normalized,
                "is_complete": is_complete,
                "progress_percent": progress,
            }
        except json.JSONDecodeError as exc:
            last_error = exc
        except Exception as exc:
            raise RuntimeError(f"Groq API error: {exc}") from exc

    raise RuntimeError(f"Failed to parse chat JSON after retry: {last_error}")
