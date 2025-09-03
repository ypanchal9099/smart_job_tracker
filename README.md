# Smart Job Tracker & Resume Matcher (NLP)

A web app built with Flask + NLP to compare your resume with job descriptions and generate a match score.
It highlights matched & missing skills to help you tailor your resume for each role.

## Features
- Upload resume (PDF/DOCX/TXT) or paste text
- Paste job description
- NLP similarity (TF-IDF cosine) + skill overlap
- Shows matched & missing skills
- Stores jobs in SQLite
- Bootstrap UI

## Run locally
```bash
[git clone https://github.com/ypanchal9099/smart_job_tracker.git]
cd smart_job_tracker
python -m venv .venv
. .venv\Scripts\activate   # Windows
# or: source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
python app.py
