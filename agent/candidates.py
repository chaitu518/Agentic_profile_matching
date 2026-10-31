"""Candidate profiles = Milestone 1 file reading + Milestone 2 metadata + role parsing for evidence.

* text      <- milestone1.fs_tools.read_file (PDF / DOCX / TXT)
* metadata  <- api.metadata.extract_metadata (name, title, skills, experience years from merged date
               ranges, per-skill years, highest degree)
* sections  <- api.chunker.split_sections (header variants -> canonical sections)
* roles     <- parsed here so every match can quote the bullet that proves it
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path

from api.chunker import split_sections
from api.metadata import _RANGE_RE, extract_metadata
from milestone1.fs_tools import read_file

from agent import config
from agent.skills import find_skills

SENIOR_WORDS = re.compile(r"\b(senior|lead|principal|staff|architect|head|sde ?(?:2|ii|3|iii))\b", re.I)
LEADERSHIP_WORDS = re.compile(r"\b(led|mentored|owned|designed|architected|drove|spearheaded)\b", re.I)
METRIC_RE = re.compile(r"\d+(?:\.\d+)?\s*(?:%|k\b|m\b|x\b|\+)|\b\d{2,}\b", re.I)
DEGREE_RANK = {"Unknown": 0, "Diploma": 1, "Bachelor's": 2, "Master's": 3, "PhD": 4}


@dataclass
class Role:
    title: str
    company: str
    dates: str
    bullets: list[str] = field(default_factory=list)


@dataclass
class Candidate:
    candidate_id: str            # file stem, e.g. "john_mathew"
    name: str
    resume_path: str             # repo-relative, same key Milestone 2 uses
    title: str = ""
    email: str = ""
    summary: str = ""
    years_experience: float = 0.0
    skill_years: dict[str, float] = field(default_factory=dict)
    skills: list[str] = field(default_factory=list)       # declared in the skills section
    text_skills: list[str] = field(default_factory=list)  # mentioned anywhere
    roles: list[Role] = field(default_factory=list)
    projects: list[str] = field(default_factory=list)
    highest_degree: str = "Unknown"
    education: str = ""
    certifications: list[str] = field(default_factory=list)

    @property
    def current_title(self) -> str:
        return self.roles[0].title if self.roles else self.title

    @property
    def experience_text(self) -> str:
        return "\n".join([*(f"{r.title}\n" + "\n".join(r.bullets) for r in self.roles), *self.projects])

    @property
    def current_role_text(self) -> str:
        return f"{self.roles[0].title}\n" + "\n".join(self.roles[0].bullets) if self.roles else ""

    def to_dict(self) -> dict:
        return asdict(self)


def normalise(text: str) -> str:
    """Same whitespace normalisation as Milestone 2's api/file_tools.read_file."""
    lines = [" ".join(line.split()) for line in text.replace("\r", "\n").split("\n")]
    text = "\n".join(lines)
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text.strip()


def parse_roles(exp: str) -> list[Role]:
    """'Title - Company' line, then a date-range line, then '- bullet' lines (PDF wraps are re-joined)."""
    lines = [ln.strip() for ln in exp.split("\n")]
    roles: list[Role] = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        date_here = _RANGE_RE.search(ln)
        if ln and not ln.startswith(("-", "•")) and (_RANGE_RE.match(nxt) or (date_here and date_here.start() > 0)):
            head = ln if not date_here else ln[:date_here.start()].strip(" |,-")
            title, _, company = head.rpartition(" - ") if " - " in head else (head, "", "")
            dates = nxt if not date_here else date_here.group(0)
            roles.append(Role(title.strip() or head, company.strip(), dates))
            i += 1 if date_here else 2
            continue
        if roles and ln.startswith(("-", "•")):
            roles[-1].bullets.append(ln.lstrip("-• ").strip())
        elif roles and ln and roles[-1].bullets and not _RANGE_RE.match(ln):
            roles[-1].bullets[-1] += " " + ln          # wrapped PDF line
        i += 1
    return roles


def _bullets(body: str) -> list[str]:
    out: list[str] = []
    for ln in body.split("\n"):
        ln = ln.strip()
        if ln.startswith(("-", "•")):
            out.append(ln.lstrip("-• ").strip())
        elif ln and out:
            out[-1] += " " + ln
        elif ln:
            out.append(ln)
    return out


def build_candidate(path: str | Path) -> Candidate:
    path = Path(path)
    res = read_file(str(path))                                   # Milestone 1 tool
    if not res.get("success"):
        raise ValueError(res.get("error"))
    text = normalise(res["content"])
    rel = path.resolve().relative_to(config.ROOT).as_posix() if path.resolve().is_relative_to(config.ROOT) else str(path)
    meta = extract_metadata(text, rel)                           # Milestone 2 metadata
    sections = dict(split_sections(text))                        # Milestone 2 section detection
    return Candidate(
        candidate_id=path.stem,
        name=meta["candidate_name"],
        resume_path=rel,
        title=meta.get("current_title", ""),
        email=meta.get("email", ""),
        summary=" ".join(sections.get("summary", "").split()),
        years_experience=float(meta["experience_years"]),
        skill_years=meta.get("skill_years", {}),
        skills=find_skills(sections.get("skills", "")),
        text_skills=find_skills(text),
        roles=parse_roles(sections.get("experience", "")),
        projects=_bullets(sections.get("projects", "")),
        highest_degree=meta.get("highest_degree", "Unknown"),
        education=meta.get("education_summary", ""),
        certifications=_bullets(sections.get("certifications", "")),
    )


@lru_cache(maxsize=4)
def load_corpus(resume_dir: str | None = None) -> dict[str, Candidate]:
    d = Path(resume_dir or config.RESUME_DIR)
    out: dict[str, Candidate] = {}
    for p in sorted(d.iterdir()):
        if p.suffix.lower() in (".pdf", ".docx", ".txt"):
            try:
                c = build_candidate(p)
                out[c.candidate_id] = c
            except Exception as e:  # keep going on one bad file, like M2's loader
                print(f"[candidates] skipped {p.name}: {e}")
    return out


def seniority_signals(c: Candidate) -> dict:
    exp = c.experience_text
    return {
        "senior_title": bool(SENIOR_WORDS.search(c.current_title)),
        "leadership_bullets": len(LEADERSHIP_WORDS.findall(exp)) + len(LEADERSHIP_WORDS.findall(c.summary)),
        "quantified_impact": sum(1 for r in c.roles for b in r.bullets if METRIC_RE.search(b)),
        "num_roles": len(c.roles),
    }
