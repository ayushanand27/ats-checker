"""API smoke tests with stub models (no downloads). Run: python -m pytest -q"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch, tmp_path, stub_model):
    monkeypatch.setenv("RESUMEMATCH_DB", str(tmp_path / "test.db"))
    import api.analysis as analysis

    monkeypatch.setattr(analysis, "get_embedding_model", lambda: stub_model())
    monkeypatch.setattr(analysis, "get_context_model", lambda: stub_model())
    from api.main import app

    with TestClient(app) as c:
        yield c


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_analyze_with_jd_returns_all_layers(client, ta_resume_text, ta_jd_text):
    r = client.post(
        "/api/analyze",
        files={"resume": ("resume.txt", ta_resume_text.encode(), "text/plain")},
        data={"jd_text": ta_jd_text},
    )
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["jd_provided"] is True
    assert d["score_breakdown"]["mode"] == "full"
    assert set(d["score_breakdown"]["weights"]) == {"structure", "skills", "context"}
    assert 0 <= d["core_score"] <= 100
    assert d["contextual"]["chunks"] >= 1
    assert {c["name"] for c in d["requirements_checks"]} >= {"Job title match", "Education level"}
    assert d["content_quality"]["score"] > 0
    assert "listed_only" in d["keyword_analysis"]


def test_analyze_without_jd_is_structure_only(client, ta_resume_text):
    r = client.post("/api/analyze", files={"resume": ("resume.txt", ta_resume_text.encode(), "text/plain")})
    d = r.json()
    assert d["score_breakdown"]["mode"] == "structure_only"
    assert d["core_score"] == d["layer1"]["score"]
    assert d["requirements_checks"] == []


def test_jd_without_skills_uses_context_not_structure(client, ta_resume_text):
    r = client.post(
        "/api/analyze",
        files={"resume": ("resume.txt", ta_resume_text.encode(), "text/plain")},
        data={"jd_text": "We are a friendly team looking for a motivated person to join us in our office."},
    )
    d = r.json()
    assert d["layer2"] is None
    assert d["score_breakdown"]["mode"] == "structure_context"
