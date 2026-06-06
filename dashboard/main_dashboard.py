"""
main_dashboard.py  (Streamlit, port 8500)
=========================================
The master launcher. One page with cards that link to each tool's UI.
The other apps must already be running on their ports (see README / run_all.sh).
Run:  streamlit run dashboard/main_dashboard.py --server.port 8500
"""

import streamlit as st

st.set_page_config(page_title="My AI Tools", page_icon="🧰", layout="centered")
st.title("🧰 My AI Tools Dashboard")
st.markdown("Pick a tool to open it in a new tab.")
st.markdown("---")

col1, col2 = st.columns(2)

# --- R&D: Science Tutor card ---
with col1:
    st.subheader("🔬 R&D — Science Tutor")
    st.write("Ask questions from the 10th grade science textbook (RAG + Qwen2.5).")
    st.link_button("Open Science Tutor →", "http://localhost:8501",
                   use_container_width=True)

# --- Plagiarism card ---
with col2:
    st.subheader("🕵️ Plagiarism Detector")
    st.write("Students upload assignments; teachers get AI/copy/paraphrase reports.")
    st.link_button("Student Portal →", "http://localhost:8502",
                   use_container_width=True)
    st.link_button("Teacher Reports →", "http://localhost:8503",
                   use_container_width=True)
