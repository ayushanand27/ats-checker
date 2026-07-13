# ResumeMatch — Demo Shoot Script (final)

**Status (verified just now):** API + frontend UP · e2e **0 failures** · auth/profile **passed**  
**Only known limit:** PDF export may fail on Windows → **use DOCX in the demo**

| Open now | Link |
|----------|------|
| **Analyze (main)** | http://localhost:3000/analyze |
| Landing | http://localhost:3000 |
| API docs (optional) | http://localhost:8000/docs |
| GitHub | https://github.com/ayushanand27/ats-checker |

---

## Before you hit Record (60 sec)

1. Open **http://localhost:3000/analyze**
2. Click **Clear this data** (page bottom)
3. Ready files:
   - Your **resume PDF**
   - A **matching JD** (Python / SQL / data / automation skills) — so Layer 2 looks strong on camera
4. Browser zoom **100%**, window fullscreen
5. Already **signed in** (optional but nicer) — or sign in during Step 7

**Do NOT use a totally unrelated JD for the main take** (that gives a low score and looks confusing on camera).

---

## What you will see (so you don’t panic)

| Moment | Expected | Say this if asked |
|--------|----------|-------------------|
| No JD | “Structure Health” ~90+, not “ATS Match” | “Without a JD there is no real ATS match score.” |
| Matching JD | High score (often **80–97**) | “Strong skill alignment.” |
| Unrelated JD | Low/mid score | “Honest — resume doesn’t match this role.” |
| After AI | Score may move only a little | “Already close; it won’t invent fake skills.” |
| Download | **DOCX works**; PDF may fail on Windows | Click DOCX only. |

---

## RECORD — 8 steps (~3.5 min)

### STEP 1 — Intro (10s)
**Open:** http://localhost:3000  

**Say:**  
> “This is ResumeMatch — an ATS resume checker I built. It scores your resume against a job description, suggests AI rewrites, and exports DOCX, PDF, and LaTeX.”

**Click:** **Get Started**

---

### STEP 2 — Upload (30s)
**Page:** http://localhost:3000/analyze  

**Say:**  
> “Upload the resume, then the job description — paste, file, or URL.”

**Do:**
1. Drop **resume**
2. JD tab → **Upload file** → drop **matching JD**
3. Quickly show **Paste** and **From URL** tabs
4. Click **Analyze Resume**
5. Wait for the gauge

---

### STEP 3 — Score (40s) ⭐
**Look at:** big gauge + Layer 1 / Layer 2  

**Say:**  
> “Here’s the ATS match score. Layer 1 is structure and parse health. Layer 2 is skill match against the JD. Weighted 35% structure and 65% skills — how real ATS systems think.”

**Point:** overall score → Layer 1 → Layer 2  

**If score is high:**  
> “Strong match for this role.”

---

### STEP 4 — Fixes + keywords (30s)
**Scroll:** Top fixes → Keyword match  

**Say:**  
> “Prioritized fixes first, then exact missing JD keywords and where they appear in the resume.”

**Point:** fix #1 → Missing keywords → Keyword map (quick scroll)

---

### STEP 5 — Parsed ATS view (20s)
**Scroll:** What the ATS extracted  

**Say:**  
> “This is what an ATS extracts — name, contact, skills, experience. Catch parse issues before a recruiter’s system does.”

**Point:** Name → Skills → Experience  

*(Optional 5s: glance at Layer 1 green checks.)*

---

### STEP 6 — AI rewrite (45s) ⭐
**Scroll:** 03 · AI Suggestions  

**Say:**  
> “One Groq call — before and after, a change log, then auto re-score. It never fabricates experience.”

**Do:**
1. Click **Get AI Suggestions**
2. Wait for success banner
3. Point **What changed**
4. Point **Before → After** score
5. Quick scroll of before/after text

---

### STEP 7 — Profile (25s)
**Top right / profile card**  

**Say:**  
> “Sign in, save a master profile once, then generate a tailored resume from any new JD.”

**Do:**
1. Show you’re signed in (or Sign in)
2. Click **Save current resume as my profile** (or point at it)
3. Point **Generate from my profile**

---

### STEP 8 — Download + end (20s)
**Scroll:** 04 · Download  

**Say:**  
> “Export DOCX from the same structured data. That’s ResumeMatch — local ATS scoring, AI rewrite, multi-format export. Code is on GitHub.”

**Do:**
1. Check **DOCX only** (skip PDF on Windows)
2. Click **Preview & Download**
3. End — say: `github.com/ayushanand27/ats-checker`

---

## One-line cheat sheet (keep this on a second screen)

`Landing → Get Started → Upload resume+JD → Analyze → Score L1/L2 → Fixes/Keywords → Parsed view → AI Suggestions → Save profile → DOCX download → GitHub`

---

## If something goes wrong mid-recording

| Problem | Fix |
|---------|-----|
| Old score on screen | **Clear this data** → re-upload |
| “Structure Health” only | You forgot JD — upload JD → Analyze again |
| AI button errors | Check Groq key / wait 5s → retry once |
| PDF fails | Use **DOCX** — say “DOCX export” |
| Page blank | Refresh http://localhost:3000/analyze |

You’re good to shoot.
