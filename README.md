# ResumeMatch

**ATS scorer · AI rewriter · Multi-format resume generator**

ResumeMatch scores how well a resume matches a job description using industry-weighted ATS checks (keyword placement, formatting parseability, semantic skill match), suggests AI-rewritten improvements, and generates downloadable resumes in **PDF**, **DOCX**, or **LaTeX**.

> Core ATS scoring is **fully deterministic** (zero API calls for scoring). AI rewrite and resume-builder chat are **optional** Groq features. Document rendering is **100% template-based**.

**Primary UI:** Next.js app in `frontend/` (`npm run dev` → http://localhost:3000/analyze). Legacy Streamlit UI remains in `resume_scorer/app.py`.

---

## Features

- **Industry-standard ATS scoring** — structure (35%) + semantic skill match (65%); keyword placement in summary/skills/experience; density warnings for stuffing
- **Keyword highlight map** — see which JD terms appear in your resume text (exact + synonym at 0.8 weight, Workday/Taleo-style)
- **Parsed ATS view** — how an ATS likely reads your sections, contact, and skills
- **Formatting compatibility** — single-column, tables, headers/footers, file-type checks
- **Instant re-score** — inline editor and AI rewrite both re-run the full score pipeline with before/after delta
- **JD input** — paste, upload, or fetch from a public job URL
- **Resume builder chat** — Groq-guided interview tailored to the JD (~20–30 questions)
- **User accounts + master profile** — sign in, save your resume once, then generate a tailored resume from just a JD (auto re-scored)
- **Analysis history** — each tailoring run is saved per user and reloadable
- **LLM observability** — optional Langfuse tracing of every Groq rewrite/chat call
- **OCR for scanned PDFs** — optional recovery when native text extraction fails (requires Tesseract binary)
- **Multi-format export** — PDF (WeasyPrint), DOCX, LaTeX from **Classic Tech** or **Classic Non-Tech** templates (+ custom DOCX)
- **Browser session save** — last analysis restored from localStorage

---

## Quick start (Next.js + API)

```bash
git clone https://github.com/ayushanand27/ats-checker.git
cd ats-checker

# Terminal 1 — API
cd resume_scorer
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
cp .env.example .env            # optional: GROQ_API_KEY for AI chat + rewrite

python -m uvicorn api.main:app --port 8000

# Terminal 2 — Frontend
cd frontend
npm install
echo NEXT_PUBLIC_API_URL=http://localhost:8000 > .env.local
npm run dev
```

Open [http://localhost:3000/analyze](http://localhost:3000/analyze).

> **First run** downloads `all-MiniLM-L6-v2` (~90 MB). Core scoring works offline after that.

### Optional: OCR for scanned PDFs

Install [Tesseract](https://github.com/tesseract-ocr/tesseract) on your system. `pytesseract` is already in `requirements.txt`.

---

## Quick start (Streamlit — legacy)

```bash
cd resume_scorer
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501).

---

## Architecture

Content generation and document rendering are **fully separated** — the same pattern used by production resume tools (Enhancv, Wobo, AIHawk):

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│ Resume/JD   │────▶│ Parser +     │────▶│ Layer 1 + 2     │
│ Upload      │     │ Structurer   │     │ ATS Score       │
└─────────────┘     │ (regex/rules)│     │ (deterministic) │
                    └──────────────┘     └────────┬────────┘
                                                  │
                    ┌──────────────┐              │ gaps
                    │ Renderers    │◀─────────────┤
                    │ PDF/DOCX/TeX │     ┌────────▼────────┐
                    │ (Jinja2)     │     │ Groq LLM        │
                    └──────────────┘     │ (1 call, opt-in)│
                           ▲             │ → JSON only     │
                           └─────────────┴─────────────────┘
```

| Layer | Module | API calls |
|-------|--------|-----------|
| Input parsing | `parser.py` | **Zero** |
| Structure extraction | `structurer.py` | **Zero** |
| Layer 1 — hygiene + formatting | `scoring/deterministic.py`, `formatting.py` | **Zero** |
| Keyword analysis | `scoring/keyword_analysis.py` | **Zero** |
| Layer 2 — skill match | `scoring/semantic_match.py` | **Zero** (local `all-MiniLM-L6-v2`) |
| AI rewriter | `insights/llm_rewriter.py` | **One** (opt-in button) |
| Accounts / profiles / history | `api/db.py`, `api/auth.py`, `api/routes/{auth,profile}.py` | **Zero** (local SQLite + JWT) |
| LLM tracing | `insights/tracing.py` | **Zero** (async to Langfuse, opt-in) |
| PDF / DOCX / TeX | `renderers/` | **Zero** |

**Score weights:** With JD → Layer 1 (35%) + Layer 2 (65%). Without JD → Layer 1 only (general ATS check).

### User accounts & JD tailoring

Sign in on `/analyze`, then:

1. **Save current resume as my profile** — stores a reusable master profile (SQLite).
2. **Generate from my profile** — paste any JD and get an AI-tailored, re-scored resume in one click.
3. **History** — every tailoring run is saved and reloadable per user.

Auth is self-contained: **PBKDF2** password hashing + **JWT** sessions, no external service. Set `JWT_SECRET` and a persistent `RESUMEMATCH_DB` path in production.

### LLM observability (Langfuse)

When `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` are set, Groq calls emit traces:

| Trace | When |
|-------|------|
| `resume_rewrite` | AI rewrite + Generate from profile |
| `resume_chat_turn` | Each resume-builder chat turn |

If keys are unset, tracing is a **no-op** — the app runs normally. Verify the connection with `python scripts/langfuse_smoke.py`.

---

## Docker

WeasyPrint's Pango/Cairo dependencies are pre-installed in the Dockerfile — no manual `apt-get` on the host.

```bash
cd resume_scorer
cp .env.example .env          # add GROQ_API_KEY if using AI suggestions
docker build -t resumematch .
docker run -d -p 8501:8501 --env-file .env --name resumematch resumematch
```

Visit `http://localhost:8501` (Streamlit). For production, deploy the FastAPI service (`uvicorn api.main:app`) + Next.js static export or Vercel — see `render.yaml`.

---

## AWS EC2 deployment

Same Docker pattern as SmartSkale InterviewBot:

1. Launch a **t2.micro** / **t3.micro** Ubuntu instance (free tier).
2. Security group — allow inbound **TCP 8501** (or **80** with Nginx reverse proxy).
3. Install Docker:
   ```bash
   sudo apt-get update && sudo apt-get install -y docker.io
   sudo usermod -aG docker $USER
   # log out and back in
   ```
4. Clone and configure:
   ```bash
   git clone https://github.com/ayushanand27/ats-checker.git
   cd ats-checker/resume_scorer
   cp .env.example .env && nano .env   # set GROQ_API_KEY
   ```
5. Build and run:
   ```bash
   docker build -t resumematch .
   docker run -d -p 8501:8501 --env-file .env --restart unless-stopped resumematch
   ```

Access at `http://<EC2-public-ip>:8501`.

---

## Usage flow

1. **Upload** a resume or **build with chat** (JD required for chat) — paste/upload/fetch JD
2. Click **Analyze** → ATS score with keyword map, parsed view, and top fixes
3. **Edit inline** or click **Get AI Suggestions** (Groq) — both auto **re-score** with before/after delta
4. Review keyword highlights, formatting checks, and change log
5. **Preview & Download** → PDF, DOCX, and/or `.tex`

---

## Project structure

```
ats-checker/
├── frontend/                       # Next.js 14 UI (primary)
│   └── app/analyze/page.tsx
└── resume_scorer/
    ├── api/                        # FastAPI
    │   ├── main.py                 # app + router wiring + DB init
    │   ├── db.py                   # SQLite (users, profiles, analyses)
    │   ├── auth.py                 # PBKDF2 hashing + JWT
    │   └── routes/                 # analyze, chat, rewrite, generate, auth, profile
    ├── app.py                      # Legacy Streamlit UI
    ├── parser.py                   # PDF/DOCX/TXT + optional OCR
    ├── structurer.py
    ├── scoring/
    │   ├── deterministic.py
    │   ├── semantic_match.py
    │   ├── keyword_analysis.py
    │   ├── formatting.py
    │   └── fix_suggestions.py
    ├── insights/
    │   ├── llm_rewriter.py
    │   ├── resume_chat.py
    │   └── tracing.py              # Langfuse (optional, no-op if unset)
    ├── scripts/
    │   ├── langfuse_smoke.py       # verify Langfuse connection
    │   └── test_auth_profile.py    # auth + profile + tailor + history test
    ├── templates/
    │   ├── jacks_tech/             # Classic Tech Resume
    │   └── classic_nontech/
    └── renderers/
```

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | No | Enables AI rewrite, chat, and JD tailoring. Get one at [console.groq.com](https://console.groq.com). |
| `JWT_SECRET` | Prod | Signs user session tokens. Use a long random string in production (dev has a fallback). |
| `RESUMEMATCH_DB` | No | Path to the SQLite DB for accounts/profiles/history. Point to a persistent volume in production. |
| `LANGFUSE_PUBLIC_KEY` | No | Enables LLM tracing. From [cloud.langfuse.com](https://cloud.langfuse.com) → Settings → API Keys. |
| `LANGFUSE_SECRET_KEY` | No | Langfuse secret key (pairs with the public key). |
| `LANGFUSE_BASE_URL` | No | Langfuse host, e.g. `https://cloud.langfuse.com`. |
| `CORS_ORIGINS` | No | Comma-separated origins allowed to call the API (e.g. your Vercel URL). |
| `SKIP_LAYER2` | No | Set to `1` on low-memory hosts to skip Layer 2 embeddings. |
| `TESSERACT_CMD` | No | Path to `tesseract.exe` if not on PATH (Windows auto-detects Program Files). |

Copy `resume_scorer/.env.example` to `.env` and fill in your keys. Core ATS scoring works without any of them.

---

## Tech stack

- **Next.js 14** + **TypeScript** + **Tailwind** (primary UI)
- **FastAPI** + **Python 3.11**
- **PyMuPDF** / **python-docx** / optional **pytesseract** (input parsing)
- **sentence-transformers** (`all-MiniLM-L6-v2`) — local semantic matching
- **Groq** (`llama-3.3-70b-versatile`) — optional chat + rewrite
- **Jinja2** + **WeasyPrint** (PDF) + **python-docx** (DOCX) + **LaTeX templates**

---

## v1 scope & limitations

| Included | Not in v1 |
|----------|-----------|
| Next.js UI + FastAPI | Cloud DB (uses local SQLite) |
| User accounts + saved master profile | Server-side `pdflatex` compile |
| JD auto-tailoring + per-user history | Multi-platform ATS profiles (Workday vs Greenhouse) |
| PDF, DOCX, TeX export | Payment / batch processing |
| Classic Tech + Non-Tech templates | LinkedIn-protected URL scraping |
| Custom DOCX template upload | Email verification / password reset |
| JD paste, upload, URL fetch | |
| Keyword placement + density analysis | |
| OCR for scanned PDFs (with Tesseract) | |
| Inline editor + auto re-score | |
| Resume builder chat | |
| Langfuse LLM tracing | |
| Browser session persistence | |

TeX output is **source only** — compile locally or upload to [Overleaf](https://www.overleaf.com).

---

## Disclaimer

ATS Compatibility Score is fully deterministic, based on parsing and keyword-matching approaches similar to real ATS systems. AI rewrite suggestions are optional, reviewed by you before use, and the AI is instructed never to fabricate experience or metrics. This tool is independent and not affiliated with any company's actual ATS system.

---

## License

MIT License — see [LICENSE](LICENSE).
