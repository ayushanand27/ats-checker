"""HTML component builders for ResumeMatch UI."""

from __future__ import annotations

import html
from typing import Any, Optional

import streamlit as st

from ui.theme import COLORS, score_color, score_label


def _esc(text: str) -> str:
    return html.escape(str(text))


def render_hero() -> None:
    st.markdown(
        """
        <div class="rm-hero">
            <div class="rm-hero-badge">Professional ATS Suite</div>
            <h1>ResumeMatch</h1>
            <p>
                Score your resume against any job description, get AI-powered rewrite
                suggestions, and export polished PDF, DOCX, or LaTeX — the same workflow
                recruiters and career coaches charge hundreds for.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_feature_sidebar() -> None:
    with st.sidebar:
        st.markdown("### ResumeMatch")
        st.markdown(
            "<span style='color:#94a3b8;font-size:0.85rem;'>"
            "Enterprise-grade ATS analysis</span>",
            unsafe_allow_html=True,
        )
        st.markdown("---")
        st.markdown(
            """
            <div class="rm-sidebar-stat">
                <strong>2-Layer Scoring</strong>
                <span>Structure checks + semantic skill match</span>
            </div>
            <div class="rm-sidebar-stat">
                <strong>Zero-LLM Core</strong>
                <span>Deterministic ATS score — works offline</span>
            </div>
            <div class="rm-sidebar-stat">
                <strong>AI Rewrite</strong>
                <span>One optional Groq call, you review first</span>
            </div>
            <div class="rm-sidebar-stat">
                <strong>Multi-Format</strong>
                <span>PDF · DOCX · TeX from one source</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("---")
        st.markdown(
            "<span style='color:#64748b;font-size:0.75rem;'>"
            "v1.0 · Independent tool · Not affiliated with any employer ATS</span>",
            unsafe_allow_html=True,
        )


def render_step_header(step: int, title: str, subtitle: str = "") -> None:
    sub_html = f'<p class="rm-step-sub">{_esc(subtitle)}</p>' if subtitle else ""
    st.markdown(
        f"""
        <div class="rm-step">
            <div class="rm-step-num">{step}</div>
            <div>
                <p class="rm-step-title">{_esc(title)}</p>
                {sub_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_score_gauge(
    score: float,
    label: str,
    hint: str = "",
) -> None:
    color = score_color(score)
    verdict = score_label(score)
    circumference = 2 * 3.14159 * 78
    offset = circumference - (score / 100) * circumference
    hint_html = f'<p class="rm-score-hint">{_esc(hint)}</p>' if hint else ""
    st.markdown(
        f"""
        <div class="rm-score-wrap">
            <div class="rm-score-ring">
                <svg width="180" height="180" viewBox="0 0 180 180">
                    <circle cx="90" cy="90" r="78" fill="none" stroke="#e2e8f0" stroke-width="12"/>
                    <circle cx="90" cy="90" r="78" fill="none" stroke="{color}" stroke-width="12"
                        stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"
                        stroke-linecap="round"/>
                </svg>
                <div class="rm-score-center">
                    <span class="rm-score-value" style="color:{color}">{score:.1f}</span>
                    <span class="rm-score-max">/ 100</span>
                </div>
            </div>
            <p class="rm-score-label">{_esc(label)} — {_esc(verdict)}</p>
            {hint_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_check_grid(checks: list[dict[str, Any]]) -> None:
    items = []
    for check in checks:
        passed = check.get("passed", False)
        css = "pass" if passed else "fail"
        icon = "✓" if passed else "✗"
        items.append(
            f"""
            <div class="rm-check-item {css}">
                <span class="rm-check-icon">{icon}</span>
                <div>
                    <div class="rm-check-name">{_esc(check.get('name', ''))}</div>
                    <div class="rm-check-reason">{_esc(check.get('reason', ''))}</div>
                </div>
            </div>
            """
        )
    st.markdown(
        f'<div class="rm-check-grid">{"".join(items)}</div>',
        unsafe_allow_html=True,
    )


def render_skill_pills(skills: list[str], variant: str = "matched") -> None:
    if not skills:
        st.markdown(
            f'<p style="color:{COLORS["text_muted"]};font-size:0.85rem;margin:0;">None</p>',
            unsafe_allow_html=True,
        )
        return
    pills = "".join(
        f'<span class="rm-pill {variant}">{_esc(s)}</span>' for s in skills
    )
    st.markdown(f'<div class="rm-pills">{pills}</div>', unsafe_allow_html=True)


def render_layer_header(title: str, score: float, layer_badge: str) -> None:
    color = score_color(score)
    st.markdown(
        f"""
        <p style="font-size:1.05rem;font-weight:700;color:{COLORS['text']};margin:1rem 0 0.5rem 0;">
            {_esc(title)}
            <span class="rm-layer-badge">{_esc(layer_badge)}</span>
            <span style="color:{color};margin-left:0.5rem;">{score}/100</span>
        </p>
        """,
        unsafe_allow_html=True,
    )


def _compare_block(header_class: str, header_text: str, body_html: str) -> str:
    return f"""
    <div class="rm-compare">
        <div class="rm-compare-header {header_class}">{_esc(header_text)}</div>
        <div class="rm-compare-body">{body_html}</div>
    </div>
    """


def _format_compare_content(data: dict[str, Any], is_rewrite: bool = False) -> str:
    parts = []
    summary = data.get("summary") or "_No summary detected_"
    parts.append(f"<h5>Summary</h5><p>{_esc(summary)}</p>")

    skills = data.get("skills", [])
    skills_text = ", ".join(skills) if skills else "_None detected_"
    parts.append(f"<h5>Skills</h5><p>{_esc(skills_text)}</p>")

    experience = data.get("experience", [])
    if experience:
        exp0 = experience[0]
        title = exp0.get("title", "")
        company = exp0.get("company", "")
        parts.append(f"<h5>Experience (first role)</h5><p><strong>{_esc(title)}</strong> @ {_esc(company)}</p>")
        bullets = exp0.get("bullets", [])[:3]
        if bullets:
            bullet_html = "".join(f"<li>{_esc(b)}</li>" for b in bullets)
            parts.append(f"<ul style='margin:0.35rem 0 0 1rem;padding:0;'>{bullet_html}</ul>")

    return "".join(parts)


def render_before_after(original: dict[str, Any], rewritten: dict[str, Any]) -> None:
    before_html = _format_compare_content(original)
    after_html = _format_compare_content(rewritten, is_rewrite=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(_compare_block("before", "Before", before_html), unsafe_allow_html=True)
    with col2:
        st.markdown(_compare_block("after", "After — AI suggested", after_html), unsafe_allow_html=True)


def render_empty_state() -> None:
    st.markdown(
        """
        <div class="rm-empty">
            <div class="rm-empty-icon">📋</div>
            <h3>Upload your resume to get started</h3>
            <p>Add an optional job description for a tailored match score and skill gap analysis.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_trust_badges() -> None:
    st.markdown(
        """
        <div class="rm-trust">
            <span class="rm-trust-item">🔒 No data stored on server</span>
            <span class="rm-trust-item">⚡ Instant deterministic scoring</span>
            <span class="rm-trust-item">🤖 AI never fabricates experience</span>
            <span class="rm-trust-item">📄 Export-ready templates</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown(
        """
        <div class="rm-footer">
            <strong>Disclaimer:</strong> ATS Compatibility Score is fully deterministic, based on
            parsing and keyword-matching approaches similar to real ATS systems. AI rewrite
            suggestions are optional, reviewed by you before use, and instructed never to fabricate
            experience or metrics. This tool is independent and not affiliated with any company's
            actual ATS system.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_change_log(items: list[str]) -> None:
    if not items:
        return
    rows = "".join(
        f'<li style="margin-bottom:0.35rem;color:{COLORS["text"]};font-size:0.88rem;">'
        f'{_esc(item)}</li>'
        for item in items
    )
    st.markdown(
        f"""
        <div class="rm-card" style="margin-bottom:1rem;">
            <p style="font-weight:700;margin:0 0 0.5rem 0;font-size:0.9rem;">What changed</p>
            <ul style="margin:0;padding-left:1.2rem;">{rows}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_ai_ready_banner() -> None:
    st.markdown(
        f"""
        <div style="background:{COLORS['success_soft']};border:1px solid #6ee7b7;
            border-radius:12px;padding:0.85rem 1.1rem;margin-bottom:1rem;">
            <span style="color:#047857;font-weight:600;font-size:0.9rem;">
                ✓ Suggestions ready — review before generating downloads
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_format_cards(pdf: bool, docx: bool, tex: bool) -> None:
    """Visual format selector labels (checkboxes remain in app logic)."""
    formats = []
    if pdf:
        formats.append(("PDF", "Print-ready, ATS-friendly"))
    if docx:
        formats.append(("DOCX", "Editable in Word"))
    if tex:
        formats.append(("TeX", "LaTeX source for Overleaf"))
    if not formats:
        return
    cards = ""
    for name, desc in formats:
        cards += f"""
        <div style="flex:1;min-width:120px;background:#f8fafc;border:1px solid #e2e8f0;
            border-radius:10px;padding:0.75rem 1rem;text-align:center;">
            <div style="font-weight:700;font-size:0.95rem;color:#0f172a;">{_esc(name)}</div>
            <div style="font-size:0.72rem;color:#64748b;margin-top:0.2rem;">{_esc(desc)}</div>
        </div>
        """
    st.markdown(
        f'<div style="display:flex;gap:0.65rem;flex-wrap:wrap;margin:0.5rem 0;">{cards}</div>',
        unsafe_allow_html=True,
    )
