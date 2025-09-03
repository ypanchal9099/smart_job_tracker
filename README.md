# Smart Job Tracker & Resume Matcher (NLP)

A web app built with Flask + NLP to compare your resume with job descriptions and generate a match score.
It highlights matched & missing skills to help you tailor your resume for each role.

## Features
- Upload your resume (PDF/DOCX/TXT) or paste text
- Paste job description
- NLP-based similarity using TF-IDF cosine
- Extracts skills from a customizable data/skills.csv
- Shows Match Score (0–100), Matched Skills, and Missing Skills
- Saves jobs with company, role, and location in the SQLite database
- Clean Bootstrap UI


##Future Improvements

🔑 User authentication (login/register)

📊 Analytics dashboard (track scores over time, most common missing skills)

📤 Export jobs & scores as CSV

✨ Auto-suggest resume bullet points for missing skills

## Run locally
```bash
[git clone https://github.com/ypanchal9099/smart_job_tracker.git]
cd smart_job_tracker
python -m venv .venv
. .venv\Scripts\activate   # Windows
# or: source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
python app.py
