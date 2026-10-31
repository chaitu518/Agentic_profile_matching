"""Three screening rounds, all deterministic and evidence-backed.

Round 1  initial screen : weighted requirement coverage + experience + RAG similarity  -> top N
Round 2  deep analysis  : evidence depth, recency, seniority, impact, strengths & gaps
Round 3  decision       : STRONG HIRE / HIRE / BORDERLINE / NO HIRE with rationale + suggestions
"""
from __future__ import annotations

from agent import config
from agent.requirements import JobRequirements, Requirement
from agent.candidates import Candidate, seniority_signals
from agent.skills import IMPLIES, find_skills, mentions

# ---------------------------------------------------------------- requirement matching


def _implied_by(c: Candidate, skill: str) -> str | None:
    for have in c.text_skills:
        if skill in IMPLIES.get(have, []):
            return have
    return None


def _evidence_line(c: Candidate, skill: str) -> str:
    for r in c.roles:
        for b in r.bullets:
            if mentions(b, skill):
                return f"{r.title} @ {r.company}: {b}"
    if mentions(c.summary, skill):
        return f"Summary: {c.summary[:120]}"
    return ""


def match_requirement(c: Candidate, req: Requirement) -> dict:
    best = {"skill": req.skill, "matched": False, "via": None, "strength": 0.0, "where": "missing",
            "evidence": "", "exp_mentions": 0}
    exp_text = c.experience_text + "\n" + c.summary
    for i, s in enumerate(req.satisfiers()):
        in_skills = s in c.skills
        n = mentions(exp_text, s)
        if in_skills and n:
            strength, where = 1.0, "skills + experience"
        elif in_skills:
            strength, where = 0.8, "skills list only"
        elif n:
            strength, where = 0.75, "experience only"
        elif (src := _implied_by(c, s)):
            strength, where = 0.55, f"implied by {src}"
        else:
            continue
        if i > 0:  # satisfied by an alternative rather than the primary skill
            strength *= 0.9
        if strength > best["strength"]:
            best.update(matched=True, via=s, strength=round(strength, 3), where=where,
                        evidence=_evidence_line(c, s), exp_mentions=n)
    if req.min_years:
        best["min_years"] = req.min_years
        best["skill_years"] = c.skill_years.get(best["via"] or req.skill, 0.0)   # Milestone 2 per-skill years
    return best


def experience_fit(years: float, min_years: float | None) -> float:
    if not min_years:
        return 1.0
    if years >= min_years:
        return 1.0
    return round((years / min_years) ** 1.5, 3)


def _coverage(c: Candidate, reqs: list[Requirement]) -> tuple[float, list[dict]]:
    if not reqs:
        return 1.0, []
    details = [match_requirement(c, r) | {"weight": r.weight} for r in reqs]
    total_w = sum(r.weight for r in reqs)
    return round(sum(d["strength"] * d["weight"] for d in details) / total_w, 4), details


# ---------------------------------------------------------------- round 1


def round1_score(c: Candidate, req: JobRequirements, weights: dict, hit: dict | None) -> dict:
    """hit = this candidate's Milestone 2 retrieval result (semantic, keyword, m2_score, excerpts)."""
    hit = hit or {}
    must, must_d = _coverage(c, req.must_have)
    nice, nice_d = _coverage(c, req.nice_to_have)
    exp = experience_fit(c.years_experience, req.min_years)
    w = dict(weights)
    if not req.nice_to_have:  # don't hand out free points: fold the weight into must-haves
        w["must_have"] += w.pop("nice_to_have")
        nice = 0.0
    total_w = sum(w.values())
    comps = {"must_have": must, "nice_to_have": nice, "experience": exp,
             "retrieval": round(float(hit.get("retrieval", 0.0)), 4)}
    contrib = {k: round(100 * comps[k] * w.get(k, 0) / total_w, 2) for k in comps}
    return {
        "candidate_id": c.candidate_id,
        "name": c.name,
        "title": c.current_title,
        "years": c.years_experience,
        "degree": c.highest_degree,
        "resume_path": c.resume_path,
        "m2_score": hit.get("m2_score"),
        "rag": {k: hit.get(k) for k in ("semantic", "keyword", "excerpts", "matched_sections")},
        "score": round(sum(contrib.values()), 1),
        "components": comps,
        "contributions": contrib,
        "must": must_d,
        "nice": nice_d,
        "matched_must": [d["skill"] for d in must_d if d["matched"]],
        "missing_must": [d["skill"] for d in must_d if not d["matched"]],
        "matched_nice": [d["skill"] for d in nice_d if d["matched"]],
        "missing_nice": [d["skill"] for d in nice_d if not d["matched"]],
    }


# ---------------------------------------------------------------- round 2


def deep_analysis(c: Candidate, req: JobRequirements, r1: dict) -> dict:
    matched = [d for d in r1["must"] if d["matched"]]
    depth = sum(min(1.0, d["exp_mentions"] / 2) for d in matched) / max(1, len(r1["must"]))
    current = c.current_role_text
    current_skills = set(find_skills(current))
    for _ in range(2):  # follow implications two hops (Next.js -> React -> JavaScript)
        current_skills |= {imp for s in list(current_skills) for imp in IMPLIES.get(s, [])}
    recency = sum(1 for d in matched if d["via"] in current_skills) / max(1, len(r1["must"]))
    sig = seniority_signals(c)
    seniority = min(1.0, (0.4 if sig["senior_title"] else 0) + 0.1 * min(sig["leadership_bullets"], 3)
                    + 0.1 * min(sig["quantified_impact"], 3))
    deep_score = round(0.70 * r1["score"] + 100 * (0.12 * depth + 0.08 * recency + 0.10 * seniority), 1)

    strengths, gaps = [], []
    for d in sorted(matched, key=lambda d: -d["exp_mentions"]):
        if d["where"] == "skills + experience" and d["exp_mentions"] >= 2:
            strengths.append(f"Deep {d['via']} evidence ({d['exp_mentions']} mentions in work history)")
    if req.min_years and c.years_experience >= req.min_years + 2:
        strengths.append(f"Exceeds experience bar: {c.years_experience:g} yrs vs {req.min_years:g}+ required")
    elif req.min_years and c.years_experience >= req.min_years:
        strengths.append(f"Meets experience bar: {c.years_experience:g} yrs")
    if sig["senior_title"]:
        strengths.append(f"Currently in a senior role ({c.current_title})")
    if sig["leadership_bullets"] >= 2:
        strengths.append(f"Ownership/leadership signals ({sig['leadership_bullets']} 'led/owned/designed/mentored' mentions)")
    for d in matched:
        if d.get("min_years") and d.get("skill_years", 0) >= d["min_years"]:
            strengths.append(f"{d['via']}: {d['skill_years']:g} yrs in roles (JD asks {d['min_years']:g}+)")
    if r1["matched_nice"]:
        strengths.append("Brings nice-to-haves: " + ", ".join(r1["matched_nice"]))
    impact = next((b for r in c.roles for b in r.bullets if "%" in b), "")
    if impact:
        strengths.append(f"Quantified impact: \"{impact}\"")

    for s in r1["missing_must"]:
        gaps.append(f"Missing must-have: {s}")
    for d in r1["must"]:
        if d["matched"] and d["where"] == "skills list only":
            gaps.append(f"{d['skill']} is listed but not evidenced in any project/role")
        elif d["matched"] and d["where"].startswith("implied"):
            gaps.append(f"{d['skill']} only inferred ({d['where']}) - verify in screen")
    for d in matched:
        if d.get("min_years") and d.get("skill_years", 0) < d["min_years"]:
            yrs = d.get("skill_years", 0)
            gaps.append(f"{d['skill']}: only {yrs:g} yrs evidenced in roles vs {d['min_years']:g}+ asked"
                        if yrs else f"{d['skill']}: years of use not evidenced in any role (JD asks {d['min_years']:g}+)")
    if req.min_years and c.years_experience < req.min_years:
        gaps.append(f"Below experience bar: {c.years_experience:g} yrs vs {req.min_years:g}+ required")
    if matched and recency < 0.34:
        gaps.append("Most matched skills are not used in the current role (possible staleness)")
    if r1["missing_nice"]:
        gaps.append("No evidence of nice-to-haves: " + ", ".join(r1["missing_nice"][:4]))

    return r1 | {
        "deep_score": deep_score,
        "signals": {"depth": round(depth, 3), "recency": round(recency, 3), "seniority": round(seniority, 3), **sig},
        "strengths": strengths,
        "gaps": gaps,
    }


# ---------------------------------------------------------------- round 3


def recommend(d: dict, req: JobRequirements) -> dict:
    s, missing = d["deep_score"], len(d["missing_must"])
    under_exp = bool(req.min_years and d["years"] < req.min_years)          # below the bar: at best BORDERLINE
    far_under = bool(req.min_years and d["years"] < 0.6 * req.min_years)    # far below: NO HIRE
    if s >= config.STRONG_HIRE_AT and missing == 0 and not under_exp:
        decision = "STRONG HIRE"
    elif s >= config.HIRE_AT and missing == 0 and not under_exp:
        decision = "HIRE"
    elif s >= config.BORDERLINE_AT and missing <= 1 and not far_under:
        decision = "BORDERLINE"
    else:
        decision = "NO HIRE"

    nearest = {"STRONG HIRE": config.STRONG_HIRE_AT, "HIRE": config.HIRE_AT,
               "BORDERLINE": config.BORDERLINE_AT, "NO HIRE": config.BORDERLINE_AT}[decision]
    margin = abs(s - nearest)
    confidence = "high" if margin >= 8 else "medium" if margin >= 3 else "low"

    reasons = []
    if missing:
        reasons.append(f"missing {missing} must-have(s): {', '.join(d['missing_must'])}")
    else:
        reasons.append("covers every must-have")
    if far_under:
        reasons.append(f"far below the {req.min_years:g}+ yr bar ({d['years']:g} yrs)")
    elif under_exp:
        reasons.append(f"below the {req.min_years:g}+ yr bar ({d['years']:g} yrs)")
    reasons.append(f"deep score {s}")
    rationale = f"{decision}: " + "; ".join(reasons) + "."

    suggestions: list[str] = []
    if decision == "BORDERLINE":
        for sk in d["missing_must"]:
            suggestions.append(f"Close the {sk} gap: run a focused technical screen or short take-home on {sk}.")
        for g in d["gaps"]:
            if "listed but not evidenced" in g:
                sk = g.split(" is listed")[0]
                suggestions.append(f"Ask for a concrete {sk} project; candidate should add a quantified {sk} bullet to the resume.")
        if req.min_years and d["years"] < req.min_years:
            suggestions.append(f"Consider for a mid-level variant of the role, or offer with a {req.min_years:g}-yr growth plan.")
        if d["signals"]["seniority"] < 0.4:
            suggestions.append("Probe ownership: ask for a project they led end-to-end; resume should state scope and impact.")
        if not suggestions:
            suggestions.append("Score is close to the HIRE bar - a strong first-round interview should be decisive.")
    return {"decision": decision, "confidence": confidence, "rationale": rationale, "suggestions": suggestions}
