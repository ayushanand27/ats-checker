"""Normalize chat-built or partial resume dicts for scoring and export."""

from __future__ import annotations

from typing import Any


def _bullet_lines(experience: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for entry in experience:
        title = (entry.get("title") or "").strip()
        company = (entry.get("company") or "").strip()
        location = (entry.get("location") or "").strip()
        dates = (entry.get("dates") or "").strip()
        header_parts = [p for p in [title, company] if p]
        header = " — ".join(header_parts)
        if location:
            header = f"{header} ({location})" if header else location
        if dates:
            header = f"{header}  {dates}" if header else dates
        if header:
            lines.append(header)
        for bullet in entry.get("bullets") or []:
            text = str(bullet).strip()
            if text:
                lines.append(f"• {text}")
    return lines


def _estimate_experience_years(experience: list[dict[str, Any]]) -> float:
    """Rough years estimate from date strings like '2022 - Present' or 'Jun 2020 - Aug 2022'."""
    import re

    total = 0.0
    year_re = re.compile(r"(20\d{2}|19\d{2})")
    for entry in experience:
        dates = entry.get("dates") or ""
        years = [int(y) for y in year_re.findall(str(dates))]
        if len(years) >= 2:
            total += max(years[-1] - years[0], 0)
        elif len(years) == 1:
            total += 1.0
    return round(total, 1)


def _flatten_skills(draft: dict[str, Any]) -> list[str]:
    flat = [str(s).strip() for s in (draft.get("skills") or []) if str(s).strip()]
    categories = draft.get("skill_categories") or {}
    if isinstance(categories, dict):
        for items in categories.values():
            if isinstance(items, list):
                flat.extend(str(s).strip() for s in items if str(s).strip())
    # Preserve order, dedupe case-insensitively
    seen: set[str] = set()
    out: list[str] = []
    for skill in flat:
        key = skill.lower()
        if key not in seen:
            seen.add(key)
            out.append(skill)
    return out


def resume_struct_to_text(resume: dict[str, Any]) -> str:
    """Build plain-text resume from structured fields (for word count / parse checks)."""
    parts: list[str] = []

    name = (resume.get("name") or "").strip()
    if name:
        parts.append(name)

    contact = resume.get("contact") or {}
    contact_bits = [
        contact.get("location"),
        contact.get("phone"),
        contact.get("email"),
        contact.get("linkedin"),
        contact.get("github"),
        contact.get("leetcode"),
        contact.get("portfolio"),
    ]
    contact_line = " | ".join(str(c).strip() for c in contact_bits if c)
    if contact_line:
        parts.append(contact_line)

    summary = (resume.get("summary") or "").strip()
    if summary:
        parts.extend(["", "SUMMARY", summary])

    skills = _flatten_skills(resume)
    categories = resume.get("skill_categories") or {}
    if isinstance(categories, dict) and any(categories.values()):
        parts.extend(["", "TECHNICAL SKILLS"])
        for label, items in categories.items():
            if items:
                parts.append(f"{label.replace('_', ' ').title()}: {', '.join(items)}")
    elif skills:
        parts.extend(["", "SKILLS", ", ".join(skills)])

    experience = resume.get("experience") or []
    if experience:
        parts.extend(["", "EXPERIENCE", *_bullet_lines(experience)])

    education = resume.get("education") or []
    if education:
        parts.append("")
        parts.append("EDUCATION")
        for edu in education:
            degree = (edu.get("degree") or "").strip()
            institution = (edu.get("institution") or "").strip()
            gpa = (edu.get("gpa") or "").strip()
            location = (edu.get("location") or "").strip()
            dates = (edu.get("dates") or "").strip()
            line = degree
            if gpa:
                line = f"{line} | CGPA: {gpa}" if line else f"CGPA: {gpa}"
            if institution:
                line = f"{line}, {institution}" if line else institution
            if location:
                line = f"{line}, {location}" if line else location
            if dates:
                line = f"{line} ({dates})" if line else dates
            if line:
                parts.append(line)

    projects = resume.get("projects") or []
    if projects:
        parts.append("")
        parts.append("PROJECTS")
        for proj in projects:
            name_p = (proj.get("name") or "").strip()
            tech = (proj.get("tech_stack") or proj.get("description") or "").strip()
            link = (proj.get("link") or "").strip()
            header = name_p
            if tech:
                header = f"{header} | {tech}" if header else tech
            if link:
                header = f"{header} | {link}" if header else link
            if header:
                parts.append(header)
            for bullet in proj.get("bullets") or []:
                text = str(bullet).strip()
                if text:
                    parts.append(f"• {text}")

    achievements = resume.get("achievements") or []
    if achievements:
        parts.append("")
        parts.append("ACHIEVEMENTS & RECOGNITION")
        for item in achievements:
            text = str(item).strip()
            if text:
                parts.append(f"• {text}")

    return "\n".join(parts).strip()


def normalize_resume_struct(draft: dict[str, Any]) -> dict[str, Any]:
    """Fill sections_found, raw_text, metrics, and experience_years for API scoring."""
    experience = [e for e in (draft.get("experience") or []) if isinstance(e, dict)]
    education = [e for e in (draft.get("education") or []) if isinstance(e, dict)]
    projects = [p for p in (draft.get("projects") or []) if isinstance(p, dict)]
    achievements = [str(a).strip() for a in (draft.get("achievements") or []) if str(a).strip()]
    skills = _flatten_skills(draft)

    sections: list[str] = []
    if (draft.get("summary") or "").strip():
        sections.append("summary")
    if skills:
        sections.append("skills")
    if experience:
        sections.append("experience")
    if education:
        sections.append("education")
    if projects:
        sections.append("projects")

    total_bullets = 0
    bullets_with_metrics = 0
    import re

    metric_re = re.compile(r"\d")
    for entry in experience:
        for bullet in entry.get("bullets") or []:
            text = str(bullet).strip()
            if not text:
                continue
            total_bullets += 1
            if metric_re.search(text):
                bullets_with_metrics += 1
    for proj in projects:
        for bullet in proj.get("bullets") or []:
            text = str(bullet).strip()
            if not text:
                continue
            total_bullets += 1
            if metric_re.search(text):
                bullets_with_metrics += 1

    normalized = {
        **draft,
        "contact": draft.get("contact") or {},
        "skills": skills,
        "experience": experience,
        "education": education,
        "projects": projects,
        "achievements": achievements,
        "sections_found": sections,
        "experience_years": _estimate_experience_years(experience),
        "metrics": {
            "total_bullets": total_bullets,
            "bullets_with_metrics": bullets_with_metrics,
        },
    }
    normalized["raw_text"] = resume_struct_to_text(normalized)
    return normalized


def empty_resume_draft() -> dict[str, Any]:
    return {
        "name": "",
        "contact": {
            "email": None,
            "phone": None,
            "location": None,
            "linkedin": None,
            "github": None,
            "leetcode": None,
            "portfolio": None,
        },
        "summary": "",
        "skills": [],
        "skill_categories": {
            "languages": [],
            "frameworks": [],
            "tools": [],
            "other": [],
        },
        "experience": [],
        "education": [],
        "projects": [],
        "achievements": [],
    }
