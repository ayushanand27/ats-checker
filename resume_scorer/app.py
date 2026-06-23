"""ResumeMatch — Streamlit entrypoint: ATS scoring, AI rewrite, multi-format export."""

from __future__ import annotations

import os
from typing import Any, Optional

import streamlit as st
from dotenv import load_dotenv

from parser import extract_text, validate_extracted_text
from structurer import structure_jd_or_none, structure_resume
from scoring.deterministic import score_deterministic
from scoring.semantic_match import score_semantic_match
from insights.llm_rewriter import get_rewrite_suggestions
from renderers.docx_renderer import render_docx
from renderers.pdf_renderer import render_pdf
from renderers.tex_renderer import render_tex

load_dotenv()

# --- Score composition constants ---
LAYER1_WEIGHT_WITH_JD = 0.35
LAYER2_WEIGHT_WITH_JD = 0.65
LAYER1_WEIGHT_NO_JD = 1.0

TEMPLATE_OPTIONS = {
    "Jack's Tech Resume": "jacks_tech",
    "Classic Non-Tech Resume": "classic_nontech",
}

st.set_page_config(
    page_title="ResumeMatch",
    page_icon="📄",
    layout="wide",
)


@st.cache_resource(show_spinner="Loading semantic model (first run may download ~90MB)…")
def load_embedding_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")


def _score_color(score: float) -> str:
    if score >= 75:
        return "#27ae60"
    if score >= 50:
        return "#f39c12"
    return "#e74c3c"


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
        "resume_text": "",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _render_score_section() -> None:
    score = st.session_state.core_score or 0
    jd_provided = st.session_state.jd_provided
    color = _score_color(score)

    label = "ATS Match Score" if jd_provided else "General ATS Score"
    st.markdown(
        f"<div style='text-align:center;padding:20px;'>"
        f"<span style='font-size:14px;color:#666;'>{label}</span><br>"
        f"<span style='font-size:72px;font-weight:bold;color:{color};'>{score}</span>"
        f"<span style='font-size:24px;color:#999;'>/100</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    if not jd_provided:
        st.info(
            "General ATS check — add a job description for a tailored match score "
            f"(Layer 1 only, {int(LAYER1_WEIGHT_NO_JD * 100)}% weight)."
        )

    l1 = st.session_state.layer1_result
    l2 = st.session_state.layer2_result

    with st.expander("Score breakdown", expanded=True):
        if l1:
            st.subheader(f"Layer 1 — Structure & Hygiene: {l1['score']}/100")
            for check in l1["checks"]:
                icon = "✅" if check["passed"] else "❌"
                st.markdown(f"{icon} **{check['name']}** — {check['reason']}")

        if jd_provided and l2:
            st.subheader(f"Layer 2 — Skill Match: {l2['score']}/100")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Matched required skills**")
                if l2["matched_required"]:
                    st.write(", ".join(l2["matched_required"]))
                else:
                    st.write("_None_")
            with col2:
                st.markdown("**Missing required skills**")
                if l2["missing_required"]:
                    st.error(", ".join(l2["missing_required"]))
                else:
                    st.success("All required skills matched!")
            if l2.get("matched_preferred"):
                st.markdown(f"**Matched preferred:** {', '.join(l2['matched_preferred'])}")
            if l2.get("missing_preferred"):
                st.markdown(f"**Missing preferred:** {', '.join(l2['missing_preferred'])}")
            if l2.get("experience_note"):
                st.warning(l2["experience_note"])


def _render_ai_section() -> None:
    st.subheader("AI Rewrite Suggestions")
    groq_key = os.getenv("GROQ_API_KEY")

    if not groq_key:
        st.warning(
            "GROQ_API_KEY is not configured. Core ATS scoring works without it. "
            "Add your key to `.env` to enable AI suggestions."
        )
        return

    if st.button("Get AI Suggestions", type="primary", key="btn_ai"):
        with st.spinner("Generating rewrite suggestions (one API call)…"):
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

    st.success("Suggestions ready — review before generating downloads.")

    if rewritten.get("change_log"):
        st.markdown("**What changed**")
        for item in rewritten["change_log"]:
            st.markdown(f"- {item}")

    original = st.session_state.resume_struct
    col_before, col_after = st.columns(2)

    with col_before:
        st.markdown("#### Before")
        st.markdown("**Summary**")
        st.write(original.get("summary") or "_No summary detected_")
        st.markdown("**Skills**")
        st.write(", ".join(original.get("skills", [])) or "_None detected_")
        if original.get("experience"):
            st.markdown("**Experience (first role)**")
            exp0 = original["experience"][0]
            st.write(f"{exp0.get('title', '')} @ {exp0.get('company', '')}")
            for b in exp0.get("bullets", [])[:3]:
                st.markdown(f"- {b}")

    with col_after:
        st.markdown("#### After (AI suggested)")
        st.markdown("**Summary**")
        st.write(rewritten.get("summary", ""))
        st.markdown("**Skills**")
        st.write(", ".join(rewritten.get("skills", [])))
        if rewritten.get("experience"):
            st.markdown("**Experience (first role)**")
            exp0 = rewritten["experience"][0]
            st.write(f"{exp0.get('title', '')} @ {exp0.get('company', '')}")
            for b in exp0.get("bullets", [])[:3]:
                st.markdown(f"- {b}")


def _render_generate_section() -> None:
    st.subheader("Generate Resume")
    st.caption(
        "Uses AI suggestions if available; otherwise exports your parsed resume content. "
        "All formats are rendered deterministically from the same JSON — no extra API calls."
    )

    fmt_pdf = st.checkbox("PDF", value=True, key="fmt_pdf")
    fmt_docx = st.checkbox("DOCX", value=True, key="fmt_docx")
    fmt_tex = st.checkbox("TeX (LaTeX source)", value=False, key="fmt_tex")

    if not (fmt_pdf or fmt_docx or fmt_tex):
        st.info("Select at least one output format.")
        return

    if st.button("Generate Resume", type="secondary", key="btn_generate"):
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

    dl_cols = st.columns(3)
    if st.session_state.get("dl_pdf"):
        dl_cols[0].download_button(
            "Download PDF",
            st.session_state["dl_pdf"],
            file_name="resume.pdf",
            mime="application/pdf",
            key="download_pdf",
        )
    if st.session_state.get("dl_docx"):
        dl_cols[1].download_button(
            "Download DOCX",
            st.session_state["dl_docx"],
            file_name="resume.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="download_docx",
        )
    if st.session_state.get("dl_tex"):
        dl_cols[2].download_button(
            "Download TeX",
            st.session_state["dl_tex"],
            file_name="resume.tex",
            mime="application/x-tex",
            key="download_tex",
        )


def main() -> None:
    _init_session_state()

    st.title("ResumeMatch")
    st.caption("ATS scorer · AI rewriter · Multi-format resume generator")

    # --- Input section ---
    st.header("1. Upload & Configure")
    resume_file = st.file_uploader(
        "Upload resume (.pdf, .docx, .txt)",
        type=["pdf", "docx", "txt"],
        key="resume_upload",
    )

    st.markdown("**Job description** _(optional — enables tailored skill matching)_")
    jd_tab_paste, jd_tab_upload = st.tabs(["Paste text", "Upload file"])
    jd_text = ""
    jd_file = None
    with jd_tab_paste:
        jd_text = st.text_area("Paste job description", height=150, key="jd_paste")
    with jd_tab_upload:
        jd_file = st.file_uploader(
            "Upload JD (.pdf, .docx, .txt)",
            type=["pdf", "docx", "txt"],
            key="jd_upload",
        )

    template_choice = st.radio(
        "Resume template",
        list(TEMPLATE_OPTIONS.keys()) + ["Upload Custom Template (coming soon)"],
        horizontal=True,
    )
    if template_choice == "Upload Custom Template (coming soon)":
        st.caption("Custom template upload is planned for a future release.")
        template_choice = "Jack's Tech Resume"

    st.session_state.template_key = TEMPLATE_OPTIONS.get(
        template_choice, "jacks_tech"
    )

    if st.button("Analyze", type="primary", key="btn_analyze"):
        if not resume_file:
            st.error("Please upload a resume first.")
        else:
            try:
                resume_raw = extract_text(resume_file.read(), resume_file.name)
                warn = validate_extracted_text(resume_raw)
                if warn:
                    st.warning(warn)

                jd_raw = jd_text.strip() if jd_text else ""
                if jd_file and not jd_raw:
                    jd_raw = extract_text(jd_file.read(), jd_file.name)

                resume_struct = structure_resume(resume_raw)
                jd_struct = structure_jd_or_none(jd_raw)
                jd_provided = jd_struct is not None

                layer1 = score_deterministic(resume_struct, jd_struct)
                layer2 = None
                if jd_provided and jd_struct:
                    model = load_embedding_model()
                    layer2 = score_semantic_match(resume_struct, jd_struct, model)

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
        st.info("Upload a resume and click **Analyze** to see your ATS score.")
        st.markdown("---")
        st.caption(
            "ATS Compatibility Score is fully deterministic, based on the same parsing/"
            "keyword-matching approach real ATS systems use. AI rewrite suggestions are "
            "optional, reviewed by you before use, and the AI is instructed never to "
            "fabricate experience or metrics. This tool is independent and not affiliated "
            "with any company's actual ATS system."
        )
        return

    # --- Results ---
    st.header("2. ATS Score")
    _render_score_section()

    st.header("3. AI Suggestions (Optional)")
    _render_ai_section()

    st.header("4. Download")
    _render_generate_section()

    st.markdown("---")
    st.caption(
        "ATS Compatibility Score is fully deterministic, based on the same parsing/"
        "keyword-matching approach real ATS systems use. AI rewrite suggestions are "
        "optional, reviewed by you before use, and the AI is instructed never to "
        "fabricate experience or metrics. This tool is independent and not affiliated "
        "with any company's actual ATS system."
    )


if __name__ == "__main__":
    main()
