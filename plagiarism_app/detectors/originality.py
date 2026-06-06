"""
originality.py
==============
The POSITIVE side of the report: evidence the student wrote it themselves.
Pure Python math, no AI. Three human signals:
  - vocab diversity (humans reuse fewer exact words)
  - burstiness (humans vary sentence length; AI is flat)
  - personal markers ("I think", "for example", ...)
"""

import re


def score_originality(text: str) -> dict:
    sentences = [s for s in text.split(".") if len(s.strip()) > 10]
    words = text.lower().split()

    # 1) Type-Token Ratio = unique words / total words.
    total = max(len(words), 1)
    ttr = len(set(words)) / total

    # 2) Burstiness = variance of sentence length / average (higher = more human).
    lengths = [len(s.split()) for s in sentences]
    if lengths:
        avg = sum(lengths) / len(lengths)
        variance = sum((l - avg) ** 2 for l in lengths) / len(lengths)
        burstiness = variance / max(avg, 1)
    else:
        burstiness = 0.0

    # 3) Count first-person / example phrases that signal a human voice.
    personal = len(re.findall(
        r"\b(I|my|me|myself|in my opinion|i think|i believe|for example)\b",
        text, re.IGNORECASE))

    # Combine into a single 0-100 originality score (weights are tunable).
    score = min(100, (ttr * 40) + (min(burstiness, 5) * 8) + (personal * 3))

    return {
        "originality_score": round(score, 1),
        "vocab_diversity": round(ttr * 100, 1),
        "burstiness": round(burstiness, 2),
        "personal_markers": personal,
    }
