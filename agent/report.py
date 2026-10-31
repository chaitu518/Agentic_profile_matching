"""Markdown renderers for the chat summary and the saved match report."""
from __future__ import annotations

from datetime import datetime

from agent.requirements import JobRequirements

DECISION_ICON = {"STRONG HIRE": "🟢", "HIRE": "🟢", "BORDERLINE": "🟡", "NO HIRE": "🔴"}


def shortlist_table(shortlist: list[dict], r1_rank: dict[str, int]) -> str:
    rows = ["| # | Candidate | Yrs | R1 | Deep | Decision | Missing must-haves |",
            "|---|---|---|---|---|---|---|"]
    for i, d in enumerate(shortlist, 1):
        miss = ", ".join(d["missing_must"]) or "-"
        rows.append(f"| {i} | {d['name']} ({d['candidate_id']}) | {d['years']:g} | {d['score']} "
                    f"(#{r1_rank.get(d['candidate_id'], '?')}) | **{d['deep_score']}** | "
                    f"{DECISION_ICON.get(d['decision'], '')} {d['decision']} | {miss} |")
    return "\n".join(rows)


def chat_summary(req: JobRequirements, shortlist: list[dict], r1_rank: dict[str, int], n_screened: int,
                 n_retrieved: int, report_path: str) -> str:
    counts: dict[str, int] = {}
    for d in shortlist:
        counts[d["decision"]] = counts.get(d["decision"], 0) + 1
    order = ["STRONG HIRE", "HIRE", "BORDERLINE", "NO HIRE"]
    funnel = " · ".join(f"{k}: {counts[k]}" for k in order if k in counts)
    top = shortlist[0] if shortlist else None
    flt = f" → {n_screened} pass filters" if n_screened < n_retrieved else ""
    parts = [
        f"## Shortlist for: {req.title}",
        req.summary(),
        "",
        f"**Funnel:** {n_retrieved} resumes scored by Milestone 2 hybrid search{flt} → round 1 scores every eligible resume → "
        f"top {len(shortlist)} deep-analysed (round 2) → round 3: {funnel}",
        "",
        shortlist_table(shortlist, r1_rank),
    ]
    if top and top["decision"] == "NO HIRE":
        parts += ["", "⚠️ **Nobody under the current criteria is hireable.** The filters or must-haves may be too "
                      "strict for this pool. Try relaxing one (e.g. \"any degree\", or move a skill to nice-to-have)."]
    elif top:
        parts += ["", f"**Top pick: {top['name']}** - {top['rationale']}"]
    promote = req.nice_to_have[0].skill if req.nice_to_have else "Docker"
    parts += ["", f"Full match report saved to `{report_path}`.",
              f"_Try: \"compare the top 3\", \"why is #1 above #2?\", \"make {promote} a must-have\", "
              "\"interview questions for #1\", \"tell me about #4\", or \"done\"._"]
    return "\n".join(parts)


def candidate_section(i: int, d: dict) -> str:
    out = [f"### #{i} {d['name']} ({d['candidate_id']}) - {DECISION_ICON.get(d['decision'], '')} {d['decision']} "
           f"({d['confidence']} confidence)",
           f"*{d['title']} · {d['years']:g} yrs · {d['degree']} · `{d['resume_path']}`* - round-1 **{d['score']}**, "
           f"deep **{d['deep_score']}**, M2 baseline {d.get('m2_score', '-')}",
           "", f"**Rationale:** {d['rationale']}", "", "**Strengths**"]
    out += [f"- {s}" for s in d["strengths"]] or ["- -"]
    out += ["", "**Gaps**"]
    out += [f"- {g}" for g in d["gaps"]] or ["- none significant"]
    out += ["", "| Requirement | Type | Status | Where | Evidence |", "|---|---|---|---|---|"]
    for kind, rows in (("must", d["must"]), ("nice", d["nice"])):
        for r in rows:
            status = "✓" if r["matched"] and r["strength"] >= 0.8 else ("~" if r["matched"] else "✗")
            via = f" via {r['via']}" if r["matched"] and r["via"] != r["skill"] else ""
            ev = (r["evidence"][:90] + "…") if len(r["evidence"]) > 90 else r["evidence"]
            out.append(f"| {r['skill']}{via} | {kind} | {status} {r['strength']:.2f} | {r['where']} | {ev or '-'} |")
    ex = (d.get("rag") or {}).get("excerpts") or []
    if ex:
        out += ["", "**RAG excerpts (Milestone 2 retrieval)**"] + [f"> {e}" for e in ex[:3]]
    sig = d["signals"]
    out += ["", f"Signals - depth {sig['depth']:.2f}, recency {sig['recency']:.2f}, seniority {sig['seniority']:.2f}, "
                f"quantified bullets {sig['quantified_impact']}"]
    if d.get("suggestions"):
        out += ["", "**Improvement suggestions (borderline)**"] + [f"- {s}" for s in d["suggestions"]]
    return "\n".join(out)


def full_report(state: dict, req: JobRequirements, shortlist: list[dict], ranked_ids: list[str],
                change_md: str | None, llm_summary: str | None) -> str:
    scores = state["all_scores"]
    lines = [
        f"# Candidate Match Report - {req.title}",
        f"_Generated {datetime.now():%Y-%m-%d %H:%M} · requirements extracted by {state.get('extraction_method', 'rules')} · "
        f"JD source: {state.get('jd_source', 'chat')}_",
        "", "## Requirements", req.summary(),
        "", "## Scoring model",
        "Round 1 = " + " + ".join(f"{int(v * 100)}% {k.replace('_', '-')}" for k, v in state["weights"].items())
        + " (RAG = Milestone 2 hybrid semantic + BM25 signal). Round 2 deep score = 70% round-1 + 12% evidence depth + 8% recency + 10% seniority/impact. "
          "Round 3: STRONG HIRE ≥85 and HIRE ≥72 need every must-have and the experience bar; BORDERLINE ≥58 allows one missing must-have or being under the bar; otherwise NO HIRE.",
    ]
    if llm_summary:
        lines += ["", "## Executive summary", llm_summary]
    lines += ["", "## Round 1 - initial screen (top 10 of "
              f"{len(scores)})", "| Rank | Candidate | Yrs | Score | Must | Nice | Exp | RAG | M2 score | Missing |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for i, cid in enumerate(ranked_ids[:10], 1):
        s = scores[cid]
        c = s["components"]
        lines.append(f"| {i} | {s['name']} | {s['years']:g} | {s['score']} | {c['must_have']:.2f} | {c['nice_to_have']:.2f} | "
                     f"{c['experience']:.2f} | {c['retrieval']:.2f} | {s.get('m2_score', '-')} | {', '.join(s['missing_must']) or '-'} |")
    lines += ["", "## Rounds 2 & 3 - deep analysis and recommendation"]
    lines += [candidate_section(i, d) + "\n" for i, d in enumerate(shortlist, 1)]
    if change_md:
        lines += ["## Changes since previous ranking", change_md]
    return "\n".join(lines)
