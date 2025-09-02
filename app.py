import os, uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from nlp import extract_text_from_file, compute_match_score

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

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120))
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    match_score = db.Column(db.Float)
    matched_skills = db.Column(db.Text)
    missing_skills = db.Column(db.Text)

class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    text = db.Column(db.Text, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

def get_active_resume_text():
    r = Resume.query.order_by(Resume.uploaded_at.desc()).first()
    return r.text if r else None

@app.route("/")
def index():
    has_resume = bool(get_active_resume_text())
    return render_template("index.html", has_resume=has_resume)

@app.route("/resume", methods=["GET","POST"])
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
            db.session.add(Resume(filename=fname, text=text))
            db.session.commit()
            flash("Resume uploaded & parsed.", "success")
            return redirect(url_for("index"))

        if pasted:
            db.session.add(Resume(filename="pasted.txt", text=pasted))
            db.session.commit()
            flash("Resume text saved.", "success")
            return redirect(url_for("index"))

        flash("Please upload a file or paste text.", "warning")

    recent = Resume.query.order_by(Resume.uploaded_at.desc()).limit(5).all()
    return render_template("resume.html", resumes=recent)

@app.route("/jobs")
def jobs_list():
    jobs = Job.query.order_by(Job.created_at.desc()).all()
    return render_template("jobs.html", jobs=jobs)

@app.route("/jobs/<int:job_id>")
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    return render_template("job_detail.html", job=job)

@app.route("/match", methods=["POST"])
def match():
    resume_text = get_active_resume_text()
    if not resume_text:
        flash("Upload your resume first.", "warning")
        return redirect(url_for("resume"))

    company = request.form.get("company","").strip() or "Unknown Company"
    role = request.form.get("role","").strip() or "Unknown Role"
    location = request.form.get("location","").strip()
    jd_text = request.form.get("job_description","").strip()
    if not jd_text:
        flash("Job description is required.", "warning")
        return redirect(url_for("index"))

    score, matched, missing = compute_match_score(resume_text, jd_text)
    job = Job(company=company, role=role, location=location,
              description=jd_text, match_score=round(score,2),
              matched_skills=",".join(matched), missing_skills=",".join(missing))
    db.session.add(job)
    db.session.commit()
    flash(f"Match score: {round(score,2)}%", "success")
    return redirect(url_for("job_detail", job_id=job.id))

@app.route("/download/<path:filename>")
def download(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
