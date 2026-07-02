"""Send a test trace to Langfuse. Run from resume_scorer/: python scripts/langfuse_smoke.py"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from insights.tracing import langfuse_enabled, start_generation


def main() -> None:
    if not langfuse_enabled():
        print("FAIL: Langfuse not configured. Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env")
        sys.exit(1)

    gen = start_generation(
        name="resumematch_smoke_test",
        model="llama-3.3-70b-versatile",
        input=[{"role": "user", "content": "hello from ResumeMatch"}],
        metadata={"provider": "resumematch", "test": True},
        tags=["smoke", "resumematch"],
    )
    gen.end(
        output="pong — Langfuse tracing is wired up",
        usage={"input": 5, "output": 8, "total": 13, "unit": "TOKENS"},
    )
    print("OK: smoke trace sent. Check Langfuse Tracing for resumematch_smoke_test")


if __name__ == "__main__":
    main()
