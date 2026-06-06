"""
plagiarism_api.py
=================
The plagiarism backend (FastAPI). Runs on port 8001.

Endpoints:
  POST /submit            -> a student uploads one assignment file
  POST /run_analysis      -> teacher runs all detectors over every submission
  GET  /all_reports       -> teacher gets the summary table
  GET  /report/{student}  -> teacher gets one student's detailed report

Files are saved under ../submissions and reports under ../reports, using paths
relative to THIS file so it works no matter which folder you launch it from.
"""

import os
import json
import shutil

from fastapi import FastAPI, UploadFile, File, Form, HTTPException

# Detectors live in the detectors/ package next to this file.
from detectors.text_extractor import extract_text
from detectors.ai_detector import detect_ai_content
from detectors.copy_checker import check_all_submissions
from detectors.paraphrase import detect_paraphrase
from detectors.originality import score_originality
from report_builder import build_report

# Absolute folder paths anchored to the project root (one level up from here).
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUBMISSIONS_DIR = os.path.join(ROOT, "submissions")
REPORTS_DIR = os.path.join(ROOT, "reports")
os.makedirs(SUBMISSIONS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

app = FastAPI(title="Plagiarism Detector API")


@app.post("/submit")
def submit(student_name: str = Form(...), file: UploadFile = File(...)):
    """Save one student's uploaded file. The filename keeps the student name."""
    safe = student_name.strip().replace(" ", "_")
    path = os.path.join(SUBMISSIONS_DIR, f"{safe}__{file.filename}")
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)  # stream the upload to disk
    return {"status": "uploaded", "student": student_name}


def _student_from_filename(name: str) -> str:
    """Pull the student name back out of "Ravi__essay.pdf" -> "Ravi"."""
    return name.split("__")[0].replace("_", " ")


@app.post("/run_analysis")
def run_analysis():
    """
    The heavy step. For every submitted file:
      1. extract text  2. score originality  3. detect AI  4. compare to peers.
    Then save one JSON report per student into the reports/ folder.
    """
    prep = _prepare()
    summary = [_analyze_student(name, prep) for name in prep["texts"]]
    return {"status": "done", "count": len(summary), "summary": summary}


# In-memory state shared between /prepare and /analyze_one so the teacher UI can
# run the slow per-student step one at a time and show a progress bar.
_PREP = {}


def _prepare() -> dict:
    """
    Fast step: clear old reports, read every submission's text, run the
    cross-student copy check, and work out each student's closest peer.
    Returns (and caches) everything the per-student step needs.
    """
    files = [f for f in os.listdir(SUBMISSIONS_DIR) if not f.startswith(".")]
    if not files:
        raise HTTPException(400, "No submissions to analyse.")

    # Clear old reports so results reflect ONLY the current submissions.
    for old in os.listdir(REPORTS_DIR):
        if old.endswith(".json"):
            os.remove(os.path.join(REPORTS_DIR, old))

    # Read text out of every file, keyed by student name.
    texts = {}
    for fname in files:
        try:
            texts[_student_from_filename(fname)] = extract_text(
                os.path.join(SUBMISSIONS_DIR, fname))
        except Exception as e:
            texts[_student_from_filename(fname)] = ""
            print(f"Could not read {fname}: {e}")

    # One cross-student copy check covers everyone at once.
    copy = check_all_submissions(texts)
    worst_peer = copy["max_similarity_per_student"]

    # For each student, find the single peer they most resemble (for paraphrase).
    closest_peer = {}
    for m in copy["matches"]:
        a, b, s = m["student_a"], m["student_b"], m["similarity_percent"]
        if s >= closest_peer.get(a, (None, 0))[1]:
            closest_peer[a] = (b, s)
        if s >= closest_peer.get(b, (None, 0))[1]:
            closest_peer[b] = (a, s)

    prep = {"texts": texts, "worst_peer": worst_peer, "closest_peer": closest_peer}
    _PREP.clear()
    _PREP.update(prep)
    return prep


def _analyze_student(student: str, prep: dict) -> dict:
    """Slow step for ONE student: AI + originality + paraphrase, save report."""
    text = prep["texts"][student]
    ai = detect_ai_content(text)              # this is the slow part (Qwen)
    orig = score_originality(text)

    peer_name = prep["closest_peer"].get(student, (None, 0))[0]
    if peer_name:
        para = detect_paraphrase(text, prep["texts"][peer_name])
    else:
        para = {"paraphrase_percent": 0.0, "pairs": []}

    report = build_report(student, ai, prep["worst_peer"].get(student, 0.0), para, orig)
    report["closest_peer"] = peer_name

    with open(os.path.join(REPORTS_DIR, f"{student}.json"), "w") as f:
        json.dump(report, f, indent=2)

    return {
        "student": student,
        "integrity_score": report["integrity_score"],
        "verdict": report["verdict"],
        "ai_percentage": ai["ai_percentage"],
        "peer_similarity": prep["worst_peer"].get(student, 0.0),
        "paraphrase_percent": para["paraphrase_percent"],
    }


@app.post("/prepare")
def prepare():
    """Teacher UI step 1: clears old reports and returns the student list."""
    prep = _prepare()
    return {"students": list(prep["texts"].keys())}


@app.post("/analyze_one/{student}")
def analyze_one(student: str):
    """Teacher UI step 2: analyse ONE student (called once per student)."""
    if student not in _PREP.get("texts", {}):
        raise HTTPException(400, "Call /prepare first.")
    return _analyze_student(student, _PREP)


@app.get("/all_reports")
def all_reports():
    """Return the summary row of every saved report (for the teacher table)."""
    rows = []
    for fname in os.listdir(REPORTS_DIR):
        if fname.endswith(".json"):
            with open(os.path.join(REPORTS_DIR, fname)) as f:
                r = json.load(f)
            rows.append({
                "student": r["student"],
                "integrity_score": r["integrity_score"],
                "verdict": r["verdict"],
                "ai_percentage": r["negative"]["ai_percentage"],
                "peer_similarity": r["negative"]["peer_similarity"],
                "paraphrase_percent": r["negative"]["paraphrase_percent"],
            })
    return rows


@app.get("/report/{student}")
def get_report(student: str):
    """Return one student's full detailed report."""
    path = os.path.join(REPORTS_DIR, f"{student}.json")
    if not os.path.exists(path):
        raise HTTPException(404, f"No report for {student}. Run analysis first.")
    with open(path) as f:
        return json.load(f)
