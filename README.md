# Resume–Job Description Matcher (Flask App)

## 📌 Overview
This Flask-based app matches a candidate's resume against a given Job Description (JD) and returns:
- Skills match percentage
- Experience match percentage
- Education match percentage
- Overall score
- Missing skills

Supports `.pdf`, `.docx`, `.txt` resumes and plain-text JDs.

---

## ⚙️ Setup Instructions

### 1️⃣ Clone Repo / Extract ZIP

git clone <repo_url>
cd resume_matcher

### 2️⃣ Create Virtual Environment
python -m venv venv
source venv/bin/activate     # On Mac/Linux
venv\Scripts\activate        # On Windows

### 3️⃣ Install Requirements
pip install -r requirements.txt

## 🚀 Running the App
python app.py


Visit: http://127.0.0.1:5000/

## 📂 Sample Usage

Input:

Resume: samples/sample_resume.pdf

Job Description: samples/sample_jd.txt

Output JSON:
See: samples/sample_output.json

## 📝 Assumptions

Resumes contain standard skill keywords.

JD is plain text or copy-paste from source.

Matching is keyword-based with optional semantic matching.

## Sample Input
<img width="1689" height="885" alt="image" src="https://github.com/user-attachments/assets/109245e6-6b70-4203-90f2-50366601d40a" />
<img width="1655" height="816" alt="image" src="https://github.com/user-attachments/assets/fd3f0f6f-9856-41c8-9f26-afd56780e918" />


## Sample Output
<img width="1534" height="833" alt="image" src="https://github.com/user-attachments/assets/ef61b952-f8a4-4be3-8404-0c40ff94780e" />
<img width="1515" height="836" alt="image" src="https://github.com/user-attachments/assets/756bcc4e-cf02-4b06-ac1a-d09b71e36f79" />
### Json Output
{
  "candidate_name": "ARPAN GHOSH",
  "explanations": {
    "jd_education": [
      "bachelor",
      "design",
      "hci",
      "master"
    ],
    "jd_min_exp_years": 5,
    "jd_skills": [
      "adobe_xd",
      "figma",
      "prototyping",
      "ui",
      "ux",
      "wireframing"
    ],
    "resume_degrees": [
      "bs",
      "design",
      "m.s",
      "m.sc"
    ],
    "resume_skills": [
      "ai",
      "analysis",
      "analytics",
      "architectures",
      "aws",
      "banking",
      "content",
      "data analytics",
      "docker",
      "engineering",
      "implicit",
      "improvement",
      "interactive",
      "json",
      "linux",
      "machine learning",
      "mathematics",
      "matplotlib",
      "mortgage",
      "pandas",
      "pdf",
      "physics",
      "process",
      "python",
      "pytorch",
      "queries",
      "reports",
      "responses",
      "saas",
      "seaborn",
      "sql",
      "statistics",
      "system",
      "tensorflow",
      "test cases",
      "ui",
      "unix",
      "ux",
      "vim",
      "workflows",
      "writing"
    ],
    "resume_years_experience": 2.08,
    "skills_matched": [
      "ui",
      "ux"
    ],
    "skills_missing": [
      "adobe_xd",
      "figma",
      "prototyping",
      "wireframing"
    ],
    "used_semantic": false
  },
  "job_title": "Senior UI/UX Designer",
  "match_scores": {
    "education_match": 100,
    "experience_match": 42,
    "overall_score": 49,
    "skills_match": 33
  }
}


