@echo off
REM ===========================================================================
REM run_all.bat  --  start every service in its own window (Windows).
REM Prerequisites (do once first): see docs\04-run-on-windows.md
REM   1. Install Ollama for Windows + pull qwen2.5:3b and nomic-embed-text
REM   2. py -3.12 -m venv .venv  &  .venv\Scripts\activate  &  pip install -r requirements.txt
REM   3. cd rag_app  &  python app.py   (builds the index, first time only)
REM ===========================================================================

set ROOT=%~dp0
set BIN=%ROOT%.venv\Scripts

if not exist "%BIN%\streamlit.exe" (
  echo ERROR: virtual environment not found.
  echo Run:  py -3.12 -m venv .venv  then  .venv\Scripts\activate  then  pip install -r requirements.txt
  pause
  exit /b 1
)

echo Starting RAG backend on :8000
start "RAG backend (8000)" cmd /k "cd /d %ROOT%rag_app && "%BIN%\uvicorn.exe" api:app --port 8000"

echo Starting RAG chat UI on :8501
start "RAG chat UI (8501)" cmd /k ""%BIN%\streamlit.exe" run "%ROOT%rag_app\rag_ui.py" --server.port 8501 --server.headless true"

echo Starting Plagiarism backend on :8001
start "Plagiarism backend (8001)" cmd /k "cd /d %ROOT%plagiarism_app && "%BIN%\uvicorn.exe" plagiarism_api:app --port 8001"

echo Starting Student UI on :8502
start "Student UI (8502)" cmd /k ""%BIN%\streamlit.exe" run "%ROOT%plagiarism_app\student_ui.py" --server.port 8502 --server.headless true"

echo Starting Teacher UI on :8503
start "Teacher UI (8503)" cmd /k ""%BIN%\streamlit.exe" run "%ROOT%plagiarism_app\teacher_ui.py" --server.port 8503 --server.headless true"

echo Starting Master dashboard on :8500
start "Dashboard (8500)" cmd /k ""%BIN%\streamlit.exe" run "%ROOT%dashboard\main_dashboard.py" --server.port 8500 --server.headless true"

echo.
echo All started. Open the dashboard:  http://localhost:8500
echo Close the windows or run stop_all.bat to stop everything.
