# ResumeMatch

**ATS scorer · AI rewriter · Multi-format resume generator**

ResumeMatch is an open-source Streamlit app that scores how well a resume matches a job description (mirroring real-world ATS systems), suggests AI-rewritten improvements, and generates downloadable resumes in **PDF**, **DOCX**, or **LaTeX** — all from a chosen template.

> Core ATS scoring is **fully deterministic** (zero API calls). AI rewrite suggestions are **optional** and use a single Groq API call. Document rendering is **100% template-based** — the LLM never generates file formats directly.

---

## Features

- **Instant ATS score** — rule-based structure checks + local semantic skill matching (no network required)
- **Optional JD tailoring** — paste or upload a job description for keyword/skill gap analysis
- **AI rewrite suggestions** — one Groq call returns structured JSON (summary, skills, bullets) with a strict no-fabrication policy
- **Multi-format export** — same JSON feeds PDF (WeasyPrint), DOCX (python-docx), and LaTeX source (Jinja2)
- **Two built-in templates** — Jack's Tech Resume & Classic Non-Tech Resume
- **Docker-ready** — WeasyPrint system deps baked in for AWS EC2 deployment

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
| Layer 1 — hygiene | `scoring/deterministic.py` | **Zero** |
| Layer 2 — skill match | `scoring/semantic_match.py` | **Zero** (local `all-MiniLM-L6-v2`) |
| AI rewriter | `insights/llm_rewriter.py` | **One** (opt-in button) |
| PDF / DOCX / TeX | `renderers/` | **Zero** |

**Score weights:** With JD → Layer 1 (35%) + Layer 2 (65%). Without JD → Layer 1 only (general ATS check).

---

## Quick start (local)

```bash
git clone https://github.com/ayushanand27/ats-checker.git
cd ats-checker/resume_scorer

python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # optional: add GROQ_API_KEY for AI suggestions
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501).

> **First run** downloads the `all-MiniLM-L6-v2` embedding model (~90 MB). Core scoring works offline after that.

---

## Docker

WeasyPrint's Pango/Cairo dependencies are pre-installed in the Dockerfile — no manual `apt-get` on the host.

```bash
cd resume_scorer
cp .env.example .env          # add GROQ_API_KEY if using AI suggestions
docker build -t resumematch .
docker run -d -p 8501:8501 --env-file .env --name resumematch resumematch
```

Visit `http://localhost:8501`.

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

1. **Upload** resume (PDF, DOCX, or TXT) + optional job description + pick a template
2. Click **Analyze** → ATS score appears instantly with expandable breakdown
3. Optionally click **Get AI Suggestions** (requires `GROQ_API_KEY`)
4. Review before/after comparison and change log
5. **Generate Resume** → download PDF, DOCX, and/or `.tex` source

---

## Project structure

```
ats-checker/
└── resume_scorer/
    ├── app.py                      # Streamlit UI entrypoint
    ├── parser.py                   # PDF/DOCX/TXT text extraction
    ├── structurer.py               # Regex section & skill extraction
    ├── skills_taxonomy.json        # ~600 skills for matching
    ├── scoring/
    │   ├── deterministic.py        # Layer 1: contact, sections, length
    │   └── semantic_match.py       # Layer 2: embedding skill match
    ├── insights/
    │   └── llm_rewriter.py         # Single optional Groq call → JSON
    ├── templates/
    │   ├── jacks_tech/             # Tech-focused (HTML + LaTeX)
    │   └── classic_nontech/        # Traditional layout (HTML + LaTeX)
    ├── renderers/
    │   ├── docx_renderer.py
    │   ├── pdf_renderer.py
    │   └── tex_renderer.py
    ├── Dockerfile
    ├── requirements.txt
    └── .env.example
```

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | No | Enables AI rewrite suggestions only. Get one at [console.groq.com](https://console.groq.com). |

Copy `resume_scorer/.env.example` to `.env` and fill in your key. Core ATS scoring works without it.

---

## Tech stack

- **Python 3.11** · **Streamlit** (UI)
- **PyMuPDF** / **python-docx** (input parsing)
- **sentence-transformers** (`all-MiniLM-L6-v2`) — local semantic matching
- **Groq** (`llama-3.3-70b-versatile`) — optional rewrite (one call)
- **Jinja2** + **WeasyPrint** (PDF) + **python-docx** (DOCX) + **LaTeX templates** (TeX source)

---

## v1 scope & limitations

| Included | Not in v1 |
|----------|-----------|
| PDF, DOCX, TeX export | Custom template upload (stubbed) |
| Two built-in templates | JD-from-URL scraping |
| Deterministic ATS score | OCR for scanned PDFs |
| Optional AI rewrite | User accounts / persistence |
| Docker + EC2 deploy | Server-side `pdflatex` compile |
| | Payment / batch processing |

TeX output is **source only** — compile locally or upload to [Overleaf](https://www.overleaf.com).

---

## Disclaimer

ATS Compatibility Score is fully deterministic, based on parsing and keyword-matching approaches similar to real ATS systems. AI rewrite suggestions are optional, reviewed by you before use, and the AI is instructed never to fabricate experience or metrics. This tool is independent and not affiliated with any company's actual ATS system.

---

## License

Open source — MIT (or add your preferred license).
