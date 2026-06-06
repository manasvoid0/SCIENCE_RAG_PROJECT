"""
student_ui.py  (Streamlit, port 8502)
=====================================
Where students upload their assignment. It just sends the file to the backend
(/submit) -- no detection happens here.
Run:  streamlit run plagiarism_app/student_ui.py --server.port 8502
"""

import streamlit as st
import requests

API = "http://localhost:8001"  # the plagiarism backend

st.set_page_config(page_title="Submit Assignment", page_icon="📤")
st.title("📤 Submit your assignment")

name = st.text_input("Your name")
# type=None -> accept ANY file. The backend reads PDF/DOCX/PPTX/TXT; other
# types are saved but will be skipped during analysis with a clear message.
file = st.file_uploader("Upload your assignment (any file)")
st.caption("Best results with PDF, Word (.docx), PowerPoint (.pptx) or .txt files.")

if st.button("Submit", type="primary"):
    if not name or not file:
        st.warning("Please enter your name and choose a file.")
    else:
        # Send name (form field) + file (upload) to the backend.
        res = requests.post(
            f"{API}/submit",
            data={"student_name": name},
            files={"file": (file.name, file.getvalue())},
        )
        if res.ok:
            st.success("✅ Submitted! Your teacher will review the report.")
        else:
            st.error(f"Upload failed: {res.text}")
