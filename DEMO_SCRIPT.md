# ResumeMatch — Simple Demo Script (follow this while recording)

**Time:** ~3–4 minutes  
**Open these first (already running locally):**

| Open | Link |
|------|------|
| Tool | http://localhost:3000/analyze |
| Landing (intro only) | http://localhost:3000 |
| API docs (optional end) | http://localhost:8000/docs |
| Repo | https://github.com/ayushanand27/ats-checker |

**Before you record**
1. Open http://localhost:3000/analyze
2. Click **Clear this data** (bottom of page)
3. Keep 2 files ready: **your resume PDF** + **1 JD PDF** that matches your skills (Python/SQL/data) — NOT a totally unrelated role

---

## STEP 1 — Landing (10 sec)

**Click:** http://localhost:3000

**Say:**
> "This is ResumeMatch — I built an ATS checker that scores a resume against a job description, suggests AI rewrites, and exports PDF, DOCX, and LaTeX."

**Do:** Click **Get Started**

---

## STEP 2 — Upload (30 sec)

**You are on:** http://localhost:3000/analyze

**Say:**
> "Step one — upload resume and job description. JD can be paste, file, or URL."

**Do:**
1. Drop resume under **Upload resume**
2. Switch JD to **Upload file** → drop JD
3. Briefly click **Paste text** and **From URL** tabs (show they exist)
4. Click **Analyze Resume**
5. Wait for score

---

## STEP 3 — Score (40 sec) ⭐ main feature

**Look at:** big gauge + Layer 1 / Layer 2

**Say:**
> "This is the ATS match score. Layer 1 is structure and parse health. Layer 2 is skill match against the JD. Together it's 35% structure and 65% skills — same idea as real ATS systems."

**Do:** Point with mouse:
1. Overall score
2. Layer 1 number
3. Layer 2 number

**If score is low:**  
> "This is honest — the JD and resume don't fully match, so the score stays low."

**If score is high:**  
> "Strong match — skills line up with this JD."

---

## STEP 4 — Fixes + keywords (30 sec)

**Scroll to:** Top fixes → Keyword match

**Say:**
> "It tells me what to fix first, and which JD keywords are missing."

**Do:**
1. Point at Top fix #1
2. Point at **Missing JD keywords**
3. Scroll **Keyword map** once

---

## STEP 5 — Parsed view (20 sec)

**Scroll to:** What the ATS extracted

**Say:**
> "This is how an ATS reads the resume — name, contact, skills, experience. If it's wrong here, it'll be wrong in a real ATS too."

**Do:** Point at Name / Skills / Experience

---

## STEP 6 — AI rewrite (45 sec) ⭐ wow moment

**Scroll to:** 03 · AI Suggestions

**Say:**
> "One click AI rewrite with Groq. It suggests changes, shows before and after, then re-scores automatically. It never invents fake experience."

**Do:**
1. Click **Get AI Suggestions**
2. Wait
3. Point at **What changed**
4. Point at **Before → After** score delta
5. Scroll before/after once

---

## STEP 7 — Sign in + save profile (30 sec)

**Top right:** Sign in

**Say:**
> "I can sign in, save this as my master profile, then tailor it to any new JD later."

**Do:**
1. Click **Sign in** (or show you're already signed in)
2. Point at **Save current resume as my profile**
3. Point at **Generate from my profile**

*(If already signed in, just click Save once and show the success message.)*

---

## STEP 8 — Download + close (20 sec)

**Scroll to:** 04 · Download

**Say:**
> "Finally export DOCX or PDF from the same structured data. That's ResumeMatch — local ATS scoring, AI rewrite, and export. Code is on GitHub."

**Do:**
1. Check **DOCX** (and PDF if you want)
2. Click **Preview & Download**
3. End on GitHub link on screen or say the URL:  
   `github.com/ayushanand27/ats-checker`

---

## What NOT to worry about during demo

| You see this | What it means | What to say |
|---|---|---|
| Score not 100 | Good — real ATS never gives perfect | "Honest scoring, not a vanity score." |
| AI score only +1 or +2 | Already close to JD; big jumps need missing skills | "Small lift — I was already partly matched." |
| "Structure Health" with no JD | You forgot JD | Upload a JD — without JD there is no real ATS match |
| PDF download fails on Windows | Known WeasyPrint limit | Use DOCX instead |

---

## Best demo combo (recommended)

1. **First run:** resume + **matching JD** → high score (shows it works)  
2. **Optional second run:** different JD → lower score (shows honesty)

Keep only ONE run if short on time — prefer the matching JD so Layer 2 looks strong on camera.
