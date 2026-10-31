"""Evaluate the Milestone 3 agent's shortlist against graded relevance labels, next to the Milestone 2 baseline.

    python scripts/evaluate_m3.py            # writes outputs/m3_metrics.json

Labels (data/ground_truth_m3.json, built by build_m3_corpus.py with M2's own relevance rule):
2 = right role family and meets min years, 1 = right family but junior, 0 = other.

Compared rankings (top 10 from 100 resumes, the 6 Milestone 2 JDs):
* M2 hybrid           - JobMatcher.match(jd), no must-have filter
* M2 hybrid + filter  - JobMatcher.match(jd) with M2's must-have / years filter (M2's headline setting)
* M3 round 1          - agent's round-1 ranking
* M3 final (round 3)  - agent's final order (decision tier, then deep score)
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent import config, pipeline  # noqa: E402
from agent.requirements import extract_requirements_rules  # noqa: E402
from agent.tools.rag_search import get_matcher  # noqa: E402


def ndcg(ranked: list[str], rel: dict[str, int], k: int = 10) -> float:
    dcg = sum((2 ** rel.get(p, 0) - 1) / math.log2(i + 2) for i, p in enumerate(ranked[:k]))
    ideal = sorted(rel.values(), reverse=True)[:k]
    idcg = sum((2 ** g - 1) / math.log2(i + 2) for i, g in enumerate(ideal))
    return dcg / idcg if idcg else 0.0


def metrics(ranked: list[str], rel: dict[str, int], k: int = 10) -> dict:
    strong = {p for p, g in rel.items() if g == 2}
    top = ranked[:k]
    r = len(strong)
    return {
        "P@10 (grade 2)": sum(p in strong for p in top) / k,
        "R-Prec (grade 2)": sum(p in strong for p in ranked[:r]) / r if r else 0.0,
        "nDCG@10": ndcg(ranked, rel, k),
        "wrong-family@10": sum(rel.get(p, 0) == 0 for p in top),
    }


def main() -> None:
    gt = json.loads((ROOT / "data" / "ground_truth_m3.json").read_text())
    m = get_matcher()
    systems: dict[str, list[dict]] = {}
    per_jd = {}
    for jd_id, info in gt["job_descriptions"].items():
        text = (ROOT / info["path"]).read_text()
        rel = info["relevance"]
        req = extract_requirements_rules(text)
        m2 = [t["resume_path"] for t in m.match(text, k=100, apply_filters=False)["top_matches"]]
        m2f = [t["resume_path"] for t in m.match(text, k=100, apply_filters=True)["top_matches"]]
        hits = pipeline.retrieve(req)
        scores = pipeline.round1(req, config.DEFAULT_WEIGHTS, {}, hits)
        r1 = sorted(scores, key=lambda c: (-scores[c]["score"], c))
        final = pipeline.round3(req, pipeline.round2(req, scores, r1[:config.SHORTLIST_SIZE]))
        path = {cid: s["resume_path"] for cid, s in scores.items()}
        m3_r1 = [path[c] for c in r1]
        m3_final = [d["resume_path"] for d in final] + [path[c] for c in r1[config.SHORTLIST_SIZE:]]
        runs = {"M2 hybrid": m2, "M2 hybrid + filter": m2f, "M3 round 1": m3_r1, "M3 final (round 3)": m3_final}
        per_jd[jd_id] = {name: metrics(r, rel) for name, r in runs.items()}
        per_jd[jd_id]["M3 decisions"] = {d["decision"]: sum(x["decision"] == d["decision"] for x in final) for d in final}
        for name, r in runs.items():
            systems.setdefault(name, []).append(metrics(r, rel))

    summary = {name: {k: round(sum(x[k] for x in rows) / len(rows), 3) for k in rows[0]}
               for name, rows in systems.items()}
    out = {"corpus": str(config.RESUME_DIR.relative_to(ROOT)), "embedder": m.rag.embedder.name,
           "summary": summary, "per_jd": per_jd}
    dest = ROOT / "outputs" / "m3_metrics.json"
    dest.write_text(json.dumps(out, indent=2))
    print(f"{'system':<22}" + "".join(f"{k:>18}" for k in next(iter(summary.values()))))
    for name, row in summary.items():
        print(f"{name:<22}" + "".join(f"{v:>18}" for v in row.values()))
    for jd_id, d in per_jd.items():
        print(jd_id, d["M3 decisions"])
    print(f"wrote {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
