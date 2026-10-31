"""Build the 100-resume corpus for Milestone 3 ("top 10 from 100 resumes").

    python scripts/build_m3_corpus.py

* copies the 36 Milestone 2 resumes from data/resumes/ (unchanged, so M2's evaluation still holds),
* generates 62 more with the Milestone 2 generator (api/generate_dataset.py: same families, header
  variants, synonym noise and PDF/DOCX/TXT mix), seeded separately so it is reproducible,
* adds 2 hand-written frontend resumes (John Mathew, Jane Cooper) used in the assignment's example
  question "Why did John rank higher than Jane?",
* writes graded relevance labels for all 100 against the 6 M2 job descriptions -> data/ground_truth_m3.json.
"""
from __future__ import annotations

import json
import random
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import api.generate_dataset as gd  # noqa: E402  (Milestone 2 generator, reused as-is)

SRC = ROOT / "data" / "resumes"
DST = ROOT / "data" / "resumes_m3"

EXTRA_FAMILIES = {"frontend": 10, "java_backend": 9, "ml_engineer": 9, "python_backend": 7, "data_engineer": 7,
                  "devops": 7, "mobile": 5, "qa": 4, "data_analyst": 4}          # 62 generated
YEARS_CYCLE = [1.5, 4.5, 7, 2.5, 5.5, 3.5, 9, 3, 6, 2, 4, 8]

HANDWRITTEN = {
    "john_mathew.txt": ("frontend", 6.1, """John Mathew
Senior Frontend Engineer
john.mathew@example.com | +1-555-201-4410 | linkedin.com/in/john

Professional Summary
Senior Frontend Engineer with 6+ years building fast, accessible web apps in React, TypeScript and Next.js. Led the design-system team and mentored four engineers.

Work Experience
Senior Frontend Engineer - Pixelcraft Studios
Oct 2022 - Present
- Led the migration of the customer dashboard to Next.js and React, cutting time-to-interactive by 45%
- Built a TypeScript component library and design system used by 6 product teams
- Introduced Cypress and Jest test suites, raising coverage from 30% to 85%

Frontend Engineer - Vertex Payments
Sep 2020 - Sep 2022
- Built checkout flows in React and Redux handling 1M+ payments per month
- Optimised bundle size with code splitting and lazy loading, reducing load time by 38%
- Worked with backend teams on GraphQL and REST API contracts

Technical Skills
React, TypeScript, JavaScript (ES6+), Next.js, Redux, HTML5, CSS3, Tailwind, GraphQL, Jest, Cypress, AWS

Education
B.Tech in Computer Science, BITS Pilani (2020)

Certifications
- Meta Front-End Developer Professional Certificate
"""),
    "jane_cooper.txt": ("frontend", 2.8, """Jane Cooper
Frontend Developer
jane.cooper@example.com | +1-555-418-2093 | linkedin.com/in/jane

Profile
Frontend developer with 2+ years building responsive, accessible interfaces with React and JavaScript. Passionate about accessibility and testing.

Experience
Frontend Developer - Orbital Retail
Apr 2024 - Present
- Built product listing and cart pages in React and JavaScript for 300k monthly shoppers
- Improved accessibility to WCAG 2.1 AA across the storefront, fixing 120+ audit issues
- Wrote Cypress end-to-end tests for the checkout journey

Web Development Intern - Aurora Media
Jan 2024 - Mar 2024
- Built marketing pages with HTML, CSS and Tailwind

Skills
React, JavaScript, HTML, CSS, Tailwind, Cypress, Storybook, Figma

Education
B.Sc in Computer Science, University of Lagos (2023)
"""),
}


def main() -> None:
    if DST.exists():
        shutil.rmtree(DST)
    DST.mkdir(parents=True)
    gt_m2 = json.loads((ROOT / "data" / "ground_truth.json").read_text())

    truth: dict[str, dict] = {}
    for p in sorted(SRC.iterdir()):
        shutil.copy2(p, DST / p.name)
        c = gt_m2["candidates"][f"data/resumes/{p.name}"]
        truth[f"data/resumes_m3/{p.name}"] = {"name": c["name"], "family": c["family"], "years": c["years"],
                                              "source": "milestone2"}

    gd.rng = random.Random(2026)          # the M2 generator reads this module-level rng
    used = {v["name"] for v in truth.values()} | {"John Mathew", "Jane Cooper"}
    pairs = [(f, l) for f in gd.FIRST for l in gd.LAST]
    gd.rng.shuffle(pairs)
    roster = [fam for fam, n in EXTRA_FAMILIES.items() for _ in range(n)]
    for i, family in enumerate(roster):
        years = YEARS_CYCLE[i % len(YEARS_CYCLE)]
        r = gd.make_resume(i % len(gd.FIRST), family, years)
        first, last = next(p for p in pairs if f"{p[0]} {p[1]}" not in used)
        name = f"{first} {last}"
        used.add(name)
        r["name"], r["id"] = name, name.lower().replace(" ", "_")
        email = f"{first.lower()}.{last.lower()}@example.com"
        r["header"] = [name, r["header"][1], r["header"][2].replace(r["header"][2].split(" | ")[0], email)
                       .replace(r["header"][2].split("/in/")[-1], first.lower())]
        fmt = ["pdf", "pdf", "docx", "txt"][i % 4]
        path = DST / f"{r['id']}.{fmt}"
        {"pdf": gd.write_pdf, "docx": gd.write_docx}.get(fmt, lambda rr, pp: pp.write_text(gd.to_text(rr)))(r, path)
        truth[f"data/resumes_m3/{path.name}"] = {"name": name, "family": family, "years": years, "source": "generated"}

    for fname, (family, years, text) in HANDWRITTEN.items():
        (DST / fname).write_text(text, encoding="utf-8")
        truth[f"data/resumes_m3/{fname}"] = {"name": text.split("\n")[0], "family": family, "years": years,
                                             "source": "handwritten"}

    gt = {"reference_date": gt_m2["reference_date"], "candidates": truth, "job_descriptions": {}}
    for jd in gd.JOB_DESCRIPTIONS:
        rel = {p: gd.relevance(c, jd) for p, c in truth.items() if gd.relevance(c, jd) > 0}
        gt["job_descriptions"][jd["id"]] = {"path": f"data/job_descriptions/{jd['id']}.txt", "family": jd["family"],
                                            "min_years": jd["min_years"], "relevance": rel}
    (ROOT / "data" / "ground_truth_m3.json").write_text(json.dumps(gt, indent=2))
    fmts: dict[str, int] = {}
    for p in DST.iterdir():
        fmts[p.suffix] = fmts.get(p.suffix, 0) + 1
    print(f"Wrote {len(truth)} resumes to {DST.relative_to(ROOT)} {fmts} + data/ground_truth_m3.json")


if __name__ == "__main__":
    main()
