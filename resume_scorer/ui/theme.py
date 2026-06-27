"""Design tokens and global CSS for ResumeMatch."""

from __future__ import annotations

import streamlit as st

# --- Design tokens ---
COLORS = {
    "bg": "#f1f5f9",
    "surface": "#ffffff",
    "surface_alt": "#f8fafc",
    "border": "#e2e8f0",
    "text": "#0f172a",
    "text_muted": "#64748b",
    "text_light": "#94a3b8",
    "primary": "#2563eb",
    "primary_dark": "#1d4ed8",
    "primary_soft": "#dbeafe",
    "success": "#059669",
    "success_soft": "#d1fae5",
    "warning": "#d97706",
    "warning_soft": "#fef3c7",
    "danger": "#dc2626",
    "danger_soft": "#fee2e2",
    "accent": "#0d9488",
}

GOOGLE_FONTS = (
    "https://fonts.googleapis.com/css2?"
    "family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap"
)


def score_color(score: float) -> str:
    if score >= 75:
        return COLORS["success"]
    if score >= 50:
        return COLORS["warning"]
    return COLORS["danger"]


def score_label(score: float) -> str:
    if score >= 85:
        return "Excellent match"
    if score >= 75:
        return "Strong match"
    if score >= 60:
        return "Good — room to improve"
    if score >= 45:
        return "Needs optimization"
    return "Low compatibility"


def inject_global_styles() -> None:
    """Inject premium SaaS styling over Streamlit defaults."""
    c = COLORS
    st.markdown(
        f"""
        <link rel="stylesheet" href="{GOOGLE_FONTS}">
        <style>
        @import url('{GOOGLE_FONTS}');

        :root {{
            --rm-bg: {c['bg']};
            --rm-surface: {c['surface']};
            --rm-border: {c['border']};
            --rm-text: {c['text']};
            --rm-muted: {c['text_muted']};
            --rm-primary: {c['primary']};
            --rm-primary-soft: {c['primary_soft']};
        }}

        .stApp {{
            background: linear-gradient(180deg, #eef2ff 0%, {c['bg']} 220px, {c['bg']} 100%);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }}

        .main .block-container {{
            padding-top: 1.5rem;
            padding-bottom: 3rem;
            max-width: 1120px;
        }}

        h1, h2, h3, h4, h5, h6, p, label, .stMarkdown {{
            font-family: 'Inter', sans-serif !important;
        }}

        /* Hide default Streamlit chrome for cleaner product feel */
        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}
        header[data-testid="stHeader"] {{
            background: transparent;
            border-bottom: none;
        }}

        /* Primary buttons */
        .stButton > button[kind="primary"],
        .stButton > button[data-testid="baseButton-primary"] {{
            background: linear-gradient(135deg, {c['primary']} 0%, {c['primary_dark']} 100%);
            border: none;
            border-radius: 10px;
            font-weight: 600;
            padding: 0.55rem 1.25rem;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.28);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }}
        .stButton > button[kind="primary"]:hover {{
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(37, 99, 235, 0.35);
        }}

        .stButton > button[kind="secondary"] {{
            border-radius: 10px;
            border: 1px solid {c['border']};
            font-weight: 600;
        }}

        /* File uploader */
        [data-testid="stFileUploader"] section {{
            border: 1.5px dashed {c['border']};
            border-radius: 14px;
            background: {c['surface']};
            padding: 0.5rem;
        }}
        [data-testid="stFileUploader"] section:hover {{
            border-color: {c['primary']};
            background: {c['primary_soft']}22;
        }}

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
            background: transparent;
        }}
        .stTabs [data-baseweb="tab"] {{
            border-radius: 8px;
            font-weight: 600;
            padding: 8px 16px;
        }}

        /* Expanders */
        .streamlit-expanderHeader {{
            font-weight: 600;
            border-radius: 10px;
        }}

        /* Sidebar */
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
        }}
        [data-testid="stSidebar"] * {{
            color: #e2e8f0 !important;
        }}
        [data-testid="stSidebar"] .stMarkdown h3 {{
            color: #f8fafc !important;
        }}

        /* Radio horizontal */
        .stRadio > div {{
            gap: 0.5rem;
        }}

        /* Download buttons */
        .stDownloadButton > button {{
            border-radius: 10px;
            font-weight: 600;
            width: 100%;
        }}

        /* Custom component classes */
        .rm-hero {{
            background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #1d4ed8 100%);
            border-radius: 20px;
            padding: 2rem 2.25rem;
            margin-bottom: 1.75rem;
            color: #f8fafc;
            box-shadow: 0 20px 50px rgba(15, 23, 42, 0.18);
            position: relative;
            overflow: hidden;
        }}
        .rm-hero::before {{
            content: '';
            position: absolute;
            top: -40%;
            right: -10%;
            width: 320px;
            height: 320px;
            background: radial-gradient(circle, rgba(59,130,246,0.35) 0%, transparent 70%);
            pointer-events: none;
        }}
        .rm-hero-badge {{
            display: inline-block;
            background: rgba(255,255,255,0.12);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 999px;
            padding: 0.25rem 0.75rem;
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin-bottom: 0.75rem;
        }}
        .rm-hero h1 {{
            font-size: 2rem !important;
            font-weight: 800 !important;
            margin: 0 0 0.35rem 0 !important;
            color: #fff !important;
            letter-spacing: -0.03em;
        }}
        .rm-hero p {{
            color: #cbd5e1 !important;
            font-size: 1.02rem;
            margin: 0;
            max-width: 640px;
            line-height: 1.55;
        }}

        .rm-step {{
            display: flex;
            align-items: flex-start;
            gap: 1rem;
            margin: 1.75rem 0 1rem 0;
        }}
        .rm-step-num {{
            flex-shrink: 0;
            width: 36px;
            height: 36px;
            border-radius: 10px;
            background: {c['primary']};
            color: #fff;
            font-weight: 700;
            font-size: 0.95rem;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 12px rgba(37,99,235,0.3);
        }}
        .rm-step-title {{
            font-size: 1.35rem;
            font-weight: 700;
            color: {c['text']};
            margin: 0;
            letter-spacing: -0.02em;
        }}
        .rm-step-sub {{
            font-size: 0.88rem;
            color: {c['text_muted']};
            margin: 0.15rem 0 0 0;
        }}

        .rm-card {{
            background: {c['surface']};
            border: 1px solid {c['border']};
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(15,23,42,0.04);
        }}

        .rm-score-wrap {{
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 1rem 0;
        }}
        .rm-score-ring {{
            position: relative;
            width: 180px;
            height: 180px;
        }}
        .rm-score-ring svg {{
            transform: rotate(-90deg);
        }}
        .rm-score-center {{
            position: absolute;
            inset: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }}
        .rm-score-value {{
            font-size: 2.75rem;
            font-weight: 800;
            line-height: 1;
            letter-spacing: -0.04em;
        }}
        .rm-score-max {{
            font-size: 0.95rem;
            color: {c['text_light']};
            font-weight: 500;
        }}
        .rm-score-label {{
            margin-top: 1rem;
            font-size: 1.05rem;
            font-weight: 600;
            color: {c['text']};
        }}
        .rm-score-hint {{
            font-size: 0.82rem;
            color: {c['text_muted']};
            margin-top: 0.25rem;
            text-align: center;
            max-width: 360px;
        }}

        .rm-check-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 0.75rem;
            margin-top: 0.5rem;
        }}
        .rm-check-item {{
            display: flex;
            gap: 0.65rem;
            align-items: flex-start;
            padding: 0.85rem 1rem;
            border-radius: 12px;
            border: 1px solid {c['border']};
            background: {c['surface_alt']};
        }}
        .rm-check-item.pass {{
            border-color: #a7f3d0;
            background: {c['success_soft']}55;
        }}
        .rm-check-item.fail {{
            border-color: #fecaca;
            background: {c['danger_soft']}55;
        }}
        .rm-check-icon {{
            font-size: 1rem;
            line-height: 1.4;
        }}
        .rm-check-name {{
            font-weight: 600;
            font-size: 0.88rem;
            color: {c['text']};
        }}
        .rm-check-reason {{
            font-size: 0.78rem;
            color: {c['text_muted']};
            margin-top: 0.1rem;
        }}

        .rm-pills {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
            margin: 0.35rem 0;
        }}
        .rm-pill {{
            display: inline-block;
            padding: 0.28rem 0.65rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 500;
        }}
        .rm-pill.matched {{
            background: {c['success_soft']};
            color: #047857;
            border: 1px solid #6ee7b7;
        }}
        .rm-pill.missing {{
            background: {c['danger_soft']};
            color: #b91c1c;
            border: 1px solid #fca5a5;
        }}
        .rm-pill.preferred {{
            background: {c['primary_soft']};
            color: #1d4ed8;
            border: 1px solid #93c5fd;
        }}

        .rm-compare {{
            border: 1px solid {c['border']};
            border-radius: 14px;
            overflow: hidden;
        }}
        .rm-compare-header {{
            padding: 0.65rem 1rem;
            font-weight: 700;
            font-size: 0.85rem;
            letter-spacing: 0.02em;
        }}
        .rm-compare-header.before {{
            background: #f1f5f9;
            color: {c['text_muted']};
            border-bottom: 1px solid {c['border']};
        }}
        .rm-compare-header.after {{
            background: linear-gradient(90deg, {c['primary_soft']}, #eff6ff);
            color: {c['primary_dark']};
            border-bottom: 1px solid #bfdbfe;
        }}
        .rm-compare-body {{
            padding: 1rem 1.1rem;
            font-size: 0.88rem;
            line-height: 1.55;
            color: {c['text']};
            min-height: 120px;
        }}
        .rm-compare-body h5 {{
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: {c['text_muted']};
            margin: 0.75rem 0 0.35rem 0;
            font-weight: 700;
        }}
        .rm-compare-body h5:first-child {{ margin-top: 0; }}

        .rm-empty {{
            text-align: center;
            padding: 3rem 2rem;
            background: {c['surface']};
            border: 1.5px dashed {c['border']};
            border-radius: 16px;
            margin: 1rem 0;
        }}
        .rm-empty-icon {{
            font-size: 2.5rem;
            margin-bottom: 0.75rem;
        }}
        .rm-empty h3 {{
            font-size: 1.15rem;
            font-weight: 700;
            color: {c['text']};
            margin: 0 0 0.35rem 0;
        }}
        .rm-empty p {{
            color: {c['text_muted']};
            font-size: 0.9rem;
            margin: 0;
        }}

        .rm-trust {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            margin: 1rem 0 0.5rem 0;
        }}
        .rm-trust-item {{
            display: flex;
            align-items: center;
            gap: 0.4rem;
            font-size: 0.78rem;
            color: {c['text_muted']};
            background: {c['surface']};
            border: 1px solid {c['border']};
            border-radius: 999px;
            padding: 0.35rem 0.75rem;
        }}

        .rm-footer {{
            margin-top: 2.5rem;
            padding: 1rem 1.25rem;
            background: {c['surface']};
            border: 1px solid {c['border']};
            border-radius: 12px;
            font-size: 0.75rem;
            color: {c['text_muted']};
            line-height: 1.55;
        }}

        .rm-layer-badge {{
            display: inline-block;
            background: {c['primary_soft']};
            color: {c['primary_dark']};
            font-size: 0.72rem;
            font-weight: 700;
            padding: 0.2rem 0.55rem;
            border-radius: 6px;
            margin-left: 0.5rem;
            vertical-align: middle;
        }}

        .rm-sidebar-stat {{
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 0.85rem 1rem;
            margin-bottom: 0.65rem;
        }}
        .rm-sidebar-stat strong {{
            display: block;
            font-size: 1.1rem;
            color: #f8fafc !important;
        }}
        .rm-sidebar-stat span {{
            font-size: 0.78rem;
            color: #94a3b8 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
