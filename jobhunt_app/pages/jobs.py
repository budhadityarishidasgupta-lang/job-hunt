"""Streamlit jobs page with persistent job list and feedback tracking."""

from __future__ import annotations

import hashlib
from typing import List

import streamlit as st

from data_sources import collect_jobs
from feedback import save_feedback as persist_feedback
from utils import make_snippet

DEFAULT_KEYWORDS = "HR Director OR Head of HR"
DEFAULT_COUNTRIES = ["Germany", "Netherlands", "UK"]


def _job_id(job: dict, fallback: int) -> str:
    """Create a stable identifier for a job using URL or title/company."""
    if job.get("url"):
        return hashlib.md5(job["url"].encode("utf-8")).hexdigest()
    if job.get("title") and job.get("company"):
        key = f"{job['title']}::{job['company']}"
        return hashlib.md5(key.encode("utf-8")).hexdigest()
    return f"job-{fallback}"


def fetch_jobs(keywords: str, countries: List[str]):
    jobs = collect_jobs(keywords, countries)
    normalized = []
    for idx, job in enumerate(jobs):
        normalized.append(
            {
                "id": _job_id(job, idx),
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "location": job.get("location", ""),
                "url": job.get("url", ""),
                "source": job.get("source", ""),
                "snippet": make_snippet(job.get("description", ""), 320),
            }
        )
    return normalized


def render_feedback_state(job_id: str, value: str):
    if "feedback" not in st.session_state:
        st.session_state.feedback = {}
    st.session_state.feedback[job_id] = value


st.title("🎯 Curated HR Jobs")
st.write("Browse collected HR leadership roles and mark relevance.")

keywords = st.text_input("Search keywords", value=DEFAULT_KEYWORDS, key="keywords")
countries = st.multiselect(
    "Countries", DEFAULT_COUNTRIES, default=DEFAULT_COUNTRIES, key="countries"
)

if st.button("🔄 Refresh jobs"):
    st.session_state.jobs = fetch_jobs(keywords, countries)

# load once and keep persistent
if "jobs" not in st.session_state:
    st.session_state.jobs = fetch_jobs(keywords, countries)
jobs = st.session_state.jobs

if not jobs:
    st.info("No jobs loaded yet. Fetch to see listings.")

for job in jobs:
    with st.expander(f"{job['title']} — {job['company']}"):
        st.write(f"**Location:** {job['location']}")
        st.write(f"**Source:** {job['source']}")
        st.write(job["snippet"])
        if job["url"]:
            st.markdown(f"[Apply / View Posting]({job['url']})")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("👍", key=f"up_{job['id']}"):
                persist_feedback(job, 1)
                # record feedback but DO NOT remove or rebuild job list
                render_feedback_state(job["id"], "up")
                st.toast("Saved 👍")
        with col2:
            if st.button("👎", key=f"down_{job['id']}"):
                persist_feedback(job, -1)
                render_feedback_state(job["id"], "down")
                st.toast("Saved 👎")
