# 5. Code Walkthrough — Every File Explained

This doc explains **what every file in the project does**, in plain language, so
you can explain it to a complete beginner. Read it top to bottom — it follows the
same order as the data flows.

> **Mental model first.** The project has two "engines" (called *backends*) that
> do the thinking, and several "screens" (called *UIs*) that people click on. The
> screens never think for themselves — they just send a request to a backend and
> show what comes back. Keep that picture in mind and everything below clicks.

---

## Part A — Words a beginner needs (30-second glossary)

| Word | Plain meaning |
|------|---------------|
| **Model** | A trained AI file. We use two: `qwen2.5` (writes/judges) and `nomic-embed-text` (turns text into numbers). |
| **Ollama** | A program that runs those models on your own computer. |
| **Embedding / vector** | A list of numbers that represents the *meaning* of text. |
| **FAISS** | A super-fast "find the most similar numbers" database. |
| **RAG** | Retrieval-Augmented Generation: find real text first, then let the AI answer from it. |
| **Backend / API** | A program that listens for requests and sends back answers (no buttons). |
| **Endpoint** | One specific "address" on a backend, like `/ask` or `/submit`. |
| **Streamlit** | A tool that turns Python into a web page with buttons — the screens. |
| **FastAPI** | A tool that builds the backends. |
| **JSON** | A simple text format for data, like a labelled box: `{"name": "Ravi", "score": 85}`. |

---

## Part B — The Science Tutor (RAG)

### `rag_app/app.py` — the index builder + terminal tutor

This file does the **one-time setup** and also has a simple text-only chat.

1. **Checks if the index already exists.** If the `faiss_science_index` folder is
   there, it skips straight to loading it (fast). If not, it builds it.
2. **Builds the index (first run only):**
   - Opens the textbook PDF and reads it page by page.
   - **Chops** the text into ~1000-character chunks (with 200 characters of
     overlap so a sentence isn't cut in half between two chunks).
   - Turns every chunk into numbers using `nomic-embed-text`.
   - Saves all those numbers into the **FAISS** folder on disk.
3. **Sets up the tutor:** loads `qwen2.5`, and writes a *system prompt* — the
   strict rule: *"Answer using ONLY the textbook. If it's not there, say so."*
   This is what stops the AI from making things up.
4. **The chat loop:** waits for you to type a question, finds the 3 most relevant
   chunks, hands them to Qwen, prints the answer. Type `exit` to quit.

> Key idea to explain: the AI is **not** answering from memory — it's answering
> from the 3 textbook pieces we *found and gave it*. That's RAG.

### `rag_app/api.py` — the tutor as a web service

Same tutor brain as `app.py`, but instead of a terminal loop it's a **web
backend** other programs can call. It:
- Loads the saved index and Qwen when it starts.
- Exposes **one endpoint**: `POST /ask`. You send `{"question": "..."}`, it
  returns `{"answer": "..."}`.
- Wraps the work in a `try/except` so if something breaks, it returns a clear
  error instead of crashing silently.

> `app.py` builds the index; `api.py` serves answers over the web. They share the
> same FAISS folder.

### `rag_app/rag_ui.py` — the chat screen

A Streamlit page (the thing you actually see in the browser). It:
- Keeps the conversation history on screen.
- When you type a question, it sends it to `api.py`'s `/ask` endpoint and shows
  the reply as a chat bubble.
- Does **no AI itself** — it's just the friendly front for `api.py`.

---

## Part C — The Plagiarism Detector

The detectors live in `plagiarism_app/detectors/`. Each one does **one job**.

### `detectors/ollama_client.py` — the single phone line to Ollama

A tiny helper so there's **one place** that knows Ollama's address
(`http://localhost:11434`). It offers three functions:
- `generate(prompt)` → ask Qwen a question, get text back.
- `embed(text)` → turn text into meaning-numbers with `nomic-embed-text`.
- `extract_json(text)` → clean up Qwen's answer into usable data.

> Why this matters: if Ollama ever moves to another computer or port, you change
> **one line here** instead of hunting through every file.

### `detectors/text_extractor.py` — get the words out of any file

Takes an uploaded PDF / Word / PowerPoint / text file and returns just the raw
words (ignores images and formatting). Each file type needs its own reader
library, so there's a small function per type, and one `extract_text()` that
picks the right one based on the file extension.

### `detectors/copy_checker.py` — catch copy-paste between students (TF-IDF)

Pure math, no AI. It turns each student's text into number-lists based on
**which words** they used, then compares everyone to everyone. High overlap = one
likely copied the other. Returns the matching pairs and each student's worst
match. *(See [doc 2](02-detection-methods.md) for the deeper how.)*

### `detectors/paraphrase.py` — catch reworded copying (embeddings)

Uses `nomic-embed-text`. It turns each sentence into a **meaning-vector**, then
compares meanings between two students. Different words but the same meaning still
score high — this catches "humanized" AI text that dodges the word-based copy
check.

### `detectors/ai_detector.py` — catch AI-written text (Qwen)

The only detector that needs the thinking model. It sends the student's text to
Qwen with a careful prompt: *"Act as an academic-integrity expert. Is this
AI-written? Reply in this exact JSON format."* It then reads back an
`ai_percentage`, a verdict, the reasoning, and flagged sentences. If Ollama is
off, it returns a safe "unavailable" result instead of crashing.

### `detectors/originality.py` — the POSITIVE score (pure math)

Measures signs the student wrote it themselves:
- **Vocabulary diversity** — humans reuse fewer exact words.
- **Burstiness** — humans vary sentence length; AI tends to be flat.
- **Personal markers** — phrases like *"I think"*, *"for example"*.

Combines them into a 0–100 originality score. No AI needed.

### `report_builder.py` — combine everything into one report

Takes all four detector results for one student and produces:
- a **negative score** (weighted blend of AI %, copy %, paraphrase %),
- an **integrity score (0–100)** = start at 100, subtract the bad signals, add a
  little for originality,
- a **verdict**: `clean` (≥70), `review` (40–69), or `flagged` (<40).

> This is the "judgment" layer — but remember, the **teacher** decides; the system
> only scores. (See [doc 3](03-crammed-answers-limitation.md).)

### `plagiarism_app/plagiarism_api.py` — the plagiarism backend

The web service the screens talk to. Its endpoints:
- `POST /submit` — save a student's uploaded file into `submissions/`.
- `POST /prepare` — clear old reports, read every file, run the copy check, and
  work out each student's closest peer. (Fast.)
- `POST /analyze_one/{student}` — run the slow per-student checks (AI +
  originality + paraphrase) for one student and save their report.
- `POST /run_analysis` — do all students at once (used outside the UI).
- `GET /all_reports` — the summary rows for the teacher's table.
- `GET /report/{student}` — one student's full detailed report.

> **Why `prepare` + `analyze_one` are separate:** so the teacher screen can show a
> **progress bar** that moves student-by-student, instead of one long blank wait.

### `plagiarism_app/student_ui.py` — the student upload screen

Very simple: type your name, pick a file, click Submit. It sends the file to
`/submit`. No analysis happens here — uploading is instant.

### `plagiarism_app/teacher_ui.py` — the teacher dashboard

The richest screen. It:
1. Has a **Run analysis** button that calls `/prepare`, then loops calling
   `/analyze_one` for each student while showing a **progress bar**.
2. Shows a clean **summary table** with color-coded percentages and a verdict
   badge per student.
3. Lets the teacher pick a student to see the **detailed report**: the positive
   (own-work) side, the negative (plagiarism) side, the exact lines flagged as
   AI-written, and side-by-side paraphrase matches.

---

## Part D — The glue

### `dashboard/main_dashboard.py` — the master menu

One simple page with cards linking to each tool (Science Tutor, Student Portal,
Teacher Reports). It's just a friendly front door — it launches nothing itself,
it only links to the other screens' web addresses.

### `run_all.sh` / `run_all.bat` — start everything

Scripts that launch all six services at once, each on its own port
(`.sh` for Mac/Linux, `.bat` for Windows). `stop_all` shuts them down.

### `requirements.txt` — the shopping list

The list of Python libraries the project needs. `pip install -r requirements.txt`
installs them all. Note: the AI models are **not** here — those come from Ollama.

### `.gitignore` — what NOT to share

Tells git to skip the virtual environment, the big PDF, the generated index,
private student uploads, and logs when you push the code.

---

## Part E — The whole journey in one breath

**Science Tutor:** you type a question → `rag_ui.py` sends it to `api.py` →
`nomic-embed-text` turns it into numbers → FAISS finds the 3 closest textbook
chunks → `qwen2.5` writes an answer from them → you see it.

**Plagiarism:** students upload files via `student_ui.py` → saved by
`plagiarism_api.py` → teacher clicks Run analysis → backend extracts text, runs
the copy/paraphrase/AI/originality checks → `report_builder.py` combines them into
an integrity score → `teacher_ui.py` shows the colour-coded report → the teacher
makes the final call.

> **The one sentence to leave a beginner with:** *"Two small AI models run on the
> computer; one finds and compares text, the other reads and judges it — and
> every screen is just a button that asks those models a question."*

---

[← Back to docs index](README.md)
