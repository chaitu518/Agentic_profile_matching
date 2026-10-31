# Demo video script (replay with: python chat_cli.py --trace --script tests/scenarios/demo.txt --delay 3)
_Source: `tests/scenarios/demo.txt`_

## Turn 1
**User:** use jd05_frontend_react.txt

<details><summary>Agent reasoning & tool calls</summary>

- Parsed JD from data/job_descriptions/jd05_frontend_react.txt (419 chars).
- Extracted 5 must-haves and 3 nice-to-haves; min years = 3.0.
- Milestone 2 hybrid search (ChromaDB semantic + BM25) scored 100 resumes; top RAG hits: Meera Eze, Noah Aziz, Zara Rahimi.
- Round 1: screened 100 resumes; top 10 = Noah Aziz, Zara Rahimi, John Mathew, Ifeoma Iyer, Meera Eze, Emma Nair, Wei Patel, Meera Obi, Arjun Joshi, Rohan Krishnan
- Round 2: deep analysis re-ordered 3 of 10 candidates.
- Round 3 decisions: {'STRONG HIRE': 1, 'HIRE': 9}
- Report written to outputs/m3_reports/match_report_20261031_174704_t1.md.
- 🔧 `list_files` → 6 JD files
- 🔧 `read_file` → 60 words
- 🔧 `extract_requirements` → 5 must, 3 nice (rules (M2 parser + sections))
- 🔧 `rag_search` → 100 candidates; best=Meera Eze
- 🔧 `write_file` → outputs/m3_reports/match_report_20261031_174704_t1.md

</details>

**Agent:**

**Understood the role** (rules (M2 parser + sections) extraction):

**Must-have:** React 3+y ×1.5, TypeScript ×1.5, JavaScript ×1.5, HTML/CSS ×1.5, Redux (or MobX/Zustand)  
**Nice-to-have:** Cypress, Accessibility, Next.js  
**Experience:** 3+ yrs

**Agent:**

## Shortlist for: Frontend Engineer (React) - Pixelcraft Studios
**Must-have:** React 3+y ×1.5, TypeScript ×1.5, JavaScript ×1.5, HTML/CSS ×1.5, Redux (or MobX/Zustand)  
**Nice-to-have:** Cypress, Accessibility, Next.js  
**Experience:** 3+ yrs

**Funnel:** 100 resumes scored by Milestone 2 hybrid search → round 1 scores every eligible resume → top 10 deep-analysed (round 2) → round 3: STRONG HIRE: 1 · HIRE: 9

| # | Candidate | Yrs | R1 | Deep | Decision | Missing must-haves |
|---|---|---|---|---|---|---|
| 1 | John Mathew (john_mathew) | 6.2 | 93.7 (#3) | **88.8** | 🟢 STRONG HIRE | - |
| 2 | Noah Aziz (noah_aziz) | 5 | 95.1 (#1) | **84.2** | 🟢 HIRE | - |
| 3 | Zara Rahimi (zara_rahimi) | 8 | 94.3 (#2) | **83.6** | 🟢 HIRE | - |
| 4 | Ifeoma Iyer (ifeoma_iyer) | 3 | 93.5 (#4) | **83.0** | 🟢 HIRE | - |
| 5 | Meera Eze (meera_eze) | 3 | 93.4 (#5) | **83.0** | 🟢 HIRE | - |
| 6 | Emma Nair (emma_nair) | 5.5 | 92.9 (#6) | **82.6** | 🟢 HIRE | - |
| 7 | Wei Patel (wei_patel) | 7 | 92.0 (#7) | **82.0** | 🟢 HIRE | - |
| 8 | Meera Obi (meera_obi) | 9 | 91.7 (#8) | **81.8** | 🟢 HIRE | - |
| 9 | Arjun Joshi (arjun_joshi) | 3.5 | 91.3 (#9) | **81.5** | 🟢 HIRE | - |
| 10 | Rohan Krishnan (rohan_krishnan) | 4.5 | 90.1 (#10) | **80.7** | 🟢 HIRE | - |

**Top pick: John Mathew** - STRONG HIRE: covers every must-have; deep score 88.8.

Full match report saved to `outputs/m3_reports/match_report_20261031_174704_t1.md`.
_Try: "compare the top 3", "why is #1 above #2?", "make Cypress a must-have", "interview questions for #1", "tell me about #4", or "done"._

## Turn 2
**User:** Compare the top 3 matches side by side

<details><summary>Agent reasoning & tool calls</summary>

- User intent → compare ['john_mathew', 'noah_aziz', 'zara_rahimi']
- Compared ['john_mathew', 'noah_aziz', 'zara_rahimi'].
- 🔧 `compare_candidates` → compared 3

</details>

**Agent:**

## Head-to-head: John Mathew vs Noah Aziz vs Zara Rahimi

| | John Mathew | Noah Aziz | Zara Rahimi |
|---|---|---|---|
| Round-1 score | 93.7 | 95.1 | 94.3 |
| Deep score | 88.8 | 84.2 | 83.6 |
| Decision | STRONG HIRE | HIRE | HIRE |
| Experience | 6.2 yrs | 5 yrs | 8 yrs |
| Current title | Senior Frontend Engineer | UI Engineer | Frontend Engineer |
| **React** (must) | ✓ | ✓ | ✓ |
| **TypeScript** (must) | ✓ | ✓ | ✓ |
| **JavaScript** (must) | ✓ | ✓ | ✓ |
| **HTML/CSS** (must) | ✓ | ✓ | ✓ |
| **Redux** (must) | ✓ | ✓ | ~ (experience only) |
| Cypress (nice) | ✓ | ~ (experience only) | ✓ |
| Accessibility (nice) | ~ (experience only) | ~ (experience only) | ~ (experience only) |
| Next.js (nice) | ✓ | ✓ | ✓ |
| Seniority signal | 1.00 | 0.20 | 0.20 |

**Verdict:** John Mathew leads on the combined deep score.
- **John Mathew** - strengths: Deep React evidence (3 mentions in work history); Deep TypeScript evidence (2 mentions in work history). Gaps: HTML/CSS is listed but not evidenced in any project/role.
- **Noah Aziz** - strengths: Deep React evidence (4 mentions in work history); Deep JavaScript evidence (3 mentions in work history). Gaps: none significant.
- **Zara Rahimi** - strengths: Deep React evidence (4 mentions in work history); Deep JavaScript evidence (3 mentions in work history). Gaps: none significant.

## Turn 3
**User:** Why did John rank higher than Jane?

<details><summary>Agent reasoning & tool calls</summary>

- User intent → explain ['john_mathew', 'jane_cooper']
- Explained ranking for ['john_mathew', 'jane_cooper'].

</details>

**Agent:**

**John Mathew** (#1, round-1 93.7) vs **Jane Cooper** (#16, round-1 68.2).
A gap of **25.5 points** in round 1.

| Round-1 factor | John Mathew | Jane Cooper | Points to John |
|---|---|---|---|
| must-have coverage | 0.96 | 0.64 | +14.1 |
| nice-to-have coverage | 0.92 | 0.58 | +5.0 |
| RAG retrieval (M2 semantic + BM25) | 0.84 | 0.62 | +4.4 |
| experience fit | 1.00 | 0.90 | +2.0 |

- The biggest round-1 driver is **must-have coverage** (+14.1 pts).
- Must-haves only John Mathew has: **TypeScript, Redux**.
- Nice-to-haves only John Mathew has: Next.js.
- Experience: 6.2 yrs vs 2.8 yrs.
- Jane Cooper is missing must-have(s): TypeScript, Redux.
- After deep analysis John Mathew is **STRONG HIRE** (deep score 88.8).
- Jane Cooper didn't make the top 10, so no deep analysis was run.

## Turn 4
**User:** Make Next.js a must-have and require 5+ years

<details><summary>Agent reasoning & tool calls</summary>

- User intent → refine  [{'op': 'min_years', 'value': 5.0}, {'op': 'add_must', 'skill': 'Next.js'}]
- Refinement applied: ['Experience bar: 3.0 -> 5.0 years', 'Moved **Next.js** to must-have']
- Milestone 2 hybrid search (ChromaDB semantic + BM25) scored 100 resumes; top RAG hits: Noah Aziz, Zara Rahimi, John Mathew.
- Round 1: screened 100 resumes; top 10 = Noah Aziz, Zara Rahimi, John Mathew, Emma Nair, Wei Patel, Meera Obi, Mei Krishnan, Rohan Krishnan, Ifeoma Iyer, Meera Eze
- Round 2: deep analysis re-ordered 6 of 10 candidates.
- Round 3 decisions: {'STRONG HIRE': 3, 'HIRE': 4, 'BORDERLINE': 3}
- Report written to outputs/m3_reports/match_report_20261031_174704_t2.md.
- 🔧 `rag_search` → 100 candidates; best=Noah Aziz
- 🔧 `write_file` → outputs/m3_reports/match_report_20261031_174704_t2.md

</details>

**Agent:**

**Updating criteria and re-ranking:**
- Experience bar: 3.0 -> 5.0 years
- Moved **Next.js** to must-have

**Must-have:** React 3+y ×1.5, TypeScript ×1.5, JavaScript ×1.5, HTML/CSS ×1.5, Redux (or MobX/Zustand), Next.js  
**Nice-to-have:** Cypress, Accessibility  
**Experience:** 5+ yrs

**Agent:**

### What changed
- Experience bar: 3.0 -> 5.0 years
- Moved **Next.js** to must-have

### Ranking movement
- **Wei Patel**: #7 -> #4 (up) - has newly required Next.js; RAG retrieval (M2 semantic + BM25) +1.0 pts; score 92.0 -> 92.6
- **Meera Obi**: #8 -> #5 (up) - has newly required Next.js; score 91.7 -> 92.2
- **Mei Krishnan**: NEW at #7 - has newly required Next.js; must-have coverage -1.1 pts; score 87.8 -> 88.1
- **Rohan Krishnan**: #10 -> #8 (up) - has newly required Next.js; experience fit -2.9 pts (4.5 yrs); RAG retrieval (M2 semantic + BM25) +1.0 pts; score 90.1 -> 87.8
- **Ifeoma Iyer**: #4 -> #9 (down) - has newly required Next.js; experience fit -10.7 pts (3 yrs); score 93.5 -> 81.9
- **Meera Eze**: #5 -> #10 (down) - has newly required Next.js; experience fit -10.7 pts (3 yrs); must-have coverage -1.1 pts; score 93.4 -> 81.3
- **Arjun Joshi**: #9 -> dropped out - has newly required Next.js; experience fit -8.3 pts (3.5 yrs); nice-to-have coverage -1.2 pts; score 91.3 -> 81.2

**Agent:**

## Shortlist for: Frontend Engineer (React) - Pixelcraft Studios
**Must-have:** React 3+y ×1.5, TypeScript ×1.5, JavaScript ×1.5, HTML/CSS ×1.5, Redux (or MobX/Zustand), Next.js  
**Nice-to-have:** Cypress, Accessibility  
**Experience:** 5+ yrs

**Funnel:** 100 resumes scored by Milestone 2 hybrid search → round 1 scores every eligible resume → top 10 deep-analysed (round 2) → round 3: STRONG HIRE: 3 · HIRE: 4 · BORDERLINE: 3

| # | Candidate | Yrs | R1 | Deep | Decision | Missing must-haves |
|---|---|---|---|---|---|---|
| 1 | John Mathew (john_mathew) | 6.2 | 94.5 (#3) | **90.5** | 🟢 STRONG HIRE | - |
| 2 | Noah Aziz (noah_aziz) | 5 | 95.4 (#1) | **85.1** | 🟢 STRONG HIRE | - |
| 3 | Zara Rahimi (zara_rahimi) | 8 | 95.2 (#2) | **85.0** | 🟢 STRONG HIRE | - |
| 4 | Wei Patel (wei_patel) | 7 | 92.6 (#5) | **83.2** | 🟢 HIRE | - |
| 5 | Meera Obi (meera_obi) | 9 | 92.2 (#6) | **82.9** | 🟢 HIRE | - |
| 6 | Emma Nair (emma_nair) | 5.5 | 93.2 (#4) | **82.2** | 🟢 HIRE | - |
| 7 | Mei Krishnan (mei_krishnan) | 6 | 88.1 (#7) | **78.7** | 🟢 HIRE | - |
| 8 | Rohan Krishnan (rohan_krishnan) | 4.5 | 87.8 (#8) | **78.5** | 🟡 BORDERLINE | - |
| 9 | Ifeoma Iyer (ifeoma_iyer) | 3 | 81.9 (#9) | **75.7** | 🟡 BORDERLINE | - |
| 10 | Meera Eze (meera_eze) | 3 | 81.3 (#10) | **75.2** | 🟡 BORDERLINE | - |

**Top pick: John Mathew** - STRONG HIRE: covers every must-have; deep score 90.5.

Full match report saved to `outputs/m3_reports/match_report_20261031_174704_t2.md`.
_Try: "compare the top 3", "why is #1 above #2?", "make Cypress a must-have", "interview questions for #1", "tell me about #4", or "done"._

## Turn 5
**User:** tell me about #2

<details><summary>Agent reasoning & tool calls</summary>

- User intent → report ['noah_aziz']

</details>

**Agent:**

### #2 Noah Aziz (noah_aziz) - 🟢 STRONG HIRE (low confidence)
*UI Engineer · 5 yrs · Bachelor's · `data/resumes_m3/noah_aziz.docx`* - round-1 **95.4**, deep **85.1**, M2 baseline 98

**Rationale:** STRONG HIRE: covers every must-have; deep score 85.1.

**Strengths**
- Deep React evidence (4 mentions in work history)
- Deep JavaScript evidence (3 mentions in work history)
- Deep HTML/CSS evidence (3 mentions in work history)
- Deep TypeScript evidence (2 mentions in work history)
- Deep Next.js evidence (2 mentions in work history)
- Meets experience bar: 5 yrs
- React: 5 yrs in roles (JD asks 3+)
- Brings nice-to-haves: Cypress, Accessibility
- Quantified impact: "Migrated a legacy SPA to Next.js with server-side rendering, improving LCP by 40%"

**Gaps**
- none significant

| Requirement | Type | Status | Where | Evidence |
|---|---|---|---|---|
| React | must | ✓ 1.00 | skills + experience | UI Engineer @ Vertex Payments: Built a component library in React and TypeScript used by 6… |
| TypeScript | must | ✓ 1.00 | skills + experience | UI Engineer @ Vertex Payments: Built a component library in React and TypeScript used by 6… |
| JavaScript | must | ✓ 1.00 | skills + experience | UI Engineer @ Vertex Payments: Migrated a legacy SPA to Next.js with server-side rendering… |
| HTML/CSS | must | ✓ 1.00 | skills + experience | Senior React Developer @ Pixelcraft Studios: Implemented accessible, responsive layouts wi… |
| Redux | must | ✓ 1.00 | skills + experience | Senior React Developer @ Pixelcraft Studios: Managed complex client state with Redux and R… |
| Next.js | must | ✓ 1.00 | skills + experience | UI Engineer @ Vertex Payments: Migrated a legacy SPA to Next.js with server-side rendering… |
| Cypress | nice | ~ 0.75 | experience only | Senior React Developer @ Pixelcraft Studios: Wrote end-to-end tests with Cypress and raise… |
| Accessibility | nice | ~ 0.75 | experience only | Senior React Developer @ Pixelcraft Studios: Implemented accessible, responsive layouts wi… |

**RAG excerpts (Milestone 2 retrieval)**
> Migrated a legacy SPA to Next.js with server-side rendering, improving LCP by 40%
> Built a component library in React and TypeScript used by 6 product teams
> Senior React Developer - Pixelcraft Studios

Signals - depth 0.92, recency 0.67, seniority 0.20, quantified bullets 2

## Turn 6
**User:** interview questions for #1

<details><summary>Agent reasoning & tool calls</summary>

- User intent → questions ['john_mathew']
- Generated interview questions for ['john_mathew'].
- 🔧 `generate_interview_questions` → 6 questions

</details>

**Agent:**

## Screening questions - John Mathew (john_mathew)
1. **[technical depth · React]** How do you decide between local state, context and a store like Redux in a large React app?  
   _why: Must-have; evidence is 'skills + experience' - verify depth._
2. **[technical depth · TypeScript]** How do you type a reusable component or API client generically in TypeScript?  
   _why: Must-have; evidence is 'skills + experience' - verify depth._
3. **[technical depth · JavaScript]** Explain the event loop and how microtasks differ from macrotasks.  
   _why: Must-have; evidence is 'skills + experience' - verify depth._
4. **[verify claim · HTML/CSS]** Your resume lists HTML/CSS but no project shows it. Where did you use it and at what scale?  
   _why: Listed without evidence._
5. **[impact verification]** You wrote: "Led the migration of the customer dashboard to Next.js and React, cutting time-to-interactive by 45%". How was that measured, and what exactly was your part?  
   _why: Validate quantified claims._
6. **[leadership]** How have you raised the bar for your team - mentoring, reviews, or design standards?  
   _why: Senior role - check multiplier impact._

## Turn 7
**User:** done

<details><summary>Agent reasoning & tool calls</summary>

- User intent → end

</details>

_Conversation ended (graph reached END)._