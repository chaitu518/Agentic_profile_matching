"""LangGraph resume-matching agent (Milestone 3), built on Milestone 1 (milestone1/fs_tools.py)
and Milestone 2 (api/: ChromaDB RAG + hybrid job matcher).

Graph (see docs/state_machine.png):

    START → parse_jd → extract_requirements → search_resumes → rank_candidates (round 1)
          → deep_analysis (round 2) → final_recommendation (round 3) → generate_report
          → human_feedback ⟲ (interrupt) → {refine | compare | explain | questions | report | ... | END}

The human_feedback node pauses the graph with `interrupt()`; the chat UI resumes it
with `Command(resume=user_text)`. A MemorySaver checkpointer keeps the full state per
thread, so the conversation, requirements, shortlist and reasoning persist across turns.
"""
from __future__ import annotations

import operator
import re
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, TypedDict

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.types import Command, interrupt

from agent import config
from agent import llm, pipeline
from agent.explain import explain_changes, explain_pair, explain_single
from agent.nlu import apply_refinement, classify
from agent.report import chat_summary, candidate_section, full_report, shortlist_table
from agent.requirements import JobRequirements
from agent.tools.agent_tools import compare_candidates, extract_requirements, generate_interview_questions
from agent.tools.filesystem_tools import list_files, read_file, write_file
from agent.tools.rag_search import rag_search

# =============================================================================== state


class AgentState(TypedDict, total=False):
    # conversation history (human + agent turns)
    messages: Annotated[list[AnyMessage], add_messages]
    # job understanding
    jd_text: str
    jd_source: str
    requirements: dict            # JobRequirements.model_dump()
    extraction_method: str        # "llm" | "rules"
    weights: dict                 # round-1 scoring weights (user can shift them)
    filters: dict                 # e.g. {"min_degree": "Master's"}
    change_log: list[str]         # what the last refinement changed
    # retrieval + screening
    retrieved: list[dict]         # RAG hits (candidate_id, score, snippet)
    all_scores: dict[str, dict]   # round-1 breakdown for EVERY candidate (so anyone can be explained)
    ranked_ids: list[str]         # round-1 ordering
    shortlist: list[dict]         # rounds 2+3: deep analysis + decision + reasoning, ordered by deep score
    previous_shortlist: list[dict]
    previous_scores: dict[str, dict]
    ranking_changes: list[dict]
    report_path: str
    # control
    intent: dict
    turn: int
    # audit trail shown in the demo
    tool_trace: Annotated[list[dict], operator.add]
    reasoning: Annotated[list[str], operator.add]


def _req(state: AgentState) -> JobRequirements:
    return JobRequirements.model_validate(state.get("requirements") or {})


def _trace(tool, args: dict, summary: str) -> dict:
    return {"tool": tool.name, "args": {k: (v if len(str(v)) < 80 else str(v)[:77] + "...") for k, v in args.items()},
            "result": summary, "at": datetime.now().strftime("%H:%M:%S")}


def _call(tool, args: dict, summarise) -> tuple[Any, dict]:
    out = tool.invoke(args)
    return out, _trace(tool, args, summarise(out))


def _last_human(state: AgentState) -> str:
    for m in reversed(state.get("messages", [])):
        if isinstance(m, HumanMessage):
            return str(m.content)
    return ""


def _order(state: AgentState) -> list[str]:
    """Displayed order: final shortlist (round 3) first, then everyone else by round-1 score."""
    short = [d["candidate_id"] for d in state.get("shortlist", [])]
    return short + [c for c in state.get("ranked_ids", []) if c not in set(short)]


def _ranks(state: AgentState) -> dict[str, int]:
    return {cid: i + 1 for i, cid in enumerate(_order(state))}


def _r1_ranks(state: AgentState) -> dict[str, int]:
    return {cid: i + 1 for i, cid in enumerate(state.get("ranked_ids", []))}


def _shortlist_ids(state: AgentState) -> list[str]:
    return [d["candidate_id"] for d in state.get("shortlist", [])]


# =============================================================================== pipeline nodes


def _jd_aliases(path: str) -> set[str]:
    stem = Path(path).stem.lower()                    # jd05_frontend_react
    short = re.sub(r"^jd\d+_", "", stem)              # frontend_react
    num = re.match(r"^(jd\d+)", stem)
    return {stem, short, short.replace("_", " "), stem.replace("_", " ")} | ({num.group(1)} if num else set())


def parse_jd(state: AgentState) -> dict:
    """Load the JD with the Milestone 1 file tools (a path, or a JD name such as 'jd05' / 'frontend_react'),
    otherwise treat the user's message itself as the job description / search."""
    text = (state.get("intent") or {}).get("text") or _last_human(state)
    trace, source = [], "chat message"
    jd_dir = config.JD_DIR.relative_to(config.ROOT).as_posix()
    files, t = _call(list_files, {"directory": jd_dir, "extension": ".txt"}, lambda r: f"{len(r)} JD files")
    trace.append(t)
    jd_files = [f["path"] for f in files if "path" in f]
    low = text.lower()
    path_m = re.search(r"[\w./-]+\.(?:txt|pdf|docx|md)\b", text)
    target = None
    if path_m:
        cand = path_m.group(0)
        target = next((f for f in jd_files if f.endswith(Path(cand).name)), cand)
    else:
        target = next((f for f in jd_files if any(re.search(r"\b" + re.escape(a) + r"\b", low)
                                                   for a in _jd_aliases(f))), None)
    if target:
        res, t = _call(read_file, {"filepath": target},
                       lambda r: f"{r['metadata']['word_count']} words" if r.get("success") else r.get("error"))
        trace.append(t)
        if res.get("success"):
            text, source = res["content"], target
        else:  # error comes back as data (Milestone 1 contract) -> fall back to the message itself
            source = f"chat message (could not read {target}: {res.get('error')})"
    return {
        "jd_text": text, "jd_source": source, "tool_trace": trace,
        # a brand-new search starts a fresh ranking history
        "previous_shortlist": [], "previous_scores": {}, "change_log": [], "ranking_changes": [],
        "filters": {}, "weights": dict(config.DEFAULT_WEIGHTS),
        "reasoning": [f"Parsed JD from {source} ({len(text)} chars)."],
    }


def extract_requirements_node(state: AgentState) -> dict:
    out, t = _call(extract_requirements, {"jd": state["jd_text"]},
                   lambda r: f"{len(r['requirements']['must_have'])} must, {len(r['requirements']['nice_to_have'])} nice ({r['method']})")
    req = JobRequirements.model_validate(out["requirements"])
    filters = {"min_degree": req.min_degree} if req.min_degree else {}
    if not req.must_have and not req.nice_to_have:
        msg = ("I couldn't find any skills in that. Paste a job description, name one of the JDs in "
               "`data/job_descriptions/` (e.g. *jd02* or *frontend_react*), or ask something like "
               "\"Find me candidates with React and 3+ years experience\".")
        return {"requirements": out["requirements"], "extraction_method": out["method"], "tool_trace": [t],
                "messages": [AIMessage(content=msg)], "reasoning": ["No requirements found; asking the user."]}
    return {
        "requirements": out["requirements"], "extraction_method": out["method"], "filters": filters,
        "tool_trace": [t],
        "messages": [AIMessage(content=f"**Understood the role** ({out['method']} extraction):\n\n{req.summary()}")],
        "reasoning": [f"Extracted {len(req.must_have)} must-haves and {len(req.nice_to_have)} nice-to-haves; "
                      f"min years = {req.min_years}."],
    }


def search_resumes(state: AgentState) -> dict:
    """Milestone 2 RAG: the requirements are rendered as a JD and sent through M2's hybrid matcher."""
    req = _req(state)
    args = {"query": req.to_jd_text(), "k": len(pipeline.corpus())}
    hits, t = _call(rag_search, args, lambda r: f"{len(r)} candidates; best={r[0]['name'] if r else '-'}")
    return {"retrieved": hits, "tool_trace": [t],
            "reasoning": [f"Milestone 2 hybrid search (ChromaDB semantic + BM25) scored {len(hits)} resumes; "
                          f"top RAG hits: {', '.join(h['name'] for h in hits[:3])}."]}


def rank_candidates(state: AgentState) -> dict:
    """Round 1: score every resume, keep the top N."""
    req = _req(state)
    scores = pipeline.round1(req, state["weights"], state.get("filters", {}), state["retrieved"])
    ranked = sorted(scores, key=lambda cid: (-scores[cid]["score"], cid))
    top = ranked[:config.SHORTLIST_SIZE]
    return {"all_scores": scores, "ranked_ids": ranked,
            "reasoning": [f"Round 1: screened {len(scores)} resumes; top {len(top)} = "
                          + ", ".join(scores[c]["name"] for c in top)]}


def deep_analysis(state: AgentState) -> dict:
    """Round 2: evidence depth, recency, seniority, strengths & gaps for the top N."""
    req = _req(state)
    top = state["ranked_ids"][:config.SHORTLIST_SIZE]
    deep = pipeline.round2(req, state["all_scores"], top)
    moved = [d["name"] for i, d in enumerate(deep) if top.index(d["candidate_id"]) != i]
    return {"shortlist": deep,
            "reasoning": [f"Round 2: deep analysis re-ordered {len(moved)} of {len(deep)} candidates."]}


def final_recommendation(state: AgentState) -> dict:
    """Round 3: hire / no-hire with rationale and improvement suggestions for borderline candidates."""
    req = _req(state)
    final = pipeline.round3(req, state["shortlist"])
    tally: dict[str, int] = {}
    for d in final:
        tally[d["decision"]] = tally.get(d["decision"], 0) + 1
    return {"shortlist": final, "reasoning": [f"Round 3 decisions: {tally}"]}


def generate_report(state: AgentState) -> dict:
    req = _req(state)
    shortlist = state["shortlist"]
    change_md, changes = None, []
    if state.get("previous_shortlist"):
        change_md, changes = explain_changes(state["previous_shortlist"], shortlist, state.get("change_log", []),
                                             state["all_scores"], state.get("previous_scores", {}))
    llm_summary = llm.narrate(
        "Write a 4-sentence hiring summary for a recruiter from this JSON. Do not invent facts.\n"
        + str([{k: d[k] for k in ("name", "deep_score", "decision", "strengths", "gaps")} for d in shortlist[:5]])
    )
    md = full_report(state, req, shortlist, state["ranked_ids"], change_md, llm_summary)
    turn = state.get("turn", 0) + 1
    out_dir = config.OUTPUT_DIR.relative_to(config.ROOT).as_posix()
    res, t = _call(write_file, {"filepath": f"{out_dir}/match_report_{datetime.now():%Y%m%d_%H%M%S}_t{turn}.md",
                                "content": md}, lambda r: r.get("filepath") or r.get("error"))
    path = res.get("filepath", "(report not written: " + str(res.get("error")) + ")")
    summary = chat_summary(req, shortlist, _r1_ranks(state), len(state["all_scores"]), len(state["retrieved"]), path)
    msgs = []
    if change_md:
        msgs.append(AIMessage(content=change_md))
    msgs.append(AIMessage(content=summary))
    return {"report_path": path, "ranking_changes": changes, "turn": turn, "tool_trace": [t], "messages": msgs,
            "reasoning": [f"Report written to {path}."]}


# =============================================================================== human-in-the-loop


def human_feedback(state: AgentState) -> dict:
    """Pause for the user. Everything before `interrupt` must be side-effect free (the node re-runs on resume)."""
    user_text = interrupt({"prompt": "Your feedback / next question", "has_shortlist": bool(state.get("shortlist"))})
    user_text = str(user_text).strip()
    corpus = pipeline.corpus()
    intent = classify(user_text, _order(state), corpus, state.get("all_scores", {}),
                      has_search=bool(state.get("shortlist")))
    return {"messages": [HumanMessage(content=user_text)], "intent": intent.model_dump(),
            "reasoning": [f"User intent → {intent.type} {intent.candidate_ids or ''} {intent.ops or ''}".strip()]}


def route_feedback(state: AgentState) -> str:
    return {
        "new_search": "parse_jd", "refine": "refine_requirements", "compare": "compare",
        "explain": "explain", "explain_changes": "explain_changes", "questions": "interview_questions",
        "report": "candidate_report", "show_ranking": "show_ranking", "help": "help", "general": "general",
        "end": END,
    }[state["intent"]["type"]]


def route_after_extract(state: AgentState) -> str:
    r = state.get("requirements") or {}
    return "search_resumes" if (r.get("must_have") or r.get("nice_to_have")) else "human_feedback"


# =============================================================================== conversational nodes


def refine_requirements(state: AgentState) -> dict:
    req, weights, filters, log = apply_refinement(_req(state), state["weights"], state.get("filters", {}),
                                                  state["intent"]["ops"])
    return {"requirements": req.model_dump(), "weights": weights, "filters": filters, "change_log": log,
            "previous_shortlist": state.get("shortlist", []), "previous_scores": state.get("all_scores", {}),
            "messages": [AIMessage(content="**Updating criteria and re-ranking:**\n" + "\n".join(f"- {l}" for l in log)
                                   + f"\n\n{req.summary()}")],
            "reasoning": [f"Refinement applied: {log}"]}


def compare(state: AgentState) -> dict:
    ids = state["intent"]["candidate_ids"][:5]
    if len(ids) < 2:
        ids = (ids + [c for c in _shortlist_ids(state) if c not in ids])[:2]
    out, t = _call(compare_candidates, {"candidate_ids": ids, "requirements": state["requirements"],
                                        "weights": state["weights"]},
                   lambda r: f"compared {len(r['profiles'])}")
    title = " vs ".join(p["name"] for p in out["profiles"])
    return {"messages": [AIMessage(content=f"## Head-to-head: {title}\n\n{out['table_markdown']}")], "tool_trace": [t],
            "reasoning": [f"Compared {ids}."]}


def explain(state: AgentState) -> dict:
    ids = state["intent"]["candidate_ids"]
    scores, ranks = state["all_scores"], _ranks(state)
    deep = {d["candidate_id"]: d for d in state.get("shortlist", [])}
    missing = [cid for cid in ids if cid not in scores]
    if missing:
        corpus = pipeline.corpus()
        who = ", ".join(f"{corpus[c].name} ({corpus[c].highest_degree})" for c in missing)
        return {"messages": [AIMessage(content=f"{who} {'is' if len(missing) == 1 else 'are'} excluded by the current "
                                               f"filter {state.get('filters')}, so not scored this round. "
                                               "Say \"any degree\" to bring them back.")]}
    if len(ids) >= 2:
        a, b = scores[ids[0]], scores[ids[1]]
        text = explain_pair(a | deep.get(ids[0], {}), b | deep.get(ids[1], {}), ranks)
        for cid in ids[:2]:
            if cid in deep:
                d = deep[cid]
                text += f"\n- After deep analysis {d['name']} is **{d['decision']}** (deep score {d['deep_score']})."
            else:
                text += f"\n- {scores[cid]['name']} didn't make the top {config.SHORTLIST_SIZE}, so no deep analysis was run."
    else:
        cid = ids[0]
        s = scores[cid] | ({k: deep[cid][k] for k in ("decision", "confidence")} if cid in deep else {})
        text = explain_single(s, ranks[cid], len(scores), config.SHORTLIST_SIZE)
        if ranks[cid] > config.SHORTLIST_SIZE:
            cutoff = scores[state["ranked_ids"][config.SHORTLIST_SIZE - 1]]
            text += f"\n\nThe #{config.SHORTLIST_SIZE} cut-off is **{cutoff['name']}** at {cutoff['score']} - " \
                    f"{cutoff['score'] - s['score']:.1f} points above."
    return {"messages": [AIMessage(content=text)], "reasoning": [f"Explained ranking for {ids}."]}


def explain_changes_node(state: AgentState) -> dict:
    if not state.get("previous_shortlist"):
        return {"messages": [AIMessage(content="Nothing has changed yet - the ranking is still the first pass. "
                                               "Try a refinement like \"make Next.js a must-have\".")]}
    md, _ = explain_changes(state["previous_shortlist"], state["shortlist"], state.get("change_log", []),
                            state["all_scores"], state.get("previous_scores", {}))
    return {"messages": [AIMessage(content=md)]}


def interview_questions(state: AgentState) -> dict:
    ids = state["intent"]["candidate_ids"][:3] or _shortlist_ids(state)[:1]
    blocks, trace = [], []
    for cid in ids:
        out, t = _call(generate_interview_questions,
                       {"candidate_id": cid, "requirements": state["requirements"], "weights": state["weights"]},
                       lambda r: f"{len(r['questions'])} questions")
        trace.append(t)
        qs = "\n".join(f"{i}. **[{q['category']}{' · ' + q['skill'] if q['skill'] != '-' else ''}]** {q['question']}  \n"
                       f"   _why: {q['why']}_" for i, q in enumerate(out["questions"], 1))
        blocks.append(f"## Screening questions - {out['name']} ({cid})\n{qs}")
    return {"messages": [AIMessage(content="\n\n".join(blocks))], "tool_trace": trace,
            "reasoning": [f"Generated interview questions for {ids}."]}


def candidate_report(state: AgentState) -> dict:
    ids = state["intent"]["candidate_ids"]
    deep = {d["candidate_id"]: d for d in state["shortlist"]}
    if not ids:
        borderline = [d for d in state["shortlist"] if d["decision"] == "BORDERLINE"]
        text = (f"Full report: `{state.get('report_path')}`\n\n" + shortlist_table(state["shortlist"], _r1_ranks(state)))
        if borderline:
            text += "\n\n### Borderline candidates - what would move them up\n" + "\n".join(
                f"- **{d['name']}**: " + " ".join(d["suggestions"]) for d in borderline)
        return {"messages": [AIMessage(content=text)]}
    parts = []
    for cid in ids[:3]:
        if cid in deep:
            i = _shortlist_ids(state).index(cid) + 1
            parts.append(candidate_section(i, deep[cid]))
        else:
            hit = next((h for h in state.get("retrieved", []) if h["candidate_id"] == cid), None)
            prof = pipeline.full_profile(_req(state), state["weights"], cid, hit)
            parts.append(f"_{prof['name']} is outside the current top {config.SHORTLIST_SIZE} (round-1 rank "
                         f"#{_ranks(state).get(cid, '?')}); running an on-demand deep analysis:_\n\n"
                         + candidate_section(_ranks(state).get(cid, 0), prof))
    return {"messages": [AIMessage(content="\n\n---\n\n".join(parts))]}


def show_ranking(state: AgentState) -> dict:
    return {"messages": [AIMessage(content=f"{_req(state).summary()}\n\n" + shortlist_table(state["shortlist"], _r1_ranks(state)))]}


HELP = """I'm a resume-matching agent over 100 resumes (Milestone 1 file tools + Milestone 2 RAG). Things you can say:
- **Search:** "Find me candidates with React and 3+ years experience", "use jd05" / "use frontend_react", or paste a JD
- **Refine:** "make Next.js a must-have", "TypeScript is only nice to have", "require 5+ years", "only Master's or higher", "prioritize experience", "remove HTML/CSS"
- **Compare:** "compare the top 3 side by side", "compare John and Zara"
- **Explain:** "why did John rank higher than Jane?", "why is Noah ranked #4?", "what changed?"
- **Deep dive:** "tell me about #2", "show the report", "interview questions for #1"
- **Finish:** "done"
"""


def help_node(state: AgentState) -> dict:
    return {"messages": [AIMessage(content=HELP)]}


def _llm_tools(state: AgentState) -> list:
    """Tools an LLM may call for open questions: Milestone 1 file tools, the Milestone 2 RAG search, and the
    Milestone 3 tools with the current requirements bound in (so the model only passes candidate ids)."""
    from langchain_core.tools import StructuredTool

    from agent.tools.filesystem_tools import FS_TOOLS

    reqs, weights = state["requirements"], state["weights"]

    def compare_ids(candidate_ids: list[str]) -> dict:
        """Head-to-head comparison of candidates (ids = resume file stems, e.g. 'john_mathew')."""
        return {"table": compare_candidates.invoke({"candidate_ids": candidate_ids, "requirements": reqs,
                                                    "weights": weights})["table_markdown"]}

    def questions_for_id(candidate_id: str) -> dict:
        """Screening questions for one candidate id."""
        return generate_interview_questions.invoke({"candidate_id": candidate_id, "requirements": reqs,
                                                    "weights": weights})

    return [*FS_TOOLS, rag_search, extract_requirements,
            StructuredTool.from_function(compare_ids, name="compare_candidates"),
            StructuredTool.from_function(questions_for_id, name="generate_interview_questions")]


def general(state: AgentState) -> dict:
    """Open questions. With an LLM configured, the model answers by calling the agent's tools itself
    (Milestone 1's function-calling loop); without one, the agent shows what it can do."""
    q = state["intent"]["text"]
    context = (f"Current requirements: {_req(state).summary()}\nShortlist (id, name, decision): "
               + str([(d["candidate_id"], d["name"], d["decision"]) for d in state.get("shortlist", [])]))
    system = ("You are a recruiting assistant. Resumes are in data/resumes_m3, JDs in data/job_descriptions, "
              "reports in outputs/m3_reports. Use the tools; never invent candidate facts.\n" + context)
    ans, trace = llm.tool_loop(q, _llm_tools(state), system)
    trace = [{**t, "at": datetime.now().strftime("%H:%M:%S")} for t in trace]
    return {"messages": [AIMessage(content=ans or "I didn't catch that.\n\n" + HELP)], "tool_trace": trace,
            "reasoning": [f"Open question answered via LLM tool loop ({len(trace)} tool calls)." if ans
                          else "Open question without an LLM configured: showed help."]}


# =============================================================================== graph


def build_graph(checkpointer: Any = "memory"):
    """checkpointer="memory" -> in-process MemorySaver; None -> let the host (LangGraph Studio/Server) provide one."""
    g = StateGraph(AgentState)
    g.add_node("parse_jd", parse_jd)
    g.add_node("extract_requirements", extract_requirements_node)
    g.add_node("search_resumes", search_resumes)
    g.add_node("rank_candidates", rank_candidates)
    g.add_node("deep_analysis", deep_analysis)
    g.add_node("final_recommendation", final_recommendation)
    g.add_node("generate_report", generate_report)
    g.add_node("human_feedback", human_feedback)
    g.add_node("refine_requirements", refine_requirements)
    g.add_node("compare", compare)
    g.add_node("explain", explain)
    g.add_node("explain_changes", explain_changes_node)
    g.add_node("interview_questions", interview_questions)
    g.add_node("candidate_report", candidate_report)
    g.add_node("show_ranking", show_ranking)
    g.add_node("help", help_node)
    g.add_node("general", general)

    g.add_edge(START, "parse_jd")
    g.add_edge("parse_jd", "extract_requirements")
    g.add_conditional_edges("extract_requirements", route_after_extract, ["search_resumes", "human_feedback"])
    g.add_edge("search_resumes", "rank_candidates")
    g.add_edge("rank_candidates", "deep_analysis")
    g.add_edge("deep_analysis", "final_recommendation")
    g.add_edge("final_recommendation", "generate_report")
    g.add_edge("generate_report", "human_feedback")
    g.add_conditional_edges("human_feedback", route_feedback,
                            ["parse_jd", "refine_requirements", "compare", "explain", "explain_changes",
                             "interview_questions", "candidate_report", "show_ranking", "help", "general", END])
    g.add_edge("refine_requirements", "search_resumes")   # re-rank with new criteria
    for n in ("compare", "explain", "explain_changes", "interview_questions", "candidate_report",
              "show_ranking", "help", "general"):
        g.add_edge(n, "human_feedback")
    return g.compile(checkpointer=MemorySaver() if checkpointer == "memory" else checkpointer)


class MatchingSession:
    """Small convenience wrapper used by the CLI, Streamlit app and tests."""

    def __init__(self, thread_id: str = "default", graph=None):
        self.graph = graph or build_graph()
        self.config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 60}
        self.started = False
        self._seen = 0

    def send(self, text: str) -> list[str]:
        """Send a user message; returns the agent's new messages for this turn."""
        if not self.started:
            self.graph.invoke({"messages": [HumanMessage(content=text)], "turn": 0}, self.config)
            self.started = True
        else:
            self.graph.invoke(Command(resume=text), self.config)
        msgs = self.state.get("messages", [])
        new = [m.content for m in msgs[self._seen:] if isinstance(m, AIMessage)]
        self._seen = len(msgs)
        return new

    @property
    def state(self) -> dict:
        return self.graph.get_state(self.config).values

    @property
    def finished(self) -> bool:
        return self.started and not self.graph.get_state(self.config).next


graph = build_graph(checkpointer=None)  # exported for `langgraph dev` / LangGraph Studio (it injects persistence)
