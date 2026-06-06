"""
report_builder.py
=================
Combines the raw detector outputs for ONE student into a single report:
a negative score (plagiarism evidence), the positive originality side, an
overall integrity score (0-100), and a verdict the teacher can act on.
"""


def build_report(student, ai_result, peer_similarity, paraphrase_result, orig_result):
    # Negative = weighted blend of the three "bad" signals.
    negative = (
        ai_result["ai_percentage"] * 0.50      # AI-generated text matters most
        + peer_similarity * 0.30               # copied from another student
        + paraphrase_result["paraphrase_percent"] * 0.20  # humanized AI
    )

    # Integrity: start at 100, subtract negative, nudge up for originality.
    integrity = 100 - (negative * 0.6) + (orig_result["originality_score"] * 0.2)
    integrity = round(max(0, min(100, integrity)))

    # Simple traffic-light verdict.
    if integrity >= 70:
        verdict = "clean"
    elif integrity >= 40:
        verdict = "review"
    else:
        verdict = "flagged"

    return {
        "student": student,
        "integrity_score": integrity,
        "verdict": verdict,
        "positive": orig_result,  # originality_score, vocab_diversity, burstiness...
        "negative": {
            "ai_percentage": ai_result["ai_percentage"],
            "ai_verdict": ai_result["verdict"],
            "ai_reasoning": ai_result.get("reasoning", ""),
            "flagged_sentences": ai_result["flagged_sentences"],
            "peer_similarity": peer_similarity,
            "paraphrase_percent": paraphrase_result["paraphrase_percent"],
            "paraphrase_pairs": paraphrase_result.get("pairs", []),
        },
    }
