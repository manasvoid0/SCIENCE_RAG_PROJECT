#!/bin/bash
# run_all.sh -- starts every service in the background, on its own port.
# Stop everything later with:  ./stop_all.sh
#
# Prerequisites (do these once first):
#   1. Install Ollama from https://ollama.com
#   2. ollama pull qwen2.5:7b
#   3. ollama pull nomic-embed-text
#   4. cd rag_app && python app.py    # builds the FAISS index (first time only)
#   5. pip install -r requirements.txt

cd "$(dirname "$0")"   # always run from the project root
mkdir -p logs

# Use the project's virtual environment tools so this works without activating.
PY="$(pwd)/.venv/bin"
UVICORN="$PY/uvicorn"
STREAMLIT="$PY/streamlit"

# NOTE: Ollama is started by the Ollama menu-bar app (installed via ollama-app),
# so we do NOT start it here. Make sure the llama icon is in your menu bar.

echo "Starting RAG backend on :8000"
( cd rag_app && "$UVICORN" api:app --port 8000 ) > logs/rag_api.log 2>&1 &

echo "Starting RAG chat UI on :8501"
"$STREAMLIT" run rag_app/rag_ui.py --server.port 8501 --server.headless true > logs/rag_ui.log 2>&1 &

echo "Starting Plagiarism backend on :8001"
( cd plagiarism_app && "$UVICORN" plagiarism_api:app --port 8001 ) > logs/plag_api.log 2>&1 &

echo "Starting Student UI on :8502"
"$STREAMLIT" run plagiarism_app/student_ui.py --server.port 8502 --server.headless true > logs/student.log 2>&1 &

echo "Starting Teacher UI on :8503"
"$STREAMLIT" run plagiarism_app/teacher_ui.py --server.port 8503 --server.headless true > logs/teacher.log 2>&1 &

echo "Starting Master dashboard on :8500"
"$STREAMLIT" run dashboard/main_dashboard.py --server.port 8500 --server.headless true > logs/dashboard.log 2>&1 &

echo ""
echo "All started. Open the dashboard:  http://localhost:8500"
echo "Logs are in the logs/ folder. Run ./stop_all.sh to stop everything."
