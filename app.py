import streamlit as st
from PyPDF2 import PdfReader
from docx import Document
import io
import pandas as pd

from data_sources import collect_jobs
from matching import compute_matches


# ---------------------------------------------------------
# Streamlit App Initialization
# ---------------------------------------------------------

st.set_page_config(page_title="EU Job Hunt Automation", layout="wide")
st.title("🚀 EU Job Hunt Automation")
st.write("Upload your CV and let the system find top-matching HR leadership roles across the EU.")


# ---------------------------------------------------------
# 1. Upload CV (PDF or DOCX)
# ---------------------------------------------------------

cv_file = st.file_uploader("📄 Upload your CV (PDF or Word)", type=["pdf", "docx"])

cv_text = ""

if cv_file:

    file_type = cv_file.name.lower()

    # --- PDF Extraction ---
    if file_type.endswith(".pdf"):
        try:
            reader = PdfReader(io.BytesIO(cv_file.read()))
            cv_text = " ".join([page.extract_text() or "" for page in reader.pages])
        except Exception as e:
            st.error("❌ Could not extract text from PDF. Try another file.")
            st.stop()

    # --- DOCX Extraction ---
    elif file_type.endswith(".docx"):
        try:
            document = Document(io.BytesIO(cv_file.read()))
            cv_text = "\n".join([p.text for p in document.paragraphs])
        except Exception as e:
            st.error("❌ Could not extract text from DOCX. Try another file.")
            st.stop()

    if not cv_text.strip():
        st.error("⚠️ Could not extract readable text from the file.")
        st.stop()

    st.success("✅ CV uploaded and parsed successfully.")
    st.write(f"🔍 Extracted {len(cv_text)} characters from your CV.")


# ---------------------------------------------------------
# 2. Search configuration
# ---------------------------------------------------------

st.subheader("🔎 Search Settings")

countries = st.multiselect(
    "Select countries",
    ["Germany", "Netherlands", "UK", "Ireland", "Spain", "Portugal", "Romania"],
    default=["Germany", "Netherlands", "UK"]
)

keywords = st.text_input(
    "Search keywords",
    value="HR Director OR Head of HR OR HR Leadership"
)

run_search = st.button("🔍 Find Matching Jobs")


# ---------------------------------------------------------
# 3. Run job search
# ---------------------------------------------------------

if run_search:

    if not cv_text:
        st.error("⚠️ Please upload your CV first.")
        st.stop()

    st.info("⏳ Fetching jobs from free EU job sources. Please wait...")

    jobs = collect_jobs(keywords, countries)

    if not jobs:
        st.warning("No jobs found from the selected sources.")
        st.stop()

    st.success(f"📥 Retrieved {len(jobs)} jobs. Computing match scores...")

    results = compute_matches(cv_text, jobs)

    if not results:
        st.warning("No strong matches found.")
        st.stop()


    # -----------------------------------------------------
    # 4. Display results
    # -----------------------------------------------------

    st.subheader("🎯 Top Matching Jobs")

    df = pd.DataFrame(results)
    df_sorted = df.sort_values(by="score", ascending=False)

    for _, row in df_sorted.iterrows():
        with st.expander(f"{row['score']}% — {row['title']} at {row['company']}"):
            st.write(f"**Source:** {row['source']}")
            st.write(f"**Location:** {row['location']}")
            st.write(f"**Description:**\n{row['snippet']}")
            st.markdown(f"[📩 Apply Here]({row['url']})")


    # Download all results
    st.subheader("📥 Export Results")
    csv_data = df_sorted.to_csv(index=False)
    st.download_button(
        "Download CSV of Matches",
        csv_data,
        file_name="job_matches.csv",
        mime="text/csv",
    )


