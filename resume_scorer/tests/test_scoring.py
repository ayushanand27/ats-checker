"""Unit tests for the v2 scoring improvements (run: python -m pytest -q)."""

from __future__ import annotations

from api.deps import compose_score, compose_score_detailed
from insights.resume_normalize import normalize_resume_struct
from scoring.content_quality import score_content_quality
from scoring.evidence import EvidenceIndex, detect_stuffing
from scoring.keyword_analysis import analyze_keywords
from scoring.requirements_check import check_education, check_job_title, run_requirement_checks
from scoring.semantic_match import score_semantic_match
from structurer import structure_jd, structure_resume


# ---------------------------------------------------------------- evidence rules
def test_listed_skill_is_claim_and_sentence_is_evidence():
    text = (
        "Built ETL pipelines in Python and SQL on AWS, reducing cost by 30%.\n"
        "Skills: Python, SQL, Tableau, Docker, Kubernetes"
    )
    ev = EvidenceIndex(text)
    assert ev.status("Python") == "demonstrated"
    assert ev.status("AWS") == "demonstrated"
    assert ev.status("Tableau") == "listed_only"
    assert ev.factor("Docker", lam=0.5) == 0.5
    assert ev.factor("Python", lam=0.5) == 1.0
    assert ev.status("Rust") == "unknown"


def test_templated_sentences_count_as_list_but_duplicates_do_not():
    text = (
        "Built production features using Go. Built production features using Rust. "
        "Created stored procedures in Oracle. Created stored procedures in Oracle."
    )
    ev = EvidenceIndex(text, skills=["Go", "Rust", "Oracle"])
    assert ev.status("Rust") == "listed_only"
    assert ev.status("Go") == "listed_only"
    assert ev.status("Oracle") == "demonstrated"  # exact duplicate bullet is not a template


def test_alias_mentions_count_as_evidence():
    ev = EvidenceIndex("Trained ML models for churn prediction with 91% recall.")
    assert ev.status("machine learning") == "demonstrated"


# ---------------------------------------------------------------- keyword stuffing
def _analyze(resume_text: str, jd_text: str):
    resume = normalize_resume_struct(structure_resume(resume_text))
    jd = structure_jd(jd_text)
    return resume, jd, analyze_keywords(resume, jd)


def test_pasted_jd_skill_list_is_discounted_and_flagged(ta_jd_text):
    base = "Jane Doe\njane@example.com\nEXPERIENCE\n- Managed retail store inventory for 2 years\n"
    jd = structure_jd(ta_jd_text)
    stuffed = base + "SKILLS\n" + ", ".join(jd["all_skills"])
    _, _, clean = _analyze(base, ta_jd_text)
    _, _, kw = _analyze(stuffed, ta_jd_text)
    assert kw["raw_keyword_score"] >= 90  # literal matching is fooled completely
    assert kw["keyword_score"] <= 0.55 * kw["raw_keyword_score"] + 1  # evidence weighting halves it
    assert kw["keyword_score"] > clean["keyword_score"]
    assert kw["stuffing_warnings"], "a pasted JD skill list should raise a warning"
    assert set(kw["listed_only"]) >= set(jd["required_skills"]) & {m["keyword"] for m in kw["matched_keywords"]}


def test_lambda_zero_removes_stuffing_gain(monkeypatch, ta_jd_text):
    monkeypatch.setenv("EVIDENCE_LIST_CREDIT", "0")
    base = "Jane Doe\njane@example.com\nEXPERIENCE\n- Managed retail store inventory for 2 years\n"
    jd = structure_jd(ta_jd_text)
    _, _, clean = _analyze(base, ta_jd_text)
    _, _, kw = _analyze(base + "SKILLS\n" + ", ".join(jd["all_skills"]), ta_jd_text)
    assert kw["keyword_score"] == clean["keyword_score"] == 0.0


def test_genuine_resume_keeps_most_credit(ta_resume_text, ta_jd_text):
    _, _, kw = _analyze(ta_resume_text, ta_jd_text)
    assert kw["keyword_score"] >= 0.75 * kw["raw_keyword_score"]
    assert not kw["stuffing_warnings"]


# ---------------------------------------------------------------- semantic layer
def test_semantic_blocklist_and_partial_credit(stub_model):
    model = stub_model(same={"Performance Testing": "Unit Testing", "jQuery": "JavaScript"})
    resume = normalize_resume_struct({
        "skills": ["Performance Testing", "jQuery"],
        "experience": [{"title": "Dev", "bullets": [
            "Ran performance testing on checkout APIs, cutting p95 latency 30%",
            "Built jQuery widgets for the admin dashboard used by 40 staff",
        ]}],
    })
    jd = {"required_skills": ["Unit Testing", "JavaScript"], "preferred_skills": [], "all_skills": []}
    out = score_semantic_match(resume, jd, model)
    assert out["missing_required"] == ["Unit Testing"]  # blocked false equivalence
    assert out["matched_required"] == ["JavaScript"]  # jQuery implies JavaScript
    detail = out["semantic_matches"][0]
    assert detail["resume_skill"] == "jQuery" and detail["credit"] == 0.75
    assert out["score"] == 37.5 and out["raw_score"] == 50.0


def test_exact_match_gets_full_credit_when_demonstrated(stub_model):
    resume = normalize_resume_struct({
        "skills": ["Python", "SQL"],
        "experience": [{"title": "Analyst", "bullets": ["Automated reports in Python and SQL, saving 6 hours a week"]}],
    })
    jd = {"required_skills": ["Python", "SQL"], "preferred_skills": [], "all_skills": []}
    assert score_semantic_match(resume, jd, stub_model())["score"] == 100.0


# ---------------------------------------------------------------- composite score
def test_compose_modes():
    full = compose_score_detailed(80, 60, True, 50)
    assert full["mode"] == "full" and full["score"] == round(0.2 * 80 + 0.4 * 60 + 0.4 * 50, 1)
    assert compose_score_detailed(80, None, True, 50)["mode"] == "structure_context"
    assert compose_score_detailed(80, 60, True, None)["score"] == round(0.35 * 80 + 0.65 * 60, 1)
    unmatched = compose_score_detailed(80, None, True, None)
    assert unmatched["mode"] == "structure_only_jd_unmatched"
    assert compose_score(80, None, False) == 80


# ---------------------------------------------------------------- requirement checks
def test_job_title_and_education_checks():
    resume = {"raw_text": "Data Analyst Intern\nB.Tech in Computer Science", "education": [{"degree": "B.Tech in Computer Science"}]}
    assert check_job_title(resume, {"title": "Data Analyst Intern"})["status"] == "pass"
    assert check_job_title(resume, {"title": "Business Analyst"})["status"] in ("partial", "fail")
    assert check_education(resume, {"raw_text": "Bachelor's degree in CS required"})["status"] == "pass"
    assert check_education(resume, {"raw_text": "Master's degree required"})["status"] == "fail"


def test_requirement_checks_need_a_jd():
    assert run_requirement_checks({"raw_text": "x"}, None) == []


# ---------------------------------------------------------------- writing quality
def test_content_quality_flags_weak_writing():
    weak = score_content_quality({"experience": [{"bullets": [
        "Responsible for handling customer queries",
        "I worked on the website as a team player",
    ]}]})
    strong = score_content_quality({"experience": [{"bullets": [
        "Reduced ticket backlog 40% by automating triage in Python",
        "Built a React dashboard used by 120 support agents",
    ]}]})
    assert strong["score"] > weak["score"]
    failed = {c["name"] for c in weak["checks"] if not c["passed"]}
    assert {"No first-person pronouns", "Bullets start with action verbs"} <= failed


def test_detect_stuffing_needs_most_jd_skills_in_one_list():
    skills = ["Python", "SQL", "Excel", "Power BI", "Tableau"]
    assert detect_stuffing(EvidenceIndex("Skills: Python, SQL, Excel, Power BI, Tableau"), skills)
    assert not detect_stuffing(EvidenceIndex("Skills: Python, Java"), skills)
    genuine = (
        "Built Power BI and Tableau dashboards from SQL views for 40 managers.\n"
        "Automated Excel reports with Python, saving 6 hours a week.\n"
        "Skills: Python, SQL, Excel, Power BI, Tableau"
    )
    assert not detect_stuffing(EvidenceIndex(genuine), skills)  # long list is fine when skills are used


def test_education_check_does_not_misread_ordinary_words():
    from scoring.requirements_check import check_education, _required_edu_level

    # "me", "MS Office" and "be" are not degrees
    assert _required_edu_level("You will join me. Must be good with MS Office.") == (0, "")
    # "Bachelor's or Master's" only requires a Bachelor's
    assert _required_edu_level("B.E/B.Tech or M.Tech in Computer Science")[0] == 1
    assert _required_edu_level("Master's degree required")[0] == 2
    resume = {"education": [{"degree": "B.Tech, CSE", "institution": "Manipal University Jaipur"}]}
    result = check_education(resume, {"raw_text": "Bachelor's or Master's in a technical field"})
    assert result["status"] == "pass"


def test_job_title_matches_role_part_after_dash_and_blocklist_extended():
    from scoring.requirements_check import check_job_title
    from scoring.semantic_match import SEMANTIC_BLOCKLIST

    resume = {"raw_text": "Aspiring AI Engineer with Python experience"}
    res = check_job_title(resume, {"title": "Digital Catalyst - AI Engineer"})
    assert res["status"] == "pass"
    assert ("data science", "big data") in SEMANTIC_BLOCKLIST


def test_education_requirement_edge_cases():
    from scoring.requirements_check import _required_edu_level

    assert _required_edu_level("Master's degree in Computer Science required")[0] == 2
    assert _required_edu_level("Bachelor's preferred; Master's required")[0] == 2
    assert _required_edu_level("Bachelor's required. Master's is a plus.")[0] == 1
    assert _required_edu_level("BE RESPONSIBLE FOR REPORTING") == (0, "")
    assert _required_edu_level("BE in Computer Science or MCA")[0] == 1


# ---------------------------------------------------------------- configurable weights + stuffing integration
def test_score_weights_can_be_configured_and_bad_values_fall_back(monkeypatch):
    from api.deps import full_weights

    monkeypatch.setenv("SCORE_WEIGHTS", "1,1,2")
    w = full_weights()
    assert abs(w["context"] - 0.5) < 1e-9 and abs(sum(w.values()) - 1) < 1e-9
    assert compose_score_detailed(80, 60, True, 40)["score"] == round(0.25 * 80 + 0.25 * 60 + 0.5 * 40, 1)
    for bad in ("abc", "1,2", "-1,1,1", "0,0,0", "nan,1,1", "inf,1,1", "1e308,1e308,0", "1,0,0"):
        monkeypatch.setenv("SCORE_WEIGHTS", bad)
        assert full_weights() == {"structure": 0.20, "skills": 0.40, "context": 0.40}


def test_genuine_bullets_outscore_a_pasted_skill_list():
    from scoring.evidence import EvidenceIndex, detect_stuffing

    jd_skills = ["Python", "SQL", "Tableau", "Excel", "Statistics"]
    stuffed = "Skills: Python, SQL, Tableau, Excel, Statistics"
    honest = (
        "Built a Python ETL job that loaded sales data into SQL tables.\n"
        "Created a Tableau dashboard used by the finance team.\n"
        "Analysed survey results in Excel using statistics such as t-tests."
    )
    idx_stuffed, idx_honest = EvidenceIndex(stuffed, jd_skills), EvidenceIndex(honest, jd_skills)
    assert detect_stuffing(idx_stuffed, jd_skills)
    assert not detect_stuffing(idx_honest, jd_skills)
    assert all(idx_honest.factor(s) == 1.0 for s in jd_skills)
    assert all(idx_stuffed.factor(s) < 1.0 for s in jd_skills)


def test_wrapped_pdf_lines_do_not_become_fake_roles_or_education_entries():
    from structurer import structure_resume

    text = (
        "Ayush Anand\nayush@example.com | +91 7004455149\n\n"
        "EXPERIENCE\nGenAI Intern — 2026\n"
        "• Built and deployed an AI platform on AWS EC2 with JWT login and\nLLM-generated questions via Groq API.\n"
        "• Added proctoring with OpenCV, penalizing multiple faces and noise. — Salesforce Trainee  Feb 2026 – Jul 2026\n"
        "• Completed training in Generative AI.\n\n"
        "EDUCATION\nManipal University Jaipur\nExpected May 2027\n"
        "B.Tech, Computer Science – CGPA 9.17/10\nJaipur, Rajasthan\n\n"
        "PROJECTS\nSMRA | Python, FastAPI\n• Wrote 86 pytest tests with GitHub Actions\nCI.\n"
    )
    r = structure_resume(text)
    titles = [e["title"] for e in r["experience"]]
    assert titles == ["GenAI Intern — 2026", "Salesforce Trainee"]
    assert r["experience"][0]["bullets"][0].endswith("LLM-generated questions via Groq API.")
    assert r["experience"][1]["dates"] == "Feb 2026 – Jul 2026"
    assert len(r["education"]) == 1
    assert r["education"][0]["institution"] == "Manipal University Jaipur"
    assert r["education"][0]["degree"].startswith("B.Tech")
    assert r["education"][0]["dates"] == "Expected May 2027"
    assert r["projects"][0]["bullets"][0].endswith("GitHub Actions CI.")


def test_bullet_without_period_is_not_merged_with_next_header():
    from structurer import structure_resume

    text = (
        "A B\na@b.com\n\nEXPERIENCE\nData Analyst Intern  Jan 2024 – Mar 2024\n"
        "• Built dashboards used by the sales team across three regions every week\n"
        "Backend Developer  Apr 2024 – Jun 2024\n• Wrote APIs.\n"
    )
    r = structure_resume(text)
    assert len(r["experience"]) == 2


def test_parser_edge_cases_from_review():
    from structurer import _parse_education, _repair_wrapped_lines, structure_resume

    # a dated bullet that is not a role header stays one bullet
    out = _repair_wrapped_lines(["• Built cloud services. — AWS Jan 2022 – Mar 2023"])
    assert out == ["• Built cloud services. — AWS Jan 2022 – Mar 2023"]
    # an undated role header after an unfinished bullet is not joined into it
    out = _repair_wrapped_lines(["• Built dashboards for the sales team", "Backend Developer (Contract)"])
    assert out == ["• Built dashboards for the sales team", "Backend Developer (Contract)"]
    # institution and degree on one line
    assert _parse_education(["Stanford University — Bachelor of Science"]) == [
        {"degree": "Bachelor of Science", "institution": "Stanford University", "dates": ""}
    ]
    # a leading location never becomes a degree
    edu = _parse_education(["Cambridge, MA", "Harvard University", "Bachelor of Science"])
    assert edu == [{"degree": "Bachelor of Science", "institution": "Harvard University", "dates": ""}]
    # unrecognised wording still yields entries (line-per-entry fallback)
    assert _parse_education(["Some Programme, Some Place"])[0]["degree"] == "Some Programme"


def test_groq_falls_back_when_model_is_unavailable(monkeypatch):
    from insights import groq_models

    monkeypatch.delenv("GROQ_MODEL", raising=False)
    monkeypatch.setattr(groq_models, "_working_model", None)
    tried = []

    class NotFound(Exception):
        status_code = 404

    class FakeCompletions:
        def create(self, model, **kwargs):
            tried.append(model)
            if model == "llama-3.3-70b-versatile":
                raise NotFound("model_not_found")
            return {"model": model}

    class FakeClient:
        class chat:  # noqa: N801
            completions = FakeCompletions()

    out = groq_models.chat_completion(FakeClient(), messages=[])
    assert out["model"] == "openai/gpt-oss-120b"
    assert tried == ["llama-3.3-70b-versatile", "openai/gpt-oss-120b"]
    # next call starts from the model that worked
    assert groq_models.preferred_model() == "openai/gpt-oss-120b"
    monkeypatch.setattr(groq_models, "_working_model", None)


def test_groq_non_model_errors_are_not_swallowed(monkeypatch):
    import pytest
    from insights import groq_models

    monkeypatch.setattr(groq_models, "_working_model", None)

    class Boom:
        class chat:  # noqa: N801
            class completions:  # noqa: N801
                @staticmethod
                def create(model, **kwargs):
                    raise ValueError("401 invalid api key")

    with pytest.raises(ValueError):
        groq_models.chat_completion(Boom(), messages=[])


def test_groq_blocked_model_403_falls_back_but_other_403_does_not(monkeypatch):
    import pytest
    from insights import groq_models

    monkeypatch.setattr(groq_models, "_working_model", None)
    monkeypatch.setattr(groq_models, "_working_for_override", "")
    monkeypatch.delenv("GROQ_MODEL", raising=False)

    class Forbidden(Exception):
        status_code = 403

    class Client:
        class chat:  # noqa: N801
            class completions:  # noqa: N801
                @staticmethod
                def create(model, **kwargs):
                    if model == "llama-3.3-70b-versatile":
                        raise Forbidden("model_permission_blocked_project")
                    return model

    assert groq_models.chat_completion(Client(), messages=[]) == "openai/gpt-oss-120b"

    class Denied:
        class chat:  # noqa: N801
            class completions:  # noqa: N801
                @staticmethod
                def create(model, **kwargs):
                    raise Forbidden("forbidden: invalid permissions")

    monkeypatch.setattr(groq_models, "_working_model", None)
    with pytest.raises(Forbidden):
        groq_models.chat_completion(Denied(), messages=[])


def test_groq_working_model_beats_unavailable_override_and_resets_on_change(monkeypatch):
    from insights import groq_models

    monkeypatch.setattr(groq_models, "_working_model", None)
    monkeypatch.setattr(groq_models, "_working_for_override", "")
    monkeypatch.setenv("GROQ_MODEL", "bad/model")
    tried = []

    class NotFound(Exception):
        status_code = 404

    class Client:
        class chat:  # noqa: N801
            class completions:  # noqa: N801
                @staticmethod
                def create(model, **kwargs):
                    tried.append(model)
                    if model in ("bad/model", "llama-3.3-70b-versatile"):
                        raise NotFound("model_not_found")
                    return model

    assert groq_models.chat_completion(Client(), messages=[]) == "openai/gpt-oss-120b"
    tried.clear()
    groq_models.chat_completion(Client(), messages=[])
    assert tried == ["openai/gpt-oss-120b"]  # no repeat of the failing override

    monkeypatch.setenv("GROQ_MODEL", "other/model")  # override changed: start over
    assert groq_models.model_candidates()[0] == "other/model"

def _make_pdf(pages=1, with_image=False, header_contact=False):
    import fitz

    doc = fitz.open()
    for i in range(pages):
        page = doc.new_page()
        page.insert_text((72, 120), "Jane Doe\nBuilt things with Python and SQL.")
        if header_contact and i == 0:
            page.insert_text((72, 20), "jane@example.com +1 415 555 0100")
        if with_image and i == 0:
            pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 20, 20), False)
            pix.clear_with(200)
            page.insert_image(fitz.Rect(400, 80, 440, 120), pixmap=pix)
    data = doc.tobytes()
    doc.close()
    return data


def test_pdf_layout_flags_images_pages_and_header_contact():
    from parser import analyze_pdf_layout

    clean = analyze_pdf_layout(_make_pdf())
    assert clean["image_count"] == 0 and clean["page_count"] == 1
    assert clean["contact_only_in_margin"] is False

    bad = analyze_pdf_layout(_make_pdf(pages=3, with_image=True, header_contact=True))
    assert bad["image_count"] == 1 and bad["page_count"] == 3
    assert bad["contact_only_in_margin"] is True


def test_pdf_checks_only_appear_when_flags_exist():
    from scoring.formatting import check_formatting

    resume = {"raw_text": "Jane Doe\nPython developer", "contact": {}}
    names = {c["name"] for c in check_formatting(resume)}
    assert "No images or graphics" not in names  # text-only input unchanged

    flags = {"image_count": 2, "page_count": 3, "garbled_ratio": 0.0, "contact_only_in_margin": True}
    checks = {c["name"]: c for c in check_formatting(resume, flags)}
    assert not checks["No images or graphics"]["passed"]
    assert not checks["Page length (1–2 pages)"]["passed"]
    assert checks["Readable text layer"]["passed"]
    assert not checks["Contact info in page body"]["passed"]


def test_mixed_bullet_styles_flagged_but_unscored():
    from scoring.formatting import check_formatting

    resume = {"raw_text": "• one\n- two\n* three", "contact": {}}
    chk = next(c for c in check_formatting(resume) if c["name"] == "Consistent bullet style")
    assert not chk["passed"] and chk["weight"] == 0


def test_vendor_views_differ_by_matching_strategy_and_never_touch_core_score():
    from scoring.vendor_views import compute_vendor_views

    resume = "Managed pipelines and built dashboards. Worked with Postgres and ML models."
    skills = ["managing", "Python", "machine learning"]
    views = {v["vendor"]: v for v in compute_vendor_views(resume, skills, 40.0, [])}
    inp = views["Taleo"]["inputs"]
    assert inp["literal"] == 0.0            # 'managing' != 'Managed', no python, no ML expansion
    assert inp["stemmed"] > inp["literal"]  # stemming finds Managed ~ managing
    assert views["Greenhouse"]["score"] is None  # no auto-scoring by design
    assert views["iCIMS"]["score"] > views["Taleo"]["score"]  # semantic more forgiving here
    assert compute_vendor_views(resume, [], None, []) == []


def test_analysis_response_includes_vendor_views():
    from api.analysis import run_analysis
    import os

    os.environ["SKIP_LAYER2"] = "1"
    os.environ["SKIP_CONTEXT"] = "1"
    resume = {"name": "Jane", "contact": {"email": "j@x.co"}, "skills": ["Python", "SQL"],
              "raw_text": "Jane\nPython SQL developer\n" + "built things " * 60,
              "sections_found": ["experience", "education", "skills"]}
    out = run_analysis(resume, "Data Engineer\nRequired: Python, SQL", "jacks_tech")
    assert {v.vendor for v in out.vendor_views} >= {"Taleo", "iCIMS", "Greenhouse"}
