"""Hands-free demo of the whole project, for recording the Milestone 3 video.

    python run_demo.py                  # full demo, about 6 minutes, nothing to type
    python run_demo.py --speed 1.5      # slower (more time to read or talk over each step)
    python run_demo.py --speed 0.6      # faster
    python run_demo.py --pause          # wait for Enter between sections (if you want to narrate live)
    python run_demo.py --no-diagram     # don't open the state-machine image
    python run_demo.py --streamlit      # finish by launching the Streamlit chat UI

Sections, each introduced by an on-screen caption so the video explains itself:
  1. Architecture     - state machine, AgentState, tools (read from the real code)
  2. Milestone 1      - file tools reading PDF / DOCX / TXT resumes
  3. Milestone 2      - hybrid RAG search (ChromaDB semantic + BM25)
  4. Milestone 3      - full agent conversation with live reasoning + tool calls
  5. Explainability   - the saved match report
  6. Tests            - pytest: 8 conversation flows + integration tests
  7. Evaluation       - agent vs Milestone 2 ranking quality on 100 resumes
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

os.environ.setdefault("PYTHONUTF8", "1")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from rich.console import Console  # noqa: E402
from rich.markdown import Markdown  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.rule import Rule  # noqa: E402
from rich.table import Table  # noqa: E402

ROOT = Path(__file__).resolve().parent
console = Console()
SPEED = 1.0
PAUSE = False


def wait(seconds: float) -> None:
    time.sleep(max(0.0, seconds * SPEED))


def read_time(text: str, base: float = 3.0, per_char: float = 1 / 90, cap: float = 22.0) -> float:
    """Pause long enough for a viewer to read what just appeared."""
    return min(cap, base + len(text) * per_char)


def section(n: int, title: str, caption: str) -> None:
    if PAUSE:
        console.input(f"\n[dim]Press Enter for section {n}: {title}[/] ")
    console.clear()
    console.print(Rule(f"[bold cyan]{n}. {title}"))
    console.print(Panel(caption, border_style="cyan", padding=(1, 2)))
    wait(read_time(caption, base=4))


def type_out(prefix: str, text: str) -> None:
    console.print(prefix, end="")
    for ch in text:
        console.print(ch, end="", highlight=False)
        time.sleep(0.03 * SPEED)
    console.print()
    wait(0.6)


def run(cmd: list[str], title: str) -> None:
    console.print(f"[bold green]$[/] {' '.join(cmd)}")
    wait(1)
    subprocess.run([sys.executable, *cmd[1:]] if cmd[0] == "python" else cmd, cwd=ROOT,
                   env={**os.environ, "PYTHONUTF8": "1"})


# ----------------------------------------------------------------------------- sections

def prepare() -> None:
    with console.status("Preparing: checking the 100-resume corpus and warming up the Milestone 2 index..."):
        corpus = ROOT / "data" / "resumes_m3"
        if not corpus.exists() or len(list(corpus.iterdir())) < 100:
            subprocess.run([sys.executable, "scripts/build_m3_corpus.py"], cwd=ROOT, check=True)
        from agent.pipeline import corpus as load_corpus
        from agent.tools.rag_search import get_matcher
        get_matcher()
        load_corpus()


def title_card() -> None:
    console.clear()
    console.print(Panel(
        "[bold]Milestone 3 - Intelligent Resume Matching Agent (LangGraph)[/]\n\n"
        "Built on Milestone 1 (LLM-Powered File System Assistant) and Milestone 2 (Resume RAG & Job Matching Engine).\n"
        "Screens 100 resumes in three rounds, explains every decision, and lets the recruiter refine the search "
        "in conversation.\n\n"
        "[dim]This demo runs hands-free: every output below is produced live by the code.[/]",
        border_style="green", padding=(1, 2)))
    wait(7)


def architecture(open_diagram: bool) -> None:
    section(1, "Architecture",
            "A LangGraph state machine: parse JD → extract requirements → search resumes → round 1 (rank 100) → "
            "round 2 (deep analysis of top 10) → round 3 (hire / no-hire) → report → human feedback loop.\n"
            "The feedback node pauses with interrupt(); each message is routed to refine, compare, explain, "
            "interview questions... and refinements loop back to search to re-rank.")
    img = ROOT / "docs" / "m3" / "state_machine.png"
    if open_diagram and img.exists():
        try:
            if sys.platform.startswith("win"):
                os.startfile(img)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(img)])
            else:
                subprocess.Popen(["xdg-open", str(img)])
            console.print(f"[dim]Opened {img.relative_to(ROOT)} - showing the state machine...[/]")
            wait(12)
        except Exception:
            pass

    from matching_agent import AgentState, build_graph
    g = build_graph().get_graph()
    nodes = [n for n in g.nodes if not n.startswith("__")]
    console.print(f"[bold]Compiled graph:[/] {len(nodes)} nodes, {len(g.edges)} edges")
    console.print("  " + " → ".join(["START", *nodes[:8], "⟲"]))
    console.print("  feedback routes: " + ", ".join(nodes[8:]) + ", END\n")
    wait(6)

    groups = {
        "Conversation history": ["messages", "intent", "turn"],
        "Job requirements understanding": ["jd_text", "jd_source", "requirements", "weights", "filters", "change_log"],
        "Candidate shortlist + reasoning": ["retrieved", "all_scores", "ranked_ids", "shortlist", "previous_shortlist",
                                            "ranking_changes", "report_path"],
        "Audit trail": ["reasoning", "tool_trace"],
    }
    t = Table(title="AgentState (from matching_agent.py)", show_lines=False)
    t.add_column("Tracks", style="bold")
    t.add_column("Fields")
    for k, fields in groups.items():
        t.add_row(k, ", ".join(f for f in fields if f in AgentState.__annotations__))
    console.print(t)
    wait(8)

    from agent.tools.agent_tools import AGENT_TOOLS
    from agent.tools.filesystem_tools import FS_TOOLS
    from agent.tools.rag_search import rag_search
    t = Table(title="Tools available to the agent")
    t.add_column("Tool", style="bold")
    t.add_column("From")
    t.add_column("Purpose")
    for tool in FS_TOOLS:
        t.add_row(tool.name, "Milestone 1", tool.description.split(".")[0])
    t.add_row(rag_search.name, "Milestone 2", "Hybrid RAG search: ChromaDB semantic + BM25, M2 match score")
    for tool in AGENT_TOOLS:
        t.add_row(tool.name, "Milestone 3", tool.description.split(".")[0])
    console.print(t)
    wait(10)


def milestone1() -> None:
    section(2, "Milestone 1 - file system tools",
            "The agent loads job descriptions and resumes with the Milestone 1 tools (unchanged code in "
            "milestone1/fs_tools.py). They read PDF, DOCX and TXT, and return errors as data so the agent can recover.")
    from agent.tools.filesystem_tools import list_files, read_file, search_in_file
    files = list_files.invoke({"directory": "data/resumes_m3"})
    by_ext: dict[str, int] = {}
    for f in files:
        by_ext[Path(f["name"]).suffix] = by_ext.get(Path(f["name"]).suffix, 0) + 1
    console.print(f"[bold green]list_files[/](data/resumes_m3) → {len(files)} resumes {by_ext}")
    wait(3)
    res = read_file.invoke({"filepath": "data/resumes_m3/priya_tanaka.pdf"})
    console.print(f"[bold green]read_file[/](priya_tanaka.pdf) → {res['metadata']}")
    console.print(Panel("\n".join(res["content"].splitlines()[:9]), title="first lines of a PDF resume",
                        border_style="dim"))
    wait(6)
    s = search_in_file.invoke({"filepath": "data/resumes_m3/john_mathew.txt", "keyword": "TypeScript"})
    console.print(f"[bold green]search_in_file[/](john_mathew.txt, 'TypeScript') → {s['match_count']} matches")
    for m in s["matches"][:2]:
        console.print(f"   …{m['context']}…")
    bad = read_file.invoke({"filepath": "data/resumes_m3/nobody.txt"})
    console.print(f"[bold green]read_file[/](nobody.txt) → {bad}   [dim](error returned as data)[/]")
    wait(6)


def milestone2() -> None:
    section(3, "Milestone 2 - RAG search",
            "The agent's rag_search tool is Milestone 2's JobMatcher: section-aware chunks embedded into ChromaDB, "
            "hybrid semantic + BM25 retrieval, and M2's own 0-100 score. Here it runs for the frontend React JD.")
    from agent.tools.rag_search import rag_search
    jd = (ROOT / "data" / "job_descriptions" / "jd05_frontend_react.txt").read_text(encoding="utf-8")
    console.print(Panel(jd.strip(), title="jd05_frontend_react.txt", border_style="dim"))
    wait(6)
    hits = rag_search.invoke({"query": jd, "k": 6})
    t = Table(title="rag_search → top 6 of 100")
    for c in ("Candidate", "Semantic", "BM25", "M2 score", "Best excerpt"):
        t.add_column(c)
    for h in hits:
        t.add_row(h["name"], f"{h['semantic']:.2f}", f"{h['keyword']:.2f}", str(h["m2_score"]),
                  (h["excerpts"][0][:70] + "…") if h["excerpts"] else "-")
    console.print(t)
    wait(10)


def conversation() -> None:
    section(4, "Milestone 3 - the agent in conversation",
            "A recruiter conversation. Each turn shows the agent's reasoning and tool calls (grey panel) and its "
            "answer (blue panel): search, side-by-side comparison, 'why A over B', changing requirements "
            "mid-conversation with re-ranking and explained moves, a candidate deep dive, and interview questions.")
    from chat_cli import show_turn
    from matching_agent import MatchingSession
    script = ROOT / "tests" / "scenarios" / "demo.txt"
    messages = [ln.strip() for ln in script.read_text(encoding="utf-8").splitlines()
                if ln.strip() and not ln.startswith("#")]
    s = MatchingSession(thread_id=str(uuid.uuid4()))
    for msg in messages:
        if PAUSE:
            console.input("[dim]Enter for next message[/] ")
        console.print(Rule(style="dim"))
        type_out("[bold green]recruiter>[/] ", msg)
        st = s.state if s.started else {}
        before = (len(st.get("reasoning", [])), len(st.get("tool_trace", [])))
        replies = s.send(msg)
        show_turn(s, replies, trace=True, before=before)
        wait(read_time("\n".join(replies), base=4))
        if s.finished:
            console.print("[bold]Graph reached END.[/]")
            wait(2)
    return s.state.get("report_path")


def report(path: str | None) -> None:
    section(5, "Explainability - the match report",
            "Every turn writes a Markdown report with the Milestone 1 write_file tool: requirements, scoring model, "
            "round-1 table with M2's baseline score, and per-candidate strengths, gaps, evidence and suggestions.")
    if not path:
        reports = sorted((ROOT / "outputs" / "m3_reports").glob("*.md"))
        path = str(reports[-1].relative_to(ROOT)) if reports else None
    if not path:
        console.print("[red]No report found.[/]")
        return
    text = (ROOT / path).read_text(encoding="utf-8")
    console.print(f"[bold]{path}[/]")
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if ln.startswith("### #1")), 0)
    end_r1 = next((i for i, ln in enumerate(lines) if ln.startswith("## Rounds 2")), 12)
    console.print(Markdown("\n".join(lines[:end_r1])))
    wait(12)
    console.print(Markdown("\n".join(lines[start:start + 40])))
    wait(14)


def tests() -> None:
    section(6, "Test scenarios",
            "pytest runs 8 complete conversation flows (search, compare, explain, refine + re-rank, multi-round "
            "screening, filters, switching jobs, clarification) plus integration tests for the M1 and M2 tools.")
    run(["python", "-m", "pytest", "-q", "tests/test_m3_agent.py"], "tests")
    wait(5)


def evaluation() -> None:
    section(7, "Does the agent rank better than Milestone 2 alone?",
            "Top-10 from 100 resumes on the 6 Milestone 2 job descriptions, scored against graded relevance labels "
            "(2 = right role and senior enough, 1 = right role but junior).")
    run(["python", "scripts/evaluate_m3.py"], "eval")
    wait(10)


def closing(streamlit: bool) -> None:
    console.clear()
    console.print(Panel(
        "[bold]Summary[/]\n\n"
        "• LangGraph agent with state for conversation, requirements, shortlist and reasoning\n"
        "• Tools: Milestone 1 file tools · Milestone 2 RAG search · extract_requirements · compare_candidates · "
        "generate_interview_questions\n"
        "• Natural-language chat, mid-conversation refinement with re-ranking and explained moves\n"
        "• Three screening rounds: top 10 of 100 → deep analysis → hire / no-hire, with suggestions for borderline\n"
        "• Explainable reports, 8 tested conversation flows, CLI and Streamlit interfaces\n\n"
        "[dim]Code: matching_agent.py · agent/ · docs: MILESTONE3.md[/]",
        border_style="green", padding=(1, 2)))
    wait(10)
    if streamlit:
        console.print("[bold]Launching the Streamlit chat UI (Ctrl+C to stop)...[/]")
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app_streamlit.py"], cwd=ROOT)


def main() -> None:
    global SPEED, PAUSE
    ap = argparse.ArgumentParser(description="Hands-free project demo")
    ap.add_argument("--speed", type=float, default=1.0, help="multiply all pauses (1.5 = slower, 0.5 = faster)")
    ap.add_argument("--pause", action="store_true", help="wait for Enter between sections and messages")
    ap.add_argument("--no-diagram", action="store_true")
    ap.add_argument("--no-tests", action="store_true")
    ap.add_argument("--streamlit", action="store_true", help="launch the Streamlit UI at the end")
    args = ap.parse_args()
    SPEED, PAUSE = args.speed, args.pause

    prepare()
    title_card()
    architecture(open_diagram=not args.no_diagram)
    milestone1()
    milestone2()
    path = conversation()
    report(path)
    if not args.no_tests:
        tests()
        evaluation()
    closing(args.streamlit)


if __name__ == "__main__":
    main()
