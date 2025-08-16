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