"""
teacher_ui.py  (Streamlit, port 8503)
=====================================
Teacher dashboard: run the analysis, see a clean summary table, then drill into
one student for the original-work vs plagiarism breakdown.
Run:  streamlit run plagiarism_app/teacher_ui.py --server.port 8503
"""

import streamlit as st
import requests
import pandas as pd

API = "http://localhost:8001"

st.set_page_config(page_title="Teacher Reports", page_icon=":material/fact_check:",
                   layout="wide")
st.title(":material/fact_check: Plagiarism Reports")

# --- Run analysis button -------------------------------------------------
if st.button("Run analysis on all submissions", type="primary",
             icon=":material/play_arrow:"):
    # Step 1: prepare (clears old reports, reads files, runs copy check).
    with st.spinner("Reading submissions and comparing for copies..."):
        prep = requests.post(f"{API}/prepare")

    if not prep.ok:
        st.error(prep.text)
    else:
        students = prep.json()["students"]
        total = len(students)

        # Step 2: analyse each student one at a time, with a live progress bar.
        bar = st.progress(0.0, text="Starting...")
        for i, name in enumerate(students, start=1):
            bar.progress((i - 1) / total, text=f"Analysing {name}  ({i} of {total})")
            requests.post(f"{API}/analyze_one/{name}")
            bar.progress(i / total, text=f"Analysed {name}  ({i} of {total})")
        bar.empty()
        st.success(f"Done. Analysed {total} submissions.", icon=":material/check_circle:")

# --- Summary table -------------------------------------------------------
rows = requests.get(f"{API}/all_reports").json()
if not rows:
    st.info("No reports yet. Collect submissions, then click 'Run analysis'.",
            icon=":material/info:")
    st.stop()

# Rename columns to clean, readable headers.
df = pd.DataFrame(rows).rename(columns={
    "student": "Student",
    "integrity_score": "Integrity",
    "verdict": "Verdict",
    "ai_percentage": "AI %",
    "peer_similarity": "Peer Copy %",
    "paraphrase_percent": "Paraphrase %",
})[["Student", "Integrity", "Verdict", "AI %", "Peer Copy %", "Paraphrase %"]]

SCORE_COLS = ["AI %", "Peer Copy %", "Paraphrase %"]


def score_colour(val):
    """Green = safe, amber = check, red = concerning. Dark text for readability."""
    if not isinstance(val, (int, float)):
        return ""
    if val >= 50:
        return "background-color: #fecaca; color: #111"
    if val >= 20:
        return "background-color: #fde68a; color: #111"
    return "background-color: #bbf7d0; color: #111"


def verdict_colour(v):
    return {
        "clean": "color: #16a34a; font-weight: 600",
        "review": "color: #d97706; font-weight: 600",
        "flagged": "color: #dc2626; font-weight: 600",
    }.get(v, "")


styled = (
    df.style
    .map(score_colour, subset=SCORE_COLS)
    .map(verdict_colour, subset=["Verdict"])
    .format("{:.0f}%", subset=SCORE_COLS)   # 85.0 -> "85%"
    .format("{:.0f}", subset=["Integrity"])
)
st.dataframe(styled, use_container_width=True, hide_index=True)

# --- Drill into one student ---------------------------------------------
st.divider()
student = st.selectbox("View detailed report for:", df["Student"])
report = requests.get(f"{API}/report/{student}").json()

# Verdict badge (professional colours, no emoji).
badge_colour = {"clean": "green", "review": "orange", "flagged": "red"}
st.subheader(f"{student}  —  Integrity {report['integrity_score']}/100")
st.badge(report["verdict"].upper(),
         color=badge_colour.get(report["verdict"], "gray"))

pos, neg = report["positive"], report["negative"]
left, right = st.columns(2)

# Positive side: signs the student wrote it themselves.
with left:
    st.markdown("### :material/check_circle: Original work signals")
    st.metric("Originality score", f"{pos['originality_score']}/100")
    st.write(f"Vocabulary diversity: **{pos['vocab_diversity']}%**")
    st.write(f"Sentence-length variation: **{pos['burstiness']}**")
    st.write(f"Personal-voice phrases: **{pos['personal_markers']}**")

# Negative side: the three plagiarism signals.
with right:
    st.markdown("### :material/warning: Plagiarism signals")
    st.write(f"AI-generated: **{neg['ai_percentage']:.0f}%** ({neg['ai_verdict']})")
    if neg.get("ai_reasoning"):
        st.caption(neg["ai_reasoning"])
    st.write(f"Copied from peer ({report.get('closest_peer') or '—'}): "
             f"**{neg['peer_similarity']:.0f}%**")
    st.write(f"Paraphrased / humanized AI: **{neg['paraphrase_percent']:.0f}%**")

# Flagged sentences: light red card, dark text, red left border.
if neg["flagged_sentences"]:
    st.markdown("### :material/error: Lines flagged as AI-written")
    for item in neg["flagged_sentences"]:
        st.markdown(
            f"<div style='background:#fde2e2;color:#111;padding:8px 10px;"
            f"border-left:4px solid #dc2626;border-radius:4px;margin-bottom:6px'>"
            f"{item.get('sentence','')}"
            f"<br><small style='color:#7f1d1d'><i>{item.get('reason','')}</i></small>"
            f"</div>",
            unsafe_allow_html=True,
        )

# Paraphrase matches shown side by side: light purple card, dark text.
if neg["paraphrase_pairs"]:
    st.markdown("### :material/content_copy: Paraphrase matches with peer")
    _style = ("background:#ede9fe;color:#111;padding:8px 10px;"
              "border-left:4px solid #7c3aed;border-radius:4px")
    for p in neg["paraphrase_pairs"]:
        a, b = st.columns(2)
        a.markdown(f"<div style='{_style}'>{p['sentence_a']}</div>", unsafe_allow_html=True)
        b.markdown(f"<div style='{_style}'>{p['sentence_b']}</div>", unsafe_allow_html=True)
        st.caption(f"Meaning similarity: {p['similarity']:.0f}%")
