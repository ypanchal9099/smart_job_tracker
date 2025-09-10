import io, re
from typing import Tuple, List
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from pdfminer.high_level import extract_text as pdf_extract_text
from docx import Document

SKILLS_PATH = "data/skills.csv"

def normalize_text(t: str) -> str:
    t = t.lower()
    t = re.sub(r"\s+", " ", t)
    return t

def extract_text_from_file(file_storage) -> str:
    filename = file_storage.filename.lower()
    data = file_storage.read()
    if filename.endswith(".pdf"):
        text = pdf_extract_text(io.BytesIO(data))
        return normalize_text(text)
    elif filename.endswith(".docx"):
        doc = Document(io.BytesIO(data))
        text = "\n".join(p.text for p in doc.paragraphs)
        return normalize_text(text)
    elif filename.endswith(".txt"):
        return normalize_text(data.decode("utf-8", errors="ignore"))
    else:
        raise ValueError("Unsupported file type. Use PDF, DOCX, or TXT.")

def load_skills() -> List[str]:
    df = pd.read_csv(SKILLS_PATH)
    skills = [str(s).strip().lower() for s in df.iloc[:,0].dropna().tolist()]
    return sorted(list(set(skills)), key=len, reverse=True)

def extract_skills_list(text: str) -> List[str]:
    skills = load_skills()
    found = []
    for s in skills:
        pattern = r"(?<![a-z0-9])" + re.escape(s) + r"(?![a-z0-9])"
        if re.search(pattern, text):
            found.append(s)
    return sorted(list(set(found)))

def compute_match_score(resume_text: str, jd_text: str) -> Tuple[float, list, list]:
    resume_text = normalize_text(resume_text)
    jd_text = normalize_text(jd_text)

    # NLP similarity
    vec = TfidfVectorizer(stop_words="english", max_features=5000)
    X = vec.fit_transform([resume_text, jd_text])
    sim = cosine_similarity(X[0:1], X[1:2])[0][0]  # 0..1

    # Skill overlap
    r_skills = set(extract_skills_list(resume_text))
    j_skills = set(extract_skills_list(jd_text))
    matched = sorted(r_skills & j_skills)
    missing = sorted(j_skills - r_skills)

    coverage = (len(matched) / max(1, len(j_skills))) if j_skills else 1.0
    score = (0.7 * sim + 0.3 * coverage) * 100.0
    return float(score), matched, missing
