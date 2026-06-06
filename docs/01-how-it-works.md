# 1. How It Works — The Big Picture

This doc explains **what the project is**, **how data flows through it**, and
**why each tool and model was chosen**. No prior AI knowledge needed.

---

## 1.1 What is this project?

It's **two separate tools living under one dashboard**, both running fully on
your own machine (no paid APIs, no internet needed once set up):

1. **🔬 Science Tutor (RAG)** — ask questions about a 10th-grade science
   textbook and get answers drawn only from the book.
2. **🕵️ Plagiarism Detector** — students upload assignments; teachers get a
   report showing AI-generated, copied, and paraphrased content.

A **master dashboard** is just a menu page that links to both.

---

## 1.2 The folder layout

```
science_rag_project/
├── dashboard/        → the menu page that links to both tools   (port 8500)
├── rag_app/          → the Science Tutor
│   ├── app.py        → one-time: reads the PDF, builds the search index
│   ├── api.py        → the tutor's backend / brain               (port 8000)
│   └── rag_ui.py     → the chat screen you type into             (port 8501)
├── plagiarism_app/   → the Plagiarism Detector
│   ├── plagiarism_api.py → the backend that runs all the checks  (port 8001)
│   ├── student_ui.py     → upload page for students             (port 8502)
│   ├── teacher_ui.py     → report page for teachers             (port 8503)
│   ├── report_builder.py → combines all scores into one report
│   └── detectors/        → the actual checking logic (see doc #2)
├── submissions/      → uploaded student files land here
├── reports/          → generated reports are saved here
└── docs/             → you are here
```

**Why split into "backend" and "UI" files?**
The UI (what you see) and the backend (the heavy thinking) are kept separate so
the logic lives in ONE place. Both the student page and teacher page talk to the
same backend — we never copy-paste the detection code twice.

---

## 1.3 The two AI models (and why two)

| Model | Job | Think of it as |
|-------|-----|----------------|
| `qwen2.5` (3b or 7b) | reads, reasons, writes answers | the **brain / tutor** |
| `nomic-embed-text` | turns text into numbers that capture **meaning** | a **meaning-ruler** |

They do **different jobs** and can't replace each other:

- `nomic-embed-text` only converts text → numbers. It can't write or judge. It's
  used to **search** (find the right textbook pages) and to **compare meaning**
  (catch reworded copying).
- `qwen2.5` actually **thinks** — it writes the tutor's answers and judges whether
  an essay looks AI-written.

> Short version: **`nomic` finds & compares, `qwen` thinks & writes.**
> On an 8 GB Mac, use `qwen2.5:3b` — see [doc #2](02-detection-methods.md) for why 3b is fine.

---

## 1.4 Flow A — The Science Tutor (RAG)

**RAG = Retrieval-Augmented Generation.** Instead of trusting the AI's memory, we
*retrieve* real textbook pages and make the AI answer from them. This stops it
making things up.

**Setup (once):** `app.py`
1. Read the textbook PDF.
2. Chop it into small chunks (~1000 characters each).
3. Turn every chunk into meaning-numbers with `nomic-embed-text`.
4. Save them all into a fast search index called **FAISS** (the `faiss_science_index/` folder).

**Every question:** `rag_ui.py` → `api.py`
1. You type a question in the chat (`rag_ui.py`).
2. The question is turned into meaning-numbers.
3. FAISS finds the **3 closest** textbook chunks.
4. Those chunks + your question are handed to `qwen2.5`.
5. Qwen writes an answer using only those chunks → shown back in the chat.

```
You ──question──▶ nomic (to numbers) ──▶ FAISS (find 3 chunks)
                                            │
                  chunks + question ────────┘
                          │
                          ▼
                       qwen2.5 ──answer──▶ You
```

---

## 1.5 Flow B — The Plagiarism Detector

**Student side:** `student_ui.py`
- Student types their name and uploads a file → it's saved in `submissions/`.
- No checking happens yet — uploading is fast.

**Teacher side:** `teacher_ui.py` → `plagiarism_api.py`
- Teacher clicks **Run analysis**. For every submitted file the backend:
  1. **Extracts text** (`text_extractor.py`) — pulls words out of PDF/Word/PPT/TXT.
  2. **AI check** (`ai_detector.py`) — Qwen judges: AI-written or human?
  3. **Copy check** (`copy_checker.py`) — compares words across all students.
  4. **Paraphrase check** (`paraphrase.py`) — compares *meaning* across students.
  5. **Originality** (`originality.py`) — positive signs of own work.
- All scores are combined (`report_builder.py`) into one **integrity score (0–100)**
  per student and saved in `reports/`.
- The teacher sees a colour-coded table and can open any student's full report.

```
Student ──upload──▶ submissions/
                         │
Teacher clicks "Run analysis"
                         ▼
   text extract → [AI check] [copy check] [paraphrase] [originality]
                         │
                         ▼
              report_builder → integrity score → reports/ → Teacher's table
```

The 3 detection methods are explained in detail in
**[doc #2](02-detection-methods.md)**.

---

## 1.6 Why we used each tool (the "why what")

| Tool | What it does here | Why this one |
|------|-------------------|--------------|
| **Ollama** | runs the AI models on your computer | free, local, private — no API bills, no data leaves your machine |
| **qwen2.5** | writes tutor answers, judges AI text | strong open model that runs locally; good reasoning for its size |
| **nomic-embed-text** | text → meaning-numbers | small, fast, accurate embeddings; powers both search and paraphrase-detection |
| **FAISS** | stores & searches the textbook numbers | extremely fast similarity search, runs offline, saves to disk |
| **LangChain** | glue that wires PDF → chunks → FAISS → Qwen | saves writing the RAG plumbing by hand |
| **FastAPI** | the backends (ports 8000 / 8001) | fast, simple Python web framework with auto test-page at `/docs` |
| **Streamlit** | all the screens (dashboard, chat, upload, reports) | build a web UI in pure Python — no HTML/CSS/JS needed |
| **scikit-learn** | TF-IDF copy check | industry-standard, exact, no AI needed for word-matching |
| **PyMuPDF / python-docx / python-pptx** | read PDF / Word / PowerPoint | each file type stores text differently; one library per format |
| **pandas** | the teacher's summary table | easy tables with colour highlighting |

**What we deliberately did NOT use:** HuggingFace classifiers or
`sentence-transformers` (big downloads) and paid detectors (OpenAI, Copyleaks).
Everything AI goes through Ollama instead — fewer downloads, no costs, fully local.

---

## 1.7 The ports cheat-sheet

| Service | Port | File |
|---------|------|------|
| Master dashboard | 8500 | `dashboard/main_dashboard.py` |
| RAG backend | 8000 | `rag_app/api.py` |
| RAG chat UI | 8501 | `rag_app/rag_ui.py` |
| Plagiarism backend | 8001 | `plagiarism_app/plagiarism_api.py` |
| Student upload UI | 8502 | `plagiarism_app/student_ui.py` |
| Teacher report UI | 8503 | `plagiarism_app/teacher_ui.py` |
| Ollama (the models) | 11434 | installed separately |

Start everything with `./run_all.sh`, then open <http://localhost:8500>.

---

**Next:** [2. Detection methods →](02-detection-methods.md)
