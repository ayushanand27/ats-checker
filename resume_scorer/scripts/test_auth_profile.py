"""Auth + profile + tailor + history flow test. Requires API at :8000."""

from __future__ import annotations

import random

import requests

API = "http://localhost:8000"


def main() -> None:
    email = f"test{random.randint(1000, 999999)}@example.com"

    r = requests.post(
        f"{API}/api/auth/register",
        json={"email": email, "password": "secret123", "name": "Test User"},
        timeout=30,
    )
    r.raise_for_status()
    tok = r.json()["access_token"]
    H = {"Authorization": f"Bearer {tok}"}
    print("register OK", r.json()["user"]["email"])

    assert requests.get(f"{API}/api/auth/me", headers=H, timeout=15).json()["email"] == email
    print("me OK")

    profile = {
        "name": "Test User",
        "contact": {"email": email},
        "summary": "Backend engineer with Python and SQL experience.",
        "skills": ["Python", "SQL", "REST API", "Docker"],
        "experience": [
            {
                "title": "Engineer",
                "company": "Acme",
                "dates": "2022-2025",
                "bullets": ["Built REST APIs in Python", "Optimized SQL queries by 30%"],
            }
        ],
        "education": [{"degree": "BSc CS", "institution": "Uni", "dates": "2018-2022"}],
        "projects": [],
    }
    r = requests.put(f"{API}/api/profile", json={"profile": profile}, headers=H, timeout=30)
    r.raise_for_status()
    print("save profile OK, updated", r.json()["updated_at"][:19])

    assert requests.get(f"{API}/api/profile", headers=H, timeout=15).json()["profile"]["name"] == "Test User"
    print("get profile OK")

    jd = "Senior Python Engineer. Requires Python, SQL, Docker, Kubernetes, REST API design. AWS a plus."
    r = requests.post(
        f"{API}/api/profile/tailor",
        json={"jd_text": jd, "template": "jacks_tech", "use_ai": True, "save": True},
        headers=H,
        timeout=120,
    )
    r.raise_for_status()
    d = r.json()
    print(
        "tailor OK score=",
        d["analysis"]["core_score"],
        "ai_used=",
        d["ai_used"],
        "analysis_id=",
        d["analysis_id"],
    )
    ka = d["analysis"].get("keyword_analysis")
    print("keyword_score=", ka["keyword_score"] if ka else None)

    h = requests.get(f"{API}/api/history", headers=H, timeout=15).json()["items"]
    print("history count", len(h))
    hid = h[0]["id"]
    det = requests.get(f"{API}/api/history/{hid}", headers=H, timeout=15).json()
    print("history detail score", det["core_score"])

    assert requests.get(f"{API}/api/profile", timeout=15).status_code in (401, 403)
    print("unauthorized blocked OK")

    assert requests.post(
        f"{API}/api/auth/register",
        json={"email": email, "password": "secret123"},
        timeout=15,
    ).status_code == 409
    print("duplicate register blocked OK")

    assert requests.post(
        f"{API}/api/auth/login",
        json={"email": email, "password": "wrong"},
        timeout=15,
    ).status_code == 401
    print("wrong password blocked OK")

    assert requests.delete(f"{API}/api/history/{hid}", headers=H, timeout=15).json()["deleted"] is True
    print("delete history OK")

    print("ALL AUTH/PROFILE TESTS PASSED")


if __name__ == "__main__":
    main()
