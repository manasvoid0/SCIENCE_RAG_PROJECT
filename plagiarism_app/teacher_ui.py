"""
teacher_ui.py  (Streamlit, port 8503)
=====================================
Teacher dashboard: run the analysis, see a colour-coded summary table, then
drill into one student to see the positive (originality) and negative
(AI / copy / paraphrase) sides with flagged lines highlighted.
Run:  streamlit run plagiarism_app/teacher_ui.py --server.port 8503
"""

import streamlit as st
import requests
import pandas as pd

API = "http://localhost:8001"

st.set_page_config(page_title="Teacher Reports", page_icon="🧑‍🏫", layout="wide")
st.title("🧑‍🏫 Plagiarism Reports")

# --- Run analysis button -------------------------------------------------
if st.button("▶ Run analysis on all submissions", type="primary"):
    with st.spinner("Analysing every submission (this can take a while)..."):
        res = requests.post(f"{API}/run_analysis")
    if res.ok:
        st.success(f"Done. Analysed {res.json()['count']} submissions.")
    else:
        st.error(res.text)

# --- Summary table -------------------------------------------------------
rows = requests.get(f"{API}/all_reports").json()
if not rows:
    st.info("No reports yet. Collect submissions, then click 'Run analysis'.")
    st.stop()

df = pd.DataFrame(rows)


def colour(val):
    """Green = safe, yellow = check, red = concerning (for score columns)."""
    if not isinstance(val, (int, float)):
        return ""
    if val >= 50:
        return "background-color: #fee2e2"  # red-ish
    if val >= 20:
        return "background-color: #fef9c3"  # yellow-ish
    return "background-color: #dcfce7"      # green-ish


score_cols = ["ai_percentage", "peer_similarity", "paraphrase_percent"]
st.dataframe(df.style.applymap(colour, subset=score_cols), use_container_width=True)

# --- Drill into one student ---------------------------------------------
st.markdown("---")
student = st.selectbox("View detailed report for:", df["student"])
report = requests.get(f"{API}/report/{student}").json()

# Overall verdict badge.
verdict_colour = {"clean": "🟢", "review": "🟡", "flagged": "🔴"}
st.subheader(
    f"{verdict_colour.get(report['verdict'], '⚪')} "
    f"{student} — Integrity {report['integrity_score']}/100 "
    f"({report['verdict'].upper()})"
)

pos, neg = report["positive"], report["negative"]
left, right = st.columns(2)

# Positive side: signs the student wrote it themselves.
with left:
    st.markdown("### ✅ Positive (own work signals)")
    st.metric("Originality score", f"{pos['originality_score']}/100")
    st.write(f"Vocabulary diversity: **{pos['vocab_diversity']}%**")
    st.write(f"Sentence-length variation (burstiness): **{pos['burstiness']}**")
    st.write(f"Personal-voice phrases: **{pos['personal_markers']}**")

# Negative side: the three plagiarism signals.
with right:
    st.markdown("### ⚠️ Negative (plagiarism signals)")
    st.write(f"AI-generated: **{neg['ai_percentage']}%** ({neg['ai_verdict']})")
    if neg.get("ai_reasoning"):
        st.caption(neg["ai_reasoning"])
    st.write(f"Copied from peer ({report.get('closest_peer') or '—'}): "
             f"**{neg['peer_similarity']}%**")
    st.write(f"Paraphrased / humanized AI: **{neg['paraphrase_percent']}%**")

# Flagged sentences highlighted in red.
if neg["flagged_sentences"]:
    st.markdown("### 🔴 Lines flagged as AI-written")
    for item in neg["flagged_sentences"]:
        st.markdown(
            f"<div style='background:#fee2e2;padding:6px;border-radius:4px;"
            f"margin-bottom:4px'>{item.get('sentence','')}"
            f"<br><small><i>{item.get('reason','')}</i></small></div>",
            unsafe_allow_html=True,
        )

# Paraphrase matches shown side by side.
if neg["paraphrase_pairs"]:
    st.markdown("### 🟣 Paraphrase matches with peer")
    for p in neg["paraphrase_pairs"]:
        a, b = st.columns(2)
        a.markdown(f"<div style='background:#f3e8ff;padding:6px;border-radius:4px'>"
                   f"{p['sentence_a']}</div>", unsafe_allow_html=True)
        b.markdown(f"<div style='background:#f3e8ff;padding:6px;border-radius:4px'>"
                   f"{p['sentence_b']}</div>", unsafe_allow_html=True)
        st.caption(f"Meaning similarity: {p['similarity']}%")
