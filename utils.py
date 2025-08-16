import os
import re
import logging
import docx2txt
from typing import Dict, List, Tuple, Any

# Silence verbose pdfminer logging (this fixes the console spam)
for _name in [
    "pdfminer", "pdfminer.pdfparser", "pdfminer.pdfdocument", "pdfminer.pdfpage",
    "pdfminer.pdfinterp", "pdfminer.converter", "pdfminer.layout"
]:
    logging.getLogger(_name).setLevel(logging.WARNING)

# pdf -> text (import after silencing to be safe)
from pdfminer.high_level import extract_text

# Resume parsing (your old project)
from pyresparser import ResumeParser

# Optional semantic
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    _SEM_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
except Exception:
    _SEM_MODEL = None
    np = None


# ------------------
# Helpers / Dictionaries
# ------------------

# Canonical UI/UX + general skills we care about; add more as needed
KNOWN_SKILLS = {
    # UI/UX
    "ui", "ux", "ui ux", "user interface", "user experience",
    "wireframe", "wireframing", "prototyping", "prototype",
    "figma", "adobe xd", "adobexd", "sketch", "zeplin",
    "photoshop", "illustrator", "invision",

    # web/dev — helpful for general resumes
    "html", "css", "html css", "javascript", "react", "angular", "node", "django", "flask",

    # data — helpful for general resumes
    "python", "tensorflow", "pytorch", "opencv", "pandas", "numpy", "docker", "aws",
}

# Degree mapping
DEGREE_MAP = {
    "phd": 3,
    "doctor": 3,
    "masters": 2, "master": 2, "m.s": 2, "m.s.": 2, "mtech": 2, "m.tech": 2, "msc": 2, "m.sc": 2, "mca": 2,
    "bachelors": 1, "bachelor": 1, "b.e": 1, "b.tech": 1, "btech": 1, "bs": 1, "b.s.": 1,
    "b.des": 1, "bdes": 1, "hci": 1, "design": 1,
}

# Aliases → canonical form
ALIASES = {
    "adobe xd": "adobe_xd",
    "adobexd": "adobe_xd",
    "html/css": "html css",
    "react js": "react",
    "node js": "node",
    "c#": "csharp",
    "ui/ux": "ui ux",
    "ux/ui": "ui ux",
    "wireframes": "wireframing",
    "wireframe": "wireframing",
    "prototype": "prototyping",
    "user interface": "ui",
    "user experience": "ux",
}


# ------------------
# I/O
# ------------------

def extract_text_from_any(path: str) -> str:
    """Extract plain text from .txt, .docx, .pdf (pdfminer) or fallback to reading file."""
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".txt":
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        if ext == ".docx":
            return docx2txt.process(path) or ""
        if ext == ".pdf":
            # pdfminer.six extract_text; pdfminer loggers are silenced above
            return extract_text(path) or ""
        # default
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


# ------------------
# Resume parsing
# ------------------

def parse_resume_with_pyresparser(resume_path: str) -> Dict[str, Any]:
    """
    Parse resume via PyResparser, with fallbacks:
      - if skills missing, scan text against KNOWN_SKILLS
      - experience fallback: scan "X years" and year ranges
      - degrees normalized
      - raw_text included for additional fallbacks
    """
    data = ResumeParser(resume_path).get_extracted_data() or {}

    # normalize containers
    data["skills"] = data.get("skills") or []
    data["degree"] = data.get("degree") or []
    data["experience"] = data.get("experience") or []

    # raw text for fallback scans
    raw_text = extract_text_from_any(resume_path) or ""
    data["raw_text"] = raw_text

    # ---------------- skills fallback ----------------
    # If pyresparser didn't find skills, do a conservative phrase scan
    if not data["skills"]:
        found = detect_skills_in_text(raw_text, list(KNOWN_SKILLS))
        data["skills"] = sorted(set(found))

    # ---------------- degrees normalize ----------------
    if not data.get("degree"):
        data["degree"] = detect_degrees_in_text(raw_text)

    # ---------------- experience fallback ----------------
    if not isinstance(data.get("total_experience"), (int, float)):
        data["total_experience"] = extract_years_experience(raw_text, data.get("experience") or [])

    return data


def detect_skills_in_text(text: str, skill_list: List[str]) -> List[str]:
    """Find occurrences of known skills in free text (word-boundary aware)."""
    hits: List[str] = []
    # normalize separators so "Adobe XD" and "Adobe/XD" are matched
    lower = " " + re.sub(r"[/|]", " ", text.lower()) + " "
    for s in skill_list:
        s_low = s.lower()
        pat = r"\b" + re.escape(s_low) + r"\b"
        if re.search(pat, lower):
            hits.append(s_low)
        else:
            # also try alias variant (like "adobe_xd" vs "adobe xd")
            alias = ALIASES.get(s_low, None)
            if alias and re.search(r"\b" + re.escape(alias.replace("_", " ")) + r"\b", lower):
                hits.append(alias)
    return normalize_skills(hits)


def detect_degrees_in_text(text: str) -> List[str]:
    toks = []
    lower = text.lower()
    for k in DEGREE_MAP.keys():
        if k in lower:
            toks.append(k)
    return sorted(set(toks))


def extract_years_experience(resume_text: str, exp_sections: List[str]) -> float:
    """
    Heuristics for experience:
      - explicit "X years" mentions (take max)
      - year ranges like '2017-2020' or 'Jan 2018 - Present' (sum distinct ranges)
      - clamp to reasonable max
    """
    resume_text = (resume_text or "").lower()
    # 1) explicit "X years"
    years_f = []
    for m in re.findall(r'(\d+(?:\.\d+)?)\s*(?:years|yrs)', resume_text):
        try:
            years_f.append(float(m))
        except Exception:
            pass

    best = max(years_f) if years_f else 0.0

    # 2) year ranges
    total_years = 0.0
    ranges = re.findall(
        r'(?P<y1>19\d{2}|20\d{2})\s*[-–]\s*(?P<y2>19\d{2}|20\d{2}|present|current|now)',
        resume_text, flags=re.IGNORECASE
    )
    used = set()
    for y1, y2 in ranges:
        if (y1, y2) in used:
            continue
        used.add((y1, y2))
        try:
            start = int(y1)
            if re.match(r'present|current|now', y2, flags=re.I):
                end = 2025
            else:
                end = int(y2)
            if 1980 <= start <= 2035 and 1980 <= end <= 2035 and end >= start:
                total_years += (end - start)
        except Exception:
            pass

    best = max(best, min(total_years, 40.0))
    return round(best, 1)


# ------------------
# JD parsing
# ------------------

def parse_job_description(jd_text: str) -> Dict[str, Any]:
    text = jd_text.strip()
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    lower = text.lower()

    # ---- job title
    job_title = ""
    for l in lines:
        if l.lower().startswith("role:"):
            job_title = l.split(":", 1)[1].strip()
            break
    if not job_title and lines:
        job_title = lines[0][:120]

    # ---- min years exp
    exp_matches = re.findall(r'(\d+)\s*\+?\s*(?:years|yrs)', lower)
    min_years = max([int(x) for x in exp_matches], default=0) if exp_matches else 0

    # ---- skills
    skill_candidates: List[str] = []

    # A) extract from lines likely to contain required skills
    for l in lines:
        low = l.lower()
        if any(k in low for k in ["required", "requirements", "skills", "key skills", "tech stack", "proficient in"]):
            # split on bullets/commas/dashes
            parts = re.split(r'[•\-\u2022,]', l)
            for p in parts:
                p = p.strip(" -•—:;().").lower()
                if not p or p.startswith(("required", "skills", "requirements", "role")):
                    continue
                if re.search(r'\d+\+?\s*(years|yrs)', p):  # ignore experience mentions
                    continue
                skill_candidates.append(p)

    # B) fallback: scan entire text against known skills
    if not skill_candidates:
        # detect_skills_in_text returns normalized skills
        found = detect_skills_in_text(lower, list(KNOWN_SKILLS))
        skill_candidates = found

    skills = normalize_skills(skill_candidates)

    # ---- education tokens
    edu_tokens = []
    for key in DEGREE_MAP.keys():
        if key in lower:
            edu_tokens.append(key)
    edu_tokens = list(sorted(set(edu_tokens)))

    return {
        "job_title": job_title,
        "min_years_experience": min_years,
        "skills": skills,
        "education": edu_tokens,
    }


# ------------------
# Scoring utilities
# ------------------

def normalize_skills(skills: List[str]) -> List[str]:
    normed: List[str] = []
    for s in skills:
        s = s.strip().lower()
        if not s:
            continue
        s = s.replace("/", " ")
        s = re.sub(r'\s+', ' ', s)
        s = ALIASES.get(s, s)

        # expand compound "ui ux" to both ui and ux
        if s in {"ui ux", "ux ui"}:
            normed.extend(["ui", "ux"])
        else:
            normed.append(s)

    # remove experience-like phrases
    cleaned = []
    for s in normed:
        if re.search(r'\d+\+?\s*(years|yrs)', s):
            continue
        cleaned.append(s)

    # de-duplicate and restrict to safe token characters
    final = []
    for s in sorted(set(cleaned)):
        if re.match(r'^[a-z0-9_][a-z0-9_ ]{0,50}$', s):
            final.append(s)
    return final


def jaccard_coverage(jd_skills: List[str], res_skills: List[str]) -> Tuple[float, List[str], List[str]]:
    jd_set = set(jd_skills)
    res_set = set(res_skills)
    if not jd_set:
        return 100.0, [], []  # no required skills -> treat as not penalized
    inter = jd_set & res_set
    missing = jd_set - res_set
    score = (len(inter) / len(jd_set)) * 100.0
    return score, sorted(inter), sorted(missing)


def semantic_coverage(jd_skills: List[str], res_skills: List[str], threshold: float = 0.75):
    if _SEM_MODEL is None or np is None or not jd_skills:
        return jaccard_coverage(jd_skills, res_skills)

    jd_emb = _SEM_MODEL.encode(jd_skills, normalize_embeddings=True)
    res_emb = _SEM_MODEL.encode(res_skills, normalize_embeddings=True)

    matched = set()
    for i, jv in enumerate(jd_emb):
        sims = np.dot(res_emb, jv)
        j = int(np.argmax(sims))
        if sims[j] >= threshold:
            matched.add(jd_skills[i])

    coverage = (len(matched) / len(jd_skills)) * 100.0 if jd_skills else 100.0
    missing = sorted(set(jd_skills) - matched)
    return coverage, sorted(matched), missing


def resume_degrees_level(resume_data: Dict[str, Any]) -> Tuple[int, List[str]]:
    degrees = [d.lower() for d in (resume_data.get("degree") or [])]
    max_level = 0
    hits = []
    for d in degrees:
        for key, lvl in DEGREE_MAP.items():
            if key in d:
                max_level = max(max_level, lvl)
                hits.append(key)
    return max_level, list(sorted(set(hits)))


def education_required_level(jd: Dict[str, Any]) -> int:
    tokens = jd.get("education") or []
    lvl = 0
    for t in tokens:
        lvl = max(lvl, DEGREE_MAP.get(t, 0))
    return lvl


def compute_scores(resume_data: Dict[str, Any], jd: Dict[str, Any], use_semantic: bool = True):
    # normalize skills
    resume_skills_raw = [s.strip().lower() for s in (resume_data.get("skills") or [])]
    resume_skills_norm = normalize_skills(resume_skills_raw)

    # JD skills normalized
    jd_skills = normalize_skills(jd.get("skills") or [])

    # If JD skills exist but resume is missing some, check raw_text fallback
    raw_text = (resume_data.get("raw_text") or "").lower()
    if jd_skills and raw_text:
        # for any jd skill not in resume_skills_norm, try to find in raw_text (flexible)
        for skill in jd_skills:
            if skill not in resume_skills_norm:
                skill_space = skill.replace("_", " ")
                if (re.search(r"\b" + re.escape(skill) + r"\b", raw_text)
                        or re.search(r"\b" + re.escape(skill_space) + r"\b", raw_text)
                        or re.search(r"\b" + re.escape(skill_space.rstrip("ing")) + r"\b", raw_text)
                        or re.search(r"\b" + re.escape(skill_space.rstrip("s")) + r"\b", raw_text)):
                    resume_skills_norm.append(skill)
        # de-dupe & normalize again
        resume_skills_norm = normalize_skills(resume_skills_norm)

    # skills score (hybrid: take better of exact Jaccard and semantic)
    jac_score, jac_match, jac_missing = jaccard_coverage(jd_skills, resume_skills_norm)
    sem_score, sem_match, sem_missing = semantic_coverage(jd_skills, resume_skills_norm) if use_semantic else (0.0, [], [])

    if sem_score > jac_score:
        skills_score = sem_score
        skills_matched = sem_match
        skills_missing = sem_missing
        method = "semantic" if _SEM_MODEL is not None else "exact"
    else:
        skills_score = jac_score
        skills_matched = jac_match
        skills_missing = jac_missing
        method = "exact"

    # experience score
    jd_min = jd.get("min_years_experience") or 0
    res_years = resume_data.get("total_experience")
    try:
        res_years = float(res_years)
    except Exception:
        res_years = 0.0

    if jd_min <= 0:
        experience_score = 100.0 if res_years > 0 else 0.0
    else:
        experience_score = min(100.0, (res_years / jd_min) * 100.0)

    # education score
    req_lvl = education_required_level(jd)
    res_lvl, res_degrees_hits = resume_degrees_level(resume_data)
    if req_lvl == 0:
        education_score = 100.0 if res_lvl > 0 else 0.0
    else:
        if res_lvl >= req_lvl:
            education_score = 100.0
        elif res_lvl == req_lvl - 1:
            education_score = 60.0
        else:
            education_score = 30.0

    # overall (weights: Skills 50%, Exp 30%, Edu 20%)
    overall = 0.5 * skills_score + 0.3 * experience_score + 0.2 * education_score

    return (
        {
            "skills": skills_score,
            "experience": experience_score,
            "education": education_score,
            "overall": overall,
        },
        {
            "resume_skills_norm": resume_skills_norm,
            "skills_matched": skills_matched,
            "skills_missing": skills_missing,
            "resume_years_experience": round(res_years, 2),
            "resume_degrees": res_degrees_hits,
            "used_semantic": (method == "semantic"),
        }
    )
