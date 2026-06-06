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

echo "Starting Ollama (if not already running)..."
ollama serve > logs/ollama.log 2>&1 &

echo "Starting RAG backend on :8000"
( cd rag_app && uvicorn api:app --port 8000 ) > logs/rag_api.log 2>&1 &

echo "Starting RAG chat UI on :8501"
streamlit run rag_app/rag_ui.py --server.port 8501 > logs/rag_ui.log 2>&1 &

echo "Starting Plagiarism backend on :8001"
( cd plagiarism_app && uvicorn plagiarism_api:app --port 8001 ) > logs/plag_api.log 2>&1 &

echo "Starting Student UI on :8502"
streamlit run plagiarism_app/student_ui.py --server.port 8502 > logs/student.log 2>&1 &

echo "Starting Teacher UI on :8503"
streamlit run plagiarism_app/teacher_ui.py --server.port 8503 > logs/teacher.log 2>&1 &

echo "Starting Master dashboard on :8500"
streamlit run dashboard/main_dashboard.py --server.port 8500 > logs/dashboard.log 2>&1 &

echo ""
echo "All started. Open the dashboard:  http://localhost:8500"
echo "Logs are in the logs/ folder. Run ./stop_all.sh to stop everything."
