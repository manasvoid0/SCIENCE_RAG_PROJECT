# 4. Running on Windows

A complete, beginner-friendly guide to run this project on a **Windows 10 / 11**
PC. Everything stays local (no paid APIs).

---

## 4.1 Requirements

| Need | Details |
|------|---------|
| OS | Windows 10 or 11 (64-bit) |
| RAM | **8 GB minimum** (use `qwen2.5:3b`). 16 GB+ can use `qwen2.5:7b`. |
| Disk | ~6 GB free (models + libraries) |
| Python | **3.12** (NOT 3.13/3.14 — some AI libraries lack wheels for those) |
| Ollama | Ollama for Windows (runs the AI models locally) |
| The PDF | `10th_science_book.pdf` inside the `rag_app/` folder (needed once to build the search index) |

---

## 4.2 Step 1 — Install Python 3.12

1. Download **Python 3.12** from <https://www.python.org/downloads/windows/>.
2. Run the installer and **tick "Add python.exe to PATH"** on the first screen.
3. Verify in a new **Command Prompt** (search "cmd" in Start menu):
   ```bat
   py -3.12 --version
   ```
   It should print `Python 3.12.x`.

---

## 4.3 Step 2 — Install Ollama and the models

1. Download **Ollama for Windows** from <https://ollama.com/download/windows>.
2. Run `OllamaSetup.exe`. It installs and starts automatically (you'll see a small
   llama icon in the system tray / bottom-right). It listens on
   `http://localhost:11434`.
3. Pull the two models — in Command Prompt:
   ```bat
   ollama pull qwen2.5:3b
   ollama pull nomic-embed-text
   ```
4. Verify:
   ```bat
   ollama list
   ```
   You should see both models. Quick test:
   ```bat
   ollama run qwen2.5:3b "say hello"
   ```
   (Press `Ctrl + D` to exit.)

---

## 4.4 Step 3 — Set up the project

Open Command Prompt and go to the project folder (adjust the path to where you
put it):

```bat
cd C:\Users\YOUR_NAME\Downloads\science_rag_project
```

Create and activate a **virtual environment** (an isolated package folder):

```bat
py -3.12 -m venv .venv
.venv\Scripts\activate
```

Your prompt now starts with `(.venv)`. Install the libraries:

```bat
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> **Remember:** every new Command Prompt window for this project must run
> `.venv\Scripts\activate` first.

---

## 4.5 Step 4 — Build the science search index (once)

This reads the textbook PDF and builds the FAISS index. Do it only the first time
(or whenever the PDF changes):

```bat
cd rag_app
python app.py
```

Wait until you see **"Your AI Tutor is Ready!"**, type `exit`, then go back:

```bat
cd ..
```

---

## 4.6 Step 5 — Run everything

The easy way — double-click **`run_all.bat`** in the project folder, OR from
Command Prompt:

```bat
run_all.bat
```

This opens one window per service. Wait ~15 seconds, then open your browser to:

### 👉 http://localhost:8500   (the master dashboard)

From there:
- **Science Tutor** — ask questions from the textbook.
- **Teacher Reports** — click *Run analysis* to score all submissions.
- **Student Portal** — upload an assignment.

> The Ollama tray app must be running (llama icon visible). The first answer is
> slow (~10–20s) while the model loads, then it speeds up.

---

## 4.7 Stopping

Double-click **`stop_all.bat`**, or run:

```bat
stop_all.bat
```

(You can also just close the individual service windows.)

---

## 4.8 The ports

| Service | URL |
|---------|-----|
| Master dashboard | http://localhost:8500 |
| Science Tutor chat | http://localhost:8501 |
| Student upload | http://localhost:8502 |
| Teacher reports | http://localhost:8503 |
| RAG backend | http://localhost:8000 |
| Plagiarism backend | http://localhost:8001 |

---

## 4.9 Common problems

| Problem | Fix |
|---------|-----|
| `'python' is not recognized` | Use `py -3.12` instead, or reinstall Python with "Add to PATH" ticked. |
| `pip install` errors about Python version | You're on 3.13/3.14. Install **3.12** and recreate the venv with `py -3.12 -m venv .venv`. |
| Pages show "Could not reach backend" | Make sure `run_all.bat` finished and the backend windows are open. |
| AI features error / "unavailable" | The Ollama tray app isn't running, or models aren't pulled. Re-check Step 2. |
| `streamlit` asks for an email | Press Enter to skip, or it's already handled by `--server.headless true`. |

---

[← Back to docs index](README.md)
