"""Explainability helpers: pairwise 'why A > B', ranking-change diffs, side-by-side tables."""
from __future__ import annotations

COMPONENT_LABEL = {
    "must_have": "must-have coverage",
    "nice_to_have": "nice-to-have coverage",
    "experience": "experience fit",
    "retrieval": "RAG retrieval (M2 semantic + BM25)",
}


def _req_map(s: dict) -> dict[str, dict]:
    return {d["skill"]: d for d in s["must"] + s["nice"]}


def explain_pair(a: dict, b: dict, rank_of: dict[str, int]) -> str:
    """Why does `a` rank above `b`? Score dicts (round-1, optionally merged with round-2/3 fields).
    `rank_of` is the displayed order (final shortlist first, then round-1 order)."""
    big = 10 ** 6
    flipped = rank_of.get(a["candidate_id"], big) > rank_of.get(b["candidate_id"], big)
    if flipped:
        a, b = b, a
    ra, rb = rank_of.get(a["candidate_id"], "?"), rank_of.get(b["candidate_id"], "?")
    lines = []
    if flipped:
        lines.append(f"Actually **{a['name']}** ranks above **{b['name']}**, so here's why it's that way round.\n")
    gap = a["score"] - b["score"]
    lines.append(f"**{a['name']}** (#{ra}, round-1 {a['score']}) vs **{b['name']}** (#{rb}, round-1 {b['score']}).")
    if gap < 0 and a.get("decision") and b.get("decision"):
        lines.append(f"\nRound 1 actually favoured {b['name']} by {-gap:.1f} points, but the final order is set in "
                     f"rounds 2-3: **{a['name']} = {a['decision']}** (deep {a['deep_score']}) vs "
                     f"**{b['name']} = {b['decision']}** (deep {b['deep_score']}"
                     + (f", missing {', '.join(b['missing_must'])}" if b['missing_must'] else "") + "). "
                     "Hire-ready candidates are listed above borderline ones.\n")
    else:
        lines.append(f"A gap of **{gap:.1f} points** in round 1.\n")
    diffs = sorted(((k, a["contributions"][k] - b["contributions"][k]) for k in a["contributions"]),
                   key=lambda kv: -abs(kv[1]))
    lines.append("| Round-1 factor | " + a["name"] + " | " + b["name"] + " | Points to " + a["name"].split()[0] + " |")
    lines.append("|---|---|---|---|")
    for k, delta in diffs:
        lines.append(f"| {COMPONENT_LABEL[k]} | {a['components'][k]:.2f} | {b['components'][k]:.2f} | {delta:+.1f} |")
    lines.append("")
    ma, mb = _req_map(a), _req_map(b)
    musts = {d["skill"] for d in a["must"]}
    only_a = [s for s in ma if ma[s]["matched"] and not mb.get(s, {}).get("matched")]
    only_b = [s for s in mb if mb[s]["matched"] and not ma.get(s, {}).get("matched")]
    only_a_must = [s for s in only_a if s in musts]
    only_a_nice = [s for s in only_a if s not in musts]
    stronger_a = [s for s in ma if ma[s]["matched"] and mb.get(s, {}).get("matched")
                  and ma[s]["strength"] - mb[s]["strength"] >= 0.15]
    reasons = []
    top_k, top_delta = diffs[0]
    reasons.append(f"The biggest round-1 driver is **{COMPONENT_LABEL[top_k]}** ({top_delta:+.1f} pts).")
    if only_a_must:
        reasons.append(f"Must-haves only {a['name']} has: **{', '.join(only_a_must)}**.")
    if only_a_nice:
        reasons.append(f"Nice-to-haves only {a['name']} has: {', '.join(only_a_nice)}.")
    if stronger_a:
        reasons.append(f"{a['name']} shows stronger evidence for {', '.join(stronger_a)} "
                       "(used in real projects, not just listed).")
    if a["years"] != b["years"]:
        reasons.append(f"Experience: {a['years']:g} yrs vs {b['years']:g} yrs.")
    if only_b:
        reasons.append(f"In {b['name']}'s favour: {', '.join(only_b)} - but not enough to close the gap.")
    if b.get("missing_must"):
        reasons.append(f"{b['name']} is missing must-have(s): {', '.join(b['missing_must'])}.")
    lines += [f"- {r}" for r in reasons]
    return "\n".join(lines)


def explain_single(s: dict, rank: int, total: int, shortlist_size: int) -> str:
    status = "in the shortlist" if rank <= shortlist_size else f"outside the top {shortlist_size}"
    out = [f"**{s['name']}** is ranked **#{rank} of {total}** ({status}) with a round-1 score of **{s['score']}**.\n",
           "| Factor | Value | Points |", "|---|---|---|"]
    for k, v in s["components"].items():
        out.append(f"| {COMPONENT_LABEL[k]} | {v:.2f} | {s['contributions'][k]:.1f} |")
    out.append("")
    if s["matched_must"]:
        out.append(f"- Has must-haves: {', '.join(s['matched_must'])}")
    if s["missing_must"]:
        out.append(f"- Missing must-haves: **{', '.join(s['missing_must'])}**")
    if s["matched_nice"]:
        out.append(f"- Nice-to-haves present: {', '.join(s['matched_nice'])}")
    weak = [d["skill"] + f" ({d['where']})" for d in s["must"] if d["matched"] and d["strength"] < 0.8]
    if weak:
        out.append(f"- Weak evidence: {', '.join(weak)}")
    out.append(f"- Experience: {s['years']:g} yrs")
    if s.get("decision"):
        out.append(f"- Round-3 decision: **{s['decision']}** ({s.get('confidence')} confidence)")
    return "\n".join(out)


def explain_changes(prev: list[dict], new: list[dict], change_log: list[str], all_new: dict[str, dict],
                    all_prev: dict[str, dict]) -> tuple[str, list[dict]]:
    """Diff two top-N lists and attribute each move to the factor that changed most."""
    prev_rank = {s["candidate_id"]: i + 1 for i, s in enumerate(prev)}
    new_rank = {s["candidate_id"]: i + 1 for i, s in enumerate(new)}
    changes = []
    for cid, nr in new_rank.items():
        pr = prev_rank.get(cid)
        if pr == nr:
            continue
        changes.append({"candidate_id": cid, "name": all_new[cid]["name"], "from": pr, "to": nr,
                        "why": _attribute(all_prev.get(cid), all_new[cid])})
    for cid, pr in prev_rank.items():
        if cid not in new_rank:
            changes.append({"candidate_id": cid, "name": all_prev[cid]["name"], "from": pr, "to": None,
                            "why": _attribute(all_prev[cid], all_new.get(cid))})
    changes.sort(key=lambda c: (c["to"] is None, c["to"] or 99))
    lines = ["### What changed", *[f"- {c}" for c in change_log], ""]
    if not changes:
        lines.append("The top of the ranking is unchanged - the update didn't separate the shortlist.")
    else:
        lines.append("### Ranking movement")
        filtered = [c["name"] for c in changes if c["to"] is None and c["why"].startswith("filtered out")]
        backfill = [c["name"] for c in changes if c["from"] is None and c["why"].startswith("score unchanged")]
        for c in changes:
            if c["name"] in filtered or c["name"] in backfill:
                continue
            if c["from"] is None:
                arrow = f"NEW at #{c['to']}"
            elif c["to"] is None:
                arrow = f"#{c['from']} -> dropped out"
            else:
                arrow = f"#{c['from']} -> #{c['to']} ({'up' if c['to'] < c['from'] else 'down'})"
            lines.append(f"- **{c['name']}**: {arrow} - {c['why']}")
        if filtered:
            lines.append(f"- Filtered out by the new criteria: {', '.join(filtered)}")
        if backfill:
            lines.append(f"- Moved into the top {len(prev) or 10} because others were filtered out (scores unchanged): "
                         + ", ".join(backfill))
    return "\n".join(lines), changes


def _attribute(before: dict | None, after: dict | None) -> str:
    if not before or not after:
        return "filtered out by the new criteria" if before and not after else "newly eligible under the new criteria"
    bits = []
    newly_missing = set(after["missing_must"]) - set(before["missing_must"])
    newly_has = (set(after["matched_must"]) - set(before["matched_must"])) - set(before["matched_nice"])
    has_promoted = set(after["matched_must"]) & set(before["matched_nice"])
    if newly_missing:
        bits.append("lacks newly required " + ", ".join(sorted(newly_missing)))
    if has_promoted or newly_has:
        bits.append("has newly required " + ", ".join(sorted(has_promoted | newly_has)))
    exp_delta = after["contributions"]["experience"] - before["contributions"]["experience"]
    if abs(exp_delta) >= 1:
        bits.append(f"experience fit {exp_delta:+.1f} pts ({after['years']:g} yrs)")
    deltas = {k: after["contributions"][k] - before["contributions"][k] for k in after["contributions"]}
    k, d = max(((k, v) for k, v in deltas.items() if k != "experience"), key=lambda kv: abs(kv[1]))
    if not bits and abs(d) < 0.05 and abs(exp_delta) < 0.05:
        return f"score unchanged ({after['score']}); moved because candidates around them were filtered out or re-scored"
    if abs(d) >= 1 or not bits:
        bits.append(f"{COMPONENT_LABEL[k]} {d:+.1f} pts")
    bits.append(f"score {before['score']} -> {after['score']}")
    return "; ".join(bits)


def compare_table(cands: list[dict], req) -> str:
    names = [c["name"] for c in cands]
    rows = ["| | " + " | ".join(names) + " |", "|---|" + "---|" * len(cands)]

    def row(label, vals):
        rows.append(f"| {label} | " + " | ".join(str(v) for v in vals) + " |")

    row("Round-1 score", [c["score"] for c in cands])
    row("Deep score", [c.get("deep_score", "-") for c in cands])
    row("Decision", [c.get("decision", "-") for c in cands])
    row("Experience", [f"{c['years']:g} yrs" for c in cands])
    row("Current title", [c["title"] for c in cands])
    for r in req.must_have:
        row(f"**{r.skill}** (must)", [_tick(_req_map(c).get(r.skill)) for c in cands])
    for r in req.nice_to_have:
        row(f"{r.skill} (nice)", [_tick(_req_map(c).get(r.skill)) for c in cands])
    row("Seniority signal", [f"{c['signals']['seniority']:.2f}" if c.get("signals") else "-" for c in cands])
    best = max(cands, key=lambda c: c.get("deep_score", c["score"]))
    out = "\n".join(rows)
    out += f"\n\n**Verdict:** {best['name']} leads on the combined deep score."
    for c in cands:
        st = "; ".join(c.get("strengths", [])[:2]) or "-"
        gp = "; ".join(c.get("gaps", [])[:2]) or "none significant"
        out += f"\n- **{c['name']}** - strengths: {st}. Gaps: {gp}."
    return out


def _tick(d: dict | None) -> str:
    if not d or not d["matched"]:
        return "✗"
    return "✓" if d["strength"] >= 0.8 else "~ (" + d["where"] + ")"
