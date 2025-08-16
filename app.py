import os
import tempfile
import traceback
import logging
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename

from utils import (
    extract_text_from_any,
    parse_resume_with_pyresparser,
    parse_job_description,
    compute_scores,
)

# basic logging to console + file
logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s [%(levelname)s] %(message)s",
                    handlers=[
                        logging.StreamHandler(),
                        logging.FileHandler("app.log", mode="a", encoding="utf-8")
                    ])
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = os.environ.get("UPLOAD_FOLDER", "Uploaded_Resumes")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/match", methods=["POST"])
def match():
    try:
        if "resume" not in request.files:
            return jsonify({"error": "resume file is required"}), 400

        resume_file = request.files["resume"]
        if resume_file.filename == "":
            return jsonify({"error": "resume file is empty"}), 400

        jd_text = request.form.get("jd_text", "") or ""
        jd_file = request.files.get("jd_file")

        # Save resume safely
        filename = secure_filename(resume_file.filename)
        resume_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        resume_file.save(resume_path)
        logger.debug(f"Saved resume to {resume_path}")

        # If JD provided as file -> read it
        if jd_file and jd_file.filename:
            with tempfile.NamedTemporaryFile(delete=False) as tmpjd:
                tmpjd_path = tmpjd.name
            jd_file.save(tmpjd_path)
            jd_text_from_file = extract_text_from_any(tmpjd_path)
            if jd_text_from_file:
                jd_text = jd_text_from_file
            try:
                os.remove(tmpjd_path)
            except Exception:
                logger.debug("Could not remove tmpjd_path")

        if not jd_text.strip():
            return jsonify({"error": "Provide jd_text or jd_file"}), 400

        # Parse resume and JD
        resume_data = parse_resume_with_pyresparser(resume_path)
        # add raw text to resume_data if not present (helps fallbacks)
        if not resume_data.get("raw_text"):
            resume_data["raw_text"] = extract_text_from_any(resume_path) or ""

        jd_struct = parse_job_description(jd_text)

        # use_semantic param handling
        use_semantic_str = (request.form.get("use_semantic") or "").lower().strip()
        use_semantic = use_semantic_str == "true" if use_semantic_str else True

        # compute scores
        scores, details = compute_scores(
            resume_data=resume_data,
            jd=jd_struct,
            use_semantic=use_semantic
        )

        response = {
            "candidate_name": resume_data.get("name") or "",
            "job_title": jd_struct.get("job_title") or "",
            "match_scores": {
                "skills_match": int(round(scores["skills"], 0)),
                "experience_match": int(round(scores["experience"], 0)),
                "education_match": int(round(scores["education"], 0)),
                "overall_score": int(round(scores["overall"], 0)),
            },
            ###"explanations": {
            ###    "jd_skills": sorted(jd_struct.get("skills", [])),
            ###    "resume_skills": sorted(details.get("resume_skills_norm", [])),
            ###    "skills_matched": sorted(details.get("skills_matched", [])),
            ###    "skills_missing": sorted(details.get("skills_missing", [])),
            ###    "jd_min_exp_years": jd_struct.get("min_years_experience"),
            ###    "resume_years_experience": details.get("resume_years_experience"),
            ###    "jd_education": jd_struct.get("education"),
            ###    "resume_degrees": details.get("resume_degrees"),
            ###    "used_semantic": details.get("used_semantic", False),
            ###} 
        }

        logger.info(f"Match computed for '{response['candidate_name']}' -> overall {response['match_scores']['overall_score']}")
        return jsonify(response), 200

    except Exception as e:
        # Log full traceback to app.log and return trace summary to client (only for debug)
        tb = traceback.format_exc()
        logger.exception("Unhandled exception in /match")
        return jsonify({
            "error": "internal_server_error",
            "detail": str(e),
            "traceback": tb.splitlines()[-10:]  # last 10 lines for brevity
        }), 500


if __name__ == "__main__":
    # Ensure debug=True while testing locally so you see tracebacks in console
    app.run(host="0.0.0.0", port=5000, debug=True)
