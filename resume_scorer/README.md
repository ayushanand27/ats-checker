# ResumeMatch

**ResumeMatch** scores how well a resume matches a job description (mirroring real-world ATS systems), suggests AI-rewritten improvements, and generates downloadable resumes in PDF, DOCX, or LaTeX — all from a chosen template.

## Architecture

Content generation and document rendering are **fully separated**:

| Layer | Role | API calls |
|-------|------|-----------|
| Parser + Structurer | Extract text & structure via regex/rules | **Zero** |
| Layer 1 (Deterministic) | Contact, sections, length, parse quality | **Zero** |
| Layer 2 (Semantic) | Embedding-based skill match vs JD | **Zero** (local model) |
| LLM Rewriter | Optional Groq call → structured JSON | **One** (opt-in) |
| Renderers | Jinja2 / python-docx / WeasyPrint → files | **Zero** |

The same structured JSON feeds all three output formats. The LLM never generates PDF, DOCX, or LaTeX directly.

## Quick start (local)

```bash
cd resume_scorer
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # optional: add GROQ_API_KEY
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501).

> **Note:** First run downloads the `all-MiniLM-L6-v2` embedding model (~90 MB). Core scoring works offline after that; AI suggestions need `GROQ_API_KEY`.

### Windows notes

- **Use a virtual environment** — installing into global Python can leave mismatched `torch` / `torchvision` versions and break Layer 2 (skill match). `requirements.txt` pins `torch==2.6.0` and `torchvision==0.21.0` together.
- **PDF export** — WeasyPrint needs GTK/Pango libraries that pip does not provide on Windows. The app hides the PDF checkbox locally; use **DOCX** or **TeX**, or run via **Docker** for PDF.
- After changing dependencies, restart Streamlit: stop the terminal (`Ctrl+C`) and run `streamlit run app.py` again.

## Docker (local or EC2)

WeasyPrint's Pango/Cairo dependencies are baked into the Dockerfile — no manual `apt-get` on the host beyond Docker itself.

```bash
cd resume_scorer
cp .env.example .env   # add GROQ_API_KEY if using AI suggestions
docker build -t resumematch .
docker run -d -p 8501:8501 --env-file .env --name resumematch resumematch
```

Visit `http://localhost:8501` (or `http://<EC2-public-ip>:8501`).

## AWS EC2 deployment

Same pattern as SmartSkale InterviewBot:

1. **Launch instance** — `t2.micro` or `t3.micro` (Ubuntu 22.04+), free tier eligible.
2. **Security group** — allow inbound TCP **8501** (or **80** if you add Nginx later) from your IP or `0.0.0.0/0` for a public demo.
3. **Install Docker** on the instance:
   ```bash
   sudo apt-get update
   sudo apt-get install -y docker.io
   sudo usermod -aG docker $USER
   # log out and back in
   ```
4. **Copy project** — `git clone`, `scp`, or build locally and push to a registry.
5. **Configure secrets** on the instance:
   ```bash
   cd resume_scorer
   cp .env.example .env
   nano .env   # set GROQ_API_KEY
   ```
6. **Build and run**:
   ```bash
   docker build -t resumematch .
   docker run -d -p 8501:8501 --env-file .env --restart unless-stopped resumematch
   ```

Optional: put Nginx on port 80 as a reverse proxy to `:8501` so the URL has no port suffix.

## Project layout

```
resume_scorer/
├── app.py                  # Streamlit UI
├── parser.py               # PDF/DOCX/TXT extraction
├── structurer.py           # Rule-based section & skill extraction
├── scoring/
│   ├── deterministic.py    # Layer 1 checks
│   └── semantic_match.py   # Layer 2 embeddings
├── insights/
│   └── llm_rewriter.py     # Single optional Groq call
├── templates/
│   ├── jacks_tech/         # Tech-focused Jake's-style
│   └── classic_nontech/    # Traditional non-tech layout
├── renderers/
│   ├── docx_renderer.py
│   ├── pdf_renderer.py
│   └── tex_renderer.py
├── skills_taxonomy.json    # ~600 skills for matching
├── Dockerfile
└── requirements.txt
```

## Usage flow

1. Upload resume + optional JD + pick template → **Analyze**
2. Core ATS score appears instantly (no API)
3. Optionally click **Get AI Suggestions** (requires Groq key)
4. **Generate Resume** → download PDF, DOCX, and/or `.tex` source

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | No | Enables AI rewrite suggestions only |

## v1 limitations

- Custom template upload: DOCX only (via docxtpl); starter template included
- No OCR for scanned PDFs
- TeX output is source only (compile locally or on Overleaf)
- No user accounts or persistence

## License

Open source — see repository license file.
