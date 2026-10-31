"""Milestone 1 file-system tools exposed to the agent.

The functions are the ones from Milestone 1 (milestone1/fs_tools.py, copied unchanged): read_file
handles PDF / DOCX / TXT, and errors come back as data ({"success": False, "error": ...}) so the
agent, or an LLM driving it, can recover. This module only adds the LangChain tool wrappers and
a sandbox so the agent can't touch anything outside data/ and outputs/.
"""
from __future__ import annotations

from pathlib import Path

from langchain_core.tools import tool

from agent import config
from milestone1 import fs_tools


def _safe(path: str) -> str | None:
    p = Path(path)
    p = (config.ROOT / p).resolve() if not p.is_absolute() else p.resolve()
    for root in config.FS_ALLOWED_ROOTS:
        root = Path(root).resolve()
        if p == root or root in p.parents:
            return str(p)
    return None


def _rel(path: str) -> str:
    try:
        return Path(path).resolve().relative_to(config.ROOT).as_posix()
    except ValueError:
        return path


@tool
def list_files(directory: str = "data/resumes_m3", extension: str = "") -> list[dict]:
    """List files in a directory with name, path, size and modified date. Optionally filter by extension ('.pdf')."""
    p = _safe(directory)
    if not p:
        return [{"error": f"Path outside sandbox: {directory}"}]
    out = fs_tools.list_files(p, extension or None)
    for f in out:
        if "path" in f:
            f["path"] = _rel(f["path"])
    return out


@tool
def read_file(filepath: str) -> dict:
    """Read a resume / JD / report (PDF, DOCX or TXT) and return its text content and metadata."""
    p = _safe(filepath)
    return fs_tools.read_file(p) if p else {"success": False, "error": f"Path outside sandbox: {filepath}"}


@tool
def search_in_file(filepath: str, keyword: str) -> dict:
    """Case-insensitive keyword search inside one file. Returns matches with surrounding text."""
    p = _safe(filepath)
    return fs_tools.search_in_file(p, keyword) if p else {"success": False, "error": f"Path outside sandbox: {filepath}"}


@tool
def write_file(filepath: str, content: str) -> dict:
    """Write text content to a file (used for match reports). Creates folders if needed."""
    p = _safe(filepath)
    if not p:
        return {"success": False, "error": f"Path outside sandbox: {filepath}"}
    out = fs_tools.write_file(p, content)
    if out.get("success"):
        out["filepath"] = _rel(out["filepath"])
    return out


FS_TOOLS = [list_files, read_file, search_in_file, write_file]
