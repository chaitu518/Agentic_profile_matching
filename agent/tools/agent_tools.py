"""Milestone 3 agent tools.

extract_requirements(jd)                 -> must-have vs nice-to-have
compare_candidates(candidate_ids, ...)   -> head-to-head comparison table
generate_interview_questions(candidate_id, ...) -> targeted screening questions
"""
from __future__ import annotations

from langchain_core.tools import tool

from agent import config
from agent import pipeline
from agent.explain import compare_table
from agent.requirements import JobRequirements
from agent.requirements import extract_requirements as _extract


@tool
def extract_requirements(jd: str) -> dict:
    """Parse a job description (or a natural-language search) into must-have and nice-to-have requirements."""
    req, method = _extract(jd)
    return {"requirements": req.model_dump(), "method": method}


def _req(requirements: dict | None) -> JobRequirements:
    return JobRequirements.model_validate(requirements or {})


def _hits(req: JobRequirements) -> dict[str, dict]:
    """Milestone 2 retrieval signals for the current requirements (cheap: index is cached)."""
    return {h["candidate_id"]: h for h in pipeline.retrieve(req)}


@tool
def compare_candidates(candidate_ids: list[str], requirements: dict, weights: dict | None = None) -> dict:
    """Head-to-head comparison of 2-5 candidates (ids = resume file stems) against the requirements."""
    req = _req(requirements)
    hits = _hits(req)
    profiles = [pipeline.full_profile(req, weights or config.DEFAULT_WEIGHTS, cid, hits.get(cid))
                for cid in candidate_ids if cid in pipeline.corpus()]
    return {"table_markdown": compare_table(profiles, req), "profiles": profiles}


QUESTION_BANK: dict[str, list[str]] = {
    "React": ["How do you decide between local state, context and a store like Redux in a large React app?",
              "Walk me through how you'd diagnose a React page that re-renders too often."],
    "TypeScript": ["How do you type a reusable component or API client generically in TypeScript?",
                   "When have strict TypeScript settings caught a real bug for you?"],
    "JavaScript": ["Explain the event loop and how microtasks differ from macrotasks."],
    "Next.js": ["When would you pick SSR vs SSG vs ISR in Next.js, and why?"],
    "Redux": ["How do you keep Redux state normalised and avoid unnecessary selectors re-running?"],
    "Unit Testing": ["What does a good unit test for a UI component or service look like? What do you avoid mocking?"],
    "Java": ["Explain how you'd find and fix a memory leak in a long-running Java service."],
    "Spring Boot": ["How do you structure transactions and error handling across Spring Boot service layers?"],
    "Kafka": ["How do you guarantee exactly-once or idempotent processing with Kafka consumers?",
              "How do you choose a partition key, and what happens when partitions are rebalanced?"],
    "Microservices": ["How do you handle a distributed transaction across microservices (saga, outbox)?"],
    "REST APIs": ["How do you version and paginate a public REST API?"],
    "SQL": ["How would you speed up a slow query that joins three large tables?"],
    "Redis": ["How do you prevent cache stampedes and keep Redis consistent with the DB?"],
    "Docker": ["How do you keep Docker images small and builds reproducible?"],
    "Kubernetes": ["How do readiness and liveness probes differ, and how have you tuned them?"],
    "AWS": ["Describe an AWS architecture you designed; what would you change for 10x traffic?"],
    "System Design": ["Design a rate limiter for a high-throughput API. Where does state live?"],
    "Python": ["How do you structure a Python service for testability and type safety?"],
    "Machine Learning": ["How do you detect and handle data drift after a model is in production?"],
    "PyTorch": ["Walk me through debugging a PyTorch model whose loss stops decreasing."],
    "NLP": ["How would you evaluate a text classifier when labels are noisy?"],
    "LLMs": ["How do you evaluate LLM output quality and reduce hallucinations in production?"],
    "RAG": ["How do you choose chunk size and retrieval strategy (dense, sparse, hybrid) for a RAG system?"],
    "Spark": ["How do you fix data skew in a Spark join?"],
    "Airflow": ["How do you make Airflow DAGs idempotent and backfill-safe?"],
    "GraphQL": ["How do you prevent N+1 queries in a GraphQL resolver layer?"],
    "Node.js": ["How do you avoid blocking the Node.js event loop with CPU-heavy work?"],
    "HTML/CSS": ["How do you keep CSS maintainable across a large design system, and which semantic HTML/ARIA "
                 "practices do you apply for accessible forms?"],
    "Deep Learning": ["How do you choose between fine-tuning a pretrained model and training from scratch?"],
    "MLOps": ["How do you version data, models and code so any production prediction can be reproduced?"],
    "Terraform": ["How do you structure Terraform state and modules across environments, and handle drift?"],
    "Linux": ["A host shows high load but low CPU usage. How do you investigate?"],
    "Snowflake": ["How do you control cost and performance in Snowflake (warehouses, clustering, caching)?"],
    "Excel": ["How would you build a reusable, auditable model in Excel that others can safely edit?"],
    "Tableau": ["How do you design a leadership dashboard that stays fast and trustworthy as data grows?"],
    "Statistics": ["An A/B test shows a 2% lift with p = 0.04 after peeking daily. Do you ship it?"],
    "Cypress": ["How do you keep end-to-end tests fast and non-flaky in CI?"],
    "Selenium": ["How do you design a Selenium framework that survives frequent UI changes?"],
    "Django": ["How do you find and fix N+1 queries in a Django app?"],
    "Android": ["How do you handle configuration changes and background work reliably on Android?"],
}


def questions_for(profile: dict, req: JobRequirements, n_tech: int = 3) -> list[dict]:
    c = pipeline.corpus()[profile["candidate_id"]]
    qs: list[dict] = []
    strong = sorted([d for d in profile["must"] if d["matched"]], key=lambda d: (-d["weight"], -d["strength"]))
    for d in strong[:n_tech]:
        bank = QUESTION_BANK.get(d["skill"]) or QUESTION_BANK.get(d["via"] or "", [])
        company = c.roles[0].company if c.roles else "your last company"
        q = bank[0] if bank else f"Walk me through the hardest {d['skill']} problem you solved at {company}."
        qs.append({"category": "technical depth", "skill": d["skill"], "question": q,
                   "why": f"Must-have; evidence is '{d['where']}' - verify depth."})
    for d in profile["must"]:
        if d["matched"] and (d["where"] == "skills list only" or d["where"].startswith("implied")):
            qs.append({"category": "verify claim", "skill": d["skill"],
                       "question": f"Your resume lists {d['skill']} but no project shows it. Where did you use it and at what scale?",
                       "why": "Listed without evidence."})
    for d in profile["must"]:
        if d["matched"] and d.get("min_years") and d.get("skill_years", 0) < d["min_years"]:
            qs.append({"category": "years check", "skill": d["skill"],
                       "question": f"The role asks for {d['min_years']:g}+ years of {d['skill']}. Walk me through where "
                                   f"you've used it, year by year.",
                       "why": f"Milestone 2 skill-years evidence: {d.get('skill_years', 0):g} yrs."})
    for s in profile["missing_must"]:
        qs.append({"category": "gap probe", "skill": s,
                   "question": f"This role needs {s}. What's the closest experience you have, and how would you ramp up in 30 days?",
                   "why": "Missing must-have."})
    impact = next((b for r in c.roles for b in r.bullets if "%" in b), None)
    if impact:
        qs.append({"category": "impact verification", "skill": "-",
                   "question": f"You wrote: \"{impact}\". How was that measured, and what exactly was your part?",
                   "why": "Validate quantified claims."})
    if req.min_years and c.years_experience < req.min_years:
        qs.append({"category": "seniority", "skill": "-",
                   "question": "Tell me about a decision where you had to push back on a senior engineer or PM. What happened?",
                   "why": f"Below the {req.min_years:g}+ yr bar - test judgement."})
    elif profile.get("signals", {}).get("senior_title"):
        qs.append({"category": "leadership", "skill": "-",
                   "question": "How have you raised the bar for your team - mentoring, reviews, or design standards?",
                   "why": "Senior role - check multiplier impact."})
    else:
        qs.append({"category": "ownership", "skill": "-",
                   "question": "Describe a feature you owned from design to production. What would you do differently?",
                   "why": "Check end-to-end ownership."})
    return qs


@tool
def generate_interview_questions(candidate_id: str, requirements: dict, weights: dict | None = None) -> dict:
    """Create tailored screening questions for one candidate: depth checks, claim verification and gap probes."""
    req = _req(requirements)
    prof = pipeline.full_profile(req, weights or config.DEFAULT_WEIGHTS, candidate_id, _hits(req).get(candidate_id))
    return {"candidate_id": candidate_id, "name": prof["name"], "questions": questions_for(prof, req)}


AGENT_TOOLS = [extract_requirements, compare_candidates, generate_interview_questions]
