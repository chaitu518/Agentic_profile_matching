"""Milestone 2 RAG search exposed to the agent.

It runs Milestone 2's own pipeline: `api.resume_rag.ResumeRAG` (section-aware chunks, embeddings,
ChromaDB) and `api.job_matcher.JobMatcher.match` (JD parsing, hybrid semantic + BM25 retrieval,
0-100 score, excerpts). The index for the agent's 100-resume corpus lives in vector_db_m3/ and is
built on first use (or when the folder's contents change).

The must-have filter is switched off here on purpose. The agent scores everyone so it can explain
anyone ("why is Jane #23?"). It reads M2's semantic and keyword signals as its retrieval component
and reports M2's own match_score as a baseline next to its own.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from langchain_core.tools import tool

from agent import config
from api.embeddings import get_embedder
from api.job_matcher import JobMatcher
from api.resume_rag import ResumeRAG

SUPPORTED = {".pdf", ".docx", ".txt", ".md"}


def _expected_paths() -> set[str]:
    return {p.resolve().relative_to(config.ROOT).as_posix()
            for p in Path(config.RESUME_DIR).iterdir() if p.suffix.lower() in SUPPORTED}


@lru_cache(maxsize=2)
def get_matcher(provider: str | None = None) -> JobMatcher:
    rag = ResumeRAG(config.VECTOR_DB, get_embedder(provider or config.EMBEDDING_PROVIDER))
    if rag.count() == 0 or set(rag.load_registry()) != _expected_paths():
        print(f"[rag] indexing {config.RESUME_DIR.relative_to(config.ROOT)} with {rag.embedder.name} ...")
        rag.ingest(config.RESUME_DIR, reset=True, verbose=False)
    return JobMatcher(rag)


def search(query: str, k: int = 100) -> list[dict]:
    m = get_matcher()
    res = m.match(query, k=k, mode="hybrid", apply_filters=False, n_chunks=max(200, m.rag.count()))
    out = []
    for t in res["top_matches"]:
        b = t["score_breakdown"]
        out.append({
            "candidate_id": Path(t["resume_path"]).stem,
            "name": t["candidate_name"],
            "resume_path": t["resume_path"],
            "semantic": b["semantic"],
            "keyword": b["keyword"],
            # M2 weights semantic 0.40 and keyword 0.15; keep that ratio for the retrieval signal
            "retrieval": round((0.40 * b["semantic"] + 0.15 * b["keyword"]) / 0.55, 4),
            "m2_score": t["match_score"],
            "excerpts": t["relevant_excerpts"],
            "matched_sections": t["matched_sections"],
        })
    return out


@tool
def rag_search(query: str, k: int = 100) -> list[dict]:
    """Milestone 2 hybrid RAG search (ChromaDB semantic + BM25 keyword) over the resume corpus.
    Returns candidates with semantic/keyword scores, M2's 0-100 match score and evidence excerpts."""
    return search(query, k)
