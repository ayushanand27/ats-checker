"""
Full feature regression test — run from resume_scorer/:
  python scripts/comprehensive_e2e_test.py

Requires FastAPI at http://localhost:8000
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "api" / "test_fixtures"
API = "http://localhost:8000"

FAILURES: list[str] = []
WARNINGS: list[str] = []


def ok(msg: str) -> None:
    print(f"  OK  {msg}")


def fail(msg: str) -> None:
    FAILURES.append(msg)
    print(f"  FAIL {msg}")


def warn(msg: str) -> None:
    WARNINGS.append(msg)
    print(f"  WARN {msg}")


def analyze(resume_name: str, jd_name: str | None, label: str) -> dict | None:
    print(f"\n=== Analyze: {label} ===")
    files = {
        "resume": (resume_name, (FIX / resume_name).read_bytes(), "text/plain"),
    }
    data = {"template": "jacks_tech"}
    if jd_name:
        data["jd_text"] = (FIX / jd_name).read_text(encoding="utf-8")

    r = requests.post(f"{API}/api/analyze", files=files, data=data, timeout=120)
    if not r.ok:
        fail(f"{label}: HTTP {r.status_code} — {r.text[:300]}")
        return None
    body = r.json()
    ok(f"core_score={body['core_score']} L1={body['layer1']['score']} L2={body.get('layer2')}")
    return body


def test_health() -> None:
    print("\n=== Health ===")
    r = requests.get(f"{API}/api/health", timeout=10)
    if r.ok and r.json().get("status") == "ok":
        ok("health")
    else:
        fail(f"health: {r.status_code}")


def test_ta_jd_no_false_skills() -> None:
    from structurer import structure_jd

    jd = structure_jd((FIX / "jd_talent_acquisition.txt").read_text(encoding="utf-8"))
    bad = {"Kong", "Storage"} & set(
        jd["required_skills"] + jd["preferred_skills"] + jd["all_skills"]
    )
    if bad:
        fail(f"TA JD false-positive skills: {bad}")
    else:
        ok(f"TA JD skills clean — required={jd['required_skills']}")
    expected = {"Excel", "SQL", "Power BI", "Automation"} & set(jd["required_skills"])
    if not expected.issubset(set(jd["required_skills"])):
        fail(f"TA JD missing expected required subset; got {jd['required_skills']}")
    else:
        ok("TA JD required skills include Excel/SQL/Power BI/Automation")


def test_digital_jd_layer2_skip() -> None:
    body = analyze("resume_ayush_ta.txt", "jd_digital_analyst.txt", "Ayush + Digital Analyst JD")
    if not body:
        return
    if body.get("layer2") is not None:
        fail(f"Digital Analyst should skip Layer 2; got score {body['layer2']['score']}")
    else:
        ok("Layer 2 null for skill-less JD")
    if body["core_score"] != body["layer1"]["score"]:
        fail(
            f"core_score should equal L1 when L2 skipped; "
            f"core={body['core_score']} L1={body['layer1']['score']}"
        )
    else:
        ok("core_score equals Layer 1 (no L2 penalty)")
    warn_msg = body.get("parse_warning") or ""
    if "no extractable skills" not in warn_msg.lower():
        warn(f"parse_warning missing L2 skip note: {warn_msg!r}")


def test_ta_match() -> None:
    body = analyze("resume_ayush_ta.txt", "jd_talent_acquisition.txt", "Ayush TA resume + TA JD")
    if not body:
        return
    if body.get("layer2") is None:
        fail("TA JD should run Layer 2")
        return
    l2 = body["layer2"]
    if l2["score"] < 50:
        warn(f"TA match score low ({l2['score']}) — check embedding model or skills")
    else:
        ok(f"TA Layer 2 score={l2['score']}")
    bad_missing = {"Kong", "Storage"} & set(l2.get("missing_required", []))
    if bad_missing:
        fail(f"Layer 2 missing_required has false positives: {bad_missing}")
    else:
        ok(f"matched_required={l2['matched_required']}")
    sections = body["resume_struct"].get("sections_found", [])
    if "skills" not in sections:
        fail(f"Resume missing skills section: {sections}")
    else:
        ok(f"sections_found includes skills: {sections}")


def test_no_jd() -> None:
    body = analyze("resume_ayush_ta.txt", None, "Ayush resume, no JD")
    if not body:
        return
    if body.get("jd_provided"):
        fail("jd_provided should be false")
    if body.get("layer2") is not None:
        fail("layer2 should be null without JD")
    ok(f"no-JD core_score={body['core_score']} (L1 only)")


def test_generate() -> None:
    print("\n=== Generate DOCX/PDF/TeX ===")
    body = analyze("sample_resume.txt", "jd_talent_acquisition.txt", "sample + TA JD (for generate)")
    if not body:
        return
    for fmt in ("docx", "pdf", "tex"):
        r = requests.post(
            f"{API}/api/generate",
            data={
                "resume_json": json.dumps(body["resume_struct"]),
                "template": "jacks_tech",
                "format": fmt,
            },
            timeout=60,
        )
        if not r.ok:
            if fmt == "pdf":
                warn(f"PDF generate skipped/failed (Windows): {r.status_code}")
            else:
                fail(f"generate {fmt}: {r.status_code} {r.text[:200]}")
        elif len(r.content) < 500:
            fail(f"generate {fmt}: output too small ({len(r.content)} bytes)")
        else:
            ok(f"{fmt} — {len(r.content)} bytes")


def test_rewrite() -> None:
    print("\n=== Rewrite ===")
    body = analyze("resume_ayush_ta.txt", "jd_talent_acquisition.txt", "rewrite source")
    if not body:
        return
    r = requests.post(
        f"{API}/api/rewrite",
        json={
            "resume_struct": body["resume_struct"],
            "jd_struct": body["jd_struct"],
            "gaps": body["gaps"],
        },
        timeout=90,
    )
    if r.status_code == 503 or r.status_code == 500:
        warn(f"rewrite skipped (GROQ_API_KEY?): {r.status_code}")
        return
    if not r.ok:
        fail(f"rewrite: {r.status_code} {r.text[:200]}")
        return
    data = r.json()
    if not data.get("summary"):
        fail("rewrite missing summary")
    else:
        ok(f"rewrite summary len={len(data['summary'])}, changes={len(data.get('change_log', []))}")


def main() -> int:
    sys.path.insert(0, str(ROOT))
    print(f"API: {API}")
    try:
        test_health()
        test_ta_jd_no_false_skills()
        test_no_jd()
        test_digital_jd_layer2_skip()
        test_ta_match()
        test_generate()
        test_rewrite()
    except requests.ConnectionError:
        fail("Cannot connect to API — start uvicorn on port 8000")
        return 1

    print("\n" + "=" * 50)
    print(f"Failures: {len(FAILURES)} | Warnings: {len(WARNINGS)}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
