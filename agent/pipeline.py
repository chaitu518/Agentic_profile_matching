"""Glue between tools and graph nodes: run the three screening rounds over the corpus."""
from __future__ import annotations

from agent import config
from agent.candidates import DEGREE_RANK, Candidate, load_corpus
from agent.requirements import JobRequirements
from agent.scoring import deep_analysis, recommend, round1_score
from agent.tools.rag_search import search

TIER = {"STRONG HIRE": 0, "HIRE": 1, "BORDERLINE": 2, "NO HIRE": 3}


def corpus() -> dict[str, Candidate]:
    return load_corpus(str(config.RESUME_DIR))


def passes_filters(c: Candidate, filters: dict) -> bool:
    deg = filters.get("min_degree")
    return not deg or DEGREE_RANK.get(c.highest_degree, 0) >= DEGREE_RANK[deg]


def retrieve(req: JobRequirements) -> list[dict]:
    """Milestone 2 hybrid retrieval over all resumes (query = the requirements rendered as a JD)."""
    return search(req.to_jd_text(), k=len(corpus()))


def round1(req: JobRequirements, weights: dict, filters: dict, retrieved: list[dict]) -> dict[str, dict]:
    """Score every eligible candidate (cheap), so anyone can be explained later, not just the shortlist."""
    hits = {h["candidate_id"]: h for h in retrieved}
    return {cid: round1_score(c, req, weights, hits.get(cid))
            for cid, c in corpus().items() if passes_filters(c, filters)}


def round2(req: JobRequirements, scores: dict[str, dict], ids: list[str]) -> list[dict]:
    deep = [deep_analysis(corpus()[cid], req, scores[cid]) for cid in ids]
    return sorted(deep, key=lambda d: -d["deep_score"])


def round3(req: JobRequirements, deep: list[dict]) -> list[dict]:
    """Final order: decision tier first (hire-ready on top), then deep score."""
    final = [d | recommend(d, req) for d in deep]
    return sorted(final, key=lambda d: (TIER[d["decision"]], -d["deep_score"]))


def full_profile(req: JobRequirements, weights: dict, cid: str, hit: dict | None = None) -> dict:
    """All three rounds for one candidate (ad-hoc compare / questions / deep dive outside the shortlist)."""
    r1 = round1_score(corpus()[cid], req, weights, hit)
    d = deep_analysis(corpus()[cid], req, r1)
    return d | recommend(d, req)
