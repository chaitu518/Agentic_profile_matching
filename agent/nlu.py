"""Natural-language understanding for the chat loop: intent routing, refinement ops, candidate references.

Rule-based first (fast, deterministic, testable); an LLM is consulted only when the
rules can't classify a message and LLM_PROVIDER is configured.
"""
from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field

from agent import llm
from agent.requirements import JobRequirements, Requirement
from agent.skills import find_skills

IntentType = Literal["new_search", "refine", "compare", "explain", "explain_changes", "questions",
                     "report", "show_ranking", "help", "end", "general"]

WORDNUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
           "nine": 9, "ten": 10, "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5}
NAME_STOPWORDS = {"top", "the", "and", "why", "rank", "will", "may"}


class Intent(BaseModel):
    type: IntentType
    candidate_ids: list[str] = Field(default_factory=list)
    ops: list[dict] = Field(default_factory=list)
    text: str = ""


# ------------------------------------------------------------------ candidate references


def resolve_candidates(text: str, ranking: list[str], corpus: dict, scores: dict) -> list[str]:
    t = text.lower()
    found: list[tuple[int, str]] = []

    m = re.search(r"\btop\s+(\d+|" + "|".join(WORDNUM) + r")\b", t)
    if m:
        n = int(m.group(1)) if m.group(1).isdigit() else WORDNUM[m.group(1)]
        return ranking[:n]
    if re.search(r"\b(top|best|first)\s+(two|pair)\b|\btop two\b", t):
        return ranking[:2]

    for m in re.finditer(r"(?:#|rank(?:ed)?\s*|number\s*|no\.\s*)(\d{1,2})\b", t):
        i = int(m.group(1)) - 1
        if 0 <= i < len(ranking):
            found.append((m.start(), ranking[i]))
    for m in re.finditer(r"\b(first|second|third|fourth|fifth)\s+(?:candidate|one|place|ranked)\b", t):
        i = WORDNUM[m.group(1)] - 1
        if i < len(ranking):
            found.append((m.start(), ranking[i]))
    for m in re.finditer(r"\b[a-z]+_[a-z]+\b", t):          # resume ids = file stems, e.g. john_mathew
        if m.group(0) in corpus:
            found.append((m.start(), m.group(0)))

    rank_pos = {cid: i for i, cid in enumerate(ranking)}

    def pref(cid):  # prefer shortlisted, then higher score
        return (rank_pos.get(cid, 999), -scores.get(cid, {}).get("score", 0))

    full_hits = set()
    for cid, c in corpus.items():
        m = re.search(r"\b" + re.escape(c.name.lower()) + r"\b", t)
        if m:
            found.append((m.start(), cid))
            full_hits.add(m.start())
    by_token: dict[str, list[str]] = {}
    for cid, c in corpus.items():
        for tok in c.name.lower().split():
            by_token.setdefault(tok, []).append(cid)
    for m in re.finditer(r"\b[a-z]{3,}\b", t):
        if m.start() in full_hits or any(abs(m.start() - h) < 25 for h in full_hits):
            continue
        cands = by_token.get(m.group(0))
        if cands and m.group(0) not in NAME_STOPWORDS:
            found.append((m.start(), sorted(cands, key=pref)[0]))

    out, seen = [], set()
    for _, cid in sorted(found):
        if cid not in seen:
            seen.add(cid)
            out.append(cid)
    return out


# ------------------------------------------------------------------ refinement parsing

RE_REMOVE = re.compile(r"\b(remove|drop|ignore|exclude|forget|without|don'?t (?:need|care about)|do not need|no longer (?:need|require)|get rid of)\b")
RE_NICE = re.compile(r"nice[- ]to[- ]have|optional|bonus|demote|not (?:required|mandatory|a must)|preferred|good[- ]to[- ]have|plus\b")
RE_MUST = re.compile(r"must[- ]?have|mandatory|required|\brequire|\bneed|essential|promote|non[- ]negotiable|\badd\b|\balso\b|\bmust\b")
RE_YEARS = re.compile(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)")
RE_NO_YEARS = re.compile(r"(?:any|no|ignore|remove|drop)\s+(?:the\s+)?(?:years?\s+of\s+)?experience(?:\s+(?:requirement|bar|filter))?|experience doesn'?t matter")
RE_DEG_CLEAR = re.compile(r"any degree|ignore (?:the )?degree|remove (?:the )?degree|degree doesn'?t matter|no degree (?:filter|requirement)")
RE_DEG = re.compile(r"\b(ph\.?d|doctorate|master'?s|masters|m\.?tech|m\.?s\b|bachelor'?s|bachelors)\b", re.I)
DEGREE_NAME = {"p": "PhD", "d": "PhD", "m": "Master's", "b": "Bachelor's"}
RE_WEIGHT = {
    "retrieval": re.compile(r"prioriti[sz]e (?:semantic|rag|retrieval|similarity)|weight (?:semantic|rag|retrieval) more"),
    "experience": re.compile(r"prioriti[sz]e experience|experience (?:matters|is) more|weight experience|more weight (?:on|to) experience|seniority matters"),
    "must_have": re.compile(r"prioriti[sz]e (?:skills|must[- ]haves?)|skills? matters? more|weight (?:skills|must[- ]haves?) more"),
    "nice_to_have": re.compile(r"nice[- ]to[- ]haves? (?:matter|are important|count) more|weight nice[- ]to[- ]haves?"),
}


def parse_refinement(text: str) -> list[dict]:
    t = text.lower()
    ops: list[dict] = []
    if RE_NO_YEARS.search(t):
        ops.append({"op": "min_years", "value": None})
    elif (m := RE_YEARS.search(t)):
        ops.append({"op": "min_years", "value": float(m.group(1))})
    if RE_DEG_CLEAR.search(t):
        ops.append({"op": "min_degree", "value": None})
    elif (m := RE_DEG.search(t)) and re.search(r"\b(only|require|requires|need|needs|must|at least|minimum|with)\b", t):
        ops.append({"op": "min_degree", "value": DEGREE_NAME[m.group(1)[0].lower()]})
    for k, rx in RE_WEIGHT.items():
        if rx.search(t):
            ops.append({"op": "weight", "key": k, "delta": 0.15})

    last_op = None
    for clause in _clauses(t):
        skills = find_skills(clause)
        if RE_REMOVE.search(clause):
            op = "remove"
        elif RE_NICE.search(clause):
            op = "add_nice"
        elif RE_MUST.search(clause):
            op = "add_must"
        else:
            op = last_op
        if skills and op:
            for s in skills:
                ops.append({"op": op, "skill": s})
        if op:
            last_op = op
    return ops


def _clauses(t: str) -> list[str]:
    """Split on , ; but then . - and split on 'and' only when the right side starts a new instruction
    ("add Docker and remove CSS") rather than continuing a list ("add Docker and Kubernetes as nice to have")."""
    out = []
    for chunk in re.split(r",|;|\bbut\b|\bthen\b|\.(?:\s|$)", t):
        parts = re.split(r"\band\b", chunk)
        cur = parts[0]
        for p in parts[1:]:
            starts_with_skill = bool(find_skills(p)) and p.strip() and find_skills(p.strip().split()[0] if p.strip() else "")
            if starts_with_skill:
                cur += " and " + p
            else:
                out.append(cur)
                cur = p
        out.append(cur)
    return [c for c in out if c.strip()]


def apply_refinement(req: JobRequirements, weights: dict, filters: dict, ops: list[dict]
                     ) -> tuple[JobRequirements, dict, dict, list[str]]:
    req = req.model_copy(deep=True)
    weights, filters, log = dict(weights), dict(filters), []
    for op in ops:
        kind = op["op"]
        if kind in ("add_must", "add_nice", "remove"):
            s = op["skill"]
            loc = req.find(s)
            existing = getattr(req, loc[0]).pop(loc[1]) if loc else None
            if kind == "remove":
                log.append(f"Removed **{s}** from requirements" if existing else f"{s} was not a requirement (no-op)")
                continue
            r = existing or Requirement(skill=s, source="added in conversation")
            target = req.must_have if kind == "add_must" else req.nice_to_have
            target.append(r)
            label = "must-have" if kind == "add_must" else "nice-to-have"
            if loc and loc[0] == ("must_have" if kind == "add_must" else "nice_to_have"):
                log.append(f"**{s}** is already a {label} (unchanged)")
            elif loc:
                log.append(f"Moved **{s}** to {label}")
            else:
                log.append(f"Added **{s}** as a {label}")
        elif kind == "min_years":
            old = req.min_years
            req.min_years = op["value"]
            log.append(f"Experience bar: {old or 'none'} -> {op['value'] or 'none'} years")
        elif kind == "min_degree":
            filters["min_degree"] = op["value"]
            req.min_degree = op["value"]
            log.append(f"Degree filter: {op['value'] + ' or higher' if op['value'] else 'any degree'}")
        elif kind == "weight":
            k = op["key"]
            weights[k] = weights.get(k, 0) + op["delta"]
            total = sum(weights.values())
            weights = {kk: round(v / total, 3) for kk, v in weights.items()}
            log.append(f"Increased weight on {k.replace('_', '-')} -> {weights[k]:.0%}")
    return req, weights, filters, log


# ------------------------------------------------------------------ intent routing

RE_END = re.compile(r"^\s*(quit|exit|bye|goodbye|done|end|stop|that'?s all|thanks?,? (?:that'?s all|that is all|bye|done)|that is all|no(?:thing)? (?:more|else))\b")
RE_HELP = re.compile(r"^\s*(help|\?|what can you do|commands)\b")
RE_COMPARE = re.compile(r"\bcompare\b|side[- ]by[- ]side|head[- ]to[- ]head|\bversus\b|\bvs\.?\b")
RE_QUESTIONS = re.compile(r"interview questions?|screening questions?|questions (?:for|to ask)|what (?:should|do) i ask|prepare .*interview")
RE_EXPLAIN_CHANGES = re.compile(r"(why|how|what) (?:did|has|have) (?:the )?(?:ranking|rankings|order|list|shortlist) chang|what changed|explain (?:the )?(?:ranking )?changes")
RE_EXPLAIN = re.compile(r"\bwhy\b|\bexplain\b|\breason\b|how come|what makes|rank(?:ed)? (?:higher|lower|above|below)")
RE_SEARCH = re.compile(r"^\s*(?:(?:now|ok(?:ay)?|so|and|also|let'?s|please|can you|could you)[\s,]+)*(find|search|look(?:ing)? for|get me|show me (?:candidates|people|engineers|developers)|i need (?:a|an|candidates)|hiring|we are hiring|new (?:jd|job|search|role))\b|candidates with|data/jds/|\.txt\b")
RE_REPORT = re.compile(r"\breport\b|\bdetails?\b|tell me (?:more )?about|\bprofile\b|strengths|gaps|recommendation|hire or|should we hire|deep dive|improvement")
RE_SHOW = re.compile(r"show (?:me )?(?:the )?(?:top|shortlist|ranking|list|results)|who (?:are|is) (?:the )?(?:top|best)|current (?:ranking|shortlist)|^\s*(?:ranking|shortlist|results)\s*$")


def classify(text: str, ranking: list[str], corpus: dict, scores: dict, has_search: bool) -> Intent:
    t = text.lower().strip()
    cands = resolve_candidates(text, ranking, corpus, scores) if has_search else []

    def mk(kind, **kw):
        return Intent(type=kind, candidate_ids=kw.get("cands", cands), ops=kw.get("ops", []), text=text)

    if RE_END.search(t):
        return mk("end")
    if RE_HELP.search(t):
        return mk("help")
    if not has_search or RE_SEARCH.search(t) or len(text) > 250:
        return mk("new_search")
    if RE_COMPARE.search(t):
        return mk("compare", cands=cands or ranking[:3])
    if RE_QUESTIONS.search(t):
        return mk("questions", cands=cands or ranking[:1])
    if RE_EXPLAIN_CHANGES.search(t):
        return mk("explain_changes")
    if RE_EXPLAIN.search(t) and cands:
        return mk("explain")
    ops = parse_refinement(text)
    if ops:
        return mk("refine", ops=ops)
    if RE_REPORT.search(t):
        return mk("report")
    if RE_SHOW.search(t):
        return mk("show_ranking")
    if RE_EXPLAIN.search(t):
        return mk("explain_changes")
    if cands:
        return mk("report")
    return _llm_classify(text) or mk("general")


LLM_INTENT_PROMPT = """You route messages for a recruiting assistant that has already shortlisted candidates.
Classify the user's message into exactly one type:
new_search (new job / new search), refine (change requirements: must-have, nice-to-have, years, degree, weights),
compare, explain (why a candidate ranks where they do), explain_changes, questions (interview questions),
report (details, strengths, gaps, recommendation), show_ranking, help, end, general.
For refine, fill ops with objects like {{"op":"add_must","skill":"Docker"}}, {{"op":"add_nice","skill":"GraphQL"}},
{{"op":"remove","skill":"HTML/CSS"}}, {{"op":"min_years","value":5}}, {{"op":"min_degree","value":"Master's"}}.
Message: {text}"""


def _llm_classify(text: str) -> Intent | None:
    out = llm.structured(LLM_INTENT_PROMPT.format(text=text), Intent)
    if out:
        out.text = text
    return out
