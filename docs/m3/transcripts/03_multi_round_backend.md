# Flow 3 - multi-round screening on the Java JD, deep dive, borderline suggestions, interview questions
_Source: `tests/scenarios/03_multi_round_backend.txt`_

## Turn 1
**User:** use jd02

<details><summary>Agent reasoning & tool calls</summary>

- Parsed JD from data/job_descriptions/jd02_java_backend.txt (443 chars).
- Extracted 5 must-haves and 5 nice-to-haves; min years = 4.0.
- Milestone 2 hybrid search (ChromaDB semantic + BM25) scored 100 resumes; top RAG hits: Tariq Kapoor, Fatima Costa, Leila Joshi.
- Round 1: screened 100 resumes; top 10 = Tariq Kapoor, Leila Joshi, Fatima Costa, Divya Ali, Fatima Joshi, Mateo Chen, Samuel Berg, Ifeoma Aziz, Hana Petrova, Noah Pillai
- Round 2: deep analysis re-ordered 10 of 10 candidates.
- Round 3 decisions: {'STRONG HIRE': 1, 'HIRE': 8, 'BORDERLINE': 1}
- Report written to outputs/m3_reports/match_report_20261031_174701_t1.md.
- 🔧 `list_files` → 6 JD files
- 🔧 `read_file` → 67 words
- 🔧 `extract_requirements` → 5 must, 5 nice (rules (M2 parser + sections))
- 🔧 `rag_search` → 100 candidates; best=Tariq Kapoor
- 🔧 `write_file` → outputs/m3_reports/match_report_20261031_174701_t1.md

</details>

**Agent:**

**Understood the role** (rules (M2 parser + sections) extraction):

**Must-have:** Java 4+y ×1.5, Spring Boot ×1.5, Microservices, Kafka, REST APIs  
**Nice-to-have:** Kubernetes, AWS, System Design, MySQL (or PostgreSQL), Redis  
**Experience:** 4+ yrs

**Agent:**

## Shortlist for: Backend Engineer (Java) - Helix Fintech
**Must-have:** Java 4+y ×1.5, Spring Boot ×1.5, Microservices, Kafka, REST APIs  
**Nice-to-have:** Kubernetes, AWS, System Design, MySQL (or PostgreSQL), Redis  
**Experience:** 4+ yrs

**Funnel:** 100 resumes scored by Milestone 2 hybrid search → round 1 scores every eligible resume → top 10 deep-analysed (round 2) → round 3: STRONG HIRE: 1 · HIRE: 8 · BORDERLINE: 1

| # | Candidate | Yrs | R1 | Deep | Decision | Missing must-haves |
|---|---|---|---|---|---|---|
| 1 | Fatima Costa (fatima_costa) | 9 | 87.4 (#3) | **86.4** | 🟢 STRONG HIRE | - |
| 2 | Mateo Chen (mateo_chen) | 6 | 84.5 (#6) | **83.2** | 🟢 HIRE | - |
| 3 | Samuel Berg (samuel_berg) | 4 | 84.4 (#7) | **83.1** | 🟢 HIRE | - |
| 4 | Fatima Joshi (fatima_joshi) | 9 | 86.5 (#5) | **81.2** | 🟢 HIRE | - |
| 5 | Leila Joshi (leila_joshi) | 4.5 | 89.1 (#2) | **80.8** | 🟢 HIRE | - |
| 6 | Tariq Kapoor (tariq_kapoor) | 8 | 93.0 (#1) | **80.3** | 🟢 HIRE | - |
| 7 | Ifeoma Aziz (ifeoma_aziz) | 5.5 | 81.5 (#8) | **78.8** | 🟢 HIRE | - |
| 8 | Divya Ali (divya_ali) | 7 | 86.5 (#4) | **74.2** | 🟢 HIRE | - |
| 9 | Hana Petrova (hana_petrova) | 4.5 | 81.3 (#9) | **73.1** | 🟢 HIRE | - |
| 10 | Noah Pillai (noah_pillai) | 3.5 | 81.2 (#10) | **75.4** | 🟡 BORDERLINE | - |

**Top pick: Fatima Costa** - STRONG HIRE: covers every must-have; deep score 86.4.

Full match report saved to `outputs/m3_reports/match_report_20261031_174701_t1.md`.
_Try: "compare the top 3", "why is #1 above #2?", "make Kubernetes a must-have", "interview questions for #1", "tell me about #4", or "done"._

## Turn 2
**User:** tell me about #1

<details><summary>Agent reasoning & tool calls</summary>

- User intent → report ['fatima_costa']

</details>

**Agent:**

### #1 Fatima Costa (fatima_costa) - 🟢 STRONG HIRE (low confidence)
*Senior Java Developer · 9 yrs · Bachelor's · `data/resumes_m3/fatima_costa.pdf`* - round-1 **87.4**, deep **86.4**, M2 baseline 94

**Rationale:** STRONG HIRE: covers every must-have; deep score 86.4.

**Strengths**
- Deep Java evidence (5 mentions in work history)
- Deep Spring Boot evidence (2 mentions in work history)
- Deep REST APIs evidence (2 mentions in work history)
- Exceeds experience bar: 9 yrs vs 4+ required
- Currently in a senior role (Senior Java Developer)
- Java: 7.6 yrs in roles (JD asks 4+)
- Brings nice-to-haves: Kubernetes, MySQL, Redis
- Quantified impact: "Migrated a monolith to event-driven Microservices using Kafka, reducing order processing delay by 60%"

**Gaps**
- No evidence of nice-to-haves: AWS, System Design

| Requirement | Type | Status | Where | Evidence |
|---|---|---|---|---|
| Java | must | ✓ 1.00 | skills + experience | Senior Java Developer @ Nimbus Cloud: Developed Spring Boot microservices in Java 17 handl… |
| Spring Boot | must | ✓ 1.00 | skills + experience | Senior Java Developer @ Nimbus Cloud: Developed Spring Boot microservices in Java 17 handl… |
| Microservices | must | ~ 0.75 | experience only | Senior Java Developer @ Helix Fintech: Migrated a monolith to event-driven Microservices u… |
| Kafka | must | ~ 0.75 | experience only | Senior Java Developer @ Helix Fintech: Migrated a monolith to event-driven Microservices u… |
| REST APIs | must | ✓ 1.00 | skills + experience | Senior Java Developer @ Helix Fintech: Designed REST APIs consumed by web and mobile clien… |
| Kubernetes | nice | ✓ 0.80 | skills list only | - |
| AWS | nice | ✗ 0.00 | missing | - |
| System Design | nice | ✗ 0.00 | missing | - |
| MySQL | nice | ✓ 1.00 | skills + experience | Senior Java Developer @ Nimbus Cloud: Tuned MySQL queries and added Redis caching, cutting… |
| Redis | nice | ~ 0.75 | experience only | Senior Java Developer @ Nimbus Cloud: Tuned MySQL queries and added Redis caching, cutting… |

**RAG excerpts (Milestone 2 retrieval)**
> Designed REST APIs consumed by web and mobile clients, with contract tests and versioning
> Migrated a monolith to event-driven Microservices using Kafka, reducing order processing delay
> Developed Spring Boot microservices in Java 17 handling 15k requests per second for the

Signals - depth 0.90, recency 0.80, seniority 0.80, quantified bullets 3

## Turn 3
**User:** show the report

<details><summary>Agent reasoning & tool calls</summary>

- User intent → report

</details>

**Agent:**

Full report: `outputs/m3_reports/match_report_20261031_174701_t1.md`

| # | Candidate | Yrs | R1 | Deep | Decision | Missing must-haves |
|---|---|---|---|---|---|---|
| 1 | Fatima Costa (fatima_costa) | 9 | 87.4 (#3) | **86.4** | 🟢 STRONG HIRE | - |
| 2 | Mateo Chen (mateo_chen) | 6 | 84.5 (#6) | **83.2** | 🟢 HIRE | - |
| 3 | Samuel Berg (samuel_berg) | 4 | 84.4 (#7) | **83.1** | 🟢 HIRE | - |
| 4 | Fatima Joshi (fatima_joshi) | 9 | 86.5 (#5) | **81.2** | 🟢 HIRE | - |
| 5 | Leila Joshi (leila_joshi) | 4.5 | 89.1 (#2) | **80.8** | 🟢 HIRE | - |
| 6 | Tariq Kapoor (tariq_kapoor) | 8 | 93.0 (#1) | **80.3** | 🟢 HIRE | - |
| 7 | Ifeoma Aziz (ifeoma_aziz) | 5.5 | 81.5 (#8) | **78.8** | 🟢 HIRE | - |
| 8 | Divya Ali (divya_ali) | 7 | 86.5 (#4) | **74.2** | 🟢 HIRE | - |
| 9 | Hana Petrova (hana_petrova) | 4.5 | 81.3 (#9) | **73.1** | 🟢 HIRE | - |
| 10 | Noah Pillai (noah_pillai) | 3.5 | 81.2 (#10) | **75.4** | 🟡 BORDERLINE | - |

### Borderline candidates - what would move them up
- **Noah Pillai**: Consider for a mid-level variant of the role, or offer with a 4-yr growth plan.

## Turn 4
**User:** interview questions for #1

<details><summary>Agent reasoning & tool calls</summary>

- User intent → questions ['fatima_costa']
- Generated interview questions for ['fatima_costa'].
- 🔧 `generate_interview_questions` → 5 questions

</details>

**Agent:**

## Screening questions - Fatima Costa (fatima_costa)
1. **[technical depth · Java]** Explain how you'd find and fix a memory leak in a long-running Java service.  
   _why: Must-have; evidence is 'skills + experience' - verify depth._
2. **[technical depth · Spring Boot]** How do you structure transactions and error handling across Spring Boot service layers?  
   _why: Must-have; evidence is 'skills + experience' - verify depth._
3. **[technical depth · REST APIs]** How do you version and paginate a public REST API?  
   _why: Must-have; evidence is 'skills + experience' - verify depth._
4. **[impact verification]** You wrote: "Migrated a monolith to event-driven Microservices using Kafka, reducing order processing delay by 60%". How was that measured, and what exactly was your part?  
   _why: Validate quantified claims._
5. **[leadership]** How have you raised the bar for your team - mentoring, reviews, or design standards?  
   _why: Senior role - check multiplier impact._

## Turn 5
**User:** done

<details><summary>Agent reasoning & tool calls</summary>

- User intent → end

</details>

_Conversation ended (graph reached END)._