"""
paraphrase.py
=============
Catches "humanized" AI plagiarism: text reworded to dodge copy-detection but
keeping the same meaning. We embed each sentence with nomic-embed-text (Ollama)
and compare meanings via cosine similarity. Different words, same meaning ->
vectors still point the same way.
"""

import numpy as np
from detectors.ollama_client import embed


def _cosine(a, b) -> float:
    """Cosine similarity between two vectors (1.0 = identical direction)."""
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def _sentences(text: str) -> list:
    """Split into reasonably long sentences; ignore tiny fragments."""
    return [s.strip() for s in text.split(".") if len(s.strip()) > 20]


def detect_paraphrase(text_a: str, text_b: str) -> dict:
    """
    Compare two students' texts at the MEANING level.
    Returns the % of A's sentences that closely match some sentence in B,
    plus the top matching pairs (for highlighting in the report).
    """
    sents_a, sents_b = _sentences(text_a), _sentences(text_b)
    if not sents_a or not sents_b:
        return {"paraphrase_percent": 0.0, "pairs": []}

    try:
        emb_a = [embed(s) for s in sents_a]
        emb_b = [embed(s) for s in sents_b]
    except Exception as e:
        return {"paraphrase_percent": 0.0, "pairs": [], "error": str(e)}

    pairs = []
    for i, ea in enumerate(emb_a):
        for j, eb in enumerate(emb_b):
            score = _cosine(ea, eb)
            if score > 0.82:  # high meaning-overlap threshold
                pairs.append({
                    "sentence_a": sents_a[i],
                    "sentence_b": sents_b[j],
                    "similarity": round(score * 100, 1),
                })

    percent = round(len(pairs) / len(sents_a) * 100, 1)
    return {"paraphrase_percent": min(percent, 100.0), "pairs": pairs[:10]}
