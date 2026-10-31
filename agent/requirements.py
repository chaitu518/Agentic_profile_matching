"""Job requirements for the agent: must-have vs nice-to-have, built on Milestone 2's JD parser.

Milestone 2 (`api.job_matcher.parse_job_description`) gives three tiers: must_have (with per-skill
years, e.g. "4+ years Java"), required, nice_to_have, plus min_years. The agent needs two editable
buckets that a recruiter can change mid-conversation, plus a bit more structure:

* section awareness - skills under "Requirements / Must have / Also expected" are must-haves,
  skills that only appear in "Responsibilities / What you'll do" become nice-to-haves, and so do
  soft asks ("familiarity with", "exposure to") and inline "a plus" / "nice to have";
* alternatives      - "PyTorch or TensorFlow", "MySQL/PostgreSQL", "Redux or similar";
* weights           - M2 hard must-haves and "strong/advanced X" weigh 1.5x;
* per-skill years   - kept from M2 ("5+ years Python") and checked in round 2.
"""
from __future__ import annotations

import re

from pydantic import BaseModel, Field

from api.job_matcher import parse_job_description

from agent import llm
from agent.skills import CONCEPT_GROUPS, IMPLIES, SKILL_TO_GROUP, canonical, skill_spans


class Requirement(BaseModel):
    skill: str = Field(description="Canonical skill name, e.g. 'React'")
    alternatives: list[str] = Field(default_factory=list, description="Other skills that also satisfy it")
    weight: float = 1.0
    min_years: float | None = Field(None, description="Per-skill years if the JD states them, e.g. '4+ years Java'")
    source: str = ""

    def satisfiers(self) -> list[str]:
        return [self.skill, *[a for a in self.alternatives if a != self.skill]]


class JobRequirements(BaseModel):
    title: str = ""
    min_years: float | None = None
    must_have: list[Requirement] = Field(default_factory=list)
    nice_to_have: list[Requirement] = Field(default_factory=list)
    min_degree: str | None = None

    def find(self, skill: str) -> tuple[str, int] | None:
        for bucket in ("must_have", "nice_to_have"):
            for i, r in enumerate(getattr(self, bucket)):
                if r.skill.lower() == skill.lower() or skill in r.alternatives:
                    return bucket, i
        return None

    def to_jd_text(self) -> str:
        """Render as a JD that Milestone 2's parser and retriever understand. Used as the RAG query, so
        a refinement ("make Next.js a must-have") changes retrieval exactly as it changes the requirements."""
        lines = [self.title or "Job", "", "Must have:"]
        if self.min_years:
            lines.append(f"- {self.min_years:g}+ years of experience")
        for r in self.must_have:
            yrs = f"{r.min_years:g}+ years " if r.min_years else ""
            alt = [a for a in r.alternatives if a != r.skill]
            lines.append(f"- {yrs}{r.skill}" + (f" or {' or '.join(alt)}" if alt else ""))
        if self.nice_to_have:
            lines += ["", "Nice to have: " + ", ".join(r.skill for r in self.nice_to_have)]
        return "\n".join(lines)

    def summary(self) -> str:
        yrs = f"{self.min_years:g}+ yrs" if self.min_years else "any experience"
        must = ", ".join(_fmt(r) for r in self.must_have) or "-"
        nice = ", ".join(_fmt(r) for r in self.nice_to_have) or "-"
        deg = f" | degree: {self.min_degree} or higher" if self.min_degree else ""
        return f"**Must-have:** {must}  \n**Nice-to-have:** {nice}  \n**Experience:** {yrs}{deg}"


def _fmt(r: Requirement) -> str:
    alt = [a for a in r.alternatives if a != r.skill]
    s = r.skill + (f" (or {'/'.join(alt)})" if alt else "")
    if r.min_years:
        s += f" {r.min_years:g}+y"
    return s + (" ×1.5" if r.weight > 1 else "")


NICE_RE = re.compile(r"nice[- ]to[- ]have|good[- ]to[- ]have|a plus|is a plus|bonus|preferred|desirable|ideally|preferably|optional", re.I)
MUST_HDR = re.compile(r"must[- ]haves?|required|requirements|mandatory|essential|qualifications|also expected|you have|what we need", re.I)
CONTEXT_HDR = re.compile(r"responsibilities|what you'?ll do|you will|about|the role|duties|day to day", re.I)
YEARS_RE = re.compile(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:-\s*\d+\s*)?(?:years?|yrs?)", re.I)
SOFT_RE = re.compile(r"\b(familiarity|familiar with|exposure to|awareness of|basic knowledge)\b", re.I)
STRONG_RE = re.compile(r"\b(strong|expert|deep|proficien\w*|advanced|excellent|solid)\b", re.I)
GROUP_RE = re.compile(r"or similar|or another|or other|or equivalent", re.I)
JOIN_RE = re.compile(r"^\s*(?:or|/)\s*$", re.I)
DEGREE_RE = re.compile(r"\b(ph\.?d|master'?s|bachelor'?s)\b(?:\s+degree)?\s*(?:or (?:higher|above))?", re.I)


def _clause_requirements(clause: str, weight: float) -> list[Requirement]:
    """One clause -> requirements. 'X or Y' / 'X/Y' become alternatives; a parenthesised group whose
    members all imply the skill before it attaches to it ('Deep Learning (PyTorch or TensorFlow)',
    'SQL databases (MySQL or PostgreSQL)'). Nice-to-have markers inside parentheses only affect the
    skills inside them ('NLP and retrieval systems (RAG is a plus)')."""
    spans = skill_spans(clause)
    if not spans:
        return []
    parens = [(m.start(), m.end()) for m in re.finditer(r"\([^)]*\)", clause)]
    nice_parens = [(a, b) for a, b in parens if NICE_RE.search(clause[a:b])]
    outside = re.sub(r"\([^)]*\)", " ", clause)
    clause_nice = bool(NICE_RE.search(outside))

    def in_paren(pos, ranges):
        return any(a <= pos < b for a, b in ranges)

    groups: list[dict] = []
    prev_end = None
    for s0, e0, canon in spans:
        between = clause[prev_end:s0] if prev_end is not None else ""
        if groups and JOIN_RE.match(between):
            groups[-1]["skills"].append(canon)
        else:
            groups.append({"skills": [canon], "paren": in_paren(s0, parens),
                           "nice": clause_nice or in_paren(s0, nice_parens)})
        prev_end = e0
    out: list[tuple[Requirement, bool]] = []
    for g in groups:
        sk = list(dict.fromkeys(g["skills"]))
        r = Requirement(skill=sk[0], alternatives=sk if len(sk) > 1 else [], weight=weight, source=clause.strip())
        if out and g["paren"] and all(out[-1][0].skill in IMPLIES.get(x, []) for x in sk):
            prev = out[-1][0]
            prev.alternatives = list(dict.fromkeys([prev.skill, *prev.alternatives, *sk]))
            continue
        out.append((r, g["nice"]))
    if GROUP_RE.search(clause):                       # "(Redux or similar)" -> whole concept group
        r = out[-1][0]
        grp = SKILL_TO_GROUP.get(r.skill)
        if grp:
            r.alternatives = list(dict.fromkeys([r.skill, *CONCEPT_GROUPS[grp]]))
    for r, nice in out:
        r.source = ("nice:" if nice else "") + r.source
    return [r for r, _ in out]


def _is_header(line: str) -> str | None:
    if len(line) > 60:
        return None
    head = line.split(":", 1)[0] if ":" in line else line
    if not (line.rstrip().endswith(":") or ":" in line[:40]):
        return None
    if NICE_RE.search(head):
        return "nice"
    if MUST_HDR.search(head):
        return "must"
    if CONTEXT_HDR.search(head):
        return "context"
    return None


def extract_requirements_rules(jd: str) -> JobRequirements:
    m2 = parse_job_description(jd)                    # Milestone 2 parser: hard must-haves + skill years
    raw_lines = [ln.strip(" -•*\t") for ln in jd.splitlines() if ln.strip()]
    single = len(raw_lines) <= 1
    req = JobRequirements(title=f"Ad-hoc search: {jd.strip()[:70]}" if single else raw_lines[0][:90])
    req.min_years = float(m2["min_years"]) if m2["min_years"] else None
    if (dm := DEGREE_RE.search(jd)):
        req.min_degree = {"p": "PhD", "m": "Master's", "b": "Bachelor's"}[dm.group(1)[0].lower()]

    has_headers = any(_is_header(ln) for ln in raw_lines)
    section = "context" if has_headers and not single else "must"
    context_skills: list[Requirement] = []
    for ln in (raw_lines if not single else raw_lines):
        kind = _is_header(ln) if not single else None
        if kind:
            section = kind
            ln = ln.split(":", 1)[1] if ":" in ln else ""
            if not ln.strip():
                continue
        if ln is raw_lines[0] and not single and has_headers:
            continue  # title line
        line_weight = 1.5 if STRONG_RE.search(ln) else 1.0
        # split into clauses so "testing with Cypress a plus" / "nice to have Kubernetes" are caught inline
        inline_nice = False
        for clause in re.split(r",(?![^()]*\))|;|\.(?=\s)", ln):
            if NICE_RE.search(re.sub(r"\([^)]*\)", " ", clause)):
                inline_nice = True          # "..., testing with Cypress a plus" / "nice to have X, Y"
            for r in _clause_requirements(clause, line_weight):
                is_nice = r.source.startswith("nice:") or inline_nice or section == "nice" or bool(SOFT_RE.search(ln))
                r.source = r.source.removeprefix("nice:")
                if section == "context" and not is_nice:
                    context_skills.append(r)
                    continue
                if req.find(r.skill):
                    continue
                (req.nice_to_have if is_nice else req.must_have).append(r)

    # Milestone 2's hard must-haves get extra weight and their per-skill years
    for skill, yrs in m2["must_have"].items():
        loc = req.find(skill)
        if not loc:
            req.must_have.append(Requirement(skill=skill, weight=1.5, min_years=yrs, source="M2 must-have"))
            continue
        r = getattr(req, loc[0])[loc[1]]
        if loc[0] == "nice_to_have":
            req.nice_to_have.pop(loc[1])
            req.must_have.append(r)
        r.weight = 1.5
        r.min_years = float(yrs) if yrs else r.min_years
    # skills only mentioned in the role description become nice-to-haves
    for r in context_skills:
        if not req.find(r.skill):
            r.source = "mentioned in responsibilities"
            req.nice_to_have.append(r)
    return req


LLM_PROMPT = """Extract hiring requirements from the job description below.
Rules: use short canonical skill names (React, TypeScript, Kafka, Spring Boot, AWS, HTML/CSS ...).
Put a skill in must_have only if the JD requires it; optional skills go to nice_to_have.
If the JD lists alternatives ("Kafka or RabbitMQ", "Jest or similar") create ONE requirement with alternatives.
weight = 1.5 for skills described as strong/expert/deep or explicitly must-have, else 1.0.
min_years = overall years of experience; a requirement's min_years = years asked for that skill.

JOB DESCRIPTION:
{jd}
"""


def extract_requirements(jd: str) -> tuple[JobRequirements, str]:
    """Returns (requirements, method). LLM first if configured, else Milestone-2-based rules."""
    rules = extract_requirements_rules(jd)
    out = llm.structured(LLM_PROMPT.format(jd=jd), JobRequirements)
    if out and (out.must_have or out.nice_to_have):
        for r in out.must_have + out.nice_to_have:
            r.skill = canonical(r.skill) or r.skill
            r.alternatives = [canonical(a) or a for a in r.alternatives]
        out.title = out.title or rules.title
        return out, "llm"
    return rules, "rules (M2 parser + sections)"
