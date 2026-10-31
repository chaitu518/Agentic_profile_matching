"""Milestone 3 configuration. Everything can be overridden with environment variables."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # repo root (same ROOT the Milestone 2 code uses)

RESUME_DIR = Path(os.getenv("RESUME_DIR", ROOT / "data" / "resumes_m3"))     # 100 resumes (36 from M2 + 64)
JD_DIR = Path(os.getenv("JD_DIR", ROOT / "data" / "job_descriptions"))       # the 6 Milestone 2 JDs
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", ROOT / "outputs" / "m3_reports"))
VECTOR_DB = Path(os.getenv("M3_VECTOR_DB", ROOT / "vector_db_m3"))           # kept apart from M2's vector_db/

# Milestone 2 embedder for the agent's RAG index. "local" (TF-IDF/LSA) keeps runs deterministic and offline;
# set huggingface / openai / cohere exactly as in Milestone 2.
EMBEDDING_PROVIDER = os.getenv("M3_EMBEDDING_PROVIDER", os.getenv("EMBEDDING_PROVIDER", "local"))

# Milestone 1 file tools may only touch these folders.
FS_ALLOWED_ROOTS = [ROOT / "data", ROOT / "outputs"]

SHORTLIST_SIZE = int(os.getenv("SHORTLIST_SIZE", 10))   # round 1 -> round 2

# Round-1 weights (sum to 1). "retrieval" = Milestone 2 hybrid signal (semantic + BM25).
DEFAULT_WEIGHTS = {"must_have": 0.45, "nice_to_have": 0.15, "experience": 0.20, "retrieval": 0.20}

# Round-3 thresholds on the deep score (0-100)
STRONG_HIRE_AT = 85
HIRE_AT = 72
BORDERLINE_AT = 58

# Optional LLM. Empty = deterministic offline mode.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "").lower()   # openrouter | openai | anthropic | groq | google | ollama
LLM_MODEL = os.getenv("LLM_MODEL", "")
