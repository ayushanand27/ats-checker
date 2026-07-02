"""Quality gates and progress for the resume-builder chat interview."""

from __future__ import annotations

from typing import Any


def _contact(draft: dict[str, Any]) -> dict[str, Any]:
    return draft.get("contact") or {}


def _word_count(text: str) -> int:
    return len((text or "").split())


def _exp_bullet_count(draft: dict[str, Any]) -> int:
    total = 0
    for exp in draft.get("experience") or []:
        total += len([b for b in (exp.get("bullets") or []) if str(b).strip()])
    return total


def _project_bullet_count(draft: dict[str, Any]) -> int:
    total = 0
    for proj in draft.get("projects") or []:
        total += len([b for b in (proj.get("bullets") or []) if str(b).strip()])
    return total


def interview_checklist(draft: dict[str, Any]) -> list[tuple[str, bool, str]]:
    """Return (key, done, hint) tuples for interview progress."""
    contact = _contact(draft)
    summary = (draft.get("summary") or "").strip()
    skills = [s for s in (draft.get("skills") or []) if str(s).strip()]
    education = draft.get("education") or []
    experience = draft.get("experience") or []
    projects = draft.get("projects") or []
    exp_bullets = _exp_bullet_count(draft)
    proj_bullets = _project_bullet_count(draft)

    edu_ok = any((e.get("degree") or "").strip() and (e.get("institution") or "").strip() for e in education)
    exp_ok = len(experience) >= 1 and exp_bullets >= 3
    if len(experience) >= 2:
        exp_ok = exp_bullets >= 4

    proj_ok = len(projects) >= 2 or (len(projects) >= 1 and proj_bullets >= 3)

    return [
        ("name", bool((draft.get("name") or "").strip()), "full legal name"),
        ("location", bool((contact.get("location") or "").strip()), "city and state/country"),
        ("phone", bool((contact.get("phone") or "").strip()), "phone number"),
        ("email", bool((contact.get("email") or "").strip()), "email address"),
        (
            "links",
            bool((contact.get("linkedin") or "").strip() or (contact.get("github") or "").strip()),
            "LinkedIn or GitHub URL",
        ),
        (
            "summary",
            _word_count(summary) >= 45,
            "3–4 sentence professional summary tailored to the JD (degree, strengths, role fit)",
        ),
        ("education", edu_ok, "degree, university, CGPA/GPA if available, graduation date"),
        ("skills", len(skills) >= 10, "at least 10 relevant skills/tools"),
        (
            "experience",
            exp_ok,
            "each role with title, company, location, dates, and 3+ impact bullets with tech/metrics",
        ),
        (
            "projects",
            proj_ok,
            "at least 2 projects (or 1 with 3 bullets) with tech stack and GitHub links",
        ),
    ]


def compute_interview_progress(draft: dict[str, Any]) -> int:
    checklist = interview_checklist(draft)
    done = sum(1 for _, ok, _ in checklist if ok)
    return int(round(done / len(checklist) * 100))


def is_interview_complete(draft: dict[str, Any]) -> bool:
    return all(ok for _, ok, _ in interview_checklist(draft))


def missing_interview_items(draft: dict[str, Any]) -> list[str]:
    return [hint for _, ok, hint in interview_checklist(draft) if not ok]


def quality_hints_for_llm(draft: dict[str, Any]) -> str:
    missing = missing_interview_items(draft)
    progress = compute_interview_progress(draft)
    exp_bullets = _exp_bullet_count(draft)
    proj_count = len(draft.get("projects") or [])

    lines = [
        f"Interview progress (server-computed): {progress}%",
        f"Experience bullets collected: {exp_bullets}",
        f"Projects collected: {proj_count}",
    ]
    if missing:
        lines.append("Still needed before completion: " + "; ".join(missing))
    else:
        lines.append("All quality gates passed — you may set is_complete=true on the next turn if the user confirms.")
    return "\n".join(lines)
