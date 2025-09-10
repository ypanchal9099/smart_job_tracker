# 📌 Smart Job Tracker & Resume Matcher (NLP)

A Flask web app that compares your **resume** with **job descriptions** and gives a **match score** with skills insights.  
Now enhanced with **Login/Logout**, **Resume Bullet Generator**, **Job Description uploads**, and **Analytics dashboards** 🎉

## 🚀 Features
- 📄 Upload your resume (**PDF/DOCX/TXT**) or paste text
- 📝 Paste job descriptions **or upload JD files**
- 🤖 **NLP similarity** (TF-IDF cosine) + skill extraction
- 🎯 Shows **Match Score (0–100)**, **Matched Skills**, and **Missing Skills**
- 🗂 Save jobs with status (**Interested, Applied, Interview, Offer, Rejected**) and notes
- ✍️ **Resume Bullet Generator**: get tailored bullet point suggestions for missing skills
- 📊 **Analytics page** with Chart.js:
  - Match score distribution
  - Top missing skills
- 🔑 **Authentication**: Login & Register so each user’s resumes/jobs are private
- 💾 CSV export of all saved jobs

## 🛠️ Tech Stack
![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)
![SQLite](https://img.shields.io/badge/SQLite-DB-lightblue?logo=sqlite)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-orange?logo=scikitlearn)
![Bootstrap](https://img.shields.io/badge/Bootstrap-UI-purple?logo=bootstrap)
![Chart.js](https://img.shields.io/badge/Chart.js-Charts-red?logo=chartdotjs)

## 🌍 Deployment

Deploy easily on Render
 or Railway
.

- Build Command: pip install -r requirements.txt
- Start Command: python app.py
- Add env var: SECRET_KEY=your-secret

## Future Improvements

- User authentication (login/register)
- Analytics dashboard (track scores over time, most common missing skills)
- Export jobs & scores as CSV
- Auto-suggest resume bullet points for missing skills

## Run locally
```bash
[git clone https://github.com/ypanchal9099/smart_job_tracker.git]
cd smart_job_tracker
python -m venv .venv
. .venv\Scripts\activate   # Windows
# or: source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
python app.py
