"""Replay every tests/scenarios/*.txt conversation and save a Markdown transcript per flow.

    python scripts/run_scenarios.py
Output: docs/m3/transcripts/<scenario>.md  (agent replies + reasoning + tool calls per turn)
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from matching_agent import MatchingSession  # noqa: E402

OUT = ROOT / "docs" / "m3" / "transcripts"


def run(path: Path) -> Path:
    lines = path.read_text(encoding="utf-8").splitlines()
    title = next((ln.lstrip("# ").strip() for ln in lines if ln.startswith("#")), path.stem)
    msgs = [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]
    s = MatchingSession(thread_id=str(uuid.uuid4()))
    md = [f"# {title}", f"_Source: `{path.relative_to(ROOT)}`_", ""]
    for i, text in enumerate(msgs, 1):
        st = s.state if s.started else {}
        r0, t0 = len(st.get("reasoning", [])), len(st.get("tool_trace", []))
        replies = s.send(text)
        st = s.state
        md += [f"## Turn {i}", f"**User:** {text}", ""]
        trace = [f"- {r}" for r in st.get("reasoning", [])[r0:]] + [
            f"- 🔧 `{t['tool']}` → {t['result']}" for t in st.get("tool_trace", [])[t0:]]
        if trace:
            md += ["<details><summary>Agent reasoning & tool calls</summary>", "", *trace, "", "</details>", ""]
        for r in replies:
            md += ["**Agent:**", "", r, ""]
        if s.finished:
            md += ["_Conversation ended (graph reached END)._"]
            break
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{path.stem}.md"
    out.write_text("\n".join(md), encoding="utf-8")
    return out


if __name__ == "__main__":
    for p in sorted((ROOT / "tests" / "scenarios").glob("*.txt")):
        print("wrote", run(p).relative_to(ROOT))
