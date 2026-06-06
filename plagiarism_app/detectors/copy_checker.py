"""
copy_checker.py
===============
Catches student-vs-student copy-paste using TF-IDF + cosine similarity.
TF-IDF turns each document into numbers (word importance); cosine similarity
measures how close two of those number-vectors are. No AI / Ollama needed.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def check_all_submissions(texts: dict) -> dict:
    """
    texts = {"Ravi": "full text...", "Priya": "full text...", ...}
    Returns matches (pairs above 30%) and each student's worst peer match.
    """
    names = list(texts.keys())
    docs = list(texts.values())

    # Need at least 2 documents to compare anything.
    if len(docs) < 2:
        return {"matches": [], "max_similarity_per_student": {n: 0.0 for n in names}}

    tfidf = TfidfVectorizer().fit_transform(docs)  # turn all docs into vectors
    sim = cosine_similarity(tfidf)  # square grid of every pair's similarity

    matches = []
    worst = {n: 0.0 for n in names}  # highest match each student is involved in

    # Loop over each unique pair (i, j) once.
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            score = round(sim[i][j] * 100, 1)  # 0-100 percentage
            worst[names[i]] = max(worst[names[i]], score)
            worst[names[j]] = max(worst[names[j]], score)
            if score > 30:  # only keep meaningful overlaps
                matches.append({
                    "student_a": names[i],
                    "student_b": names[j],
                    "similarity_percent": score,
                    "severity": "high" if score > 70 else "medium",
                })

    return {"matches": matches, "max_similarity_per_student": worst}
