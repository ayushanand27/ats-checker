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
