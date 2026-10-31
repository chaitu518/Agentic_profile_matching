"""Skill taxonomy for the agent = Milestone 2's taxonomy (api/skills_taxonomy.py) + a few extras,
plus two relations M2 doesn't have:

* IMPLIES        - having X gives partial credit for Y (MySQL => SQL, Next.js => React)
* CONCEPT_GROUPS - a JD saying "Redux or similar" / "Kafka or another ..." accepts any member

Canonical names are M2's, so M2 metadata (skills, skill_years) and M3 requirements line up.
"""
from __future__ import annotations

import re
from functools import lru_cache

from api.skills_taxonomy import SKILL_ALIASES as M2_ALIASES

EXTRA_ALIASES: dict[str, list[str]] = {
    "Jest": ["jest"],
    "Mocha": ["mocha"],
    "Unit Testing": ["unit testing", "unit tests", "unit test", "tdd"],
    "Webpack": ["webpack"],
    "Storybook": ["storybook"],
    "Accessibility": ["accessibility", "accessible", "a11y", "wcag"],
    "Performance Optimization": ["performance optimization", "web performance", "code splitting"],
    "MobX": ["mobx"],
    "Zustand": ["zustand"],
    "Figma": ["figma"],
    "Express": ["express.js", "expressjs"],
    "LangChain": ["langchain"],
    "Vector Databases": ["vector database", "vector databases", "vector db", "chromadb", "pinecone", "faiss"],
    "Hugging Face": ["hugging face", "huggingface"],
    "Helm": ["helm"],
    "ArgoCD": ["argocd", "argo cd"],
    "Firebase": ["firebase"],
}

SKILL_ALIASES: dict[str, list[str]] = {**M2_ALIASES, **EXTRA_ALIASES}

IMPLIES: dict[str, list[str]] = {
    "MySQL": ["SQL"], "PostgreSQL": ["SQL"], "Snowflake": ["SQL"],
    "Next.js": ["React"], "Redux": ["React"], "React": ["JavaScript"], "TypeScript": ["JavaScript"],
    "Angular": ["JavaScript"], "Vue.js": ["JavaScript"], "Node.js": ["JavaScript"],
    "Spring Boot": ["Java", "REST APIs"], "Hibernate": ["Java"],
    "Django": ["Python", "REST APIs"], "Flask": ["Python"], "FastAPI": ["Python", "REST APIs"], "Pandas": ["Python"],
    "PyTorch": ["Deep Learning", "Machine Learning"], "TensorFlow": ["Deep Learning", "Machine Learning"],
    "Deep Learning": ["Machine Learning"], "scikit-learn": ["Machine Learning"],
    "LLMs": ["NLP"], "RAG": ["LLMs"], "LangChain": ["LLMs"], "Hugging Face": ["NLP"],
    "Kubernetes": ["Docker"], "Helm": ["Kubernetes"],
    "Airflow": ["ETL"], "dbt": ["ETL"],
    "Jest": ["Unit Testing"], "JUnit": ["Unit Testing"], "Pytest": ["Unit Testing"], "Mocha": ["Unit Testing"],
    "Cypress": ["Test Automation"], "Selenium": ["Test Automation"],
}

CONCEPT_GROUPS: dict[str, list[str]] = {
    "State Management": ["Redux", "MobX", "Zustand"],
    "Unit Testing": ["Unit Testing", "Jest", "JUnit", "Pytest", "Mocha"],
    "Test Automation": ["Test Automation", "Selenium", "Cypress"],
    "Event Streaming": ["Kafka", "RabbitMQ"],
    "SQL Databases": ["SQL", "MySQL", "PostgreSQL"],
    "Cloud": ["AWS", "Azure", "GCP"],
    "Deep Learning Frameworks": ["PyTorch", "TensorFlow"],
    "BI Tools": ["Tableau", "Power BI"],
    "Frontend Frameworks": ["React", "Angular", "Vue.js"],
}
SKILL_TO_GROUP = {s: g for g, members in CONCEPT_GROUPS.items() for s in members}

_CASE_SENSITIVE = {"R": ["R"], "Go": ["Go"]}   # same special-casing as Milestone 2


@lru_cache(maxsize=None)
def _patterns() -> list[tuple[str, re.Pattern]]:
    pats = []
    for canon, aliases in SKILL_ALIASES.items():
        for a in sorted(set(aliases + [canon.lower()]), key=len, reverse=True):
            if canon in _CASE_SENSITIVE and a in ("r", "go"):
                continue
            pats.append((canon, re.compile(r"(?<![A-Za-z0-9+#])" + re.escape(a) + r"(?![A-Za-z0-9+#])", re.I)))
    for canon, toks in _CASE_SENSITIVE.items():
        for t in toks:
            pats.append((canon, re.compile(r"(?<![A-Za-z0-9+#/])" + re.escape(t) + r"(?![A-Za-z0-9+#/.'])")))
    return pats


def skill_spans(text: str) -> list[tuple[int, int, str]]:
    """(start, end, canonical) for the first occurrence of each skill, in text order.
    Overlapping hits keep the longer one ("react native" beats "react")."""
    hits = [(m.start(), m.end(), canon) for canon, pat in _patterns() for m in pat.finditer(text)]
    hits.sort(key=lambda h: (h[0], -(h[1] - h[0])))
    kept, last_end = [], -1
    for s, e, c in hits:
        if s >= last_end:
            kept.append((s, e, c))
            last_end = e
    out, seen = [], set()
    for s, e, c in kept:
        if c not in seen:
            seen.add(c)
            out.append((s, e, c))
    return out


def find_skills(text: str) -> list[str]:
    return [c for _, _, c in skill_spans(text)]


def mentions(text: str, skill: str) -> int:
    """Number of times a canonical skill (any alias) is mentioned."""
    n = 0
    for canon, pat in _patterns():
        if canon == skill:
            n += len(pat.findall(text))
    return n


def canonical(name: str) -> str | None:
    for canon in SKILL_ALIASES:
        if canon.lower() == name.strip().lower():
            return canon
    found = find_skills(name)
    return found[0] if found else None
