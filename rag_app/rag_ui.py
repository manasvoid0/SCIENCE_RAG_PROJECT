"""
rag_ui.py  (Streamlit chat, port 8501)
======================================
A proper chat interface for your existing RAG backend (api.py on port 8000).
It just calls the /ask endpoint and shows the conversation -- the heavy AI work
stays in api.py.
Run:  streamlit run rag_app/rag_ui.py --server.port 8501
"""

import streamlit as st
import requests

API = "http://localhost:8000"  # your existing RAG FastAPI backend

st.set_page_config(page_title="Science Tutor", page_icon="🔬")
st.title("🔬 10th Grade Science Tutor")
st.caption("Ask anything from the textbook. Answers come only from the book.")

# Keep the chat history across reruns using Streamlit's session memory.
if "messages" not in st.session_state:
    st.session_state.messages = []

# Replay the existing conversation.
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input box at the bottom.
question = st.chat_input("Your question...")
if question:
    # Show the user's message immediately.
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # Ask the backend and show the answer.
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                res = requests.post(f"{API}/ask", json={"question": question}, timeout=300)
                answer = res.json().get("answer", res.text) if res.ok else f"Error: {res.text}"
            except Exception as e:
                answer = f"Could not reach the tutor backend (is api.py running?). {e}"
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
