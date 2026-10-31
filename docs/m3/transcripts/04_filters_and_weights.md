# Flow 4 - degree filter, re-weighting, explaining candidates, clearing the filter
_Source: `tests/scenarios/04_filters_and_weights.txt`_

## Turn 1
**User:** use jd01_senior_ml_engineer

<details><summary>Agent reasoning & tool calls</summary>

- Parsed JD from data/job_descriptions/jd01_senior_ml_engineer.txt (648 chars).
- Extracted 4 must-haves and 5 nice-to-haves; min years = 5.0.
- Milestone 2 hybrid search (ChromaDB semantic + BM25) scored 100 resumes; top RAG hits: Sofia Patel, Aarav Pillai, Noah Reddy.
- Round 1: screened 100 resumes; top 10 = Priya Tanaka, Omar Rao, Sofia Patel, Noah Reddy, Aarav Patel, Aarav Sharma, Aarav Pillai, Samuel Novak, Isabel Haddad, Liam Silva
- Round 2: deep analysis re-ordered 7 of 10 candidates.
- Round 3 decisions: {'STRONG HIRE': 1, 'HIRE': 5, 'BORDERLINE': 4}
- Report written to outputs/m3_reports/match_report_20261031_174702_t1.md.
- 🔧 `list_files` → 6 JD files
- 🔧 `read_file` → 100 words
- 🔧 `extract_requirements` → 4 must, 5 nice (rules (M2 parser + sections))
- 🔧 `rag_search` → 100 candidates; best=Sofia Patel
- 🔧 `write_file` → outputs/m3_reports/match_report_20261031_174702_t1.md

</details>

**Agent:**

**Understood the role** (rules (M2 parser + sections) extraction):

**Must-have:** Python 5+y ×1.5, Machine Learning ×1.5, Deep Learning (or PyTorch/TensorFlow) ×1.5, NLP  
**Nice-to-have:** RAG, AWS, Docker, MLOps, LLMs  
**Experience:** 5+ yrs

**Agent:**

## Shortlist for: Senior Machine Learning Engineer - Kestrel AI
**Must-have:** Python 5+y ×1.5, Machine Learning ×1.5, Deep Learning (or PyTorch/TensorFlow) ×1.5, NLP  
**Nice-to-have:** RAG, AWS, Docker, MLOps, LLMs  
**Experience:** 5+ yrs

**Funnel:** 100 resumes scored by Milestone 2 hybrid search → round 1 scores every eligible resume → top 10 deep-analysed (round 2) → round 3: STRONG HIRE: 1 · HIRE: 5 · BORDERLINE: 4

| # | Candidate | Yrs | R1 | Deep | Decision | Missing must-haves |
|---|---|---|---|---|---|---|
| 1 | Priya Tanaka (priya_tanaka) | 6 | 90.0 (#1) | **86.0** | 🟢 STRONG HIRE | - |
| 2 | Aarav Sharma (aarav_sharma) | 8 | 81.4 (#6) | **79.0** | 🟢 HIRE | - |
| 3 | Noah Reddy (noah_reddy) | 6 | 87.0 (#4) | **78.4** | 🟢 HIRE | - |
| 4 | Sofia Patel (sofia_patel) | 8 | 88.8 (#3) | **78.2** | 🟢 HIRE | - |
| 5 | Aarav Patel (aarav_patel) | 7 | 85.2 (#5) | **74.6** | 🟢 HIRE | - |
| 6 | Liam Silva (liam_silva) | 5.5 | 75.6 (#10) | **72.9** | 🟢 HIRE | - |
| 7 | Omar Rao (omar_rao) | 4.5 | 89.5 (#2) | **81.7** | 🟡 BORDERLINE | - |
| 8 | Samuel Novak (samuel_novak) | 3 | 77.7 (#8) | **79.9** | 🟡 BORDERLINE | - |
| 9 | Isabel Haddad (isabel_haddad) | 4 | 77.0 (#9) | **72.4** | 🟡 BORDERLINE | - |
| 10 | Aarav Pillai (aarav_pillai) | 4 | 79.9 (#7) | **70.9** | 🟡 BORDERLINE | - |

**Top pick: Priya Tanaka** - STRONG HIRE: covers every must-have; deep score 86.0.

Full match report saved to `outputs/m3_reports/match_report_20261031_174702_t1.md`.
_Try: "compare the top 3", "why is #1 above #2?", "make RAG a must-have", "interview questions for #1", "tell me about #4", or "done"._

## Turn 2
**User:** only Master's or higher

<details><summary>Agent reasoning & tool calls</summary>

- User intent → refine  [{'op': 'min_degree', 'value': "Master's"}]
- Refinement applied: ["Degree filter: Master's or higher"]
- Milestone 2 hybrid search (ChromaDB semantic + BM25) scored 100 resumes; top RAG hits: Sofia Patel, Aarav Pillai, Noah Reddy.
- Round 1: screened 22 resumes; top 10 = Priya Tanaka, Noah Reddy, Aarav Patel, Aarav Sharma, Isabel Haddad, Sofia Ali, Karthik Ito, Olivia Rossi, Lucas Reddy, Lucas Sato
- Round 2: deep analysis re-ordered 7 of 10 candidates.
- Round 3 decisions: {'STRONG HIRE': 1, 'HIRE': 3, 'BORDERLINE': 2, 'NO HIRE': 4}
- Report written to outputs/m3_reports/match_report_20261031_174702_t2.md.
- 🔧 `rag_search` → 100 candidates; best=Sofia Patel
- 🔧 `write_file` → outputs/m3_reports/match_report_20261031_174702_t2.md

</details>

**Agent:**

**Updating criteria and re-ranking:**
- Degree filter: Master's or higher

**Must-have:** Python 5+y ×1.5, Machine Learning ×1.5, Deep Learning (or PyTorch/TensorFlow) ×1.5, NLP  
**Nice-to-have:** RAG, AWS, Docker, MLOps, LLMs  
**Experience:** 5+ yrs | degree: Master's or higher

**Agent:**

### What changed
- Degree filter: Master's or higher

### Ranking movement
- **Aarav Patel**: #5 -> #4 (up) - score unchanged (85.2); moved because candidates around them were filtered out or re-scored
- **Isabel Haddad**: #9 -> #6 (up) - score unchanged (77.0); moved because candidates around them were filtered out or re-scored
- Filtered out by the new criteria: Sofia Patel, Liam Silva, Omar Rao, Samuel Novak, Aarav Pillai
- Moved into the top 10 because others were filtered out (scores unchanged): Sofia Ali, Olivia Rossi, Karthik Ito, Lucas Reddy, Lucas Sato

**Agent:**

## Shortlist for: Senior Machine Learning Engineer - Kestrel AI
**Must-have:** Python 5+y ×1.5, Machine Learning ×1.5, Deep Learning (or PyTorch/TensorFlow) ×1.5, NLP  
**Nice-to-have:** RAG, AWS, Docker, MLOps, LLMs  
**Experience:** 5+ yrs | degree: Master's or higher

**Funnel:** 100 resumes scored by Milestone 2 hybrid search → 22 pass filters → round 1 scores every eligible resume → top 10 deep-analysed (round 2) → round 3: STRONG HIRE: 1 · HIRE: 3 · BORDERLINE: 2 · NO HIRE: 4

| # | Candidate | Yrs | R1 | Deep | Decision | Missing must-haves |
|---|---|---|---|---|---|---|
| 1 | Priya Tanaka (priya_tanaka) | 6 | 90.0 (#1) | **86.0** | 🟢 STRONG HIRE | - |
| 2 | Aarav Sharma (aarav_sharma) | 8 | 81.4 (#4) | **79.0** | 🟢 HIRE | - |
| 3 | Noah Reddy (noah_reddy) | 6 | 87.0 (#2) | **78.4** | 🟢 HIRE | - |
| 4 | Aarav Patel (aarav_patel) | 7 | 85.2 (#3) | **74.6** | 🟢 HIRE | - |
| 5 | Sofia Ali (sofia_ali) | 3 | 69.2 (#6) | **74.9** | 🟡 BORDERLINE | - |
| 6 | Isabel Haddad (isabel_haddad) | 4 | 77.0 (#5) | **72.4** | 🟡 BORDERLINE | - |
| 7 | Olivia Rossi (olivia_rossi) | 1.5 | 59.2 (#8) | **58.4** | 🔴 NO HIRE | - |
| 8 | Karthik Ito (karthik_ito) | 2 | 62.7 (#7) | **54.4** | 🔴 NO HIRE | Deep Learning |
| 9 | Lucas Reddy (lucas_reddy) | 5.5 | 50.5 (#9) | **40.3** | 🔴 NO HIRE | Deep Learning, NLP |
| 10 | Lucas Sato (lucas_sato) | 4.5 | 43.5 (#10) | **35.5** | 🔴 NO HIRE | Deep Learning, NLP |

**Top pick: Priya Tanaka** - STRONG HIRE: covers every must-have; deep score 86.0.

Full match report saved to `outputs/m3_reports/match_report_20261031_174702_t2.md`.
_Try: "compare the top 3", "why is #1 above #2?", "make RAG a must-have", "interview questions for #1", "tell me about #4", or "done"._

## Turn 3
**User:** prioritize experience

<details><summary>Agent reasoning & tool calls</summary>

- User intent → refine  [{'op': 'weight', 'key': 'experience', 'delta': 0.15}]
- Refinement applied: ['Increased weight on experience -> 30%']
- Milestone 2 hybrid search (ChromaDB semantic + BM25) scored 100 resumes; top RAG hits: Sofia Patel, Aarav Pillai, Noah Reddy.
- Round 1: screened 22 resumes; top 10 = Priya Tanaka, Noah Reddy, Aarav Patel, Aarav Sharma, Isabel Haddad, Sofia Ali, Karthik Ito, Lucas Reddy, Olivia Rossi, Lucas Sato
- Round 2: deep analysis re-ordered 8 of 10 candidates.
- Round 3 decisions: {'STRONG HIRE': 1, 'HIRE': 3, 'BORDERLINE': 2, 'NO HIRE': 4}
- Report written to outputs/m3_reports/match_report_20261031_174702_t3.md.
- 🔧 `rag_search` → 100 candidates; best=Sofia Patel
- 🔧 `write_file` → outputs/m3_reports/match_report_20261031_174702_t3.md

</details>

**Agent:**

**Updating criteria and re-ranking:**
- Increased weight on experience -> 30%

**Must-have:** Python 5+y ×1.5, Machine Learning ×1.5, Deep Learning (or PyTorch/TensorFlow) ×1.5, NLP  
**Nice-to-have:** RAG, AWS, Docker, MLOps, LLMs  
**Experience:** 5+ yrs | degree: Master's or higher

**Agent:**

### What changed
- Increased weight on experience -> 30%

The top of the ranking is unchanged - the update didn't separate the shortlist.

**Agent:**

## Shortlist for: Senior Machine Learning Engineer - Kestrel AI
**Must-have:** Python 5+y ×1.5, Machine Learning ×1.5, Deep Learning (or PyTorch/TensorFlow) ×1.5, NLP  
**Nice-to-have:** RAG, AWS, Docker, MLOps, LLMs  
**Experience:** 5+ yrs | degree: Master's or higher

**Funnel:** 100 resumes scored by Milestone 2 hybrid search → 22 pass filters → round 1 scores every eligible resume → top 10 deep-analysed (round 2) → round 3: STRONG HIRE: 1 · HIRE: 3 · BORDERLINE: 2 · NO HIRE: 4

| # | Candidate | Yrs | R1 | Deep | Decision | Missing must-haves |
|---|---|---|---|---|---|---|
| 1 | Priya Tanaka (priya_tanaka) | 6 | 91.3 (#1) | **86.9** | 🟢 STRONG HIRE | - |
| 2 | Aarav Sharma (aarav_sharma) | 8 | 83.8 (#4) | **80.7** | 🟢 HIRE | - |
| 3 | Noah Reddy (noah_reddy) | 6 | 88.8 (#2) | **79.7** | 🟢 HIRE | - |
| 4 | Aarav Patel (aarav_patel) | 7 | 87.2 (#3) | **76.0** | 🟢 HIRE | - |
| 5 | Sofia Ali (sofia_ali) | 3 | 66.2 (#6) | **72.8** | 🟡 BORDERLINE | - |
| 6 | Isabel Haddad (isabel_haddad) | 4 | 76.3 (#5) | **71.9** | 🟡 BORDERLINE | - |
| 7 | Olivia Rossi (olivia_rossi) | 1.5 | 53.6 (#9) | **54.5** | 🔴 NO HIRE | - |
| 8 | Karthik Ito (karthik_ito) | 2 | 57.8 (#7) | **51.0** | 🔴 NO HIRE | Deep Learning |
| 9 | Lucas Reddy (lucas_reddy) | 5.5 | 56.9 (#8) | **44.8** | 🔴 NO HIRE | Deep Learning, NLP |
| 10 | Lucas Sato (lucas_sato) | 4.5 | 48.9 (#10) | **39.2** | 🔴 NO HIRE | Deep Learning, NLP |

**Top pick: Priya Tanaka** - STRONG HIRE: covers every must-have; deep score 86.9.

Full match report saved to `outputs/m3_reports/match_report_20261031_174702_t3.md`.
_Try: "compare the top 3", "why is #1 above #2?", "make RAG a must-have", "interview questions for #1", "tell me about #4", or "done"._

## Turn 4
**User:** why is #3 ranked there?

<details><summary>Agent reasoning & tool calls</summary>

- User intent → explain ['noah_reddy']
- Explained ranking for ['noah_reddy'].

</details>

**Agent:**

**Noah Reddy** is ranked **#3 of 22** (in the shortlist) with a round-1 score of **88.8**.

| Factor | Value | Points |
|---|---|---|
| must-have coverage | 0.95 | 37.0 |
| nice-to-have coverage | 0.32 | 4.2 |
| experience fit | 1.00 | 30.4 |
| RAG retrieval (M2 semantic + BM25) | 0.98 | 17.1 |

- Has must-haves: Python, Machine Learning, Deep Learning, NLP
- Nice-to-haves present: AWS, MLOps
- Experience: 6 yrs
- Round-3 decision: **HIRE** (medium confidence)

## Turn 5
**User:** any degree

<details><summary>Agent reasoning & tool calls</summary>

- User intent → refine  [{'op': 'min_degree', 'value': None}]
- Refinement applied: ['Degree filter: any degree']
- Milestone 2 hybrid search (ChromaDB semantic + BM25) scored 100 resumes; top RAG hits: Sofia Patel, Aarav Pillai, Noah Reddy.
- Round 1: screened 100 resumes; top 10 = Priya Tanaka, Sofia Patel, Omar Rao, Noah Reddy, Aarav Patel, Aarav Sharma, Aarav Pillai, Liam Silva, Isabel Haddad, Samuel Novak
- Round 2: deep analysis re-ordered 6 of 10 candidates.
- Round 3 decisions: {'STRONG HIRE': 1, 'HIRE': 5, 'BORDERLINE': 4}
- Report written to outputs/m3_reports/match_report_20261031_174702_t4.md.
- 🔧 `rag_search` → 100 candidates; best=Sofia Patel
- 🔧 `write_file` → outputs/m3_reports/match_report_20261031_174702_t4.md

</details>

**Agent:**

**Updating criteria and re-ranking:**
- Degree filter: any degree

**Must-have:** Python 5+y ×1.5, Machine Learning ×1.5, Deep Learning (or PyTorch/TensorFlow) ×1.5, NLP  
**Nice-to-have:** RAG, AWS, Docker, MLOps, LLMs  
**Experience:** 5+ yrs

**Agent:**

### What changed
- Degree filter: any degree

### Ranking movement
- **Sofia Patel**: NEW at #4 - newly eligible under the new criteria
- **Aarav Patel**: #4 -> #5 (down) - score unchanged (87.2); moved because candidates around them were filtered out or re-scored
- **Liam Silva**: NEW at #6 - newly eligible under the new criteria
- **Omar Rao**: NEW at #7 - newly eligible under the new criteria
- **Samuel Novak**: NEW at #8 - newly eligible under the new criteria
- **Isabel Haddad**: #6 -> #9 (down) - score unchanged (76.3); moved because candidates around them were filtered out or re-scored
- **Aarav Pillai**: NEW at #10 - newly eligible under the new criteria
- **Sofia Ali**: #5 -> dropped out - score unchanged (66.2); moved because candidates around them were filtered out or re-scored
- **Olivia Rossi**: #7 -> dropped out - score unchanged (53.6); moved because candidates around them were filtered out or re-scored
- **Karthik Ito**: #8 -> dropped out - score unchanged (57.8); moved because candidates around them were filtered out or re-scored
- **Lucas Reddy**: #9 -> dropped out - score unchanged (56.9); moved because candidates around them were filtered out or re-scored
- **Lucas Sato**: #10 -> dropped out - score unchanged (48.9); moved because candidates around them were filtered out or re-scored

**Agent:**

## Shortlist for: Senior Machine Learning Engineer - Kestrel AI
**Must-have:** Python 5+y ×1.5, Machine Learning ×1.5, Deep Learning (or PyTorch/TensorFlow) ×1.5, NLP  
**Nice-to-have:** RAG, AWS, Docker, MLOps, LLMs  
**Experience:** 5+ yrs

**Funnel:** 100 resumes scored by Milestone 2 hybrid search → round 1 scores every eligible resume → top 10 deep-analysed (round 2) → round 3: STRONG HIRE: 1 · HIRE: 5 · BORDERLINE: 4

| # | Candidate | Yrs | R1 | Deep | Decision | Missing must-haves |
|---|---|---|---|---|---|---|
| 1 | Priya Tanaka (priya_tanaka) | 6 | 91.3 (#1) | **86.9** | 🟢 STRONG HIRE | - |
| 2 | Aarav Sharma (aarav_sharma) | 8 | 83.8 (#6) | **80.7** | 🟢 HIRE | - |
| 3 | Noah Reddy (noah_reddy) | 6 | 88.8 (#4) | **79.7** | 🟢 HIRE | - |
| 4 | Sofia Patel (sofia_patel) | 8 | 90.3 (#2) | **79.2** | 🟢 HIRE | - |
| 5 | Aarav Patel (aarav_patel) | 7 | 87.2 (#5) | **76.0** | 🟢 HIRE | - |
| 6 | Liam Silva (liam_silva) | 5.5 | 78.8 (#8) | **75.2** | 🟢 HIRE | - |
| 7 | Omar Rao (omar_rao) | 4.5 | 89.0 (#3) | **81.3** | 🟡 BORDERLINE | - |
| 8 | Samuel Novak (samuel_novak) | 3 | 73.6 (#10) | **77.0** | 🟡 BORDERLINE | - |
| 9 | Isabel Haddad (isabel_haddad) | 4 | 76.3 (#9) | **71.9** | 🟡 BORDERLINE | - |
| 10 | Aarav Pillai (aarav_pillai) | 4 | 78.8 (#7) | **70.2** | 🟡 BORDERLINE | - |

**Top pick: Priya Tanaka** - STRONG HIRE: covers every must-have; deep score 86.9.

Full match report saved to `outputs/m3_reports/match_report_20261031_174702_t4.md`.
_Try: "compare the top 3", "why is #1 above #2?", "make RAG a must-have", "interview questions for #1", "tell me about #4", or "done"._

## Turn 6
**User:** done

<details><summary>Agent reasoning & tool calls</summary>

- User intent → end

</details>

_Conversation ended (graph reached END)._