# Flow 1 - natural-language search, side-by-side comparison, pairwise explanation
_Source: `tests/scenarios/01_nl_search_and_compare.txt`_

## Turn 1
**User:** Find me candidates with React and 3+ years experience

<details><summary>Agent reasoning & tool calls</summary>

- Parsed JD from chat message (53 chars).
- Extracted 1 must-haves and 0 nice-to-haves; min years = 3.0.
- Milestone 2 hybrid search (ChromaDB semantic + BM25) scored 100 resumes; top RAG hits: Meera Eze, Arjun Joshi, Ifeoma Iyer.
- Round 1: screened 100 resumes; top 10 = Meera Eze, Arjun Joshi, Ifeoma Iyer, Meera Obi, Zara Rahimi, Noah Aziz, Rohan Krishnan, Wei Patel, John Mathew, Emma Nair
- Round 2: deep analysis re-ordered 8 of 10 candidates.
- Round 3 decisions: {'STRONG HIRE': 8, 'HIRE': 2}
- Report written to outputs/m3_reports/match_report_20261031_174659_t1.md.
- 🔧 `list_files` → 6 JD files
- 🔧 `extract_requirements` → 1 must, 0 nice (rules (M2 parser + sections))
- 🔧 `rag_search` → 100 candidates; best=Meera Eze
- 🔧 `write_file` → outputs/m3_reports/match_report_20261031_174659_t1.md

</details>

**Agent:**

**Understood the role** (rules (M2 parser + sections) extraction):

**Must-have:** React 3+y ×1.5  
**Nice-to-have:** -  
**Experience:** 3+ yrs

**Agent:**

## Shortlist for: Ad-hoc search: Find me candidates with React and 3+ years experience
**Must-have:** React 3+y ×1.5  
**Nice-to-have:** -  
**Experience:** 3+ yrs

**Funnel:** 100 resumes scored by Milestone 2 hybrid search → round 1 scores every eligible resume → top 10 deep-analysed (round 2) → round 3: STRONG HIRE: 8 · HIRE: 2

| # | Candidate | Yrs | R1 | Deep | Decision | Missing must-haves |
|---|---|---|---|---|---|---|
| 1 | Meera Eze (meera_eze) | 3 | 99.6 (#1) | **91.7** | 🟢 STRONG HIRE | - |
| 2 | John Mathew (john_mathew) | 6.2 | 86.5 (#9) | **90.5** | 🟢 STRONG HIRE | - |
| 3 | Arjun Joshi (arjun_joshi) | 3.5 | 96.7 (#2) | **89.7** | 🟢 STRONG HIRE | - |
| 4 | Ifeoma Iyer (ifeoma_iyer) | 3 | 96.7 (#3) | **89.7** | 🟢 STRONG HIRE | - |
| 5 | Meera Obi (meera_obi) | 9 | 93.5 (#4) | **87.5** | 🟢 STRONG HIRE | - |
| 6 | Zara Rahimi (zara_rahimi) | 8 | 91.4 (#5) | **86.0** | 🟢 STRONG HIRE | - |
| 7 | Noah Aziz (noah_aziz) | 5 | 91.3 (#6) | **85.9** | 🟢 STRONG HIRE | - |
| 8 | Rohan Krishnan (rohan_krishnan) | 4.5 | 90.4 (#7) | **85.3** | 🟢 STRONG HIRE | - |
| 9 | Wei Patel (wei_patel) | 7 | 87.1 (#8) | **83.0** | 🟢 HIRE | - |
| 10 | Emma Nair (emma_nair) | 5.5 | 86.4 (#10) | **82.5** | 🟢 HIRE | - |

**Top pick: Meera Eze** - STRONG HIRE: covers every must-have; deep score 91.7.

Full match report saved to `outputs/m3_reports/match_report_20261031_174659_t1.md`.
_Try: "compare the top 3", "why is #1 above #2?", "make Docker a must-have", "interview questions for #1", "tell me about #4", or "done"._

## Turn 2
**User:** Compare the top 3 matches side by side

<details><summary>Agent reasoning & tool calls</summary>

- User intent → compare ['meera_eze', 'john_mathew', 'arjun_joshi']
- Compared ['meera_eze', 'john_mathew', 'arjun_joshi'].
- 🔧 `compare_candidates` → compared 3

</details>

**Agent:**

## Head-to-head: Meera Eze vs John Mathew vs Arjun Joshi

| | Meera Eze | John Mathew | Arjun Joshi |
|---|---|---|---|
| Round-1 score | 99.6 | 86.5 | 96.7 |
| Deep score | 91.7 | 90.5 | 89.7 |
| Decision | STRONG HIRE | STRONG HIRE | STRONG HIRE |
| Experience | 3 yrs | 6.2 yrs | 3.5 yrs |
| Current title | Frontend Engineer | Senior Frontend Engineer | Frontend Engineer |
| **React** (must) | ✓ | ✓ | ✓ |
| Seniority signal | 0.20 | 1.00 | 0.20 |

**Verdict:** Meera Eze leads on the combined deep score.
- **Meera Eze** - strengths: Deep React evidence (4 mentions in work history); Meets experience bar: 3 yrs. Gaps: none significant.
- **John Mathew** - strengths: Deep React evidence (3 mentions in work history); Exceeds experience bar: 6.2 yrs vs 3+ required. Gaps: none significant.
- **Arjun Joshi** - strengths: Deep React evidence (4 mentions in work history); Meets experience bar: 3.5 yrs. Gaps: none significant.

## Turn 3
**User:** Why did John rank higher than Jane?

<details><summary>Agent reasoning & tool calls</summary>

- User intent → explain ['john_mathew', 'jane_cooper']
- Explained ranking for ['john_mathew', 'jane_cooper'].

</details>

**Agent:**

**John Mathew** (#2, round-1 86.5) vs **Jane Cooper** (#12, round-1 85.8).
A gap of **0.7 points** in round 1.

| Round-1 factor | John Mathew | Jane Cooper | Points to John |
|---|---|---|---|
| experience fit | 1.00 | 0.90 | +2.0 |
| RAG retrieval (M2 semantic + BM25) | 0.33 | 0.39 | -1.2 |
| must-have coverage | 1.00 | 1.00 | +0.0 |
| nice-to-have coverage | 0.00 | 0.00 | +0.0 |

- The biggest round-1 driver is **experience fit** (+2.0 pts).
- Experience: 6.2 yrs vs 2.8 yrs.
- After deep analysis John Mathew is **STRONG HIRE** (deep score 90.5).
- Jane Cooper didn't make the top 10, so no deep analysis was run.

## Turn 4
**User:** done

<details><summary>Agent reasoning & tool calls</summary>

- User intent → end

</details>

_Conversation ended (graph reached END)._