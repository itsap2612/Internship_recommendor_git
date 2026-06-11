from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

# MongoDB helpers
from database import insert_internship, get_internships, insert_profile

# Combined API loader
from data_loader import load_internships_combined  

app = Flask(__name__)
CORS(app)

# ---------------- Skill utilities ----------------
SKILL_LIST = [
    "python", "flask", "fastapi", "django", "sql", "mysql", "postgresql",
    "rest", "api", "git", "docker", "linux",
    "html", "css", "javascript", "react", "tailwind",
    "java", "spring", "spring boot",
    "excel", "pandas", "numpy", "scikit-learn", "machine learning", "ml",
]

STOPWORDS = set("""a an the and or if but while for with without to from in on at by of as is are was were be been being
this that those these there here it its they them he she we you your our their i me my mine ours""".split())

def normalize(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9#+ ]+", " ", text)
    tokens = [t for t in text.split() if t not in STOPWORDS and len(t) > 1]
    return " ".join(tokens)

def extract_skills(text: str):
    found = []
    low = text.lower()
    for skill in SKILL_LIST:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, low):
            found.append(skill)
    return sorted(set(found))

# ---------------- Recommendation ----------------
def recommend_for_resume(resume_text: str, internships, top_k=3):
    if not resume_text.strip():
        return {"error": "Empty resume text."}
    
    if not internships:
        return {"results": [], "message": "No internships found to recommend."}
    
    corpus = [normalize(resume_text)]
    for j in internships:
        desc = f"{j.get('title','')} {j.get('title','')} {j.get('description','')}"
        corpus.append(normalize(desc))

    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(corpus)
    resume_vec = X[0:1]
    job_vecs = X[1:]
    
    sims = cosine_similarity(resume_vec, job_vecs).flatten()

    rank_idx = sims.argsort()[::-1][:min(top_k, len(internships))]
    resume_skills = extract_skills(resume_text)
    results = []

    for i in rank_idx:
        job = internships[i]
        job_text = f"{job.get('title','')} {job.get('description','')}"
        job_skills = extract_skills(job_text)
        missing = sorted(set(job_skills) - set(resume_skills))
        results.append({
            "id": str(job.get("_id")),
            "title": job.get("title"),
            "location": job.get("location",""),
            "description": job.get("description"),
            "score": round(float(sims[i]), 4),
            "skills_required": job_skills,
            "resume_skills": resume_skills,
            "missing_skills": missing,
            "link": job.get("link", "#"),
            "company": job.get("company", "N/A"),
            "salary": job.get("salary", "Not disclosed"),
            "source": job.get("source", "unknown")
        })

    return {"query_resume": resume_text, "top_k": top_k, "results": results}

# ---------------- Routes ----------------
@app.get("/health")
def health():
    return jsonify({"status":"ok"})

@app.get("/internships")
def list_internships():
    query = request.args.get("query", "")
    location = request.args.get("location", "")
    top_k = int(request.args.get("top_k", 20))
    db_internships = get_internships(query=query, location=location, limit=top_k)
    return jsonify({"count": len(db_internships), "items": db_internships})

LOCATION_KEYWORDS = ["india", "usa", "united states", "uk", "canada", "remote"]

@app.post("/recommend")
def recommend_endpoint():
    data = request.get_json(force=True, silent=True) or {}
    resume_text = (data.get("resume") or "").strip()
    location = (data.get("location") or "").strip() 
    
    if not location:
        for loc_keyword in LOCATION_KEYWORDS:
            pattern = r'\b' + re.escape(loc_keyword) + r'\b'
            if re.search(pattern, resume_text, re.IGNORECASE):
                location = loc_keyword
                resume_text = re.sub(pattern, '', resume_text, flags=re.IGNORECASE).strip()
                break

    if not resume_text:
        skills = data.get("skills")
        if isinstance(skills, list) and skills:
            resume_text = " ".join(map(str, skills))

    top_k = int(data.get("top_k", 3))
    top_k = max(1, min(10, top_k))

    api_internships = load_internships_combined(query=resume_text, location=location, top_k=30)
    for job in api_internships:
        insert_internship(job)

    db_internships = get_internships(query=resume_text, location=location, limit=50)

    payload = recommend_for_resume(resume_text, db_internships, top_k)

    if "error" in payload:
        return jsonify(payload), 400
    return jsonify(payload)

@app.post("/create-profile")
def create_profile_endpoint():
    data = request.get_json(force=True, silent=True) or {}
    name = data.get("name", "").strip()
    skills = data.get("skills", "").strip()
    interests = data.get("interests", "").strip()

    if not name or not skills:
        return jsonify({"error": "Name and skills are required."}), 400

    profile = {
        "name": name,
        "skills": [s.strip() for s in skills.split(',')],
        "interests": [i.strip() for i in interests.split(',')]
    }
    try:
        insert_profile(profile)
        return jsonify({"status": "Profile created successfully."}), 201
    except Exception as e:
        return jsonify({"error": "Could not create profile. It might already exist."}), 409

@app.get("/")
def home():
    return render_template("index.html")

# ---------------- Main ----------------
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)