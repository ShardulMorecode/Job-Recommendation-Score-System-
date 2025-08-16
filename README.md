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

Output as JSON on webpage

## 📝 Assumptions

Resumes contain standard skill keywords.

JD is plain text or copy-paste from source.

Matching is keyword-based with optional semantic matching.
## Input and Output
<img width="1544" height="957" alt="image" src="https://github.com/user-attachments/assets/b260aa85-5469-4f77-8b28-bba2c6ba7124" />

## Sample Input
<img width="1557" height="895" alt="image" src="https://github.com/user-attachments/assets/e5854157-86bb-4f72-bbf2-93f78e9b91f4" />
<img width="1207" height="741" alt="image" src="https://github.com/user-attachments/assets/0d874b2e-6781-40b2-9f6d-d04f2b6200d2" />

## Sample Output
<img width="1172" height="403" alt="image" src="https://github.com/user-attachments/assets/101c52d3-ac3a-4cf3-8213-bd2842c4ba13" />

### Sample output along with explanation
<img width="1534" height="833" alt="image" src="https://github.com/user-attachments/assets/ef61b952-f8a4-4be3-8404-0c40ff94780e" />
<img width="1515" height="836" alt="image" src="https://github.com/user-attachments/assets/756bcc4e-cf02-4b06-ac1a-d09b71e36f79" />



