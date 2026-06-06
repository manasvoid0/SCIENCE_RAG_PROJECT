# 2. Detection Methods — The 3 Ways Cheating Is Caught

Your system catches cheating in **three different ways**. Each works on a
different principle — which is why two of them don't need the AI brain (Qwen) and
one does.

> Quick map: **two checks *measure*, one check *judges*.** Measuring is exact and
> never affected by model size. Judging needs intelligence, so it's the only part
> that gets sharper with a bigger model.

---

## Check 1 — Copy check (TF-IDF)

**Catches:** Student B copy-pasted from Student A.
**Code:** [`detectors/copy_checker.py`](../plagiarism_app/detectors/copy_checker.py) — uses `scikit-learn`, never Qwen.

**How it works (pure word-counting math, no AI):**
1. **TF-IDF** turns each essay into a list of numbers based on *which words appear
   and how often*. Rare meaningful words ("photosynthesis", "chloroplast") score
   high; common words ("the", "is") score near-zero.
2. It then compares two students' number-lists. Same important words in the same
   proportions → nearly identical lists → high similarity %.

**Why it's rock-solid:** It's just counting and comparing — no opinion. The same
two essays always give the exact same score, in milliseconds. Math never has an
off day.

**Its blind spot:** It only sees *words*. Swap words for synonyms
("happy" → "joyful") and the counts change, fooling it. → That's what Check 2 fixes.

---

## Check 2 — Paraphrase check (embeddings)

**Catches:** A student took AI text (or a peer's) and **reworded** it to dodge Check 1.
**Code:** [`detectors/paraphrase.py`](../plagiarism_app/detectors/paraphrase.py) — uses `embed()` (nomic-embed-text), never `generate()`.

**How it works (uses `nomic-embed-text`, NOT Qwen):**
1. The embedding model turns each sentence into a **meaning-vector** — numbers
   that capture *what it means*, not which words it uses.
2. "The cell makes energy" and "Energy is produced by the cell" → almost the
   **same vector**, even though the words differ.
3. Compare vectors. Close vectors = same meaning = paraphrased copy.

**Why it's reliable (but not "rock-solid"):** Like TF-IDF it's measurement, so
it's consistent and repeatable. But it measures something fuzzier (*meaning*), so
it's reliable rather than perfectly exact.

**Key point:** `nomic-embed-text` only *measures* meaning into numbers — it never
thinks or judges. That's why a small embed model is totally fine here; it's not
the weak link.

---

## Check 3 — AI-detector (Qwen)

**Catches:** Student used ChatGPT / Gemini to generate the essay.
**Code:** [`detectors/ai_detector.py`](../plagiarism_app/detectors/ai_detector.py) — calls `generate()` (Qwen).

**How it works (this one DOES use Qwen):** There's no math formula for "is this
AI-written?" — it needs real reading and judgment:
- Is the grammar suspiciously perfect?
- Is the vocabulary too advanced for a 10th grader?
- Is there any personal voice, or is it generic and flat?

Only a thinking model (Qwen) can weigh all that and form an opinion, so we
literally **ask Qwen** to read the essay and judge it.

**Why it gets weaker at 3b:** This is the only check that depends on
*intelligence* rather than *measurement*. A bigger brain (7b) makes sharper, more
consistent judgments; a smaller brain (3b) is decent but more likely to waver or
be over-confident. The other two checks aren't judging — they're measuring — so
model size doesn't affect them.

---

## One-line summary

| Check | Principle | Tool | Affected by 3b vs 7b? |
|-------|-----------|------|------------------------|
| Copy (TF-IDF) | counts **words** | math only | ❌ No — pure math |
| Paraphrase | measures **meaning** | `nomic-embed-text` | ❌ No — measuring, not judging |
| AI-detector | **judges** writing style | `qwen2.5` | ✅ Yes — it's a thinking task |

So **2 of your 3 defenses are immune to model size** — that's why the detector
stays trustworthy even on a small machine. Only the AI-style judgment softens a
bit at 3b, and the other two are there to back it up.

---

**Next:** [3. The crammed-answer limit →](03-crammed-answers-limitation.md)
&nbsp;·&nbsp; [← Back to How it works](01-how-it-works.md)
