# ResumeMatch — Demo Script

**Total time:** ~4–5 min · **Audio:** optional (lines double as on-screen captions)

---

## [0:00–0:20] Intro — Landing page

**Screen:** `http://localhost:3000`

> "Hi, this is **ResumeMatch** — a two-layer ATS resume checker I built. It scores how well a resume matches a job description, gives AI-powered rewrite suggestions, and exports polished resumes in PDF, DOCX, and LaTeX. The core scoring is fully deterministic and runs locally — zero API calls, zero cost."

**Action:** Hover the 4 feature cards (2-Layer Score, AI Chat, AI Rewrite, Export) → click **Get Started**.

---

## [0:20–0:50] Upload & Configure

**Screen:** Analyze page

> "The workflow is simple. I upload my resume — PDF, DOCX, or TXT. Then I add a job description, and here's a nice touch: I can **paste** it, **upload a file**, or **fetch it directly from a public job URL**."

**Action:**
1. Drop the resume PDF.
2. Upload the JD file.
3. Show the 3 tabs: Paste / Upload / From URL.
4. Show the output-template dropdown → click **Analyze Resume**.

---

## [0:50–1:40] ATS Score (core feature)

**Screen:** Score card (gauge + Layer 1 / Layer 2)

> "Here's the two-layer score. **Layer 1** is structure and hygiene — parseability, sections, formatting — weighted 35%. **Layer 2** is semantic skill matching using local embeddings — weighted 65%.
>
> Notice this is an **honest score of 35**. My resume is AI and machine-learning focused, but this is a marketing analytics role — so Layer 2 correctly shows a low match. This is exactly how real ATS systems like Workday or Greenhouse behave. It doesn't just flatter you — it tells the truth."

**Action:** Point to the gauge, Layer 1 (100), Layer 2 (0).

---

## [1:40–2:10] Top fixes + keyword analysis

**Screen:** Top fixes + keyword match section

> "Below the score, I get **prioritized fixes** in industry-standard coaching order. And this is the **keyword analysis** — it shows keyword overlap, which ATS systems weight around 30–40%. I can see the exact JD keywords I'm missing — Data Analytics, KPI Reporting, Web Analytics, SEO — and whether they appear in my summary, skills, or experience."

**Action:** Top fixes → missing-keyword chips → scroll the keyword map.

---

## [2:10–2:45] Parsed ATS view

**Screen:** "What the ATS extracted" + Layer 1 checks

> "This is one of my favorite features — the **parsed view**. This is exactly what an ATS extracts from my resume: name, contact details, all 35 skills, experience, and education. If something parses wrong here, it'll parse wrong in a real ATS too — so you catch problems before a recruiter's system does. And below, every Layer 1 hygiene check is passing — 100 out of 100."

**Action:** Scroll parsed fields → show Layer 1 green checks.

---

## [2:45–3:40] AI rewrite (star feature)

**Screen:** AI Suggestions → before/after

> "Now the powerful part. I click **Get AI Suggestions** — this makes a single Groq LLM call. It rewrites my resume to target the JD and shows me a **before-and-after comparison** side by side, plus a change log of exactly what it did.
>
> It naturally worked Data Analytics, KPI Reporting, and Web Analytics into my bullets and skills — **without fabricating any experience**. And critically, the score **re-runs automatically**, so I see my match rate improve in real time. This is the same accept-and-re-score loop that paid tools like Jobscan charge for."

**Action:** Click **Get AI Suggestions** → show "What changed" → scroll Before/After columns → show the new score.

---

## [3:40–4:10] Accounts + profile tailoring

**Screen:** Signed-in profile & history panel

> "This is also a full product. I can **sign in**, save my resume as a **master profile** once, then tailor it to any new job description in one click — it auto re-scores. Every run is saved in my **history**. Auth is self-contained with PBKDF2 hashing and JWT sessions."

**Action:** Show **Save current resume as my profile** → **Generate from my profile**.

---

## [4:10–4:40] Export + observability (close)

**Screen:** Download section → Langfuse dashboard

> "Finally, I export the polished resume in **PDF, DOCX, or LaTeX** — all generated from one structured source.
>
> And behind the scenes, every AI call is traced in **Langfuse** for full LLM observability — so I can debug and monitor the AI features like a production system."

**Action:** DOCX/PDF/TeX checkboxes → **Preview & Download** → then show one trace in the Langfuse dashboard.

> "That's ResumeMatch — deterministic ATS scoring, semantic matching, AI rewriting, and multi-format export, all in one local tool. Thanks for watching."

---

## Recording tips

- Show **two analyses** for contrast: one honest low-match (score ~35) and one matching JD (score 80+).
- Before starting, click **Clear this data** to clear the cached session.
- Record at **1080p**, browser zoom at 100%.
- No audio? Use these lines as on-screen captions/overlays.
