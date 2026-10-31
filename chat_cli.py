"""Terminal chat interface.

    python chat_cli.py                       # interactive
    python chat_cli.py --trace               # also print the agent's reasoning + tool calls each turn
    python chat_cli.py --script tests/scenarios/demo.txt   # replay a scripted conversation (great for the demo video)
"""
from __future__ import annotations

import argparse
import time
import uuid

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from matching_agent import HELP, MatchingSession

console = Console()


def show_turn(session: MatchingSession, replies: list[str], trace: bool, before: tuple[int, int]) -> None:
    st = session.state
    if trace:
        r_new = st.get("reasoning", [])[before[0]:]
        t_new = st.get("tool_trace", [])[before[1]:]
        lines = [f"• {r}" for r in r_new] + [f"🔧 {t['tool']}({', '.join(f'{k}={v!r}' for k, v in t['args'].items())}) → {t['result']}"
                                              for t in t_new]
        if lines:
            console.print(Panel("\n".join(lines), title="agent reasoning", border_style="dim", expand=True))
    for r in replies:
        console.print(Panel(Markdown(r), title="agent", border_style="cyan"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", action="store_true", help="print reasoning and tool calls")
    ap.add_argument("--script", help="file with one user message per line")
    ap.add_argument("--delay", type=float, default=0.0, help="pause between scripted turns (seconds)")
    args = ap.parse_args()

    session = MatchingSession(thread_id=str(uuid.uuid4()))
    console.print(Panel(Markdown("# Resume Matching Agent\n" + HELP), border_style="green"))

    scripted = []
    if args.script:
        scripted = [ln.strip() for ln in open(args.script, encoding="utf-8") if ln.strip() and not ln.startswith("#")]

    while not session.finished:
        if scripted:
            text = scripted.pop(0)
            console.print(f"[bold green]you>[/] {text}")
            time.sleep(args.delay)
        else:
            try:
                text = console.input("[bold green]you>[/] ").strip()
            except (EOFError, KeyboardInterrupt):
                break
        if not text:
            continue
        st = session.state if session.started else {}
        before = (len(st.get("reasoning", [])), len(st.get("tool_trace", [])))
        with console.status("thinking..."):
            replies = session.send(text)
        show_turn(session, replies, args.trace, before)
    console.print("[bold]Session ended.[/] Reports are in output/reports/.")


if __name__ == "__main__":
    main()
