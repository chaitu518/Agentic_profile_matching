# Flow 5 - start vague, clarify, refine, compare by name and rank, switch to a new search
_Source: `tests/scenarios/05_switch_jobs.txt`_

## Turn 1
**User:** hi there

<details><summary>Agent reasoning & tool calls</summary>

- Parsed JD from chat message (8 chars).
- No requirements found; asking the user.
- 🔧 `list_files` → 6 JD files
- 🔧 `extract_requirements` → 0 must, 0 nice (rules (M2 parser + sections))

</details>

**Agent:**

I couldn't find any skills in that. Paste a job description, name one of the JDs in `data/job_descriptions/` (e.g. *jd02* or *frontend_react*), or ask something like "Find me candidates with React and 3+ years experience".

## Turn 2
**User:** use jd04

<details><summary>Agent reasoning & tool calls</summary>

- User intent → new_search
- Parsed JD from data/job_descriptions/jd04_devops_sre.txt (419 chars).
- Extracted 6 must-haves and 2 nice-to-haves; min years = 4.0.
- Milestone 2 hybrid search (ChromaDB semantic + BM25) scored 100 resumes; top RAG hits: Arjun Sato, Sakura Novak, Diego Rossi.
- Round 1: screened 100 resumes; top 10 = Arjun Sato, Diego Rossi, Tariq Dubois, Sakura Novak, Chloe Pillai, Leila Iyer, Priya Brooks, Chloe Garcia, Arjun Menon, Chloe Rahimi
- Round 2: deep analysis re-ordered 5 of 10 candidates.
- Round 3 decisions: {'HIRE': 5, 'BORDERLINE': 4, 'NO HIRE': 1}
- Report written to outputs/m3_reports/match_report_20261031_174703_t1.md.
- 🔧 `list_files` → 6 JD files
- 🔧 `read_file` → 64 words
- 🔧 `extract_requirements` → 6 must, 2 nice (rules (M2 parser + sections))
- 🔧 `rag_search` → 100 candidates; best=Arjun Sato
- 🔧 `write_file` → outputs/m3_reports/match_report_20261031_174703_t1.md

</details>

**Agent:**

**Understood the role** (rules (M2 parser + sections) extraction):

**Must-have:** Kubernetes ×1.5, Terraform ×1.5, AWS, Docker, Linux, Python (or Bash)  
**Nice-to-have:** CI/CD, Prometheus  
**Experience:** 4+ yrs

**Agent:**

## Shortlist for: Site Reliability / DevOps Engineer - Nimbus Cloud
**Must-have:** Kubernetes ×1.5, Terraform ×1.5, AWS, Docker, Linux, Python (or Bash)  
**Nice-to-have:** CI/CD, Prometheus  
**Experience:** 4+ yrs

**Funnel:** 100 resumes scored by Milestone 2 hybrid search → round 1 scores every eligible resume → top 10 deep-analysed (round 2) → round 3: HIRE: 5 · BORDERLINE: 4 · NO HIRE: 1

| # | Candidate | Yrs | R1 | Deep | Decision | Missing must-haves |
|---|---|---|---|---|---|---|
| 1 | Diego Rossi (diego_rossi) | 6 | 92.2 (#2) | **79.2** | 🟢 HIRE | - |
| 2 | Sakura Novak (sakura_novak) | 4 | 91.9 (#4) | **79.0** | 🟢 HIRE | - |
| 3 | Tariq Dubois (tariq_dubois) | 6 | 92.1 (#3) | **78.1** | 🟢 HIRE | - |
| 4 | Arjun Sato (arjun_sato) | 9 | 95.1 (#1) | **77.6** | 🟢 HIRE | - |
| 5 | Chloe Pillai (chloe_pillai) | 10 | 89.7 (#5) | **77.5** | 🟢 HIRE | - |
| 6 | Priya Brooks (priya_brooks) | 4 | 88.3 (#7) | **76.5** | 🟡 BORDERLINE | Python |
| 7 | Leila Iyer (leila_iyer) | 8 | 88.5 (#6) | **75.6** | 🟡 BORDERLINE | Python |
| 8 | Chloe Garcia (chloe_garcia) | 3 | 86.3 (#8) | **75.1** | 🟡 BORDERLINE | - |
| 9 | Arjun Menon (arjun_menon) | 2.5 | 79.1 (#9) | **72.0** | 🟡 BORDERLINE | - |
| 10 | Chloe Rahimi (chloe_rahimi) | 2 | 64.9 (#10) | **60.8** | 🔴 NO HIRE | Python |

**Top pick: Diego Rossi** - HIRE: covers every must-have; deep score 79.2.

Full match report saved to `outputs/m3_reports/match_report_20261031_174703_t1.md`.
_Try: "compare the top 3", "why is #1 above #2?", "make CI/CD a must-have", "interview questions for #1", "tell me about #4", or "done"._

## Turn 3
**User:** make Prometheus a must-have

<details><summary>Agent reasoning & tool calls</summary>

- User intent → refine  [{'op': 'add_must', 'skill': 'Prometheus'}]
- Refinement applied: ['Moved **Prometheus** to must-have']
- Milestone 2 hybrid search (ChromaDB semantic + BM25) scored 100 resumes; top RAG hits: Arjun Sato, Sakura Novak, Diego Rossi.
- Round 1: screened 100 resumes; top 10 = Arjun Sato, Tariq Dubois, Diego Rossi, Sakura Novak, Chloe Pillai, Leila Iyer, Priya Brooks, Chloe Garcia, Arjun Menon, Lucas Fischer
- Round 2: deep analysis re-ordered 5 of 10 candidates.
- Round 3 decisions: {'HIRE': 5, 'BORDERLINE': 4, 'NO HIRE': 1}
- Report written to outputs/m3_reports/match_report_20261031_174703_t2.md.
- 🔧 `rag_search` → 100 candidates; best=Arjun Sato
- 🔧 `write_file` → outputs/m3_reports/match_report_20261031_174703_t2.md

</details>

**Agent:**

**Updating criteria and re-ranking:**
- Moved **Prometheus** to must-have

**Must-have:** Kubernetes ×1.5, Terraform ×1.5, AWS, Docker, Linux, Python (or Bash), Prometheus  
**Nice-to-have:** CI/CD  
**Experience:** 4+ yrs

**Agent:**

### What changed
- Moved **Prometheus** to must-have

### Ranking movement
- **Tariq Dubois**: #3 -> #1 (up) - has newly required Prometheus; nice-to-have coverage +1.9 pts; score 92.1 -> 93.0
- **Arjun Sato**: #4 -> #2 (up) - has newly required Prometheus; nice-to-have coverage +1.9 pts; score 95.1 -> 95.7
- **Diego Rossi**: #1 -> #3 (down) - has newly required Prometheus; must-have coverage -1.2 pts; score 92.2 -> 90.9
- **Sakura Novak**: #2 -> #4 (down) - has newly required Prometheus; score 91.9 -> 90.9
- **Chloe Garcia**: #8 -> #7 (up) - has newly required Prometheus; nice-to-have coverage +1.9 pts; score 86.3 -> 87.2
- **Leila Iyer**: #7 -> #8 (down) - has newly required Prometheus; nice-to-have coverage -1.9 pts; score 88.5 -> 88.0
- **Lucas Fischer**: NEW at #10 - lacks newly required Prometheus; nice-to-have coverage +7.5 pts; score 61.2 -> 63.9
- **Chloe Rahimi**: #10 -> dropped out - has newly required Prometheus; nice-to-have coverage -5.6 pts; score 64.9 -> 59.1

**Agent:**

## Shortlist for: Site Reliability / DevOps Engineer - Nimbus Cloud
**Must-have:** Kubernetes ×1.5, Terraform ×1.5, AWS, Docker, Linux, Python (or Bash), Prometheus  
**Nice-to-have:** CI/CD  
**Experience:** 4+ yrs

**Funnel:** 100 resumes scored by Milestone 2 hybrid search → round 1 scores every eligible resume → top 10 deep-analysed (round 2) → round 3: HIRE: 5 · BORDERLINE: 4 · NO HIRE: 1

| # | Candidate | Yrs | R1 | Deep | Decision | Missing must-haves |
|---|---|---|---|---|---|---|
| 1 | Tariq Dubois (tariq_dubois) | 6 | 93.0 (#2) | **80.2** | 🟢 HIRE | - |
| 2 | Arjun Sato (arjun_sato) | 9 | 95.7 (#1) | **79.8** | 🟢 HIRE | - |
| 3 | Diego Rossi (diego_rossi) | 6 | 90.9 (#3) | **78.5** | 🟢 HIRE | - |
| 4 | Sakura Novak (sakura_novak) | 4 | 90.9 (#4) | **78.5** | 🟢 HIRE | - |
| 5 | Chloe Pillai (chloe_pillai) | 10 | 90.5 (#5) | **78.2** | 🟢 HIRE | - |
| 6 | Priya Brooks (priya_brooks) | 4 | 87.8 (#7) | **77.5** | 🟡 BORDERLINE | Python |
| 7 | Chloe Garcia (chloe_garcia) | 3 | 87.2 (#8) | **77.0** | 🟡 BORDERLINE | - |
| 8 | Leila Iyer (leila_iyer) | 8 | 88.0 (#6) | **75.6** | 🟡 BORDERLINE | Python |
| 9 | Arjun Menon (arjun_menon) | 2.5 | 81.0 (#9) | **71.3** | 🟡 BORDERLINE | Prometheus |
| 10 | Lucas Fischer (lucas_fischer) | 1.5 | 63.9 (#10) | **52.4** | 🔴 NO HIRE | Prometheus |

**Top pick: Tariq Dubois** - HIRE: covers every must-have; deep score 80.2.

Full match report saved to `outputs/m3_reports/match_report_20261031_174703_t2.md`.
_Try: "compare the top 3", "why is #1 above #2?", "make CI/CD a must-have", "interview questions for #1", "tell me about #4", or "done"._

## Turn 4
**User:** compare Diego and #2

<details><summary>Agent reasoning & tool calls</summary>

- User intent → compare ['diego_rossi', 'arjun_sato']
- Compared ['diego_rossi', 'arjun_sato'].
- 🔧 `compare_candidates` → compared 2

</details>

**Agent:**

## Head-to-head: Diego Rossi vs Arjun Sato

| | Diego Rossi | Arjun Sato |
|---|---|---|
| Round-1 score | 90.9 | 95.7 |
| Deep score | 78.5 | 79.8 |
| Decision | HIRE | HIRE |
| Experience | 6 yrs | 9 yrs |
| Current title | Platform Engineer | Platform Engineer |
| **Kubernetes** (must) | ✓ | ✓ |
| **Terraform** (must) | ✓ | ✓ |
| **AWS** (must) | ✓ | ✓ |
| **Docker** (must) | ✓ | ✓ |
| **Linux** (must) | ✓ | ✓ |
| **Python** (must) | ✓ | ✓ |
| **Prometheus** (must) | ~ (experience only) | ~ (experience only) |
| CI/CD (nice) | ~ (experience only) | ✓ |
| Seniority signal | 0.40 | 0.40 |

**Verdict:** Arjun Sato leads on the combined deep score.
- **Diego Rossi** - strengths: Deep Kubernetes evidence (4 mentions in work history); Deep Terraform evidence (2 mentions in work history). Gaps: Python is listed but not evidenced in any project/role; Most matched skills are not used in the current role (possible staleness).
- **Arjun Sato** - strengths: Deep Kubernetes evidence (4 mentions in work history); Deep Docker evidence (2 mentions in work history). Gaps: Python is listed but not evidenced in any project/role; Most matched skills are not used in the current role (possible staleness).

## Turn 5
**User:** Now find Java developers with Kafka and Spring Boot, 4+ years, nice to have Kubernetes

<details><summary>Agent reasoning & tool calls</summary>

- User intent → new_search
- Parsed JD from chat message (86 chars).
- Extracted 3 must-haves and 1 nice-to-haves; min years = 4.0.
- Milestone 2 hybrid search (ChromaDB semantic + BM25) scored 100 resumes; top RAG hits: Samuel Berg, Hana Petrova, Elena Eze.
- Round 1: screened 100 resumes; top 10 = Fatima Joshi, Fatima Costa, Divya Ali, Hana Petrova, Elena Eze, Tariq Kapoor, Leila Joshi, Mateo Chen, Samuel Berg, Ifeoma Aziz
- Round 2: deep analysis re-ordered 10 of 10 candidates.
- Round 3 decisions: {'HIRE': 7, 'BORDERLINE': 2, 'NO HIRE': 1}
- Report written to outputs/m3_reports/match_report_20261031_174703_t3.md.
- 🔧 `list_files` → 6 JD files
- 🔧 `extract_requirements` → 3 must, 1 nice (rules (M2 parser + sections))
- 🔧 `rag_search` → 100 candidates; best=Samuel Berg
- 🔧 `write_file` → outputs/m3_reports/match_report_20261031_174703_t3.md

</details>

**Agent:**

**Understood the role** (rules (M2 parser + sections) extraction):

**Must-have:** Java, Kafka, Spring Boot  
**Nice-to-have:** Kubernetes  
**Experience:** 4+ yrs

**Agent:**

## Shortlist for: Ad-hoc search: Now find Java developers with Kafka and Spring Boot, 4+ years, nice to
**Must-have:** Java, Kafka, Spring Boot  
**Nice-to-have:** Kubernetes  
**Experience:** 4+ yrs

**Funnel:** 100 resumes scored by Milestone 2 hybrid search → round 1 scores every eligible resume → top 10 deep-analysed (round 2) → round 3: HIRE: 7 · BORDERLINE: 2 · NO HIRE: 1

| # | Candidate | Yrs | R1 | Deep | Decision | Missing must-haves |
|---|---|---|---|---|---|---|
| 1 | Fatima Costa (fatima_costa) | 9 | 87.8 (#2) | **84.8** | 🟢 HIRE | - |
| 2 | Fatima Joshi (fatima_joshi) | 9 | 87.9 (#1) | **79.2** | 🟢 HIRE | - |
| 3 | Mateo Chen (mateo_chen) | 6 | 79.8 (#8) | **79.2** | 🟢 HIRE | - |
| 4 | Samuel Berg (samuel_berg) | 4 | 78.5 (#9) | **78.3** | 🟢 HIRE | - |
| 5 | Ifeoma Aziz (ifeoma_aziz) | 5.5 | 75.7 (#10) | **74.7** | 🟢 HIRE | - |
| 6 | Divya Ali (divya_ali) | 7 | 86.0 (#3) | **74.2** | 🟢 HIRE | - |
| 7 | Leila Joshi (leila_joshi) | 4.5 | 80.1 (#7) | **72.7** | 🟢 HIRE | - |
| 8 | Hana Petrova (hana_petrova) | 4.5 | 81.2 (#4) | **71.8** | 🟡 BORDERLINE | - |
| 9 | Tariq Kapoor (tariq_kapoor) | 8 | 80.8 (#6) | **70.6** | 🟡 BORDERLINE | - |
| 10 | Elena Eze (elena_eze) | 2 | 80.9 (#5) | **78.6** | 🔴 NO HIRE | - |

**Top pick: Fatima Costa** - HIRE: covers every must-have; deep score 84.8.

Full match report saved to `outputs/m3_reports/match_report_20261031_174703_t3.md`.
_Try: "compare the top 3", "why is #1 above #2?", "make Kubernetes a must-have", "interview questions for #1", "tell me about #4", or "done"._

## Turn 6
**User:** interview questions for #2

<details><summary>Agent reasoning & tool calls</summary>

- User intent → questions ['fatima_joshi']
- Generated interview questions for ['fatima_joshi'].
- 🔧 `generate_interview_questions` → 5 questions

</details>

**Agent:**

## Screening questions - Fatima Joshi (fatima_joshi)
1. **[technical depth · Java]** Explain how you'd find and fix a memory leak in a long-running Java service.  
   _why: Must-have; evidence is 'skills + experience' - verify depth._
2. **[technical depth · Spring Boot]** How do you structure transactions and error handling across Spring Boot service layers?  
   _why: Must-have; evidence is 'skills + experience' - verify depth._
3. **[technical depth · Kafka]** How do you guarantee exactly-once or idempotent processing with Kafka consumers?  
   _why: Must-have; evidence is 'experience only' - verify depth._
4. **[impact verification]** You wrote: "Migrated a monolith to event-driven Microservices using Kafka, reducing order processing delay by 60%". How was that measured, and what exactly was your part?  
   _why: Validate quantified claims._
5. **[ownership]** Describe a feature you owned from design to production. What would you do differently?  
   _why: Check end-to-end ownership._

## Turn 7
**User:** done

<details><summary>Agent reasoning & tool calls</summary>

- User intent → end

</details>

_Conversation ended (graph reached END)._