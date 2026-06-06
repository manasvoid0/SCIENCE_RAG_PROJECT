"""
ai_detector.py
==============
Job: decide whether a piece of text was written by an AI (ChatGPT / Gemini / etc.)
or by a real human student.

Instead of downloading a separate HuggingFace classifier model, we simply ASK
Qwen2.5 (running in Ollama) to act as an academic-integrity expert and return a
structured JSON verdict. This keeps the whole project Ollama-only.
"""

from detectors.ollama_client import generate, extract_json

# The instructions we send to Qwen. We describe AI signals vs human signals,
# then force it to answer in a fixed JSON shape we can read in code.
_PROMPT_TEMPLATE = """You are an academic integrity expert. Analyse the following student text and decide if it was written by an AI (like ChatGPT, Gemini, or Claude) or by a human student.

AI signals:
- Unnaturally perfect grammar and structure
- Overly formal vocabulary for a student's grade level
- No personal voice, errors, or colloquial expressions
- Repetitive sentence patterns
- Generic examples with no personal context

Human signals:
- Small grammar mistakes or informal phrasing
- Personal anecdotes or local examples
- Varying sentence lengths (some short, some long)
- First-person opinions and uncertainty ("I think", "maybe")

Text to analyse:
\"\"\"{text}\"\"\"

Respond ONLY with valid JSON in this EXACT format, no other text:
{{
  "ai_probability": 0.85,
  "verdict": "high",
  "reasoning": "One short sentence explaining why",
  "flagged_sentences": [
    {{"sentence": "exact sentence here", "reason": "why it seems AI-written"}}
  ],
  "positive_signals": ["e.g. natural grammar variation present"]
}}

verdict must be exactly one of: "low", "medium", "high"
ai_probability must be a float between 0.0 and 1.0"""


def detect_ai_content(text: str) -> dict:
    """
    Returns a dict like:
    {
      "ai_percentage": 85.0,        # 0-100, easy for the report to display
      "verdict": "high",
      "reasoning": "...",
      "flagged_sentences": [ {"sentence": ..., "reason": ...}, ... ],
      "positive_signals": [ ... ]
    }
    If Ollama is unreachable or returns junk, we degrade gracefully instead of
    crashing the whole analysis.
    """
    # Cap the length so very large essays still fit comfortably in the prompt.
    snippet = text[:6000]
    prompt = _PROMPT_TEMPLATE.format(text=snippet)

    try:
        raw = generate(prompt, temperature=0.1)  # ask Qwen
        data = extract_json(raw)  # parse its JSON answer
    except Exception as e:
        # Never let one failed model call kill the run -- report it instead.
        return {
            "ai_percentage": 0.0,
            "verdict": "unknown",
            "reasoning": f"AI detector unavailable: {e}",
            "flagged_sentences": [],
            "positive_signals": [],
        }

    # Convert the 0.0-1.0 probability into a friendly 0-100 percentage.
    prob = float(data.get("ai_probability", 0.0))
    return {
        "ai_percentage": round(prob * 100, 1),
        "verdict": data.get("verdict", "low"),
        "reasoning": data.get("reasoning", ""),
        "flagged_sentences": data.get("flagged_sentences", []),
        "positive_signals": data.get("positive_signals", []),
    }
