# My AI Tools — Science RAG + Plagiarism Detector

Two tools under one dashboard, running **100% locally on Ollama**
(`qwen2.5:7b` + `nomic-embed-text`). No paid APIs, no HuggingFace downloads.

## What's inside

```
science_rag_project/
├── dashboard/
│   └── main_dashboard.py     # master launcher              (port 8500)
│
├── rag_app/                  # your existing science tutor
│   ├── app.py                # one-time: build FAISS index from the PDF
│   ├── api.py                # RAG backend, /ask endpoint    (port 8000)
│   ├── rag_ui.py             # NEW chat interface            (port 8501)
│   ├── 10th_science_book.pdf
│   └── faiss_science_index/
│
├── plagiarism_app/
│   ├── plagiarism_api.py     # backend: /submit /run_analysis /report (port 8001)
│   ├── student_ui.py         # students upload assignments   (port 8502)
│   ├── teacher_ui.py         # teacher report dashboard      (port 8503)
│   ├── report_builder.py     # combines scores into one report
│   └── detectors/
│       ├── ollama_client.py  # one place that talks to Ollama
│       ├── text_extractor.py # PDF / DOCX / PPTX -> text
│       ├── ai_detector.py    # Qwen2.5 judges AI vs human
│       ├── copy_checker.py   # TF-IDF cosine (student vs student)
│       ├── paraphrase.py     # nomic-embed meaning match (humanized AI)
│       └── originality.py    # positive "own work" score
│
├── submissions/              # uploaded files land here
├── reports/                  # generated JSON reports land here
├── requirements.txt
├── run_all.sh / stop_all.sh
```

## How the plagiarism flow works

1. Student uploads a file → saved in `submissions/`.
2. Teacher clicks **Run analysis**. For every file:
   - extract text,
   - **AI check** (Qwen): is it AI-written?
   - **copy check** (TF-IDF): too similar to another student?
   - **paraphrase check** (embeddings): same meaning as a peer, reworded?
   - **originality** (math): signs the student wrote it themselves.
3. Each student gets an **integrity score (0–100)** + a report saved in `reports/`.
4. Teacher views a colour-coded table and drills into any student.

## Setup (do once)

```bash
# 1. Install Ollama from https://ollama.com, then:
ollama pull qwen2.5:7b
ollama pull nomic-embed-text

# 2. Python dependencies
pip install -r requirements.txt

# 3. Build the science index (first time only)
cd rag_app && python app.py    # type 'exit' once it's ready, then go back: cd ..
```

## Run everything

```bash
./run_all.sh          # starts all services
# open http://localhost:8500
./stop_all.sh         # stop them later
```

Or start any single app manually, e.g.:
```bash
streamlit run plagiarism_app/teacher_ui.py --server.port 8503
```

## Notes

- Ollama must be installed and the two models pulled before the AI features work.
  Until then the apps still launch; AI calls just return an "unavailable" message.
- The Ollama address defaults to `http://localhost:11434`. Override with
  `export OLLAMA_HOST=...` if it runs elsewhere.
```
```
