"""Streamlit chat UI:  streamlit run app_streamlit.py"""
from __future__ import annotations

import uuid
from pathlib import Path

import pandas as pd
import streamlit as st

from agent import config
from matching_agent import HELP, MatchingSession

st.set_page_config(page_title="Resume Matching Agent", page_icon="🧭", layout="wide")

if "session" not in st.session_state:
    st.session_state.session = MatchingSession(thread_id=str(uuid.uuid4()))
    st.session_state.chat = [("assistant", "Hi! I screen 100 resumes with your Milestone 1 file tools and "
                                           "Milestone 2 RAG engine. Paste a JD, pick one from the sidebar, or ask e.g. "
                                           "*\"Find me candidates with React and 3+ years experience\"*.")]
session: MatchingSession = st.session_state.session


def send(text: str) -> None:
    st.session_state.chat.append(("user", text))
    with st.spinner("Agent is screening..."):
        replies = session.send(text)
    for r in replies:
        st.session_state.chat.append(("assistant", r))
    if session.finished:
        st.session_state.chat.append(("assistant", "Session ended - click **New session** to start again."))


# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.header("🧭 Resume Matching Agent")
    if st.button("New session", width="stretch"):
        for k in ("session", "chat"):
            st.session_state.pop(k, None)
        st.rerun()
    st.subheader("Sample JDs")
    for jd in sorted(Path(config.JD_DIR).glob("*.txt")):
        if st.button(f"Use {jd.stem}", key=jd.stem, width="stretch", disabled=session.started and session.finished):
            send(f"use {jd.name}")
            st.rerun()
    st.subheader("Quick actions")
    for q in ["Compare the top 3 matches side by side", "Why did John rank higher than Jane?",
              "Make Next.js a must-have", "Require 5+ years", "Only Master's or higher", "Interview questions for #1",
              "Show the report", "What changed?"]:
        if st.button(q, key="q_" + q, width="stretch", disabled=not session.started or session.finished):
            send(q)
            st.rerun()
    with st.expander("Help"):
        st.markdown(HELP)

# ------------------------------------------------------------------ main
tab_chat, tab_state, tab_trace = st.tabs(["💬 Chat", "📊 Agent state", "🔧 Reasoning & tools"])

with tab_chat:
    for role, text in st.session_state.chat:
        with st.chat_message(role):
            st.markdown(text)

with tab_state:
    if session.started:
        s = session.state
        st.markdown("**Requirements**")
        st.json(s.get("requirements", {}), expanded=False)
        st.markdown(f"**Weights:** {s.get('weights')} · **Filters:** {s.get('filters')}")
        if s.get("shortlist"):
            df = pd.DataFrame([{"candidate": d["name"], "id": d["candidate_id"], "years": d["years"],
                                "degree": d["degree"], "M2 score": d.get("m2_score"), "round1": d["score"],
                                "deep": d["deep_score"], "decision": d["decision"],
                                "missing_must": ", ".join(d["missing_must"]), "resume": d["resume_path"]}
                               for d in s["shortlist"]])
            st.dataframe(df, width="stretch", hide_index=True)
            st.bar_chart(df.set_index("candidate")[["M2 score", "round1", "deep"]])
        if s.get("report_path"):
            p = config.ROOT / s["report_path"]
            if p.exists():
                st.download_button("Download match report (.md)", p.read_text(encoding="utf-8"), file_name=p.name)

with tab_trace:
    if session.started:
        s = session.state
        st.markdown("**Reasoning log**")
        for r in s.get("reasoning", []):
            st.markdown(f"- {r}")
        st.markdown("**Tool calls**")
        st.dataframe(pd.DataFrame(s.get("tool_trace", [])), width="stretch", hide_index=True)
    img = config.ROOT / "docs" / "m3" / "state_machine.png"
    if img.exists():
        st.image(str(img), caption="LangGraph state machine")

prompt = st.chat_input("Ask the agent...", disabled=session.started and session.finished)
if prompt:
    send(prompt)
    st.rerun()
