# ResumeMatch API

REST API wrapping the same Python logic used by the Streamlit app (`parser`, `structurer`, `scoring`, `insights`, `renderers`). Intended as the contract for a future Next.js frontend.

## Run locally

```bash
cd resume_scorer
pip install -r requirements.txt
cp .env.example .env   # optional: GROQ_API_KEY for /api/rewrite

uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

- API base: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`
- Health check: `GET /api/health`

CORS allows `http://localhost:3000` by default. Add production origins via env:

```bash
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

---

## `GET /api/health`

**Response**

```json
{ "status": "ok" }
```

---

## `POST /api/analyze`

Parse and score a resume, optionally against a job description.

**Content-Type:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `resume` | file | yes | `.pdf`, `.docx`, or `.txt` |
| `jd_text` | string | no | Job description as plain text |
| `jd_file` | file | no | Job description file (used if `jd_text` empty) |
| `template` | string | no | `jacks_tech` (default), `classic_nontech`, or `custom` |

**Response** `200 application/json`

```json
{
  "core_score": 72.5,
  "jd_provided": true,
  "template": "jacks_tech",
  "parse_warning": null,
  "resume_struct": { "...": "parsed resume JSON from structurer.py" },
  "jd_struct": { "...": "parsed JD JSON, or null" },
  "layer1": {
    "score": 85.0,
    "checks": [
      { "name": "Contact email", "passed": true, "reason": "...", "weight": 10, "score": 10 }
    ],
    "word_count": 656
  },
  "layer2": {
    "score": 65.0,
    "matched_required": ["Python", "Git"],
    "missing_required": ["Kubernetes"],
    "matched_preferred": [],
    "missing_preferred": [],
    "experience_note": null
  },
  "gaps": {
    "missing_required": ["Kubernetes"],
    "missing_preferred": [],
    "experience_note": null
  }
}
```

- `core_score`: combined score (35% Layer 1 + 65% Layer 2 when JD provided; Layer 1 only otherwise).
- `layer2` is `null` when no JD is provided, or if the embedding model fails to load.
- `gaps` is pre-computed for convenience when calling `/api/rewrite`.

**Example**

```bash
curl -s -X POST http://localhost:8000/api/analyze \
  -F "resume=@resume.pdf" \
  -F "jd_text=Software Engineer with Python and TCP/IP networking..." \
  -F "template=jacks_tech"
```

---

## `POST /api/rewrite`

Optional single Groq call for AI rewrite suggestions. Requires `GROQ_API_KEY` in environment.

**Content-Type:** `application/json`

**Request body**

```json
{
  "resume_struct": { "...": "from /api/analyze response" },
  "jd_struct": { "...": "from /api/analyze, or null" },
  "gaps": {
    "missing_required": ["Kubernetes"],
    "missing_preferred": [],
    "experience_note": null
  }
}
```

Use the `gaps` object from `/api/analyze` directly, or omit it for defaults.

**Response** `200 application/json`

```json
{
  "summary": "Rewritten professional summary...",
  "skills": ["Python", "Git", "..."],
  "experience": [
    {
      "title": "Software Engineer Intern",
      "company": "Acme Corp",
      "dates": "Jun 2024 - Present",
      "bullets": ["..."]
    }
  ],
  "education": [{ "degree": "...", "institution": "...", "dates": "..." }],
  "projects": [{ "name": "...", "description": "...", "bullets": ["..."] }],
  "change_log": ["Reorganized experience section...", "..."]
}
```

**Errors**

| Status | Cause |
|--------|-------|
| 400 | Missing `GROQ_API_KEY` |
| 502 | Groq API or JSON parse failure |

**Example**

```bash
curl -s -X POST http://localhost:8000/api/rewrite \
  -H "Content-Type: application/json" \
  -d @rewrite_request.json
```

---

## `POST /api/generate`

Render a structured resume to DOCX, PDF, or TeX.

**Content-Type:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `resume_json` | string | yes | JSON string of `resume_struct` from `/api/analyze` |
| `template` | string | no | `jacks_tech`, `classic_nontech`, or `custom` |
| `format` | string | no | `docx` (default), `pdf`, or `tex` |
| `rewritten_json` | string | no | Content fields from `/api/rewrite` (merged with resume contact/name) |
| `custom_template` | file | if `template=custom` | `.docx` with Jinja2 placeholders |

**Response** `200` — binary file with headers:

- `Content-Type`: `application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, or `application/x-tex`
- `Content-Disposition`: `attachment; filename="resume.<ext>"`

**Errors**

| Status | Cause |
|--------|-------|
| 400 | Invalid JSON, custom template error, custom+pdf/tex |
| 503 | PDF unavailable (e.g. Windows without WeasyPrint libs) |

**Example — DOCX with built-in template**

```bash
curl -s -X POST http://localhost:8000/api/generate \
  -F "resume_json=$(cat resume_struct.json)" \
  -F "template=jacks_tech" \
  -F "format=docx" \
  -o resume.docx
```

**Example — DOCX with AI rewrite**

```bash
curl -s -X POST http://localhost:8000/api/generate \
  -F "resume_json=$(cat resume_struct.json)" \
  -F "rewritten_json=$(cat rewrite_response.json)" \
  -F "template=classic_nontech" \
  -F "format=docx" \
  -o resume.docx
```

---

## Score weights

| Scenario | Formula |
|----------|---------|
| JD provided + Layer 2 | `0.35 × Layer1 + 0.65 × Layer2` |
| No JD | `Layer1` only |

Same constants as `app.py` / Streamlit UI.

---

## Notes for Next.js integration

1. Call `/api/analyze` first; store `resume_struct`, `jd_struct`, `gaps`, and scores in client state.
2. Optionally call `/api/rewrite` with those structures.
3. Call `/api/generate` with `resume_json` and optional `rewritten_json` for downloads.
4. Streamlit (`streamlit run app.py`) remains independent — no changes required to use the API.
