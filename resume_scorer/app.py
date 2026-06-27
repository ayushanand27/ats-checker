"""ResumeMatch — Streamlit entrypoint: ATS scoring, AI rewrite, multi-format export."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import streamlit as st
from dotenv import load_dotenv

from parser import extract_text, validate_extracted_text
from structurer import structure_jd_or_none, structure_resume
from scoring.deterministic import score_deterministic
from scoring.semantic_match import score_semantic_match
from insights.llm_rewriter import get_rewrite_suggestions
from renderers.docx_renderer import render_docx
from renderers.custom_docx_renderer import render_custom_docx
from renderers.pdf_renderer import pdf_export_available, render_pdf
from renderers.tex_renderer import render_tex
from ui.components import (
    render_ai_ready_banner,
    render_before_after,
    render_change_log,
    render_check_grid,
    render_empty_state,
    render_feature_sidebar,
    render_footer,
    render_hero,
    render_layer_header,
    render_score_gauge,
    render_skill_pills,
    render_step_header,
    render_trust_badges,
)
from ui.theme import inject_global_styles

load_dotenv()

# --- Score composition constants ---
LAYER1_WEIGHT_WITH_JD = 0.35
LAYER2_WEIGHT_WITH_JD = 0.65
LAYER1_WEIGHT_NO_JD = 1.0

TEMPLATE_OPTIONS = {
    "Jack's Tech Resume": "jacks_tech",
    "Classic Non-Tech Resume": "classic_nontech",
}
CUSTOM_TEMPLATE_LABEL = "Upload Custom Template"
STARTER_TEMPLATE_PATH = (
    Path(__file__).parent / "templates" / "custom_starter" / "starter_template.docx"
)

st.set_page_config(
    page_title="ResumeMatch — ATS Scorer & Resume Generator",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource(show_spinner="Loading semantic model (first run may download ~90MB)…")
def load_embedding_model():
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception as exc:
        raise RuntimeError(
            "Could not load the local embedding model (sentence-transformers). "
            "This is usually a torch/torchvision version mismatch. "
            "In the project folder run: pip install -r requirements.txt "
            "(pins torch==2.6.0 and torchvision==0.21.0). "
            "Using a virtual environment is strongly recommended on Windows. "
            f"Original error: {exc}"
        ) from exc


def _compose_score(layer1: float, layer2: Optional[float], jd_provided: bool) -> float:
    if jd_provided and layer2 is not None:
        return round(
            layer1 * LAYER1_WEIGHT_WITH_JD + layer2 * LAYER2_WEIGHT_WITH_JD,
            1,
        )
    return round(layer1 * LAYER1_WEIGHT_NO_JD, 1)


def _merge_for_render(
    original: dict[str, Any],
    rewritten: Optional[dict[str, Any]],
) -> dict[str, Any]:
    """Build render payload: AI rewrite content + original contact/name."""
    if not rewritten:
        return original
    return {
        "name": original.get("name", ""),
        "contact": original.get("contact", {}),
        "summary": rewritten.get("summary", original.get("summary", "")),
        "skills": rewritten.get("skills", original.get("skills", [])),
        "experience": rewritten.get("experience", original.get("experience", [])),
        "education": rewritten.get("education", original.get("education", [])),
        "projects": rewritten.get("projects", original.get("projects", [])),
    }


def _init_session_state() -> None:
    defaults = {
        "analyzed": False,
        "resume_struct": None,
        "jd_struct": None,
        "layer1_result": None,
        "layer2_result": None,
        "core_score": None,
        "jd_provided": False,
        "rewrite_result": None,
        "template_key": "jacks_tech",
        "is_custom_template": False,
        "custom_template_bytes": None,
        "resume_text": "",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _render_score_section() -> None:
    score = st.session_state.core_score or 0
    jd_provided = st.session_state.jd_provided

    label = "ATS Match Score" if jd_provided else "General ATS Score"
    hint = ""
    if not jd_provided:
        hint = (
            f"General ATS check — add a job description for tailored skill matching "
            f"(Layer 1 only, {int(LAYER1_WEIGHT_NO_JD * 100)}% weight)."
        )

    col_gauge, col_meta = st.columns([1, 1])
    with col_gauge:
        render_score_gauge(score, label, hint)

    l1 = st.session_state.layer1_result
    l2 = st.session_state.layer2_result

    with col_meta:
        if l1:
            passed = sum(1 for c in l1["checks"] if c["passed"])
            total = len(l1["checks"])
            st.metric("Structure checks passed", f"{passed}/{total}")
        if jd_provided and l2:
            matched = len(l2.get("matched_required", []))
            missing = len(l2.get("missing_required", []))
            st.metric("Required skills matched", f"{matched} matched · {missing} gaps")

    with st.expander("Detailed score breakdown", expanded=False):
        if l1:
            render_layer_header(
                "Layer 1 — Structure & Hygiene",
                l1["score"],
                "Deterministic",
            )
            render_check_grid(l1["checks"])

        if jd_provided and l2:
            render_layer_header(
                "Layer 2 — Skill Match",
                l2["score"],
                "Semantic",
            )
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(
                    "<p style='font-weight:600;font-size:0.85rem;margin:0.5rem 0;'>"
                    "Matched required skills</p>",
                    unsafe_allow_html=True,
                )
                render_skill_pills(l2.get("matched_required", []), "matched")
            with col2:
                st.markdown(
                    "<p style='font-weight:600;font-size:0.85rem;margin:0.5rem 0;'>"
                    "Missing required skills</p>",
                    unsafe_allow_html=True,
                )
                render_skill_pills(l2.get("missing_required", []), "missing")
            if l2.get("matched_preferred"):
                st.markdown(
                    "<p style='font-weight:600;font-size:0.85rem;margin:0.75rem 0 0.35rem 0;'>"
                    "Matched preferred</p>",
                    unsafe_allow_html=True,
                )
                render_skill_pills(l2["matched_preferred"], "preferred")
            if l2.get("missing_preferred"):
                st.markdown(
                    "<p style='font-weight:600;font-size:0.85rem;margin:0.75rem 0 0.35rem 0;'>"
                    "Missing preferred</p>",
                    unsafe_allow_html=True,
                )
                render_skill_pills(l2["missing_preferred"], "missing")
            if l2.get("experience_note"):
                st.warning(l2["experience_note"])


def _render_ai_section() -> None:
    groq_key = os.getenv("GROQ_API_KEY")

    if not groq_key:
        st.warning(
            "**AI suggestions unavailable** — add `GROQ_API_KEY` to your `.env` file. "
            "Core ATS scoring works without it."
        )
        return

    st.markdown(
        "<p style='color:#64748b;font-size:0.88rem;margin-bottom:1rem;'>"
        "Optional one-shot rewrite powered by Groq. You review every change before export — "
        "the AI is instructed never to fabricate experience or metrics.</p>",
        unsafe_allow_html=True,
    )

    if st.button("Get AI Suggestions", type="primary", key="btn_ai", use_container_width=False):
        with st.spinner("Generating rewrite suggestions…"):
            try:
                gaps: dict[str, Any] = {}
                l2 = st.session_state.layer2_result
                if l2:
                    gaps = {
                        "missing_required": l2.get("missing_required", []),
                        "missing_preferred": l2.get("missing_preferred", []),
                        "experience_note": l2.get("experience_note"),
                    }
                result = get_rewrite_suggestions(
                    st.session_state.resume_struct,
                    st.session_state.jd_struct,
                    gaps,
                )
                st.session_state.rewrite_result = result
            except ValueError as exc:
                st.error(str(exc))
            except RuntimeError as exc:
                st.error(f"AI suggestion failed: {exc}")

    rewritten = st.session_state.rewrite_result
    if not rewritten:
        return

    render_ai_ready_banner()
    render_change_log(rewritten.get("change_log", []))
    render_before_after(st.session_state.resume_struct, rewritten)


def _render_generate_section() -> None:
    st.markdown(
        "<p style='color:#64748b;font-size:0.88rem;margin-bottom:0.75rem;'>"
        "Uses AI suggestions if available; otherwise exports your parsed resume. "
        "All formats rendered deterministically from the same JSON — no extra API calls.</p>",
        unsafe_allow_html=True,
    )

    is_custom = st.session_state.get("is_custom_template", False)

    if is_custom:
        st.info(
            "Custom templates support **DOCX only**. "
            "PDF/TeX are available for built-in templates."
        )
        fmt_docx = True
        fmt_pdf = False
        fmt_tex = False
    else:
        pdf_ok, pdf_err = pdf_export_available()
        if pdf_ok:
            fmt_pdf = st.checkbox("PDF", value=True, key="fmt_pdf")
        else:
            fmt_pdf = False
            st.warning(pdf_err or "PDF export is unavailable on this system.")
        fmt_docx = st.checkbox("DOCX", value=True, key="fmt_docx")
        fmt_tex = st.checkbox("TeX (LaTeX source)", value=False, key="fmt_tex")

    if not (fmt_pdf or fmt_docx or fmt_tex):
        st.info("Select at least one output format.")
        return

    if is_custom and not st.session_state.get("custom_template_bytes"):
        st.warning("Upload a custom .docx template above before generating.")
        return

    if st.button("Generate Resume", type="primary", key="btn_generate"):
        payload = _merge_for_render(
            st.session_state.resume_struct,
            st.session_state.rewrite_result,
        )
        template = st.session_state.template_key

        if fmt_pdf:
            try:
                pdf_bytes = render_pdf(payload, template)
                st.session_state["dl_pdf"] = pdf_bytes
            except Exception as exc:
                st.session_state.pop("dl_pdf", None)
                st.error(f"PDF generation failed: {exc}")

        if fmt_docx:
            try:
                if is_custom:
                    docx_bytes, tpl_error = render_custom_docx(
                        st.session_state.custom_template_bytes,
                        payload,
                    )
                    if tpl_error:
                        st.session_state.pop("dl_docx", None)
                        st.error(tpl_error)
                    else:
                        st.session_state["dl_docx"] = docx_bytes
                else:
                    docx_bytes = render_docx(payload, template)
                    st.session_state["dl_docx"] = docx_bytes
            except Exception as exc:
                st.session_state.pop("dl_docx", None)
                st.error(f"DOCX generation failed: {exc}")

        if fmt_tex:
            try:
                tex_str = render_tex(payload, template)
                st.session_state["dl_tex"] = tex_str.encode("utf-8")
            except Exception as exc:
                st.session_state.pop("dl_tex", None)
                st.error(f"TeX generation failed: {exc}")

    has_downloads = any(
        st.session_state.get(k) for k in ("dl_pdf", "dl_docx", "dl_tex")
    )
    if has_downloads:
        st.markdown(
            "<p style='font-weight:600;font-size:0.9rem;margin:1.25rem 0 0.5rem 0;'>"
            "Your files are ready</p>",
            unsafe_allow_html=True,
        )

    dl_cols = st.columns(3)
    if st.session_state.get("dl_pdf"):
        dl_cols[0].download_button(
            "⬇ Download PDF",
            st.session_state["dl_pdf"],
            file_name="resume.pdf",
            mime="application/pdf",
            key="download_pdf",
            use_container_width=True,
        )
    if st.session_state.get("dl_docx"):
        dl_cols[1].download_button(
            "⬇ Download DOCX",
            st.session_state["dl_docx"],
            file_name="resume.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="download_docx",
            use_container_width=True,
        )
    if st.session_state.get("dl_tex"):
        dl_cols[2].download_button(
            "⬇ Download TeX",
            st.session_state["dl_tex"],
            file_name="resume.tex",
            mime="application/x-tex",
            key="download_tex",
            use_container_width=True,
        )


def main() -> None:
    _init_session_state()
    inject_global_styles()
    render_feature_sidebar()
    render_hero()

    # --- Step 1: Upload ---
    render_step_header(
        1,
        "Upload & Configure",
        "Resume required · Job description optional for tailored matching",
    )

    col_resume, col_jd = st.columns(2)
    with col_resume:
        st.markdown("**Resume**")
        resume_file = st.file_uploader(
            "PDF, DOCX, or TXT",
            type=["pdf", "docx", "txt"],
            key="resume_upload",
            label_visibility="collapsed",
        )
    with col_jd:
        st.markdown("**Job description** _(optional)_")
        jd_tab_paste, jd_tab_upload = st.tabs(["Paste", "Upload"])
        jd_text = ""
        jd_file = None
        with jd_tab_paste:
            jd_text = st.text_area(
                "Paste JD",
                height=140,
                key="jd_paste",
                label_visibility="collapsed",
                placeholder="Paste the full job description here for skill-gap analysis…",
            )
        with jd_tab_upload:
            jd_file = st.file_uploader(
                "Upload JD",
                type=["pdf", "docx", "txt"],
                key="jd_upload",
                label_visibility="collapsed",
            )

    st.markdown("**Output template**")
    template_choice = st.radio(
        "Template",
        list(TEMPLATE_OPTIONS.keys()) + [CUSTOM_TEMPLATE_LABEL],
        horizontal=True,
        label_visibility="collapsed",
    )

    is_custom = template_choice == CUSTOM_TEMPLATE_LABEL
    st.session_state.is_custom_template = is_custom

    if is_custom:
        st.session_state.template_key = "custom"
        tpl_col, dl_col = st.columns([3, 1])
        with tpl_col:
            custom_tpl_file = st.file_uploader(
                "Custom .docx template (Jinja2 placeholders)",
                type=["docx"],
                key="custom_template_upload",
            )
            if custom_tpl_file is not None:
                st.session_state.custom_template_bytes = custom_tpl_file.read()
        with dl_col:
            if STARTER_TEMPLATE_PATH.is_file():
                st.download_button(
                    "Starter template",
                    data=STARTER_TEMPLATE_PATH.read_bytes(),
                    file_name="resume_starter_template.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="download_starter_template",
                    use_container_width=True,
                )
    else:
        st.session_state.template_key = TEMPLATE_OPTIONS.get(
            template_choice, "jacks_tech"
        )
        st.session_state.custom_template_bytes = None

    render_trust_badges()

    analyze_col, _ = st.columns([1, 3])
    with analyze_col:
        analyze_clicked = st.button(
            "Analyze Resume",
            type="primary",
            key="btn_analyze",
            use_container_width=True,
        )

    if analyze_clicked:
        if not resume_file:
            st.error("Please upload a resume first.")
        else:
            try:
                resume_bytes = resume_file.read()
                resume_raw = extract_text(resume_bytes, resume_file.name)
                warn = validate_extracted_text(resume_raw)
                if warn:
                    st.warning(warn)

                jd_raw = jd_text.strip() if jd_text else ""
                if jd_file and not jd_raw:
                    jd_raw = extract_text(jd_file.read(), jd_file.name)

                pdf_bytes = resume_bytes if resume_file.name.lower().endswith(".pdf") else None
                resume_struct = structure_resume(resume_raw, pdf_bytes=pdf_bytes)
                jd_struct = structure_jd_or_none(jd_raw)
                jd_provided = jd_struct is not None

                layer1 = score_deterministic(resume_struct, jd_struct)
                layer2 = None
                if jd_provided and jd_struct:
                    try:
                        model = load_embedding_model()
                        layer2 = score_semantic_match(resume_struct, jd_struct, model)
                    except RuntimeError as exc:
                        st.warning(
                            f"Layer 2 (skill match) skipped — Layer 1 score still valid. {exc}"
                        )

                core = _compose_score(
                    layer1["score"],
                    layer2["score"] if layer2 else None,
                    jd_provided,
                )

                st.session_state.analyzed = True
                st.session_state.resume_struct = resume_struct
                st.session_state.jd_struct = jd_struct
                st.session_state.layer1_result = layer1
                st.session_state.layer2_result = layer2
                st.session_state.core_score = core
                st.session_state.jd_provided = jd_provided
                st.session_state.resume_text = resume_raw
                st.session_state.rewrite_result = None
                st.session_state.pop("dl_pdf", None)
                st.session_state.pop("dl_docx", None)
                st.session_state.pop("dl_tex", None)
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")

    if not st.session_state.analyzed:
        render_empty_state()
        render_footer()
        return

    st.markdown("<hr style='border:none;border-top:1px solid #e2e8f0;margin:2rem 0;'>", unsafe_allow_html=True)

    render_step_header(2, "ATS Score", "Two-layer analysis — structure + skill alignment")
    _render_score_section()

    st.markdown("<hr style='border:none;border-top:1px solid #e2e8f0;margin:2rem 0;'>", unsafe_allow_html=True)

    render_step_header(3, "AI Suggestions", "Optional — review every change before export")
    _render_ai_section()

    st.markdown("<hr style='border:none;border-top:1px solid #e2e8f0;margin:2rem 0;'>", unsafe_allow_html=True)

    render_step_header(4, "Download", "Generate polished resume files")
    _render_generate_section()

    render_footer()


if __name__ == "__main__":
    main()
