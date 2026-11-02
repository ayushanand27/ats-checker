"""Baselines and layer ablation for ResumeMatch v2 on the same 1,759 labelled pairs.

    python scripts/baselines_ablation.py --csv test.csv --out ../docs/baselines_ablation.json

Compares the full v2 score against
  * classic baselines: TF-IDF cosine, BM25 (resume = document, JD = query)
  * embedding baselines: all-MiniLM-L6-v2 and BGE-small (same chunk-and-average recipe, no other layers)
and ablates each layer of v2: structure only, skills only, context only, structure+skills, full.
Metrics match scripts/evaluate_dataset.py: pooled AUC (Fit vs No Fit), within-JD AUC,
and 1-of-10 ranking (MRR / Hit@1, ties broken at random in expectation), same seed.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import sys
from collections import Counter
from pathlib import Path

# Evaluate the default configuration, whatever the shell has set. Must run before the imports
# below, because the context model name is read when the scoring modules are imported.
for _var in ("SCORE_WEIGHTS", "EVIDENCE_LIST_CREDIT", "CONTEXT_MODEL"):
    os.environ.pop(_var, None)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sentence_transformers import SentenceTransformer  # noqa: E402
from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402

from api.deps import compose_score_detailed, get_context_model, get_embedding_model  # noqa: E402
from evaluate_dataset import Cached  # noqa: E402
from scoring.contextual_match import calibrate, chunk_words  # noqa: E402
from scoring.deterministic import score_deterministic  # noqa: E402
from scoring.semantic_match import score_semantic_match  # noqa: E402
from structurer import structure_jd, structure_resume  # noqa: E402

TOKEN = re.compile(r"[a-z0-9+#.]+")


def tok(t: str) -> list[str]:
    return TOKEN.findall(t.lower())


class BM25:
    def __init__(self, docs: list[list[str]], k1=1.5, b=0.75):
        self.k1, self.b = k1, b
        self.N = len(docs)
        self.avg = sum(map(len, docs)) / self.N
        df = Counter(w for d in docs for w in set(d))
        self.idf = {w: math.log(1 + (self.N - n + 0.5) / (n + 0.5)) for w, n in df.items()}

    def score(self, query: list[str], doc: list[str]) -> float:
        tf, L, s = Counter(doc), len(doc), 0.0
        for w in set(query):
            if w in tf:
                f = tf[w]
                s += self.idf.get(w, 0) * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * L / self.avg))
        return s


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out", default="baselines_ablation.json")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    df = pd.read_csv(args.csv)
    df["y"] = df.label.map({"No Fit": 0, "Potential Fit": 1, "Good Fit": 2})
    skill_model = Cached(get_embedding_model())
    bge = get_context_model()
    minilm = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    R = {t: structure_resume(t) for t in df.resume_text.unique()}
    J = {t: structure_jd(t) for t in df.job_description_text.unique()}
    L1 = {t: score_deterministic(r)["score"] for t, r in R.items()}

    def vecs(model):
        def dv(t):
            e = model.encode(chunk_words(t), normalize_embeddings=True).mean(0)
            return e / np.linalg.norm(e)
        rv = {t: dv(t) for t in R}
        jv = dict(zip(J, model.encode(list(J), normalize_embeddings=True)))
        return rv, jv

    RB, JB = vecs(bge)
    RM, JM = vecs(minilm)
    tf = TfidfVectorizer(sublinear_tf=True, stop_words="english", token_pattern=r"[A-Za-z0-9+#.]{2,}")
    tf.fit(list(R) + list(J))
    TR = dict(zip(R, tf.transform(list(R))))
    TJ = dict(zip(J, tf.transform(list(J))))
    RT = {t: tok(t) for t in R}
    JT = {t: tok(t) for t in J}
    bm = BM25(list(RT.values()))
    cache: dict = {}

    def scores(rt, jt):
        k = (rt, jt)
        if k in cache:
            return cache[k]
        l2 = score_semantic_match(R[rt], J[jt], skill_model)
        l2 = l2["score"] if l2 else None
        ctx = calibrate(float(RB[rt] @ JB[jt]))
        out = {
            "TF-IDF cosine": float((TR[rt] @ TJ[jt].T).toarray()[0, 0]),
            "BM25": bm.score(JT[jt], RT[rt]),
            "MiniLM chunk-avg cosine": float(RM[rt] @ JM[jt]),
            "BGE-small chunk-avg cosine": float(RB[rt] @ JB[jt]),
            "Structure only": L1[rt],
            "Skills only": l2 or 0.0,
            "Context only": ctx,
            "Structure + skills": compose_score_detailed(L1[rt], l2, True)["score"],
            "Full v2 (all three)": compose_score_detailed(L1[rt], l2, True, ctx)["score"],
        }
        cache[k] = out
        return out

    S = pd.DataFrame([scores(r, j) for r, j in zip(df.resume_text, df.job_description_text)])
    y = (df.y >= 1).values
    names = list(S.columns)

    def within(col):
        v = []
        for _, idx in df.groupby("job_description_text").groups.items():
            idx = list(idx)
            if y[idx].min() != y[idx].max():
                v.append(roc_auc_score(y[idx], S[col].values[idx]))
        if not v:
            sys.exit("No JD has both Fit and No-Fit resumes; within-JD AUC is undefined for this data.")
        return float(np.mean(v))

    res = {n: {"auc": round(float(roc_auc_score(y, S[n])), 3), "within_jd_auc": round(within(n), 3)} for n in names}

    rnd = random.Random(args.seed)
    fit = set(zip(df.job_description_text[df.y >= 1], df.resume_text[df.y >= 1]))
    pool = list(R)
    good = [i for i in df.index[df.y == 2] if J[df.job_description_text[i]]["all_skills"]]
    if not good:
        sys.exit("No Good-Fit pair has extracted JD skills; the ranking metrics are undefined for this data.")
    rr = {n: [] for n in names}
    h1 = {n: [] for n in names}
    for i in good:
        jt, rt = df.job_description_text[i], df.resume_text[i]
        cands = [rt] + rnd.sample([r for r in pool if r != rt and (jt, r) not in fit], 9)
        sc = [scores(c, jt) for c in cands]
        for n in names:
            v = np.array([s[n] for s in sc])
            g, t = int((v[1:] > v[0]).sum()), int((v[1:] == v[0]).sum())
            ranks = np.arange(g + 1, g + t + 2)
            rr[n].append(float(np.mean(1 / ranks)))
            h1[n].append(float(np.mean(ranks == 1)))
    for n in names:
        res[n]["mrr"], res[n]["hit1"] = round(float(np.mean(rr[n])), 3), round(float(np.mean(h1[n])), 3)
    out = {
        "command": "python scripts/baselines_ablation.py --csv test.csv",
        "seed": args.seed,
        "dataset": "cnamuangtoun/resume-job-description-fit, test split",
        "models": {
            "skill_matching": "all-MiniLM-L6-v2",
            "context_layer": "BAAI/bge-small-en-v1.5",
            "baseline": "sentence-transformers/all-MiniLM-L6-v2",
        },
        "n_pairs": len(df),
        "n_ranking_queries": len(good),
        "methods": res,
    }
    Path(args.out).write_text(json.dumps(out, indent=2))
    print(f"{'method':32s} {'AUC':>6s} {'wJD':>6s} {'MRR':>6s} {'Hit@1':>6s}")
    for n, m in res.items():
        print(f"{n:32s} {m['auc']:6.3f} {m['within_jd_auc']:6.3f} {m['mrr']:6.3f} {m['hit1']:6.3f}")


if __name__ == "__main__":
    main()
