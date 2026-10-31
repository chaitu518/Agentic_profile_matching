# Milestone 3 demo video script (5-6 minutes)

**Before recording:** run `python scripts/build_m3_corpus.py` and do one warm-up run so `vector_db_m3/` is built. Use a large terminal font, and keep `docs/m3/state_machine.png` and VS Code open. Runs are deterministic, so your numbers will match the ones below.

- Live: `python chat_cli.py --trace`
- Hands-free: `python chat_cli.py --trace --script tests/scenarios/demo.txt --delay 3`
- UI: `streamlit run app_streamlit.py`. Use the sidebar buttons, then show the "Reasoning & tools" tab.

---

### 0:00 – 0:50 · How the three milestones fit
- Show `state_machine.png`. The green nodes reuse earlier work: `parse_jd` and `generate_report` use **Milestone 1's** `read_file` and `write_file`, and `search_resumes` is **Milestone 2's** `JobMatcher` over ChromaDB.
- *"After the report the graph pauses in `human_feedback` with `interrupt()`. Each message gets routed to refine, compare, explain or questions. Refinement loops back to search, so the agent re-ranks."*
- Scroll through `AgentState`: conversation, job understanding, and shortlist with reasoning.

### 0:50 – 1:50 · `use jd05_frontend_react.txt`
- Trace panel: `list_files` → `read_file` (M1) → `extract_requirements` → `rag_search` (M2) → `write_file` (M1).
- Requirements: "3+ years React" comes from M2's parser as a hard must-have (×1.5, 3+ yrs). "Redux or similar" accepts MobX or Zustand. "Cypress a plus" is a nice-to-have, and Next.js appears only in Responsibilities, so it's a nice-to-have too.
- Funnel: 100 resumes scored by M2 hybrid search → round 1 on all → top 10 deep-analysed → 1 STRONG HIRE, 9 HIRE.
- **Point out:** John Mathew is #3 after round 1 (93.7) but #1 after round 2 (88.8). That's because of his senior title, led/mentored bullets, and React used across 6.2 years of roles.

### 1:50 – 2:30 · `Compare the top 3 matches side by side`
- `compare_candidates` matrix. Zara's Redux shows "~ (experience only)": it's in her bullets but not her skills list. Seniority signal is 1.00 for John against 0.20 for the other two.

### 2:30 – 3:20 · `Why did John rank higher than Jane?`
- Jane is #16 and not in the shortlist. She can still be explained because round 1 scores all 100.
- Gap of 25.5 points. The biggest driver is must-have coverage (+14.1), because she's missing **TypeScript and Redux**. She also has 2.8 years against a 3+ bar, and M2 retrieval similarity is +4.4 in John's favour.

### 3:20 – 4:30 · `Make Next.js a must-have and require 5+ years`
- The change log and the loop back to `search_resumes` (it's the M2 query that changes).
- Read three lines of the **ranking movement**:
  - *Wei Patel #7 → #4 (up): has newly required Next.js*
  - *Ifeoma Iyer #4 → #9: experience fit −10.7 pts (3 yrs)*
  - *Arjun Joshi dropped out*
- 3 candidates are now BORDERLINE because they're under the new 5-year bar. Their improvement suggestions are in the report.

### 4:30 – 5:15 · `tell me about #2` and `interview questions for #1`
- Noah Aziz card. M3 deep score 85.1 sits next to the **M2 baseline of 98**. It shows "React: 5 yrs in roles (JD asks 3+)", which uses M2's per-skill years. The evidence table quotes resume lines, and the M2 RAG excerpts are listed below it.
- John's questions: depth checks on React, TypeScript and JavaScript. HTML/CSS is "listed but not shown in any role", so there's a verify question for it. There's also a check on the "45% faster time-to-interactive" claim and a leadership question.

### 5:15 – 6:00 · Wrap-up
- Type `done`. The graph reaches END. Open `outputs/m3_reports/…_t2.md`.
- `pytest -q tests/test_m3_agent.py`: 13 tests pass in about 10 s.
- `python scripts/evaluate_m3.py`: on the same 100 resumes, the agent's final ranking reaches **R-Prec 1.0 and nDCG@10 1.0**, against 0.835 and 0.970 for M2's hybrid search alone.
- Closing line: *"Milestone 1 reads and writes the files, Milestone 2 retrieves, and Milestone 3 adds the reasoning, the conversation and the explanations. Every score can be traced back to a line in a resume."*
