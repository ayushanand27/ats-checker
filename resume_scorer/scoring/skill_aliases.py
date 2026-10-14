"""Skill acronym and synonym expansion for Layer 2 semantic matching."""

from __future__ import annotations

# Bidirectional alias groups — any member matches any other in the group
ALIAS_GROUPS: list[frozenset[str]] = [
    frozenset({"ml", "machine learning"}),
    frozenset({"ai", "artificial intelligence"}),
    frozenset({"nlp", "natural language processing"}),
    frozenset({"sql", "structured query language"}),
    frozenset({"power bi", "powerbi", "microsoft power bi"}),
    frozenset({"excel", "microsoft excel", "ms excel"}),
    frozenset({"aws", "amazon web services"}),
    frozenset({"gcp", "google cloud", "google cloud platform"}),
    frozenset({"ci/cd", "cicd", "continuous integration", "continuous deployment"}),
    frozenset({"rest", "rest api", "restful api"}),
    frozenset({"js", "javascript"}),
    frozenset({"ts", "typescript"}),
    frozenset({"k8s", "kubernetes"}),
    frozenset({"seo", "search engine optimization"}),
    frozenset({"ui", "user interface"}),
    frozenset({"ux", "user experience"}),
    frozenset({"etl", "extract transform load"}),
    frozenset({"bi", "business intelligence"}),
    frozenset({"salesforce", "salesforce crm", "sfdc"}),
    frozenset({"power automate", "microsoft power automate", "powerautomate"}),
    frozenset({"rag", "retrieval augmented generation"}),
    frozenset({"llm", "large language model", "large language models"}),
    frozenset({"api", "apis", "application programming interface"}),
    frozenset({"oop", "object oriented programming", "object-oriented programming"}),
    frozenset({"tcp/ip", "tcp ip", "tcpip"}),
    frozenset({"ccna", "cisco ccna"}),
    # Added in v2 — common spelling variants seen in Indian and global JDs
    frozenset({"react", "react.js", "reactjs"}),
    frozenset({"node.js", "nodejs", "node js"}),
    frozenset({"next.js", "nextjs"}),
    frozenset({"vue.js", "vue", "vuejs"}),
    frozenset({"angular", "angularjs", "angular.js"}),
    frozenset({"postgresql", "postgres"}),
    frozenset({"mongodb", "mongo db"}),
    frozenset({"sql server", "ms sql", "mssql", "microsoft sql server"}),
    frozenset({"go", "golang"}),
    frozenset({"generative ai", "genai", "gen ai"}),
    frozenset({"scikit-learn", "sklearn", "scikit learn"}),
    frozenset({"c#", "c sharp", "csharp"}),
    frozenset({".net", "dotnet"}),
    frozenset({"html", "html5"}),
    frozenset({"css", "css3"}),
    frozenset({"azure", "microsoft azure"}),
    frozenset({"spring boot", "springboot"}),
    frozenset({"microsoft office", "ms office"}),
    frozenset({"data structures", "dsa", "data structures and algorithms"}),
    frozenset({"internet of things", "iot"}),
    frozenset({"hugging face", "huggingface"}),
    frozenset({"vector database", "vector db", "vector databases"}),
    frozenset({"mlops", "ml ops"}),
    frozenset({"devops", "dev ops"}),
    frozenset({"restful", "restful apis", "rest apis"}),
]

_LOOKUP: dict[str, set[str]] = {}


def _build_lookup() -> dict[str, set[str]]:
    if _LOOKUP:
        return _LOOKUP
    for group in ALIAS_GROUPS:
        normalized = {s.lower().strip() for s in group}
        for term in normalized:
            _LOOKUP[term] = normalized - {term}
    return _LOOKUP


def expand_skills_for_matching(skills: list[str]) -> list[str]:
    """Return deduplicated skills plus known aliases (for embedding match only)."""
    lookup = _build_lookup()
    seen: set[str] = set()
    out: list[str] = []
    for skill in skills:
        key = skill.lower().strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(skill)
        for alias in lookup.get(key, ()):
            if alias not in seen:
                seen.add(alias)
                out.append(alias)
    return out
