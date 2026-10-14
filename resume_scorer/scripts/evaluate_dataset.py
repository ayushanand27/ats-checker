"""Evaluate ResumeMatch v1 (old formula) vs v2 (this version) on public labelled data.

Dataset: test split of https://huggingface.co/datasets/cnamuangtoun/resume-job-description-fit
(1,759 resume-JD pairs labelled No Fit / Potential Fit / Good Fit).

    python scripts/evaluate_dataset.py --csv test.csv --out eval_results.json

Reports, for v1 and v2:
  * ROC-AUC (Fit vs. No Fit), pooled and within-JD (mean over JDs with both classes)
  * 1-of-10 ranking of the true Good-Fit resume against 9 non-fitting resumes, with
    expected Hit@1 / MRR under random tie-breaking (ties are common for keyword scores)
  * keyword stuffing: 200 No-Fit resumes with the JD's skill list pasted in — share that
    then reach the median Good-Fit score
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402

from api.deps import compose_score_detailed, get_context_model, get_embedding_model  # noqa: E402
from scoring.contextual_match import calibrate, chunk_words  # noqa: E402
from scoring.deterministic import score_deterministic  # noqa: E402
from scoring.semantic_match import score_semantic_match  # noqa: E402
from scoring.skill_aliases import expand_skills_for_matching  # noqa: E402
from structurer import structure_jd, structure_resume  # noqa: E402


class Cached:
    """Memoise sentence embeddings (skills repeat across thousands of pairs)."""

    def __init__(self, model):
        self.model, self.cache = model, {}

    def encode(self, texts, convert_to_numpy=True, normalize_embeddings=False, **_):
        missing = [t for t in dict.fromkeys(texts) if t not in self.cache]
        if missing:
            for t, e in zip(missing, self.model.encode(missing, batch_size=64, normalize_embeddings=normalize_embeddings)):
                self.cache[t] = e
        return np.stack([self.cache[t] for t in texts])


def legacy_layer2(resume, jd, model, threshold=0.6):
    """v1 Layer 2: binary credit for any exact/alias/embedding match, no evidence weighting."""
    req, pref = jd.get("required_skills") or [], jd.get("preferred_skills") or []
    if not req and not pref:
        req = jd.get("all_skills") or []
    if not req and not pref:
        return None
    rs = expand_skills_for_matching(resume.get("skills", []))
    if not rs:
        return 0.0
    E = model.encode(rs)
    E = E / np.linalg.norm(E, axis=1, keepdims=True)
    def hit(s):
        e = model.encode([s])[0]
        return float(np.max(E @ (e / np.linalg.norm(e)))) >= threshold
    earned = 2.0 * sum(hit(s) for s in req) + 1.0 * sum(hit(s) for s in pref)
    return round(100 * earned / (2.0 * len(req) + len(pref)), 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out", default="eval_results.json")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    t0 = time.time()

    df = pd.read_csv(args.csv)
    df["y"] = df.label.map({"No Fit": 0, "Potential Fit": 1, "Good Fit": 2})
    skill_model = Cached(get_embedding_model())
    ctx_model = get_context_model()

    R = {t: structure_resume(t) for t in df.resume_text.unique()}
    J = {t: structure_jd(t) for t in df.job_description_text.unique()}
    L1 = {t: score_deterministic(r)["score"] for t, r in R.items()}
    print(f"structured in {time.time() - t0:.0f}s", flush=True)

    # Contextual layer: mean-pooled chunk embeddings per resume, one embedding per JD.
    def doc_vec(text):
        e = ctx_model.encode(chunk_words(text), normalize_embeddings=True).mean(0)
        return e / np.linalg.norm(e)
    RV = {t: doc_vec(t) for t in R}
    JV = {t: v for t, v in zip(J, ctx_model.encode(list(J), normalize_embeddings=True))}
    print(f"embedded in {time.time() - t0:.0f}s", flush=True)

    def scores(rt, jt, res=None, rv=None):
        res = res or R[rt]
        l1 = score_deterministic(res)["score"] if res is not R.get(rt) else L1[rt]
        old_l2 = legacy_layer2(res, J[jt], skill_model)
        new = score_semantic_match(res, J[jt], skill_model)
        new_l2 = new["score"] if new else None
        ctx = calibrate(float((rv if rv is not None else RV[rt]) @ JV[jt]))
        v1 = compose_score_detailed(l1, old_l2, True)["score"]
        v2 = compose_score_detailed(l1, new_l2, True, ctx)["score"]
        return {"v1": v1, "v2": v2, "skills_v1": old_l2 or 0.0, "skills_v2": new_l2 or 0.0, "context": ctx}

    rows = [scores(r, j) for r, j in zip(df.resume_text, df.job_description_text)]
    S = pd.DataFrame(rows)
    y = (df.y >= 1).values
    out = {"n_pairs": len(df), "methods": {}}

    def within_jd(col):
        vals = []
        for _, idx in df.groupby("job_description_text").groups.items():
            idx = list(idx)
            if y[idx].min() != y[idx].max():
                vals.append(roc_auc_score(y[idx], S[col].values[idx]))
        return round(float(np.mean(vals)), 3)

    for col in S.columns:
        out["methods"][col] = {"auc": round(float(roc_auc_score(y, S[col])), 3), "within_jd_auc": within_jd(col)}
    print(f"agreement done in {time.time() - t0:.0f}s", flush=True)

    # Ranking
    rnd = random.Random(args.seed)
    fit = set(zip(df.job_description_text[df.y >= 1], df.resume_text[df.y >= 1]))
    pool_all = list(R)
    good = [i for i in df.index[df.y == 2] if J[df.job_description_text[i]]["all_skills"]]
    rr = {k: [] for k in ("v1", "v2", "context")}
    h1 = {k: [] for k in rr}
    for i in good:
        jt, rt = df.job_description_text[i], df.resume_text[i]
        cands = [rt] + rnd.sample([r for r in pool_all if r != rt and (jt, r) not in fit], 9)
        sc = [scores(c, jt) for c in cands]
        for k in rr:
            v = np.array([s[k] for s in sc])
            g = int((v[1:] > v[0]).sum()); t = int((v[1:] == v[0]).sum())
            ranks = np.arange(g + 1, g + t + 2)
            rr[k].append(float(np.mean(1 / ranks))); h1[k].append(float(np.mean(ranks == 1)))
    out["ranking"] = {k: {"mrr": round(float(np.mean(rr[k])), 3), "hit1": round(float(np.mean(h1[k])), 3)} for k in rr}
    out["ranking"]["n_queries"] = len(good)
    print(f"ranking done in {time.time() - t0:.0f}s", flush=True)

    # Keyword stuffing
    nofit = rnd.sample([i for i in df.index[df.y == 0] if J[df.job_description_text[i]]["all_skills"]], 200)
    ref = {k: float(S.loc[df.y == 2, k].median()) for k in ("v1", "v2")}
    stuff = {k: {"before": [], "after": []} for k in ref}
    for i in nofit:
        rt, jt = df.resume_text[i], df.job_description_text[i]
        stuffed = rt + "\nSkills\n" + ", ".join(J[jt]["all_skills"])
        a, b = scores(rt, jt), scores(stuffed, jt, res=structure_resume(stuffed), rv=doc_vec(stuffed))
        for k in ref:
            stuff[k]["before"].append(a[k]); stuff[k]["after"].append(b[k])
    out["stuffing"] = {
        k: {
            "mean_before": round(float(np.mean(v["before"])), 1),
            "mean_after": round(float(np.mean(v["after"])), 1),
            "pass_rate_before": round(float(np.mean(np.array(v["before"]) >= ref[k])), 3),
            "pass_rate_after": round(float(np.mean(np.array(v["after"]) >= ref[k])), 3),
        }
        for k, v in stuff.items()
    }
    out["seconds"] = round(time.time() - t0)
    Path(args.out).write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
