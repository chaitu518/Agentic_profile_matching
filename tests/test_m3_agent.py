"""Milestone 3 tests: 8 conversation flows + unit tests for the M1/M2 integration.

    pytest -q tests/test_m3_agent.py
Runs offline and deterministically (local TF-IDF/LSA embedder, no LLM).
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from langchain_core.messages import AIMessage  # noqa: E402

from agent import config, llm  # noqa: E402
from agent.nlu import parse_refinement  # noqa: E402
from agent.requirements import extract_requirements_rules  # noqa: E402
from agent.tools.filesystem_tools import read_file, write_file  # noqa: E402
from agent.tools.rag_search import rag_search  # noqa: E402
from matching_agent import MatchingSession  # noqa: E402

HIRE_TIERS = {"STRONG HIRE", "HIRE"}
DECISIONS = {"STRONG HIRE", "HIRE", "BORDERLINE", "NO HIRE"}
GT = json.loads((ROOT / "data" / "ground_truth_m3.json").read_text())


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "")


def new_session() -> MatchingSession:
    return MatchingSession(thread_id=str(uuid.uuid4()))


def musts(st):
    return [r["skill"] for r in st["requirements"]["must_have"]]


def nices(st):
    return [r["skill"] for r in st["requirements"]["nice_to_have"]]


# ----------------------------------------------------------------------------- flow 1
def test_flow1_natural_language_search():
    s = new_session()
    out = s.send("Find me candidates with React and 3+ years experience")
    st = s.state
    assert musts(st) == ["React"] and st["requirements"]["min_years"] == 3
    assert len(st["all_scores"]) == 100 and len(st["shortlist"]) == config.SHORTLIST_SIZE
    top = st["shortlist"][0]
    assert top["decision"] in HIRE_TIERS and top["years"] >= 3 and not top["missing_must"]
    assert any("Shortlist for" in m for m in out)


# ----------------------------------------------------------------------------- flow 2
def test_flow2_compare_and_explain_pair():
    s = new_session()
    s.send("use jd05")
    assert s.state["jd_source"].endswith("jd05_frontend_react.txt")
    cmp = "\n".join(s.send("Compare the top 3 matches side by side"))
    top3 = [d["name"] for d in s.state["shortlist"][:3]]
    assert "Head-to-head" in cmp and all(n in cmp for n in top3) and "**React** (must)" in cmp

    why = "\n".join(s.send("Why did John rank higher than Jane?"))
    assert "John Mathew" in why and "Jane Cooper" in why
    assert "TypeScript" in why and "biggest round-1 driver" in why
    assert s.state["intent"]["type"] == "explain"


# ----------------------------------------------------------------------------- flow 3
def test_flow3_iterative_refinement_reranks_and_explains():
    s = new_session()
    s.send("use frontend_react")
    before = [d["candidate_id"] for d in s.state["shortlist"]]
    out = "\n".join(s.send("Make Next.js a must-have and require 5+ years"))
    st = s.state
    assert "Next.js" in musts(st) and "Next.js" not in nices(st)
    assert st["requirements"]["min_years"] == 5
    assert [d["candidate_id"] for d in st["shortlist"]] != before
    assert st["ranking_changes"] and "What changed" in out and "Ranking movement" in out
    for d in st["shortlist"]:                     # under the new bar -> never hire-ready
        if d["years"] < 5:
            assert d["decision"] not in HIRE_TIERS
    assert "Ranking movement" in "\n".join(s.send("what changed?"))


# ----------------------------------------------------------------------------- flow 4
def test_flow4_multi_round_screening_report_and_tools():
    s = new_session()
    s.send("use data/job_descriptions/jd02_java_backend.txt")
    st = s.state
    assert len(st["all_scores"]) == 100 and len(st["shortlist"]) == 10
    rel = GT["job_descriptions"]["jd02_java_backend"]["relevance"]
    for d in st["shortlist"]:
        assert {"deep_score", "strengths", "gaps", "signals", "decision", "rationale", "m2_score"} <= d.keys()
        assert d["decision"] in DECISIONS
        if d["decision"] == "BORDERLINE":
            assert d["suggestions"]
        if d["decision"] in HIRE_TIERS:           # every hire-ready pick is a right-family, senior-enough resume
            assert rel.get(d["resume_path"]) == 2
    report = (config.ROOT / st["report_path"]).read_text(encoding="utf-8")
    assert "Round 1 - initial screen" in report and "Rounds 2 & 3" in report and "M2 score" in report
    tools_used = {t["tool"] for t in st["tool_trace"]}
    assert {"list_files", "read_file", "extract_requirements", "rag_search", "write_file"} <= tools_used


# ----------------------------------------------------------------------------- flow 5
def test_flow5_questions_deep_dive_and_degree_filter():
    s = new_session()
    s.send("use jd01")
    q = "\n".join(s.send("interview questions for #1"))
    assert "Screening questions" in q and "technical depth" in q
    s.send("only Master's or higher")
    st = s.state
    assert st["filters"]["min_degree"] == "Master's"
    assert all(d["degree"] in ("Master's", "PhD") for d in st["shortlist"])
    out = "\n".join(s.send("why is Ravi Mensah ranked so low?"))
    assert "excluded by the current filter" in out or "Ravi Mensah" in out
    s.send("any degree")
    assert not s.state["filters"].get("min_degree") and len(s.state["all_scores"]) == 100


# ----------------------------------------------------------------------------- flow 6
def test_flow6_switch_job_mid_conversation():
    s = new_session()
    s.send("use jd01_senior_ml_engineer")
    assert s.state["shortlist"][0]["decision"] in HIRE_TIERS
    s.send("make RAG a must-have")
    assert "RAG" in musts(s.state) and s.state["previous_shortlist"]
    s.send("Now find Java developers with Kafka and Spring Boot, 4+ years, nice to have Kubernetes")
    st = s.state
    assert {"Java", "Kafka", "Spring Boot"} <= set(musts(st)) and nices(st) == ["Kubernetes"]
    assert st["previous_shortlist"] == []
    assert "Java" in st["shortlist"][0]["matched_must"]


# ----------------------------------------------------------------------------- flow 7
def test_flow7_clarify_then_search_then_end():
    s = new_session()
    assert "couldn't find any skills" in s.send("hi there")[-1]
    assert not s.state.get("shortlist")
    s.send("Find me data engineers with Spark and Airflow")
    assert s.state["shortlist"]
    assert "Refine" in "\n".join(s.send("help"))
    s.send("done")
    assert s.finished


# ----------------------------------------------------------------------------- flow 8
def test_flow8_demote_remove_and_reweight():
    s = new_session()
    s.send("use jd05")
    s.send("TypeScript is only a nice to have, remove HTML/CSS")
    assert "TypeScript" in nices(s.state)
    assert "HTML/CSS" not in musts(s.state) + nices(s.state)
    w = s.state["weights"]["experience"]
    s.send("prioritize experience")
    assert s.state["weights"]["experience"] > w and abs(sum(s.state["weights"].values()) - 1) < 0.01


# ----------------------------------------------------------------------------- integration units
def test_requirements_build_on_m2_parser():
    jd02 = extract_requirements_rules((config.JD_DIR / "jd02_java_backend.txt").read_text())
    java = next(r for r in jd02.must_have if r.skill == "Java")
    assert java.min_years == 4 and java.weight == 1.5          # M2's "4+ years Java" hard must-have
    assert {"Microservices", "Kafka", "REST APIs"} <= {r.skill for r in jd02.must_have}   # "Also expected"
    assert {"Kubernetes", "AWS"} <= {r.skill for r in jd02.nice_to_have}
    jd01 = extract_requirements_rules((config.JD_DIR / "jd01_senior_ml_engineer.txt").read_text())
    dl = next(r for r in jd01.must_have if r.skill == "Deep Learning")
    assert {"PyTorch", "TensorFlow"} <= set(dl.alternatives)   # "Deep Learning (PyTorch or TensorFlow)"
    assert "RAG" in {r.skill for r in jd01.nice_to_have}       # "(RAG is a plus)"
    assert "MLOps" in {r.skill for r in jd01.nice_to_have}     # "Familiarity with ..."
    jd05 = extract_requirements_rules((config.JD_DIR / "jd05_frontend_react.txt").read_text())
    redux = next(r for r in jd05.must_have if r.skill == "Redux")
    assert len(redux.alternatives) > 1                         # "Redux or similar"
    assert "Cypress" in {r.skill for r in jd05.nice_to_have}   # "testing with Cypress a plus"


def test_milestone1_tools_sandbox_and_errors_as_data():
    ok = read_file.invoke({"filepath": "data/resumes_m3/john_mathew.txt"})
    assert ok["success"] and "John Mathew" in ok["content"]
    pdf = read_file.invoke({"filepath": "data/resumes_m3/priya_tanaka.pdf"})
    assert pdf["success"] and pdf["metadata"]["extension"] == ".pdf"
    assert read_file.invoke({"filepath": "/etc/passwd"})["success"] is False
    assert read_file.invoke({"filepath": "data/resumes_m3/nobody.txt"})["success"] is False
    assert write_file.invoke({"filepath": "../escape.txt", "content": "x"})["success"] is False


def test_milestone2_rag_search_tool():
    hits = rag_search.invoke({"query": (config.JD_DIR / "jd04_devops_sre.txt").read_text(), "k": 10})
    assert len(hits) == 10 and {"semantic", "keyword", "m2_score", "excerpts"} <= hits[0].keys()
    rel = GT["job_descriptions"]["jd04_devops_sre"]["relevance"]
    assert sum(rel.get(h["resume_path"], 0) > 0 for h in hits[:5]) >= 4


def test_refinement_parser():
    assert parse_refinement("add Docker and Kubernetes as nice to have") == [
        {"op": "add_nice", "skill": "Docker"}, {"op": "add_nice", "skill": "Kubernetes"}]
    assert parse_refinement("add Docker and remove HTML/CSS") == [
        {"op": "add_must", "skill": "Docker"}, {"op": "remove", "skill": "HTML/CSS"}]
    assert {"op": "min_degree", "value": "Master's"} in parse_refinement("only candidates with a Master's")


def test_llm_tool_loop_runs_agent_tools():
    """The LLM path (Milestone 1 style function calling) with a scripted fake model."""

    class FakeLLM:
        def __init__(self):
            self.step = 0

        def bind_tools(self, tools):
            return self

        def invoke(self, msgs):
            self.step += 1
            if self.step == 1:
                return AIMessage(content="", tool_calls=[{"name": "list_files", "id": "1",
                                                          "args": {"directory": "data/job_descriptions"}}])
            return AIMessage(content=f"There are {msgs[-1].content.count('jd0')} JD files.")

    from agent.tools.filesystem_tools import FS_TOOLS
    ans, trace = llm.tool_loop("how many JDs?", FS_TOOLS, "system", llm=FakeLLM())
    assert trace[0]["tool"] == "list_files" and "JD files" in ans
