"""Export the compiled LangGraph as Mermaid and render PNGs.

    python scripts/draw_graph.py

Writes docs/m3/state_machine_generated.mmd (straight from the compiled graph) and renders
it plus the annotated docs/m3/state_machine.mmd to PNG with mermaid-cli (`mmdc`) if available.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from matching_agent import build_graph  # noqa: E402

DOCS = ROOT / "docs" / "m3"


def main() -> None:
    DOCS.mkdir(exist_ok=True)
    mmd = build_graph().get_graph().draw_mermaid()
    gen = DOCS / "state_machine_generated.mmd"
    gen.write_text(mmd, encoding="utf-8")
    print(f"wrote {gen}")
    mmdc = shutil.which("mmdc")
    if not mmdc:
        print("mmdc not found - paste the .mmd files into https://mermaid.live to export PNGs")
        return
    for src, out in ((gen, DOCS / "state_machine_generated.png"), (DOCS / "state_machine.mmd", DOCS / "state_machine.png")):
        if src.exists():
            subprocess.run([mmdc, "-i", str(src), "-o", str(out), "-b", "white", "-s", "2"], check=True)
            print(f"rendered {out}")


if __name__ == "__main__":
    main()
