# ---------- app.py (FULL FILE) ----------
import os, uuid, csv
from io import StringIO
from datetime import datetime
from collections import Counter

from flask import (
    Flask, render_template, request, redirect, url_for, flash,
    send_from_directory, Response
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, login_user, logout_user, login_required,
    current_user, UserMixin
)
from werkzeug.security import generate_password_hash, check_password_hash

from nlp import extract_text_from_file, compute_match_score

# ----- App & DB setup -----
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
UPLOAD_DIR = os.path.join(INSTANCE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(INSTANCE_DIR, "app.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
    return app

app = create_app()
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

# ----- Models -----
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(180), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, pw): self.password_hash = generate_password_hash(pw)
    def check_password(self, pw): return check_password_hash(self.password_hash, pw)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    company = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120))
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    match_score = db.Column(db.Float)
    matched_skills = db.Column(db.Text)   # comma-separated
    missing_skills = db.Column(db.Text)   # comma-separated
    status = db.Column(db.String(40), default="Interested")
    notes = db.Column(db.Text)

class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    text = db.Column(db.Text, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ----- Helpers -----
def get_active_resume_text():
    if not current_user.is_authenticated:
        return None
    r = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.uploaded_at.desc()).first()
    return r.text if r else None

def suggest_bullets(missing_skills):
    # simple rule-based bullet generator you can customize
    patterns = {
        "python": "Developed data pipelines and automation scripts using Python to reduce manual effort by 30%.",
        "sql": "Wrote optimized SQL queries, joins, and window functions to support analytics and reporting.",
        "tableau": "Built Tableau dashboards with filters and KPIs to monitor product and operational metrics.",
        "power bi": "Designed Power BI reports using DAX measures to visualize trends and business KPIs.",
        "aws": "Deployed and monitored data workloads on AWS (S3, Lambda, EC2) following best practices.",
        "azure": "Implemented Azure-based ETL workflows using Data Factory and Azure Functions.",
        "gcp": "Managed GCP services (BigQuery, Cloud Storage) for large-scale analytics.",
        "docker": "Containerized applications with Docker, improving local parity and deployment consistency.",
        "kubernetes": "Orchestrated containerized services with Kubernetes for resilient scaling.",
        "airflow": "Created and scheduled DAGs in Apache Airflow for reliable data workflows.",
        "spark": "Processed large datasets with Apache Spark (PySpark) to accelerate analytics.",
        "nlp": "Built NLP pipelines (tokenization, TF-IDF, similarity) to extract insights from unstructured text.",
        "javascript": "Implemented interactive UI features with JavaScript to improve user experience.",
        "react": "Built reusable React components and integrated REST APIs using Axios/fetch."
    }
    bullets = []
    for s in missing_skills:
        s_low = s.lower().strip()
        if s_low in patterns:
            bullets.append(f"• {patterns[s_low]}")
        else:
            bullets.append(f"• Demonstrated proficiency with {s} through hands-on projects and documentation.")
    # Limit to top 6
    return bullets[:6]

# ----- Auth routes -----
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","").strip()
        if not email or not password:
            flash("Email and password are required.", "warning")
            return redirect(url_for("register"))
        if User.query.filter_by(email=email).first():
            flash("Account already exists. Please log in.", "warning")
            return redirect(url_for("login"))
        u = User(email=email)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("auth_register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","").strip()
        u = User.query.filter_by(email=email).first()
        if u and u.check_password(password):
            login_user(u)
            flash("Logged in.", "success")
            return redirect(url_for("index"))
        flash("Invalid credentials.", "danger")
    return render_template("auth_login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "success")
    return redirect(url_for("login"))

# ----- Core routes -----
@app.route("/")
@login_required
def index():
    has_resume = bool(get_active_resume_text())
    return render_template("index.html", has_resume=has_resume)

@app.route("/resume", methods=["GET","POST"])
@login_required
def resume():
    if request.method == "POST":
        file = request.files.get("resume_file")
        pasted = request.form.get("resume_text", "").strip()

        if file and file.filename:
            try:
                text = extract_text_from_file(file)
            except Exception as e:
                flash(f"Failed to read resume: {e}", "danger")
                return redirect(url_for("resume"))
            fname = f"{uuid.uuid4().hex}_{file.filename}"
            file.stream.seek(0)
            file.save(os.path.join(UPLOAD_DIR, fname))
            db.session.add(Resume(user_id=current_user.id, filename=fname, text=text))
            db.session.commit()
            flash("Resume uploaded & parsed.", "success")
            return redirect(url_for("index"))

        if pasted:
            db.session.add(Resume(user_id=current_user.id, filename="pasted.txt", text=pasted))
            db.session.commit()
            flash("Resume text saved.", "success")
            return redirect(url_for("index"))

        flash("Please upload a file or paste text.", "warning")

    recent = (Resume.query.filter_by(user_id=current_user.id)
              .order_by(Resume.uploaded_at.desc()).limit(5).all())
    return render_template("resume.html", resumes=recent)

@app.route("/jobs")
@login_required
def jobs_list():
    jobs = Job.query.filter_by(user_id=current_user.id).order_by(Job.created_at.desc()).all()
    return render_template("jobs.html", jobs=jobs)

@app.route("/jobs/<int:job_id>")
@login_required
def job_detail(job_id):
    job = Job.query.filter_by(id=job_id, user_id=current_user.id).first_or_404()
    # suggested bullets based on this job's missing skills
    missing = [s.strip() for s in (job.missing_skills or "").split(",") if s.strip()]
    bullets = suggest_bullets(missing) if missing else []
    return render_template("job_detail.html", job=job, bullets=bullets)

@app.route("/jobs/<int:job_id>/update", methods=["POST"])
@login_required
def update_job(job_id):
    job = Job.query.filter_by(id=job_id, user_id=current_user.id).first_or_404()
    job.status = request.form.get("status", job.status)
    job.notes = request.form.get("notes", job.notes)
    db.session.commit()
    flash("Job updated.", "success")
    return redirect(url_for("job_detail", job_id=job.id))

@app.route("/match", methods=["POST"])
@login_required
def match():
    resume_text = get_active_resume_text()
    if not resume_text:
        flash("Upload your resume first.", "warning")
        return redirect(url_for("resume"))

    # Accept pasted JD or uploaded JD file
    jd_text = request.form.get("job_description","").strip()
    jd_file = request.files.get("jd_file")
    if jd_file and jd_file.filename:
        try:
            jd_text = extract_text_from_file(jd_file)
        except Exception as e:
            flash(f"Failed to read job description file: {e}", "danger")
            return redirect(url_for("index"))

    company = request.form.get("company","").strip() or "Unknown Company"
    role = request.form.get("role","").strip() or "Unknown Role"
    location = request.form.get("location","").strip()
    if not jd_text:
        flash("Job description is required (paste text or upload PDF/DOCX/TXT).", "warning")
        return redirect(url_for("index"))

    score, matched, missing = compute_match_score(resume_text, jd_text)
    job = Job(
        user_id=current_user.id,
        company=company, role=role, location=location,
        description=jd_text, match_score=round(score,2),
        matched_skills=",".join(matched), missing_skills=",".join(missing)
    )
    db.session.add(job)
    db.session.commit()
    flash(f"Match score: {round(score,2)}%", "success")
    return redirect(url_for("job_detail", job_id=job.id))

@app.route("/export.csv")
@login_required
def export_csv():
    jobs = Job.query.filter_by(user_id=current_user.id).order_by(Job.created_at.desc()).all()
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["created_at","company","role","location","status","match_score","matched_skills","missing_skills"])
    for j in jobs:
        writer.writerow([
            j.created_at.strftime("%Y-%m-%d %H:%M"),
            j.company, j.role, j.location or "", j.status or "",
            j.match_score or "", j.matched_skills or "", j.missing_skills or "",
        ])
    output = si.getvalue()
    return Response(
        output, mimetype="text/csv",
        headers={"Content-Disposition":"attachment; filename=jobs_export.csv"}
    )

@app.route("/analytics")
@login_required
def analytics():
    jobs = Job.query.filter_by(user_id=current_user.id).all()
    scores = [j.match_score for j in jobs if j.match_score is not None]
    miss = []
    for j in jobs:
        if j.missing_skills:
            miss.extend([s.strip() for s in j.missing_skills.split(",") if s.strip()])
    top_missing = Counter(miss).most_common(10)
    # Pass raw arrays to template; Chart.js will render
    labels = [k for k,_ in top_missing]
    values = [v for _,v in top_missing]
    return render_template("analytics.html", scores=scores, labels=labels, values=values)

@app.route("/download/<path:filename>")
@login_required
def download(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
