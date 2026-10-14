"""Evidence-weighted credit (EWC) — reward skills that are *used*, not just listed.

A skill that only appears in a comma-separated skills list (or in copy-pasted
template sentences) is a *claim*. A skill that appears inside a sentence that
describes work ("Built an ETL pipeline in Python that cut runtime 40%") is
*evidence*. Keyword stuffing — pasting the job description's skill list into
the resume — produces claims only, so discounting claims makes stuffing stop
paying off.

Rules (deterministic, no model):

* The text is cut into clauses at sentence ends, line breaks and bullet symbols.
* A clause is **list-like** when its comma / semicolon / slash / pipe separated
  items have a median length of at most ``MAX_ITEM_TOKENS`` tokens
  (e.g. "Python, SQL, Power BI").
* A clause is also list-like when, after masking skill names, it is identical
  to another clause that names *different* skills — the "one templated sentence
  per skill" trick ("Built features using Python." / "Built features using SQL.").
  Exact duplicate bullets are not penalised.
* A mention outside list-like clauses is **prose evidence**. A matched skill
  earns full credit with prose evidence and ``list_credit()`` (default 0.5)
  when every mention is list-like.

Evaluated on 1,759 labelled resume–JD pairs (see ``scripts/evaluate_dataset.py``):
on clean resumes the label agreement is unchanged or slightly better, and the
keyword score's gain from a pasted skill list falls by about 45% at λ = 0.5 and
to zero at λ = 0.
"""

from __future__ import annotations

import os
import re
from collections import defaultdict
from functools import lru_cache
from typing import Iterable, Optional

import numpy as np

from scoring.skill_aliases import _build_lookup

CLAUSE_SPLIT = re.compile(r"[.!?\n•●▪▸►]+")
ITEM_SPLIT = re.compile(r"[,;|/]")
TOKEN_RE = re.compile(r"[A-Za-z0-9+#.&-]+")
MAX_ITEM_TOKENS = 3

# Section-header words that may prefix a skills list ("Skills: Python, SQL")
_HEADER_PREFIX = re.compile(
    r"^\s*(?:technical\s+)?(?:skills?|technologies|tools(?:\s+and\s+technologies)?|"
    r"languages|frameworks|core\s+competencies|competencies|other|libraries)\s*[:\-–—]\s*",
    re.I,
)


def list_credit() -> float:
    """Credit multiplier λ for skills that are only listed (env EVIDENCE_LIST_CREDIT)."""
    raw = os.getenv("EVIDENCE_LIST_CREDIT", "").strip()
    try:
        value = float(raw) if raw else 0.5
    except ValueError:
        value = 0.5
    return max(0.0, min(1.0, value))


def _term_regex(term: str) -> re.Pattern[str]:
    escaped = re.escape(term.lower().strip())
    return re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", re.I)


@lru_cache(maxsize=4096)
def _cached_regex(term: str) -> re.Pattern[str]:
    return _term_regex(term)


class EvidenceIndex:
    """Index of one resume text: which clauses are list-like vs prose."""

    def __init__(self, text: str, skills: Optional[Iterable[str]] = None):
        self.text = text or ""
        self._lookup = _build_lookup()
        self.clauses: list[tuple[int, int, bool]] = []
        pos = 0
        for m in list(CLAUSE_SPLIT.finditer(self.text)) + [None]:
            end = m.start() if m else len(self.text)
            seg = _HEADER_PREFIX.sub("", self.text[pos:end])
            items = [it for it in ITEM_SPLIT.split(seg) if it.strip()]
            lens = [len(TOKEN_RE.findall(it)) for it in items] or [0]
            self.clauses.append((pos, end, float(np.median(lens)) <= MAX_ITEM_TOKENS))
            pos = m.end() if m else len(self.text)
        self._apply_template_rule(list(skills or []))
        self._starts = np.array([c[0] for c in self.clauses]) if self.clauses else np.zeros(0, int)
        self._cache: dict[str, Optional[bool]] = {}

    # -- template detection -------------------------------------------------
    def _apply_template_rule(self, skills: list[str]) -> None:
        if not skills or not self.text:
            self.template_clauses = 0
            return
        mask = np.zeros(len(self.text) + 1, dtype=bool)
        for skill in skills:
            for m in _cached_regex(skill).finditer(self.text):
                mask[m.start():m.end()] = True
        skeletons: list[Optional[str]] = []
        fillers: list[tuple[str, ...]] = []
        for a, b, _ in self.clauses:
            seg = self.text[a:b]
            chars = ["#" if mask[a + i] else ch for i, ch in enumerate(seg)]
            sk = re.sub(r"#+", "#", re.sub(r"\s+", " ", "".join(chars).lower())).strip()
            flags = "".join("1" if mask[a + i] else "0" for i in range(len(seg)))
            fill = tuple(seg[x.start():x.end()].lower() for x in re.finditer(r"1+", flags))
            skeletons.append(sk if "#" in sk and len(sk.split()) >= 3 else None)
            fillers.append(fill)
        groups: dict[str, set[tuple[str, ...]]] = defaultdict(set)
        for sk, fl in zip(skeletons, fillers):
            if sk:
                groups[sk].add(fl)
        template = [sk is not None and len(groups[sk]) >= 2 for sk in skeletons]
        self.template_clauses = sum(template)
        self.clauses = [(a, b, lst or tp) for (a, b, lst), tp in zip(self.clauses, template)]

    # -- queries ------------------------------------------------------------
    def _clause_is_list(self, start: int) -> bool:
        k = int(np.searchsorted(self._starts, start, side="right")) - 1
        return self.clauses[max(k, 0)][2] if self.clauses else False

    def has_prose_evidence(self, term: str) -> Optional[bool]:
        """True if any mention of term (or an alias) is in prose; None if never mentioned."""
        key = term.lower().strip()
        if key in self._cache:
            return self._cache[key]
        occurrences: list[int] = []
        for variant in [key, *sorted(self._lookup.get(key, ()))]:
            occurrences += [m.start() for m in _cached_regex(variant).finditer(self.text)]
        result = None if not occurrences else any(not self._clause_is_list(o) for o in occurrences)
        self._cache[key] = result
        return result

    def factor(self, term: str, lam: Optional[float] = None) -> float:
        """Credit multiplier for a matched skill: 1.0 with prose evidence, else λ."""
        lam = list_credit() if lam is None else lam
        evidence = self.has_prose_evidence(term)
        if evidence is None:
            return 1.0  # matched through structure we cannot localise — no penalty
        return 1.0 if evidence else lam

    def status(self, term: str) -> str:
        evidence = self.has_prose_evidence(term)
        if evidence is None:
            return "unknown"
        return "demonstrated" if evidence else "listed_only"


def detect_stuffing(index: EvidenceIndex, jd_skills: list[str]) -> list[str]:
    """Warnings when the JD's skill list looks pasted into the resume."""
    warnings: list[str] = []
    if not jd_skills or not index.text:
        return warnings
    jd_lower = [s.lower() for s in jd_skills]
    # Merge consecutive list-like clauses: PDFs wrap one long skills list over lines.
    blocks: list[tuple[int, int]] = []
    for a, b, is_list in index.clauses:
        if not is_list:
            continue
        if blocks and not index.text[blocks[-1][1]:a].strip(" \n\t•.;,"):
            blocks[-1] = (blocks[-1][0], b)
        else:
            blocks.append((a, b))
    for a, b in blocks:
        clause = index.text[a:b]
        hits = [s for s in jd_lower if _cached_regex(s).search(clause)]
        if len(jd_skills) < 4 or len(hits) < 0.7 * len(jd_skills):
            continue
        # A long, JD-shaped list is normal for a good candidate *if* the skills are
        # also used in bullets. Warn only when most of them are never demonstrated.
        unproven = [s for s in hits if index.has_prose_evidence(s) is False]
        if len(unproven) >= 0.7 * len(hits):
            warnings.append(
                f"One list in your resume contains {len(hits)} of the {len(jd_skills)} JD skills, and "
                f"{len(unproven)} of them appear nowhere else — this looks like a pasted keyword list. "
                "Show each skill inside a project or experience bullet instead."
            )
            break
    if index.template_clauses >= 3:
        warnings.append(
            f"{index.template_clauses} sentences differ only by the skill name — templated keyword sentences "
            "are treated as a skills list."
        )
    return warnings
